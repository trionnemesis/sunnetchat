import pytest
from langchain_core.documents import Document
from app.vector_store import build_vector_store

class FakeEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text))] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]

@pytest.fixture
def sample_documents():
    return [
        Document(page_content="LangChain is a framework for developing applications powered by language models.", metadata={"source": "doc1.txt"}),
        Document(page_content="The quick brown fox jumps over the lazy dog.", metadata={"source": "doc2.txt"}),
    ]

def test_build_vector_store_and_retrieval(sample_documents):
    """
    Tests the creation of a vector store and the retrieval of relevant documents.
    """
    fake_embedder = FakeEmbeddings()
    vector_store = build_vector_store(documents=sample_documents, embedding_model=fake_embedder)
    
    assert vector_store is not None, "Vector store should be created."
    
    retriever = vector_store.as_retriever()
    
    # Test retrieval
    # With our FakeEmbeddings, documents/queries with similar lengths will match.
    # The new query length is closer to the LangChain doc length (79) than the fox doc length (43).
    query = "I want to learn about a framework for AI applications that uses language models."
    
    retrieved_docs = retriever.invoke(query)
    
    assert len(retrieved_docs) > 0, "Should retrieve at least one document."
    assert "LangChain" in retrieved_docs[0].page_content