#!/usr/bin/env python3
"""
LeadPilot main pipeline orchestrator.

Reads rows with Status=GO from the Pipeline sheet, runs the full pipeline for each:
  GO → SCRAPING → BUILDING → DEPLOYING → DEPLOYED (with Preview URL)
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
import build_website
import deploy_netlify

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

            # ── BUILDING ──────────────────────────────────────────────────
            update_sheet.update_row(sheet_name, row_num, {"Status": "BUILDING"})

            # Strip internal keys before sending to Claude
            business_data = {k: v for k, v in row.items() if not k.startswith("_")}
            html = build_website.build_website(business_data, scraped_text)

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
                "Status": "DEPLOYED",
                "Preview URL": live_url,
            })

            print(f"  DEPLOYED: {live_url}\n")

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
