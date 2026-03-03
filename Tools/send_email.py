#!/usr/bin/env python3
"""
Send a cold email via Resend API.

Sends personalized emails from dan@aiboostly.com using Resend.
Test mode redirects all emails to RESEND_TEST_EMAIL.

Usage:
    python Tools/send_email.py --to "info@business.nl" --body "Hoi..." --business-name "Jansen"
    python Tools/send_email.py --to "info@business.nl" --body "Hoi..." --business-name "Jansen" --test-email "dan.ivdnis@gmail.com"

Output: JSON result to stdout, logs to stderr.
"""

import sys
import os
import json
import time
import argparse
from dotenv import load_dotenv
import resend
from email_template import build_html_email

load_dotenv()

MAX_RETRIES = 3


def send_email(
    to_email: str,
    email_body: str,
    business_name: str = "",
    campaign_id: str = None,
    test_mode: bool = False,
) -> dict:
    """
    Send a personalized cold email via Resend API.

    Returns dict: {"status": "sent", "to_email": "...", "subject": "..."}
    """
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY must be set in .env")

    resend.api_key = api_key

    from_name = os.getenv("RESEND_FROM_NAME", os.getenv("SMTP_FROM_NAME", "Dan van AiBoostly"))
    from_email = os.getenv("RESEND_FROM_EMAIL", os.getenv("SMTP_FROM_EMAIL", "dan@contact.aiboostly.com"))

    # Test mode: redirect to test email
    actual_recipient = to_email
    if test_mode:
        test_email = os.getenv("RESEND_TEST_EMAIL", os.getenv("SMTP_TEST_EMAIL", "dan.ivdnis@gmail.com"))
        print(f"[send_email] TEST MODE: redirecting {to_email} → {test_email}", file=sys.stderr)
        actual_recipient = test_email

    # Subject line
    subject = f"Preview website voor {business_name}" if business_name else "Uw preview website"

    # Build HTML version
    html_body = build_html_email(email_body, business_name)

    print(f"[send_email] Sending to {actual_recipient} via Resend...", file=sys.stderr)

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            params: resend.Emails.SendParams = {
                "from": f"{from_name} <{from_email}>",
                "to": [actual_recipient],
                "subject": subject,
                "html": html_body,
                "text": email_body,
                "reply_to": f"{from_name} <{from_email}>",
            }

            result = resend.Emails.send(params)

            print(f"[send_email] Sent successfully to {actual_recipient} (id: {result.get('id', 'unknown')})", file=sys.stderr)
            return {
                "status": "sent",
                "to_email": actual_recipient,
                "subject": subject,
                "resend_id": result.get("id"),
            }

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait = [5, 10, 20][attempt]
                print(f"[send_email] Resend error, retrying in {wait}s (attempt {attempt+1}/{MAX_RETRIES}): {e}", file=sys.stderr)
                time.sleep(wait)
                continue
            raise

    raise last_error


def main():
    parser = argparse.ArgumentParser(description="Send email via Resend")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--body", required=True, help="Email body text")
    parser.add_argument("--business-name", default="", help="Business name (for subject line)")
    parser.add_argument("--test-email", default=None, help="Override recipient for testing")
    args = parser.parse_args()

    test_mode = bool(args.test_email)
    if args.test_email:
        os.environ["RESEND_TEST_EMAIL"] = args.test_email

    result = send_email(
        to_email=args.to,
        email_body=args.body,
        business_name=args.business_name,
        test_mode=test_mode,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
