"""
Legacy tests updated to use the new core agent
Maintains backward compatibility while using the unified architecture
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestLegacyCompatibility:
    """Test backward compatibility with old graph_flow interface"""

    @patch("app.core_agent.GoogleGenerativeAIEmbeddings")
    @patch("app.core_agent.chromadb.HttpClient")
    @patch("app.core_agent.Chroma")
    @patch("app.core_agent.ChatOllama")
    @patch("app.core_agent.TavilySearchResults")
    @patch("app.core_agent.upload_qa_to_drive")
    def test_agent_local_path(
        self,
        mock_upload,
        mock_tavily,
        mock_ollama,
        mock_chroma,
        mock_http_client,
        mock_embeddings,
    ):
        """Tests the agent path when local documents are graded as relevant."""

        # Mock all the components
        mock_embeddings.return_value = MagicMock()
        mock_http_client.return_value = MagicMock()
        mock_vectorstore = MagicMock()
        mock_chroma.return_value = mock_vectorstore

        # Mock retriever
        mock_retriever = MagicMock()
        mock_retriever.get_relevant_documents.return_value = ["本地文件內容"]
        mock_vectorstore.as_retriever.return_value = mock_retriever

        # Mock LLMs
        mock_json_llm = MagicMock()
        mock_json_llm.invoke = AsyncMock(return_value={"score": "yes"})

        mock_text_llm = MagicMock()
        mock_text_llm.invoke = AsyncMock(return_value="從本地文件生成的答案")

        mock_ollama.side_effect = [mock_json_llm, mock_text_llm]

        mock_tavily.return_value = MagicMock()

        # Import and test the agent
        from app.agent import graph

        # Mock the core agent methods
        with patch.object(graph._agent, "llm_json", mock_json_llm), patch.object(
            graph._agent, "llm_text", mock_text_llm
        ), patch.object(graph._agent, "retriever", mock_retriever):

            # Test using the compatibility interface
            inputs = {"question": "test"}
            result = graph.invoke(inputs)

            # Assertions
            assert result["generation"] == "從本地文件生成的答案"
            # Upload should not be called for vectorstore results
            mock_upload.assert_not_called()

    @patch("app.core_agent.GoogleGenerativeAIEmbeddings")
    @patch("app.core_agent.chromadb.HttpClient")
    @patch("app.core_agent.Chroma")
    @patch("app.core_agent.ChatOllama")
    @patch("app.core_agent.TavilySearchResults")
    @patch("app.core_agent.upload_qa_to_drive")
    def test_agent_web_search_path(
        self,
        mock_upload,
        mock_tavily,
        mock_ollama,
        mock_chroma,
        mock_http_client,
        mock_embeddings,
    ):
        """Tests the agent path when local documents are graded as irrelevant."""

        # Mock all the components
        mock_embeddings.return_value = MagicMock()
        mock_http_client.return_value = MagicMock()
        mock_vectorstore = MagicMock()
        mock_chroma.return_value = mock_vectorstore

        # Mock retriever
        mock_retriever = MagicMock()
        mock_retriever.get_relevant_documents.return_value = ["文件內容"]
        mock_vectorstore.as_retriever.return_value = mock_retriever

        # Mock LLMs - grader returns 'no' to trigger web search
        mock_json_llm = MagicMock()
        mock_json_llm.invoke = AsyncMock(return_value={"score": "no"})

        mock_text_llm = MagicMock()
        mock_text_llm.invoke = AsyncMock(return_value="從網路搜尋生成的答案")

        mock_ollama.side_effect = [mock_json_llm, mock_text_llm]

        # Mock web search tool
        mock_web_search = MagicMock()
        mock_web_search.invoke = AsyncMock(return_value=["網路搜尋結果"])
        mock_tavily.return_value = mock_web_search

        # Import and test the agent
        from app.agent import graph

        # Mock the core agent methods
        with patch.object(graph._agent, "llm_json", mock_json_llm), patch.object(
            graph._agent, "llm_text", mock_text_llm
        ), patch.object(graph._agent, "retriever", mock_retriever), patch.object(
            graph._agent, "web_search_tool", mock_web_search
        ):

            # Test using the compatibility interface
            inputs = {"question": "test"}
            result = graph.invoke(inputs)

            # Assertions
            assert result["generation"] == "從網路搜尋生成的答案"
            # Web search should have been called
            mock_web_search.invoke.assert_called()

    @patch("app.core_agent.get_agent")
    @pytest.mark.asyncio
    async def test_agent_async_interface(self, mock_get_agent):
        """Test the async interface of the compatibility layer"""

        # Mock the agent
        mock_agent = MagicMock()
        mock_agent.process_question = AsyncMock(
            return_value={"generation": "Async answer", "status": "completed"}
        )
        mock_get_agent.return_value = mock_agent

        # Import and test
        from app.agent import graph

        # Test async stream interface
        inputs = {"question": "async test"}
        async for output in graph.astream(inputs):
            assert "agent" in output
            result = output["agent"]
            assert result["generation"] == "Async answer"

    def test_legacy_functions(self):
        """Test the legacy get_answer functions"""
        with patch("app.core_agent.get_agent") as mock_get_agent:
            # Mock the agent
            mock_agent = MagicMock()
            mock_agent.process_question = AsyncMock(
                return_value={"generation": "Legacy answer", "status": "completed"}
            )
            mock_get_agent.return_value = mock_agent

            # Test sync function
            from app.agent import get_answer

            result = get_answer("legacy test")
            assert result == "Legacy answer"

    @pytest.mark.asyncio
    async def test_legacy_async_functions(self):
        """Test the legacy async get_answer functions"""
        with patch("app.core_agent.get_agent") as mock_get_agent:
            # Mock the agent
            mock_agent = MagicMock()
            mock_agent.process_question = AsyncMock(
                return_value={
                    "generation": "Legacy async answer",
                    "status": "completed",
                }
            )
            mock_get_agent.return_value = mock_agent

            # Test async function
            from app.agent import get_answer_async

            result = await get_answer_async("legacy async test")
            assert result == "Legacy async answer"


if __name__ == "__main__":
    pytest.main([__file__])
