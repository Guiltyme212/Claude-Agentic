#!/usr/bin/env python3
"""
Send a cold email via SMTP (GoDaddy/Outlook).

Sends personalized emails directly from dan@aiboostly.com using SMTP.
Test mode redirects all emails to SMTP_TEST_EMAIL.

Usage:
    python Tools/send_email.py --to "info@business.nl" --body "Hoi..." --business-name "Jansen"
    python Tools/send_email.py --to "info@business.nl" --body "Hoi..." --business-name "Jansen" --test-email "dan.ivdnis@gmail.com"

Output: JSON result to stdout, logs to stderr.
"""

import sys
import os
import json
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate, make_msgid
from dotenv import load_dotenv

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
    Send a personalized cold email via SMTP.

    Returns dict: {"status": "sent", "to_email": "...", "subject": "..."}
    """
    # SMTP config from env
    smtp_host = os.getenv("SMTP_HOST", "smtp.office365.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_name = os.getenv("SMTP_FROM_NAME", "Dan van AiBoostly")
    from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user)

    if not smtp_user or not smtp_password:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set in .env")

    # Test mode: redirect to test email
    actual_recipient = to_email
    if test_mode:
        test_email = os.getenv("SMTP_TEST_EMAIL", "dan.ivdnis@gmail.com")
        print(f"[send_email] TEST MODE: redirecting {to_email} → {test_email}", file=sys.stderr)
        actual_recipient = test_email

    # Subject line
    subject = f"Preview website voor {business_name}" if business_name else "Uw preview website"

    # Build MIME message (multipart/alternative: plain text + HTML)
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((from_name, from_email))
    msg["To"] = actual_recipient
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=from_email.split("@")[1])
    msg["Reply-To"] = formataddr((from_name, from_email))

    # Plain text version (the email body from draft_email is already plain text)
    plain_body = email_body
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))

    # HTML version (convert newlines to <br>, keep it simple — no heavy templates)
    html_lines = email_body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_lines = html_lines.replace("\n", "<br>\n")
    html_body = f"""\
<html>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.6;">
<p>{html_lines}</p>
</body>
</html>"""
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Send with retry
    print(f"[send_email] Sending to {actual_recipient} via {smtp_host}:{smtp_port}...", file=sys.stderr)

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [actual_recipient], msg.as_string())

            print(f"[send_email] Sent successfully to {actual_recipient}", file=sys.stderr)
            return {
                "status": "sent",
                "to_email": actual_recipient,
                "subject": subject,
            }

        except smtplib.SMTPAuthenticationError as e:
            raise RuntimeError(f"SMTP auth failed: {e}") from e

        except (smtplib.SMTPException, OSError) as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait = [5, 10, 20][attempt]
                print(f"[send_email] SMTP error, retrying in {wait}s (attempt {attempt+1}/{MAX_RETRIES}): {e}", file=sys.stderr)
                import time
                time.sleep(wait)
                continue
            raise

    raise last_error


def main():
    parser = argparse.ArgumentParser(description="Send email via SMTP")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--body", required=True, help="Email body text")
    parser.add_argument("--business-name", default="", help="Business name (for subject line)")
    parser.add_argument("--test-email", default=None, help="Override recipient for testing")
    args = parser.parse_args()

    test_mode = bool(args.test_email)
    if args.test_email:
        os.environ["SMTP_TEST_EMAIL"] = args.test_email

    result = send_email(
        to_email=args.to,
        email_body=args.body,
        business_name=args.business_name,
        test_mode=test_mode,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
