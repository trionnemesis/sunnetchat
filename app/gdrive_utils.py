import os
import json
import io
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Google Drive Configuration ---

# Load credentials from environment variable
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if GOOGLE_CREDS_JSON:
    try:
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        SCOPES = ["https://www.googleapis.com/auth/drive"]
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES
        )
        drive_service = build("drive", "v3", credentials=creds)
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to load Google credentials from JSON: {e}")
        drive_service = None
else:
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS_JSON not found in .env file.")
    drive_service = None

GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")


def upload_qa_to_drive(question: str, answer: str):
    """
    Uploads a question and its answer as a new text file to a specified Google Drive folder.
    """
    if not drive_service or not GOOGLE_DRIVE_FOLDER_ID:
        logger.error("Google Drive service is not configured. Skipping upload.")
        return

    try:
        # Sanitize the question to create a valid filename
        file_name = f"{question[:50].replace(' ', '_').replace('/', '_')}.txt"
        file_content = f"Question:\n{question}\n\nAnswer:\n{answer}"

        file_metadata = {"name": file_name, "parents": [GOOGLE_DRIVE_FOLDER_ID]}

        # Create a file-like object from the content string
        fh = io.BytesIO(file_content.encode("utf-8"))
        media = MediaIoBaseUpload(fh, mimetype="text/plain", resumable=True)

        # Create the file in Google Drive
        file = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        logger.info(
            f"Successfully uploaded new knowledge to Google Drive. File ID: {file.get('id')}"
        )

    except Exception as e:
        logger.error(f"Failed to upload to Google Drive: {e}")


# Example usage
if __name__ == "__main__":
    # This is for direct testing.
    # Ensure your .env file is correctly set up.
    test_question = "什麼是 LangGraph?"
    test_answer = "LangGraph 是一個用於建立有狀態、多參與者應用程式的函式庫，它擴展了 LangChain 表達式語言。"
    upload_qa_to_drive(test_question, test_answer)
