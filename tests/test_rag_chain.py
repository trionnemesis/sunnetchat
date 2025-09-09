import pytest
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.language_models.llms import LLM
from typing import Any, List, Mapping, Optional

from app.vector_store import build_vector_store
from app.rag_chain import create_rag_chain  # This will fail initially

# --- Mocks and Fixtures ---


class FakeEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text))] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]


class FakeLLM(LLM):
    """Fake LLM for testing purposes."""

    def _call(
        self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any
    ) -> str:
        if "LangChain" in prompt:
            return "The answer is about LangChain."
        return "I don't know."

    @property
    def _llm_type(self) -> str:
        return "fake"


@pytest.fixture
def sample_retriever():
    """Creates a simple retriever from a vector store."""
    docs = [
        Document(
            page_content="LangChain is a framework for developing applications powered by language models.",
            metadata={"source": "doc1.txt"},
        ),
    ]
    embedder = FakeEmbeddings()
    vector_store = build_vector_store(documents=docs, embedding_model=embedder)
    return vector_store.as_retriever()


# --- Test ---


def test_create_and_invoke_rag_chain(sample_retriever):
    """
    Tests the creation and invocation of the full RAG chain.
    """
    fake_llm = FakeLLM()

    # This function will create the runnable RAG chain
    rag_chain = create_rag_chain(retriever=sample_retriever, llm=fake_llm)

    # The query is designed to retrieve the LangChain document
    query = "Tell me about that framework for AI apps."

    result = rag_chain.invoke(query)

    assert isinstance(result, str)
    assert "The answer is about LangChain." in result
