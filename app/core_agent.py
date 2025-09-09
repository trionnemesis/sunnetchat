"""
Unified Core Agent - Consolidates all agent functionality
Handles RAG, web search, document grading, and Google Drive integration
with comprehensive async support and error handling.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, TypedDict, Optional, Any
from enum import Enum
import logging

from langchain.schema import Document
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import END, StateGraph

from .gdrive_utils import upload_qa_to_drive

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration
class Config:
    """Centralized configuration management"""

    # Vector Store
    CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
    CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")
    CHROMA_DB_PATH = os.getenv("VECTOR_DB_PATH", "chroma_db")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "internal_sop")

    # LLM Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

    # Embeddings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/embedding-001")

    # External Services
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    GOOGLE_CREDS_PATH = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")

    # Agent Settings
    LANGUAGE = os.getenv("AGENT_LANGUAGE", "zh-TW")  # zh-TW or en
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))
    WEB_SEARCH_RESULTS = int(os.getenv("WEB_SEARCH_RESULTS", "3"))


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class AgentError(Exception):
    """Custom exception for agent errors"""

    def __init__(self, message: str, error_code: str = None, retry_count: int = 0):
        self.message = message
        self.error_code = error_code
        self.retry_count = retry_count
        super().__init__(self.message)


# State Management
class GraphState(TypedDict):
    """Enhanced graph state with error handling and progress tracking"""

    question: str
    documents: List[Document]
    web_search_results: Optional[str]
    generation: str
    source: str  # 'vectorstore' or 'web_search'
    status: TaskStatus
    error_message: Optional[str]
    retry_count: int
    progress: Dict[str, Any]


# Prompt Templates
class PromptTemplates:
    """Centralized prompt management with multi-language support"""

    @staticmethod
    def get_document_grader_prompt(language: str = "zh-TW") -> PromptTemplate:
        if language == "zh-TW":
            template = (
                "您是一位資訊分級助理。評估檢索到的文件是否與使用者問題相關。"
                '只需回答 \'yes\' 或 \'no\'，格式為 JSON: {"score": "yes"} 或 {"score": "no"}。'
                "\n\n問題: {question}\n\n文件: {documents}"
            )
        else:
            template = (
                "You are a document grader. Assess if retrieved documents are relevant to the user's question. "
                'Provide a binary score \'yes\' or \'no\' in JSON format: {"score": "yes"} or {"score": "no"}.'
                "\n\nQuestion: {question}\n\nDocuments: {documents}"
            )

        return PromptTemplate(
            template=template, input_variables=["question", "documents"]
        )

    @staticmethod
    def get_generation_prompt(language: str = "zh-TW") -> PromptTemplate:
        if language == "zh-TW":
            template = (
                "基於以下提供的上下文來回答問題。如果不知道答案，請說不知道，不要編造。"
                "盡量讓答案簡潔，使用繁體中文回答。最多三句話。"
                "\n\n問題: {question}\n\n上下文: {context}\n\n回答:"
            )
        else:
            template = (
                "Use the following retrieved context to answer the question. "
                "If you don't know the answer, say you don't know. Use three sentences maximum."
                "\n\nQuestion: {question}\n\nContext: {context}\n\nAnswer:"
            )

        return PromptTemplate(
            template=template, input_variables=["question", "context"]
        )

    @staticmethod
    def get_web_generation_prompt(language: str = "zh-TW") -> PromptTemplate:
        if language == "zh-TW":
            template = (
                "您是一位訓練助理。基於網路搜尋結果，為使用者問題提供清楚的分步回答。"
                "請在答案中包含來源網址。使用繁體中文回答。"
                "\n\n問題: {question}\n\n網路搜尋結果: {context}"
            )
        else:
            template = (
                "You are a training assistant. Based on web search results, provide a clear, "
                "step-by-step answer to the user's question. Include source URLs in your answer."
                "\n\nQuestion: {question}\n\nWeb Results: {context}"
            )

        return PromptTemplate(
            template=template, input_variables=["question", "context"]
        )


# Core Agent Components
class CoreAgent:
    """Unified agent with async support and comprehensive error handling"""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._initialize_components()
        self._build_graph()

    def _initialize_components(self):
        """Initialize all agent components"""
        try:
            # Initialize embeddings
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=self.config.EMBEDDING_MODEL
            )

            # Initialize vector store with fallback
            try:
                # Try HTTP client first (for Docker)
                self.vectorstore = Chroma(
                    client=chromadb.HttpClient(
                        host=self.config.CHROMA_HOST, port=self.config.CHROMA_PORT
                    ),
                    collection_name=self.config.COLLECTION_NAME,
                    embedding_function=self.embeddings,
                )
            except Exception:
                # Fallback to local directory
                logger.warning("HTTP client failed, using local directory")
                self.vectorstore = Chroma(
                    persist_directory=self.config.CHROMA_DB_PATH,
                    collection_name=self.config.COLLECTION_NAME,
                    embedding_function=self.embeddings,
                )

            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

            # Initialize LLMs
            self.llm_json = ChatOllama(
                base_url=self.config.OLLAMA_BASE_URL,
                model=self.config.OLLAMA_MODEL,
                format="json",
                temperature=0,
            )

            self.llm_text = ChatOllama(
                base_url=self.config.OLLAMA_BASE_URL,
                model=self.config.OLLAMA_MODEL,
                temperature=0,
            )

            # Initialize web search tool
            if self.config.TAVILY_API_KEY:
                self.web_search_tool = TavilySearchResults(
                    k=self.config.WEB_SEARCH_RESULTS,
                    tavily_api_key=self.config.TAVILY_API_KEY,
                )
            else:
                logger.warning("TAVILY_API_KEY not found, web search disabled")
                self.web_search_tool = None

            # Initialize prompt templates
            self.prompts = PromptTemplates()

            logger.info("Agent components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize agent components: {e}")
            raise AgentError(f"Initialization failed: {e}", "INIT_ERROR")

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry mechanism with exponential backoff"""
        last_error = None

        for attempt in range(self.config.MAX_RETRIES):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.config.MAX_RETRIES - 1:
                    delay = self.config.RETRY_DELAY * (2**attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.MAX_RETRIES} attempts failed")

        raise AgentError(
            f"Max retries exceeded: {last_error}",
            "MAX_RETRIES",
            self.config.MAX_RETRIES,
        )

    # Graph Nodes
    async def retrieve_documents(self, state: GraphState) -> Dict[str, Any]:
        """Retrieve relevant documents from vector store"""
        logger.info("---NODE: RETRIEVE DOCUMENTS---")

        try:
            question = state["question"]

            documents = await self._retry_with_backoff(
                self.retriever.get_relevant_documents, question
            )

            logger.info(f"Retrieved {len(documents)} documents")

            return {
                "documents": documents,
                "source": "vectorstore",
                "status": TaskStatus.RUNNING,
                "progress": {"step": "documents_retrieved", "count": len(documents)},
            }

        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return {
                "documents": [],
                "status": TaskStatus.FAILED,
                "error_message": f"Document retrieval failed: {e}",
            }

    async def grade_documents(self, state: GraphState) -> Dict[str, Any]:
        """Grade document relevance to question"""
        logger.info("---NODE: GRADE DOCUMENTS---")

        try:
            question = state["question"]
            documents = state["documents"]

            if not documents:
                logger.info("No documents to grade, proceeding to web search")
                return {"documents": [], "status": TaskStatus.RUNNING}

            prompt = self.prompts.get_document_grader_prompt(self.config.LANGUAGE)
            chain = prompt | self.llm_json | JsonOutputParser()

            result = await self._retry_with_backoff(
                chain.invoke, {"question": question, "documents": documents}
            )

            grade = result.get("score", "no").lower()

            if grade == "yes":
                logger.info("---DECISION: Documents are relevant---")
                return {
                    "documents": documents,
                    "status": TaskStatus.RUNNING,
                    "progress": {"step": "documents_graded", "grade": "relevant"},
                }
            else:
                logger.info("---DECISION: Documents not relevant, need web search---")
                return {
                    "documents": [],
                    "status": TaskStatus.RUNNING,
                    "progress": {"step": "documents_graded", "grade": "not_relevant"},
                }

        except Exception as e:
            logger.error(f"Document grading failed: {e}")
            # Default to web search on grading failure
            return {
                "documents": [],
                "status": TaskStatus.RUNNING,
                "error_message": f"Document grading failed: {e}, proceeding to web search",
            }

    async def web_search(self, state: GraphState) -> Dict[str, Any]:
        """Perform web search for questions"""
        logger.info("---NODE: WEB SEARCH---")

        try:
            if not self.web_search_tool:
                raise AgentError("Web search tool not available", "WEB_SEARCH_DISABLED")

            question = state["question"]

            search_results = await self._retry_with_backoff(
                self.web_search_tool.invoke, {"query": question}
            )

            logger.info(f"Web search completed with {len(search_results)} results")

            return {
                "web_search_results": search_results,
                "source": "web_search",
                "status": TaskStatus.RUNNING,
                "progress": {
                    "step": "web_search_completed",
                    "results_count": len(search_results),
                },
            }

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {
                "web_search_results": None,
                "status": TaskStatus.FAILED,
                "error_message": f"Web search failed: {e}",
            }

    async def generate_answer(self, state: GraphState) -> Dict[str, Any]:
        """Generate answer from documents or web search results"""
        logger.info("---NODE: GENERATE ANSWER---")

        try:
            question = state["question"]
            source = state.get("source", "vectorstore")

            if source == "web_search":
                context = state.get("web_search_results", "")
                prompt = self.prompts.get_web_generation_prompt(self.config.LANGUAGE)
            else:
                context = state.get("documents", [])
                prompt = self.prompts.get_generation_prompt(self.config.LANGUAGE)

            chain = prompt | self.llm_text | StrOutputParser()

            generation = await self._retry_with_backoff(
                chain.invoke, {"context": context, "question": question}
            )

            logger.info("Answer generation completed")

            return {
                "generation": generation,
                "status": TaskStatus.RUNNING,
                "progress": {"step": "answer_generated", "source": source},
            }

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            fallback_message = (
                "抱歉，我在處理您的問題時遇到了錯誤。"
                if self.config.LANGUAGE == "zh-TW"
                else "Sorry, I encountered an error processing your question."
            )

            return {
                "generation": fallback_message,
                "status": TaskStatus.FAILED,
                "error_message": f"Answer generation failed: {e}",
            }

    async def save_knowledge(self, state: GraphState) -> Dict[str, Any]:
        """Save new knowledge to Google Drive if from web search"""
        logger.info("---NODE: SAVE KNOWLEDGE---")

        try:
            source = state.get("source")

            if source == "web_search" and state.get("generation"):
                question = state["question"]
                answer = state["generation"]

                # Save to Google Drive in background
                asyncio.create_task(self._save_to_drive_async(question, answer))

                logger.info("Knowledge save initiated (background task)")

            return {
                "status": TaskStatus.COMPLETED,
                "progress": {
                    "step": "knowledge_saved",
                    "saved": source == "web_search",
                },
            }

        except Exception as e:
            logger.error(f"Knowledge save failed: {e}")
            return {
                "status": TaskStatus.COMPLETED,  # Don't fail the whole process
                "error_message": f"Knowledge save failed: {e}",
            }

    async def _save_to_drive_async(self, question: str, answer: str):
        """Async wrapper for Google Drive save"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SOP_{question[:30].replace(' ', '_')}_{timestamp}.txt"
            content = f"Question: {question}\n\nAnswer:\n{answer}\n\nSource: Web Search"

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, upload_qa_to_drive, question, answer)

            logger.info(f"Successfully saved knowledge to Google Drive: {filename}")

        except Exception as e:
            logger.error(f"Background save to Google Drive failed: {e}")

    # Graph Edges
    def decide_to_generate(self, state: GraphState) -> str:
        """Decide whether to generate from documents or search web"""
        documents = state.get("documents", [])
        if documents:
            return "generate_from_docs"
        else:
            return "web_search"

    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("retrieve", self.retrieve_documents)
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("web_search", self.web_search)
        workflow.add_node("generate_from_docs", self.generate_answer)
        workflow.add_node("generate_from_web", self.generate_answer)
        workflow.add_node("save_knowledge", self.save_knowledge)

        # Set entry point
        workflow.set_entry_point("retrieve")

        # Add edges
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "generate_from_docs": "generate_from_docs",
                "web_search": "web_search",
            },
        )
        workflow.add_edge("web_search", "generate_from_web")
        workflow.add_edge("generate_from_docs", "save_knowledge")
        workflow.add_edge("generate_from_web", "save_knowledge")
        workflow.add_edge("save_knowledge", END)

        # Compile graph
        self.graph = workflow.compile()
        logger.info("Agent graph compiled successfully")

    async def process_question(self, question: str) -> Dict[str, Any]:
        """Main entry point for processing questions"""
        logger.info(f"Processing question: {question}")

        initial_state = {
            "question": question,
            "documents": [],
            "web_search_results": None,
            "generation": "",
            "source": "",
            "status": TaskStatus.PENDING,
            "error_message": None,
            "retry_count": 0,
            "progress": {"step": "initialized"},
        }

        try:
            final_state = None
            async for output in self.graph.astream(initial_state):
                for key, value in output.items():
                    logger.info(f"Node '{key}' completed")
                    final_state = value

            return final_state

        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            return {
                **initial_state,
                "status": TaskStatus.FAILED,
                "error_message": f"Graph execution failed: {e}",
                "generation": (
                    "處理您的問題時發生錯誤。"
                    if self.config.LANGUAGE == "zh-TW"
                    else "An error occurred while processing your question."
                ),
            }


# Global agent instance
_agent_instance = None


def get_agent() -> CoreAgent:
    """Get singleton agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CoreAgent()
    return _agent_instance


# Backward compatibility
async def process_question(question: str) -> str:
    """Process a question and return the answer (backward compatibility)"""
    agent = get_agent()
    result = await agent.process_question(question)
    return result.get("generation", "Sorry, I couldn't process your question.")
