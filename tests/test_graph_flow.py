import pytest
from unittest.mock import patch, MagicMock

# Mock all external services before importing the graph
@patch.dict('sys.modules', {
    'app.rag_core': MagicMock(),
    'app.gdrive_utils': MagicMock(),
    'langchain_community.tools.tavily_search': MagicMock(),
})
def test_graph_flow_local_path():
    """Tests the graph path when local documents are graded as relevant."""
    from app import graph_flow

    # Mock the grader to always return 'yes'
    mock_grader_llm = MagicMock()
    mock_grader_llm.invoke.return_value = {'score': 'yes'}
    graph_flow.llm = mock_grader_llm

    # Mock the retriever
    graph_flow.retriever.get_relevant_documents.return_value = ["本地文件內容"]

    # Mock the generation LLM
    mock_gen_llm = MagicMock()
    mock_gen_llm.invoke.return_value = "從本地文件生成的答案"
    graph_flow.generation_llm = mock_gen_llm

    # Mock the gdrive upload function
    mock_upload = graph_flow.upload_qa_to_drive

    # Compile and run the graph
    app = graph_flow.workflow.compile()
    inputs = {"question": "test"}
    result = app.invoke(inputs)

    # Assertions
    assert result['generation'] == "從本地文件生成的答案"
    # Ensure web search was NOT called
    graph_flow.web_search_tool.invoke.assert_not_called()
    # Ensure GDrive upload was NOT called
    mock_upload.assert_not_called()

@patch.dict('sys.modules', {
    'app.rag_core': MagicMock(),
    'app.gdrive_utils': MagicMock(),
    'langchain_community.tools.tavily_search': MagicMock(),
})
def test_graph_flow_web_search_path():
    """Tests the graph path when local documents are graded as irrelevant."""
    from app import graph_flow

    # Mock the grader to always return 'no'
    mock_grader_llm = MagicMock()
    mock_grader_llm.invoke.return_value = {'score': 'no'}
    graph_flow.llm = mock_grader_llm

    # Mock the web search tool
    graph_flow.web_search_tool.invoke.return_value = ["網路搜尋結果"]

    # Mock the generation LLM
    mock_gen_llm = MagicMock()
    mock_gen_llm.invoke.return_value = "從網路搜尋生成的答案"
    graph_flow.generation_llm = mock_gen_llm

    # Mock the gdrive upload function
    mock_upload = graph_flow.upload_qa_to_drive

    # Compile and run the graph
    app = graph_flow.workflow.compile()
    inputs = {"question": "test"}
    result = app.invoke(inputs)

    # Assertions
    assert result['generation'] == "從網路搜尋生成的答案"
    # Ensure web search WAS called
    graph_flow.web_search_tool.invoke.assert_called_once()
    # Ensure GDrive upload WAS called
    mock_upload.assert_called_once_with("test", "從網路搜尋生成的答案")
