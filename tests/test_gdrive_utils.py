import pytest
from unittest.mock import patch, MagicMock
import os

# Set dummy env vars for testing
os.environ["GOOGLE_DRIVE_FOLDER_ID"] = "fake_folder_id"
os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = (
    '{"type": "service_account", "client_email": "test@example.com"}'
)


# Mock the googleapiclient before importing the module we're testing
@patch.dict(
    "sys.modules",
    {
        "google.oauth2.service_account": MagicMock(),
        "googleapiclient.discovery": MagicMock(),
        "googleapiclient.http": MagicMock(),
    },
)
def test_upload_function_call():
    """
    Tests that the upload_qa_to_drive function calls the Google Drive API correctly.
    """
    from app import gdrive_utils

    # Get the mocked build function from the mocked discovery module
    mock_build = gdrive_utils.build
    mock_drive_service = MagicMock()
    mock_build.return_value = mock_drive_service

    test_question = "測試問題"
    test_answer = "測試答案"

    # Call the function to be tested
    gdrive_utils.upload_qa_to_drive(test_question, test_answer)

    # Assert that the create method of the files service was called
    mock_drive_service.files().create.assert_called_once()

    # You can also inspect the arguments it was called with
    call_args, call_kwargs = mock_drive_service.files().create.call_args
    assert call_kwargs["body"]["name"] == f"{test_question}.txt"
    assert call_kwargs["body"]["parents"] == ["fake_folder_id"]


@patch.dict(
    "sys.modules",
    {
        "google.oauth2.service_account": MagicMock(),
        "googleapiclient.discovery": MagicMock(),
        "googleapiclient.http": MagicMock(),
    },
)
@patch("app.gdrive_utils.drive_service", None)
def test_upload_skips_if_service_not_configured():
    """
    Tests that the upload is skipped if the drive service is not initialized.
    """
    from app import gdrive_utils

    # Reload the module to re-evaluate the drive_service global
    import importlib

    importlib.reload(gdrive_utils)

    # We need a mock logger to check if it was called
    with patch("app.gdrive_utils.logger") as mock_logger:
        gdrive_utils.upload_qa_to_drive("q", "a")
        mock_logger.error.assert_called_with(
            "Google Drive service is not configured. Skipping upload."
        )
