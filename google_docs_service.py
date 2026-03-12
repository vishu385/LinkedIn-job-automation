import os

# Scopes are centrally managed in auth_util, but kept here for reference if needed
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']

def get_gdocs_service():
    """
    Handles authentication and returns the Google Docs and Drive services.
    Uses unified auth_util.
    """
    from auth_util import get_gdocs_service
    return get_gdocs_service()

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
        
        # 3. Handle target folder (Move from root to folder)
        folder_id = os.getenv("GOOGLE_DOCS_FOLDER_ID")
        if folder_id:
            try:
                # Retrieve the existing parents to remove
                file = drive_service.files().get(fileId=document_id, fields='parents').execute()
                previous_parents = ",".join(file.get('parents'))
                # Move the file to the new folder
                drive_service.files().update(
                    fileId=document_id,
                    addParents=folder_id,
                    removeParents=previous_parents,
                    fields='id, parents'
                ).execute()
                # print(f"📁 Moved to folder: {folder_id}")
            except Exception as fe:
                print(f"⚠️ Error moving to folder: {fe}")

        # 4. Set permissions to "Anyone with the link can view"
        try:
            drive_service.permissions().create(
                fileId=document_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
        except: pass

        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
        print(f"📄 Created Google Doc: {doc_url}")
        return doc_url

    except Exception as e:
        print(f"❌ Error creating Google Doc: {e}")
        # If it's a JSON parse error, it might be due to empty response from API
        if "Expecting value" in str(e):
            print("💡 This often happens due to API timeouts or connection resets. Please try again.")
        return None

if __name__ == "__main__":
    # Test the service
    try:
        docs, drive = get_gdocs_service()
        print("✅ Success!")
    except Exception as e:
        print(f"❌ Failed: {e}")
