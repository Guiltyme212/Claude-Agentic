#!/usr/bin/env python3
"""Railway entry point — polls Google Sheet for GO rows and runs pipeline."""

import os
import sys
import base64
import time


def ensure_google_token():
    """Decode GOOGLE_TOKEN_PICKLE_B64 env var → token.pickle on disk."""
    token_b64 = os.getenv("GOOGLE_TOKEN_PICKLE_B64")
    token_path = os.path.join(os.path.dirname(__file__), "token.pickle")

    if token_b64:
        token_bytes = base64.b64decode(token_b64)
        with open(token_path, "wb") as f:
            f.write(token_bytes)
        print(f"[railway] Wrote token.pickle ({len(token_bytes)} bytes)")
    elif not os.path.exists(token_path):
        print("[railway] ERROR: No GOOGLE_TOKEN_PICKLE_B64 env var and no token.pickle file")
        sys.exit(1)


def main():
    ensure_google_token()

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Tools"))
    from run_pipeline import run

    sheet = os.getenv("PIPELINE_SHEET", "Pipeline test")
    limit = int(os.getenv("PIPELINE_LIMIT", "5"))
    interval = int(os.getenv("POLL_INTERVAL", "120"))

    print(f"[railway] Polling every {interval}s | Sheet: {sheet} | Limit: {limit}")

    while True:
        try:
            run(sheet_name=sheet, limit=limit)
        except Exception as e:
            print(f"[railway] Pipeline error: {e}", file=sys.stderr)
        time.sleep(interval)


if __name__ == "__main__":
    main()
