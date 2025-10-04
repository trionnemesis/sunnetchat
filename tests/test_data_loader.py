import os
import pytest
from app.data_processor import load_documents_from_path

# Define the path to the test data directory for clarity
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture(scope="module")
def setup_dummy_files():
    """A fixture to create a set of dummy files for the whole test module."""
    dummy_files = {
        "doc1.txt": "This is a text file.",
        "doc2.pdf": "",  # Mock file, content doesn't matter for loader
        # selection
        "doc3.docx": "",  # Mock file
        "unsupported.xyz": "Some data",
    }
    # Ensure the test data directory exists
    os.makedirs(TEST_DATA_DIR, exist_ok=True)

    for filename, content in dummy_files.items():
        with open(os.path.join(TEST_DATA_DIR, filename), "w") as f:
            f.write(content)

    yield TEST_DATA_DIR  # provide the directory path to the tests

    # Teardown
    for filename in dummy_files:
        try:
            os.remove(os.path.join(TEST_DATA_DIR, filename))
        except OSError:
            pass


def test_load_single_text_file(setup_dummy_files):
    """
    Tests loading a single text file and verifies its content.
    """
    test_file_path = os.path.join(setup_dummy_files, "doc1.txt")
    documents = load_documents_from_path(test_file_path)

    assert isinstance(documents, list)
    assert len(documents) == 1
    doc = documents[0]
    assert "This is a text file." in doc.page_content
    assert doc.metadata["source"] == test_file_path


def test_load_from_non_existent_path():
    """
    Tests that the function handles a non-existent path gracefully.
    """
    with pytest.raises(FileNotFoundError):
        load_documents_from_path("non_existent_path/non_existent_file.txt")


def test_load_documents_from_directory(setup_dummy_files):
    """
    Tests loading all supported documents from a given directory.
    It should load .txt, .pdf, .docx and ignore unsupported file types.
    """
    # This test will fail until we implement directory loading
    # and support for PDF and DOCX files.
    documents = load_documents_from_path(setup_dummy_files)

    assert isinstance(documents, list)
    # Should load the .txt, .pdf, and .docx files, but not the .xyz file
    assert len(documents) == 3

    # Check that the sources are correctly identified
    sources = {os.path.basename(doc.metadata["source"]) for doc in documents}
    expected_sources = {"doc1.txt", "doc2.pdf", "doc3.docx"}
    assert sources == expected_sources
