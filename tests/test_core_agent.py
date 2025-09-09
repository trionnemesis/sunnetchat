"""
Tests for the unified core agent functionality
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.core_agent import CoreAgent, Config, TaskStatus, AgentError


class TestCoreAgent:
    """Test suite for CoreAgent"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        config = Config()
        config.TAVILY_API_KEY = "test_api_key"
        config.LANGUAGE = "zh-TW"
        config.MAX_RETRIES = 2
        config.RETRY_DELAY = 0.1
        return config

    @pytest.fixture
    @patch("app.core_agent.GoogleGenerativeAIEmbeddings")
    @patch("app.core_agent.chromadb.HttpClient")
    @patch("app.core_agent.Chroma")
    @patch("app.core_agent.ChatOllama")
    @patch("app.core_agent.TavilySearchResults")
    def mock_agent(
        self,
        mock_tavily,
        mock_ollama,
        mock_chroma,
        mock_http_client,
        mock_embeddings,
        mock_config,
    ):
        """Create a mock agent with all dependencies mocked"""

        # Mock the components
        mock_embeddings.return_value = MagicMock()
        mock_http_client.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()
        mock_ollama.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        # Create agent
        agent = CoreAgent(mock_config)

        # Mock the retriever
        agent.retriever = MagicMock()
        agent.retriever.get_relevant_documents = AsyncMock()

        return agent

    @pytest.mark.asyncio
    async def test_document_retrieval_success(self, mock_agent):
        """Test successful document retrieval"""
        # Setup
        mock_documents = [MagicMock(), MagicMock()]
        mock_agent.retriever.get_relevant_documents.return_value = mock_documents

        state = {"question": "test question"}

        # Execute
        result = await mock_agent.retrieve_documents(state)

        # Assert
        assert result["documents"] == mock_documents
        assert result["source"] == "vectorstore"
        assert result["status"] == TaskStatus.RUNNING
        assert "count" in result["progress"]

    @pytest.mark.asyncio
    async def test_document_retrieval_failure(self, mock_agent):
        """Test document retrieval failure handling"""
        # Setup
        mock_agent.retriever.get_relevant_documents.side_effect = Exception("DB Error")

        state = {"question": "test question"}

        # Execute
        result = await mock_agent.retrieve_documents(state)

        # Assert
        assert result["documents"] == []
        assert result["status"] == TaskStatus.FAILED
        assert "DB Error" in result["error_message"]

    @pytest.mark.asyncio
    async def test_document_grading_relevant(self, mock_agent):
        """Test document grading when documents are relevant"""
        # Setup
        mock_documents = [MagicMock()]
        mock_agent.llm_json.invoke = AsyncMock(return_value={"score": "yes"})

        state = {"question": "test question", "documents": mock_documents}

        # Execute
        result = await mock_agent.grade_documents(state)

        # Assert
        assert result["documents"] == mock_documents
        assert result["status"] == TaskStatus.RUNNING
        assert result["progress"]["grade"] == "relevant"

    @pytest.mark.asyncio
    async def test_document_grading_not_relevant(self, mock_agent):
        """Test document grading when documents are not relevant"""
        # Setup
        mock_documents = [MagicMock()]
        mock_agent.llm_json.invoke = AsyncMock(return_value={"score": "no"})

        state = {"question": "test question", "documents": mock_documents}

        # Execute
        result = await mock_agent.grade_documents(state)

        # Assert
        assert result["documents"] == []
        assert result["status"] == TaskStatus.RUNNING
        assert result["progress"]["grade"] == "not_relevant"

    @pytest.mark.asyncio
    async def test_web_search_success(self, mock_agent):
        """Test successful web search"""
        # Setup
        mock_results = ["result1", "result2", "result3"]
        mock_agent.web_search_tool.invoke = AsyncMock(return_value=mock_results)

        state = {"question": "test question"}

        # Execute
        result = await mock_agent.web_search(state)

        # Assert
        assert result["web_search_results"] == mock_results
        assert result["source"] == "web_search"
        assert result["status"] == TaskStatus.RUNNING
        assert result["progress"]["results_count"] == 3

    @pytest.mark.asyncio
    async def test_web_search_disabled(self, mock_agent):
        """Test web search when tool is disabled"""
        # Setup
        mock_agent.web_search_tool = None

        state = {"question": "test question"}

        # Execute
        result = await mock_agent.web_search(state)

        # Assert
        assert result["web_search_results"] is None
        assert result["status"] == TaskStatus.FAILED
        assert "not available" in result["error_message"]

    @pytest.mark.asyncio
    async def test_answer_generation_from_documents(self, mock_agent):
        """Test answer generation from documents"""
        # Setup
        mock_agent.llm_text.invoke = AsyncMock(return_value="Generated answer")

        state = {
            "question": "test question",
            "documents": ["doc1", "doc2"],
            "source": "vectorstore",
        }

        # Execute
        result = await mock_agent.generate_answer(state)

        # Assert
        assert result["generation"] == "Generated answer"
        assert result["status"] == TaskStatus.RUNNING
        assert result["progress"]["source"] == "vectorstore"

    @pytest.mark.asyncio
    async def test_answer_generation_from_web(self, mock_agent):
        """Test answer generation from web search results"""
        # Setup
        mock_agent.llm_text.invoke = AsyncMock(return_value="Web-based answer")

        state = {
            "question": "test question",
            "web_search_results": ["web1", "web2"],
            "source": "web_search",
        }

        # Execute
        result = await mock_agent.generate_answer(state)

        # Assert
        assert result["generation"] == "Web-based answer"
        assert result["status"] == TaskStatus.RUNNING
        assert result["progress"]["source"] == "web_search"

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, mock_agent):
        """Test the retry mechanism with exponential backoff"""

        # Setup - fail twice, then succeed
        async def failing_function():
            if hasattr(failing_function, "call_count"):
                failing_function.call_count += 1
            else:
                failing_function.call_count = 1

            if failing_function.call_count <= 2:
                raise Exception("Temporary error")
            return "Success"

        # Execute
        result = await mock_agent._retry_with_backoff(failing_function)

        # Assert
        assert result == "Success"
        assert failing_function.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, mock_agent):
        """Test retry mechanism when all attempts fail"""

        # Setup - always fail
        async def always_failing_function():
            raise Exception("Persistent error")

        # Execute & Assert
        with pytest.raises(AgentError) as exc_info:
            await mock_agent._retry_with_backoff(always_failing_function)

        assert "Max retries exceeded" in str(exc_info.value)
        assert exc_info.value.error_code == "MAX_RETRIES"

    @pytest.mark.asyncio
    @patch("app.core_agent.upload_qa_to_drive")
    async def test_knowledge_save_web_search(self, mock_upload, mock_agent):
        """Test knowledge saving for web search results"""
        # Setup
        mock_upload.return_value = None

        state = {
            "question": "test question",
            "generation": "test answer",
            "source": "web_search",
        }

        # Execute
        result = await mock_agent.save_knowledge(state)

        # Assert
        assert result["status"] == TaskStatus.COMPLETED
        assert result["progress"]["saved"] == True

        # Wait a bit for the background task
        await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_knowledge_save_vectorstore(self, mock_agent):
        """Test knowledge saving for vectorstore results (should skip)"""
        # Setup
        state = {
            "question": "test question",
            "generation": "test answer",
            "source": "vectorstore",
        }

        # Execute
        result = await mock_agent.save_knowledge(state)

        # Assert
        assert result["status"] == TaskStatus.COMPLETED
        assert result["progress"]["saved"] == False

    @pytest.mark.asyncio
    @patch("app.core_agent.CoreAgent.retrieve_documents")
    @patch("app.core_agent.CoreAgent.grade_documents")
    @patch("app.core_agent.CoreAgent.generate_answer")
    @patch("app.core_agent.CoreAgent.save_knowledge")
    async def test_full_process_question_flow(
        self, mock_save, mock_generate, mock_grade, mock_retrieve, mock_agent
    ):
        """Test the complete question processing flow"""
        # Setup mocks
        mock_retrieve.return_value = {
            "documents": ["doc1"],
            "status": TaskStatus.RUNNING,
            "progress": {"step": "retrieved"},
        }

        mock_grade.return_value = {
            "documents": ["doc1"],
            "status": TaskStatus.RUNNING,
            "progress": {"step": "graded", "grade": "relevant"},
        }

        mock_generate.return_value = {
            "generation": "Final answer",
            "status": TaskStatus.RUNNING,
            "progress": {"step": "generated"},
        }

        mock_save.return_value = {
            "status": TaskStatus.COMPLETED,
            "progress": {"step": "saved"},
        }

        # Execute
        result = await mock_agent.process_question("test question")

        # Assert
        assert "generation" in result
        assert result["status"] == TaskStatus.COMPLETED


class TestPromptTemplates:
    """Test prompt template generation"""

    def test_document_grader_prompt_chinese(self):
        """Test Chinese document grader prompt"""
        from app.core_agent import PromptTemplates

        prompt = PromptTemplates.get_document_grader_prompt("zh-TW")

        assert "資訊分級助理" in prompt.template
        assert "{question}" in prompt.template
        assert "{documents}" in prompt.template

    def test_document_grader_prompt_english(self):
        """Test English document grader prompt"""
        from app.core_agent import PromptTemplates

        prompt = PromptTemplates.get_document_grader_prompt("en")

        assert "document grader" in prompt.template
        assert "{question}" in prompt.template
        assert "{documents}" in prompt.template

    def test_generation_prompt_chinese(self):
        """Test Chinese generation prompt"""
        from app.core_agent import PromptTemplates

        prompt = PromptTemplates.get_generation_prompt("zh-TW")

        assert "繁體中文" in prompt.template
        assert "{question}" in prompt.template
        assert "{context}" in prompt.template

    def test_generation_prompt_english(self):
        """Test English generation prompt"""
        from app.core_agent import PromptTemplates

        prompt = PromptTemplates.get_generation_prompt("en")

        assert "retrieved context" in prompt.template
        assert "{question}" in prompt.template
        assert "{context}" in prompt.template


class TestConfig:
    """Test configuration management"""

    def test_config_defaults(self):
        """Test configuration default values"""
        config = Config()

        assert config.CHROMA_HOST == "chromadb"
        assert config.CHROMA_PORT == "8000"
        assert config.OLLAMA_MODEL == "llama3"
        assert config.LANGUAGE == "zh-TW"
        assert config.MAX_RETRIES == 3

    @patch.dict(
        "os.environ",
        {
            "CHROMA_HOST": "localhost",
            "OLLAMA_MODEL": "llama2",
            "AGENT_LANGUAGE": "en",
            "MAX_RETRIES": "5",
        },
    )
    def test_config_from_env(self):
        """Test configuration from environment variables"""
        config = Config()

        assert config.CHROMA_HOST == "localhost"
        assert config.OLLAMA_MODEL == "llama2"
        assert config.LANGUAGE == "en"
        assert config.MAX_RETRIES == 5


if __name__ == "__main__":
    pytest.main([__file__])
