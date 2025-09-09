import os
import json
from datetime import datetime
from typing import List, TypedDict

from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import END, StateGraph

# --- Google Drive Utilities ---
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import io

# --- Configuration ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")
COLLECTION_NAME = "internal_sop"
LLM_MODEL = "llama3"
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_CREDS_PATH = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")

# --- Initialize Models, Tools, and Vectorstore ---
llm = ChatOllama(model=LLM_MODEL, format="json", temperature=0)
str_llm = ChatOllama(model=LLM_MODEL, temperature=0) # For string outputs
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vectorstore = Chroma(
    client=chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT),
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
)
retriever = vectorstore.as_retriever()
web_search_tool = TavilySearchResults(max_results=3)

# --- Graph State Definition ---
class GraphState(TypedDict):
    question: str
    generation: str
    documents: List[Document]
    web_search_results: str

# --- Google Drive Helper Function ---
def save_to_google_drive(filename: str, content: str):
    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDS_PATH, scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': filename,
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }
        
        media = MediaFileUpload(io.BytesIO(content.encode('utf-8')), mimetype='text/plain', resumable=True)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"---SUCCESS: Saved to Google Drive with File ID: {file.get('id')}---")
        return f"Saved to Google Drive with File ID: {file.get('id')}"
    except Exception as e:
        print(f"---ERROR: Failed to save to Google Drive: {e}---")
        return f"Error saving to Google Drive: {e}"

# --- Nodes of the Graph ---
def retrieve(state):
    # ... (same as before)
    print("---RETRIEVE---")
    question = state["question"]
    documents = retriever.get_relevant_documents(question)
    return {"documents": documents, "question": question}

def grade_documents(state):
    # ... (same as before)
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    
    prompt = PromptTemplate(
        template="Given the user's question and retrieved documents, classify if the documents are relevant to answer the question. 
        Provide a binary score 'yes' or 'no' in JSON format. Question: {question} \n\n Documents: {documents} ",
        input_variables=["question", "documents"],
    )
    chain = prompt | llm | JsonOutputParser()
    try:
        score = chain.invoke({"question": question, "documents": documents})
        grade = score['score']
    except Exception:
        grade = "no" # Default to web search on error

    state["documents"] = documents
    if grade == "yes":
        print("---DECISION: DOCUMENTS ARE RELEVANT---")
        return {"web_search_results": ""}
    else:
        print("---DECISION: DOCUMENTS ARE NOT RELEVANT, WEB SEARCH NEEDED---")
        return {"web_search_results": "needs_search"}

def web_search(state):
    print("---WEB SEARCH---")
    question = state["question"]
    search_results = web_search_tool.invoke({"query": question})
    return {"web_search_results": search_results}

def generate(state):
    print("---GENERATE FROM INTERNAL DOCS---")
    # ... (same as before)
    question = state["question"]
    documents = state["documents"]
    prompt = PromptTemplate(
        template="You are an assistant for question-answering tasks. Use the following retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise. 
        Question: {question} \n\n Context: {context} \n\n Answer:" ,
        input_variables=["question", "context"],
    )
    chain = prompt | str_llm | StrOutputParser()
    generation = chain.invoke({"context": documents, "question": question})
    return {"generation": generation}

def generate_and_store(state):
    print("---GENERATE FROM WEB AND STORE---")
    question = state["question"]
    search_results = state["web_search_results"]
    
    prompt = PromptTemplate(
        template="""You are a training assistant. Based on the following web search results, write a clear, step-by-step answer to the user's question. 
        Include the source URLs in your answer. Question: {question} \n\n Web Results: {context} """ ,
        input_variables=["question", "context"],
    )
    chain = prompt | str_llm | StrOutputParser()
    generation = chain.invoke({"context": search_results, "question": question})
    
    # Save the generated knowledge to Google Drive
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SOP_{question[:30].replace(' ', '_')}_{timestamp}.txt"
    drive_content = f"Question: {question}\n\nAnswer:\n{generation}\n\nSource: Web Search"
    save_to_google_drive(filename, drive_content)
    
    return {"generation": generation}

# --- Conditional Edges ---
def decide_to_generate(state):
    print("---ASSESS GRADED DOCUMENTS---")
    if not state.get("web_search_results"):
        return "generate_internal"
    else:
        return "web_search"

# --- Build the Graph ---
workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("web_search", web_search)
workflow.add_node("generate", generate)
workflow.add_node("generate_and_store", generate_and_store)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "generate_internal": "generate",
        "web_search": "web_search",
    },
)
workflow.add_edge("web_search", "generate_and_store")
workflow.add_edge("generate", END)
workflow.add_edge("generate_and_store", END)

graph = workflow.compile()