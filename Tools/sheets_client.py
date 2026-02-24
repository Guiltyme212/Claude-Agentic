"""
Shared Google Sheets auth helper.

First-time setup: run Tools/setup_google_auth.py to generate token.pickle.
Subsequent runs reuse and auto-refresh the cached token.
"""

import os
import pickle
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "token.pickle")
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "..", "credentials.json")


def get_client() -> gspread.Client:
    """Return an authenticated gspread client, refreshing token if needed."""
    creds = None

    token_path = os.path.abspath(TOKEN_PATH)
    if os.path.exists(token_path):
        with open(token_path, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
        else:
            raise RuntimeError(
                "No valid Google credentials found.\n"
                "Run: python Tools/setup_google_auth.py"
            )

    return gspread.authorize(creds)
