#!/usr/bin/env python3
"""
LeadPilot main pipeline orchestrator.

Reads rows with Status=GO from the Pipeline sheet, runs the full pipeline for each:
  GO → SCRAPING → BUILDING → DEPLOYING → DEPLOYED → EMAILING → SENDING → DONE
  Any failure → ERROR (with Notes explaining what went wrong)

Usage:
    python Tools/run_pipeline.py [--sheet "Pipeline test"] [--limit 1]

Options:
    --sheet   Sheet name (default: Pipeline test for safety)
    --limit   Max rows to process in one run (default: 1)
"""

import sys
import os
import json
import argparse
import traceback
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

import read_sheet
import update_sheet
import scrape_website
import fetch_reviews
import build_website
import deploy_netlify
import draft_email
import send_email

TMP_DIR = os.path.join(os.path.dirname(__file__), "..", ".tmp")


def run(sheet_name: str = "Pipeline test", limit: int = 1) -> None:
    os.makedirs(TMP_DIR, exist_ok=True)

    print(f"\n=== LeadPilot Pipeline ===")
    print(f"Sheet: {sheet_name} | Limit: {limit}\n")

    rows = read_sheet.get_go_rows(sheet_name=sheet_name, limit=limit)
    if not rows:
        print("No rows with Status=GO found. Done.")
        return

    print(f"Found {len(rows)} row(s) to process.\n")

    for row in rows:
        row_num = row["_row"]
        business_name = row.get("Business Name", "").strip() or f"Row {row_num}"
        website_url = row.get("Website", "").strip()

        print(f"--- Processing: {business_name} (row {row_num}) ---")

        try:
            # ── SCRAPING ──────────────────────────────────────────────────
            update_sheet.update_row(sheet_name, row_num, {"Status": "SCRAPING"})
            scraped_text = scrape_website.scrape(website_url)

            # ── FETCH REVIEWS + PHOTOS ────────────────────────────────────
            place_id = row.get("Google Place ID", "").strip()
            place_data = fetch_reviews.fetch(place_id)
            reviews_text = fetch_reviews.format_for_prompt(place_data)

            # ── BUILDING ──────────────────────────────────────────────────
            update_sheet.update_row(sheet_name, row_num, {"Status": "BUILDING"})

            # Strip internal keys before sending to Claude
            business_data = {k: v for k, v in row.items() if not k.startswith("_")}
            html = build_website.build_website(business_data, scraped_text, reviews_text)

            # Save HTML to .tmp for inspection / debugging
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in business_name)[:50]
            html_path = os.path.join(TMP_DIR, f"{safe_name}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  HTML saved to: {html_path}")

            # ── DEPLOYING ─────────────────────────────────────────────────
            update_sheet.update_row(sheet_name, row_num, {"Status": "DEPLOYING"})
            live_url = deploy_netlify.deploy(html, business_name)

            # ── DEPLOYED ──────────────────────────────────────────────────
            update_sheet.update_row(sheet_name, row_num, {
                "Status": "Deployed",
                "Preview URL": live_url,
            })
            print(f"  Deployed: {live_url}")

            # ── EMAIL DRAFTING ────────────────────────────────────────────
            email_status = row.get("Email Status", "").strip().upper()
            if email_status in ("BLACKLISTED", "INVALID"):
                print(f"  Skipping email: Email Status is {row.get('Email Status')}")
                update_sheet.update_row(sheet_name, row_num, {"Status": "Deployed"})
                print(f"  Deployed (no email)\n")
                continue

            update_sheet.update_row(sheet_name, row_num, {"Status": "EMAILING"})
            email_body = draft_email.draft_email(business_data, live_url, scraped_text, reviews_text)
            update_sheet.update_row(sheet_name, row_num, {
                "Status": "Email Draft Written",
                "Email Draft": email_body,
            })
            print(f"  Email Draft Written")

            # ── SENDING ──────────────────────────────────────────────────
            to_email = row.get("Email", "").strip()
            if not to_email:
                print(f"  Skipping send: no email address in sheet")
                update_sheet.update_row(sheet_name, row_num, {"Status": "Email Draft Written"})
                print(f"  Email Draft Written (no recipient)\n")
                continue

            update_sheet.update_row(sheet_name, row_num, {"Status": "SENDING"})
            test_mode = bool(os.getenv("SMTP_TEST_EMAIL"))
            send_result = send_email.send_email(
                to_email=to_email,
                email_body=email_body,
                business_name=business_name,
                test_mode=test_mode,
            )

            # ── SENT ────────────────────────────────────────────────────
            from datetime import datetime
            sent_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            update_sheet.update_row(sheet_name, row_num, {
                "Status": "Email sent succesfully",
                "Sent Date": sent_date,
            })
            print(f"  Email sent succesfully ({sent_date})\n")

        except Exception as e:
            tb = traceback.format_exc()
            error_msg = f"{type(e).__name__}: {e}"
            print(f"  ERROR: {error_msg}", file=sys.stderr)
            print(tb, file=sys.stderr)

            update_sheet.update_row(sheet_name, row_num, {
                "Status": "ERROR",
                "Notes": error_msg[:500],
            })

    print("=== Pipeline complete ===\n")


def main():
    parser = argparse.ArgumentParser(description="LeadPilot pipeline orchestrator")
    parser.add_argument(
        "--sheet",
        default=os.getenv("GOOGLE_SHEETS_PIPELINE_TEST", "Pipeline test"),
        help="Sheet name (default: Pipeline test)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Max rows to process (default: 1)",
    )
    args = parser.parse_args()
    run(sheet_name=args.sheet, limit=args.limit)


if __name__ == "__main__":
    main()
