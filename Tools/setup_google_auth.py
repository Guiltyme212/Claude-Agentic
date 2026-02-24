#!/usr/bin/env python3
"""
One-time Google OAuth setup — Codespaces-compatible copy-paste flow.

No local server needed. Steps:
1. Script prints an authorization URL
2. You open it in your browser and approve
3. Google redirects to localhost (it will error — that's fine)
4. Copy the FULL URL from the browser address bar and paste it here
5. Done — token.pickle is saved

Run: python Tools/setup_google_auth.py
"""

import os
import pickle
from urllib.parse import urlparse, parse_qs
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "token.pickle")


def setup():
    creds_path = os.path.abspath(CREDENTIALS_PATH)
    token_path = os.path.abspath(TOKEN_PATH)

    if not os.path.exists(creds_path):
        print(f"ERROR: credentials.json not found at {creds_path}")
        return

    # Check if existing token is still valid
    if os.path.exists(token_path):
        with open(token_path, "rb") as f:
            creds = pickle.load(f)
        if creds and creds.valid:
            print("Token is already valid. Nothing to do.")
            return
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)
            print(f"Token refreshed: {token_path}")
            return

    # Build the flow with http://localhost as redirect URI (matches credentials.json)
    flow = InstalledAppFlow.from_client_secrets_file(
        creds_path,
        scopes=SCOPES,
        redirect_uri="http://localhost",
    )

    auth_url, _ = flow.authorization_url(prompt="consent")

    print()
    print("=" * 60)
    print("STEP 1: Open this URL in your browser:")
    print()
    print(auth_url)
    print()
    print("STEP 2: Sign in and click Allow.")
    print()
    print("STEP 3: Your browser will redirect to localhost and show")
    print("        'This site can't be reached' — that's expected.")
    print("        Copy the FULL URL from the address bar and paste below.")
    print("=" * 60)
    print()

    redirect_url = input("Paste the full redirect URL here: ").strip()

    # Extract the authorization code from the pasted URL
    parsed = urlparse(redirect_url)
    params = parse_qs(parsed.query)

    if "code" not in params:
        print(f"ERROR: No 'code' found in URL. Got params: {list(params.keys())}")
        return

    code = params["code"][0]
    print(f"\nGot authorization code. Exchanging for token...")

    flow.fetch_token(code=code)
    creds = flow.credentials

    with open(token_path, "wb") as f:
        pickle.dump(creds, f)

    print(f"Success! Token saved to {token_path}")
    print("You can now run: python Tools/run_pipeline.py")


if __name__ == "__main__":
    setup()
