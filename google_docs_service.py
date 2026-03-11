import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2 import service_account

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']

def get_gdocs_service():
    """Builds and returns the Google Docs and Drive services."""
    creds = None
    # Use existing token.json if found
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Fallback to service account if available for background tasks
            creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")
            if os.path.exists(creds_path):
                try:
                    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
                    print(f"✅ Using Service Account for Google Docs: {creds_path}")
                except Exception as e:
                    print(f"⚠️ Service Account error: {e}")
            
            if not creds:
                raise Exception("No valid credentials found for Google Docs. Run authorized login.")

    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return docs_service, drive_service

def create_doc_from_markdown(title, markdown_content):
    """
    Creates a Google Doc from Markdown content.
    Returns the URL of the created document.
    """
    try:
        docs_service, drive_service = get_gdocs_service()

        # 1. Create a blank document
        doc = docs_service.documents().create(body={'title': title}).execute()
        document_id = doc.get('documentId')
        
        # 2. Add content (very basic conversion for now - plain text insertion)
        # We can expand this with basic formatting if needed
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': markdown_content
                }
            }
        ]
        
        docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        
        # 3. Set permissions to "Anyone with the link can view" (Optional but helpful)
        drive_service.permissions().create(
            fileId=document_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
        print(f"📄 Created Google Doc: {doc_url}")
        return doc_url

    except Exception as e:
        print(f"❌ Error creating Google Doc: {e}")
        return None

if __name__ == "__main__":
    # Test
    test_title = "Test Resume - " + os.path.basename(os.getcwd())
    test_content = "This is a test document generated from the automation script."
    url = create_doc_from_markdown(test_title, test_content)
    if url:
        print(f"Success! URL: {url}")
    else:
        print("Failed to create document.")
