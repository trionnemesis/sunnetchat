import os
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_rag_chain():
    """Fixture to mock the entire RAG chain for isolated testing."""
    # This mock simulates the behavior of the assembled RAG chain.
    # It allows us to test the get_answer function without needing a real DB or LLM.
    with patch('app.rag_core.rag_chain') as mock_chain:
        # Configure the mock to return a specific answer when invoked.
        mock_chain.invoke.return_value = "這是一個模擬的答案。"
        yield mock_chain

@patch('app.rag_core.os.path.exists')
def test_get_answer_with_mock_chain(mock_path_exists, mock_rag_chain):
    """
    Tests the get_answer function to ensure it calls the RAG chain
    and returns its result.
    """
    # Arrange: Ensure the function thinks the DB exists.
    mock_path_exists.return_value = True
    from app.rag_core import get_answer
    
    test_question = "這是一個測試問題。"
    
    # Act: Call the function we are testing.
    answer = get_answer(test_question)
    
    # Assert:
    # 1. Check that the RAG chain was called with the correct question.
    mock_rag_chain.invoke.assert_called_once_with(test_question)
    
    # 2. Check that the function returned the mock's response.
    assert answer == "這是一個模擬的答案。"

@patch('app.rag_core.os.path.exists')
def test_get_answer_db_not_found(mock_path_exists):
    """
    Tests that get_answer returns an error message if the database path does not exist.
    """
    # Arrange: Ensure the function thinks the DB does NOT exist.
    mock_path_exists.return_value = False
    from app.rag_core import get_answer

    # Act: Call the function.
    answer = get_answer("任何問題")

    # Assert: Check that the specific error message is returned.
    assert "錯誤：向量資料庫不存在" in answer
