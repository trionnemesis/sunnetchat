import os
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredFileLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import chromadb

# --- Configuration ---
SOURCE_DIRECTORY = os.getenv("SOURCE_DOCS_PATH", "/app/local_documents")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")
COLLECTION_NAME = "internal_sop"


def main():
    print(f"Starting ingestion from: {SOURCE_DIRECTORY}")

    # 1. Load Documents
    # Use DirectoryLoader with UnstructuredFileLoader for various file types
    loader = DirectoryLoader(
        SOURCE_DIRECTORY,
        glob="**/*.*",
        use_multithreading=True,
        show_progress=True,
        loader_cls=lambda path: UnstructuredFileLoader(path),
    )
    docs = loader.load()

    if not docs:
        print("No documents found. Exiting.")
        return

    print(f"Loaded {len(docs)} documents.")

    # 2. Split Documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    print(f"Split into {len(splits)} chunks.")

    # 3. Create Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # 4. Store in ChromaDB
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    # Ensure collection exists
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(name=COLLECTION_NAME)

    print(f"Creating new collection: {COLLECTION_NAME}")
    collection = client.create_collection(name=COLLECTION_NAME)

    # Add documents in batches
    batch_size = 100
    for i in range(0, len(splits), batch_size):
        batch_splits = splits[i:i + batch_size]
        batch_texts = [split.page_content for split in batch_splits]
        batch_metadatas = [split.metadata for split in batch_splits]
        batch_ids = [f"doc_{i + j}" for j in range(len(batch_splits))]

        collection.add(
            documents=batch_texts,
            metadatas=batch_metadatas,
            ids=batch_ids,
            embeddings=embeddings.embed_documents(batch_texts),
        )
        print(f"Added batch {i // batch_size + 1} to ChromaDB.")

    print("--- Ingestion Complete ---")


if __name__ == "__main__":
    main()
