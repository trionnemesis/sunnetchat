import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# Load environment variables
load_dotenv()

# Get configuration from environment variables
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

# --- RAG Chain Components ---

# 1. Vector Store Retriever
vectorstore = Chroma(
    persist_directory=VECTOR_DB_PATH, 
    embedding_function=GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 2. Prompt Template
# This template is crucial for guiding the LLM. It's designed for Traditional Chinese.
TEMPLATE = """基於以下提供的上下文來回答問題。
如果你不知道答案，就說你不知道，不要試圖編造答案。
盡量讓答案簡潔，並使用繁體中文回答。

上下文:
{context}

問題:
{question}

有用的回答:"""

prompt = ChatPromptTemplate.from_template(TEMPLATE)

# 3. LLM Model
llm = ChatOllama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)

# --- RAG Chain Assembly ---

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def get_answer(question: str) -> str:
    """
    Invokes the RAG chain with a question and returns the answer.
    """
    if not os.path.exists(VECTOR_DB_PATH):
        return "錯誤：向量資料庫不存在。請先執行 `scripts/ingest.py` 來建立資料庫。"
    
    print(f"Invoking RAG chain for question: {question}")
    response = rag_chain.invoke(question)
    return response

# Example usage (for direct testing)
if __name__ == '__main__':
    print("--- RAG Core Test ---")
    # Make sure the vector database exists before running this test.
    test_question = "什麼是 LangChain?"
    answer = get_answer(test_question)
    print(f"Question: {test_question}")
    print(f"Answer: {answer}")
