import os
from typing import List, Dict, TypedDict
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END

from .rag_core import retriever # Re-use the retriever from our simple RAG
from .gdrive_utils import upload_qa_to_drive

# --- Environment and Tools --- 
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

web_search_tool = TavilySearchResults(k=3, tavily_api_key=TAVILY_API_KEY)
llm = ChatOllama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, format="json")
generation_llm = ChatOllama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)

# --- Graph State --- 
class GraphState(TypedDict):
    question: str
    documents: List[str]
    generation: str
    source: str # To track if the answer came from 'vectorstore' or 'web_search'

# --- Nodes --- 

def retrieve(state):
    print("---NODE: RETRIEVE---")
    question = state["question"]
    documents = retriever.get_relevant_documents(question)
    return {"documents": documents, "question": question, "source": "vectorstore"}

def grade_documents(state):
    print("---NODE: GRADE DOCUMENTS---")
    question = state["question"]
    documents = state["documents"]
    
    prompt = ChatPromptTemplate.from_template(
        """您是一位資訊分級助理。您的任務是評估檢索到的文件是否與使用者的問題相關。
        只需回答 'yes' 或 'no'。您的答案必須是 JSON 格式，鍵為 'score'。
        
        檢索到的文件:
        {documents}
        
        使用者問題: {question}"""
    )
    grader = prompt | llm | JsonOutputParser()
    result = grader.invoke({"documents": documents, "question": question})
    grade = result['score']
    
    if grade.lower() == "yes":
        print("---DECISION: Documents are relevant---")
        return {"documents": documents}
    else:
        print("---DECISION: Documents are NOT relevant, proceeding to web search---")
        return {"documents": []} # Clear documents to signal web search

def web_search(state):
    print("---NODE: WEB SEARCH---")
    question = state["question"]
    documents = web_search_tool.invoke({"query": question})
    return {"documents": documents, "source": "web_search"}

def generate(state):
    print("---NODE: GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    prompt = ChatPromptTemplate.from_template(
        """基於以下提供的上下文來回答問題。
        盡量讓答案簡潔，並使用繁體中文回答。
        
        上下文:
        {context}
        
        問題:
        {question}
        
        有用的回答:"""
    )
    chain = prompt | generation_llm | StrOutputParser()
    generation = chain.invoke({"context": documents, "question": question})
    return {"generation": generation}

def save_to_drive(state):
    print("---NODE: SAVE TO DRIVE---")
    if state["source"] == "web_search":
        print("---Source was web search, saving to Google Drive---")
        upload_qa_to_drive(state["question"], state["generation"])
    else:
        print("---Source was vectorstore, skipping save---")
    return

# --- Graph Edges --- 

def decide_to_generate(state):
    return "generate" if state["documents"] else "web_search"

# --- Build Graph --- 
workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("web_search", web_search)
workflow.add_node("generate", generate)
workflow.add_node("save_to_drive", save_to_drive)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {"web_search": "web_search", "generate": "generate"}
)
workflow.add_edge("web_search", "generate")
workflow.add_edge("generate", "save_to_drive")
workflow.add_edge("save_to_drive", END)

app_graph = workflow.compile()

def get_answer_from_graph(question: str) -> str:
    """Invokes the graph with a question and returns the final generation."""
    inputs = {"question": question}
    result = app_graph.invoke(inputs)
    return result.get("generation", "抱歉，我無法找到答案。")

if __name__ == '__main__':
    question = "什麼是 agent memory?"
    print(f"Question: {question}")
    answer = get_answer_from_graph(question)
    print(f"Answer: {answer}")
