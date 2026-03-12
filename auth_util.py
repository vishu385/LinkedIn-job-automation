import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import gspread
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/documents', 
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def get_google_creds():
    """
    Handles central authentication for Google APIs.
    Prioritizes Personal OAuth (token.json) for 15GB storage.
    Uses .env variables for Client ID/Secret if no session exists.
    """
    creds = None
    token_file = 'token.json'
    # 1. TRY PERSONAL LOGIN (OAuth) - 15GB space
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing personal login session...")
                creds.refresh(Request())
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
        except Exception as e:
            print(f"⚠️ Personal login session invalid: {e}")
            if "invalid_grant" in str(e).lower():
                print("🗑️ Deleting invalid token.json...")
                try: os.remove(token_file)
                except: pass
            creds = None

    # 3. FRESH LOGIN (Use Client ID/Secret from .env)
    if not (creds and creds.valid):
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        
        if client_id and client_secret:
            print("🔑 No valid session found. Opening browser for Personal Google Login...")
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            # Desktop App flow automatically handles the redirect to localhost:0
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"✅ Login successful! Token saved to {token_file}")
        else:
            if not creds:
                raise Exception("❌ NO AUTH FOUND: Please provide GOOGLE_OAUTH_CLIENT_ID in .env")

    return creds

def get_gdocs_service():
    creds = get_google_creds()
    return build('docs', 'v1', credentials=creds), build('drive', 'v3', credentials=creds)

def get_gspread_client():
    creds = get_google_creds()
    return gspread.authorize(creds)
