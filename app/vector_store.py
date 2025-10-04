from typing import List
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_vector_store(
    documents: List[Document], embedding_model: Embeddings
) -> VectorStore:
    """
    Builds a vector store from a list of documents.

    Args:
        documents: A list of Document objects to be added to the vector store.
        embedding_model: The embedding model to use for vectorizing the
            documents.

    Returns:
        A VectorStore object containing the vectorized documents.
    """
    # 1. Split documents into smaller chunks for better retrieval accuracy
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    all_splits = text_splitter.split_documents(documents)

    # 2. Create the vector store from the chunks using Chroma DB.
    # This will run in-memory by default.
    vector_store = Chroma.from_documents(
        documents=all_splits, embedding=embedding_model
    )

    return vector_store
