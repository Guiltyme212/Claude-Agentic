#!/usr/bin/env python3
"""
Read rows from the Pipeline Google Sheet where Status == GO.

Usage:
    python Tools/read_sheet.py [--sheet "Pipeline test"] [--limit 1]

Output: JSON array of row dicts to stdout. Each dict includes '_row' (1-indexed sheet row).
"""

import sys
import json
import argparse
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))
import sheets_client


def get_go_rows(sheet_name: str = None, limit: int = None) -> list[dict]:
    """Return rows where Status == 'GO', up to `limit` rows."""
    if sheet_name is None:
        sheet_name = os.getenv("GOOGLE_SHEETS_PIPELINE_TEST", "Pipeline test")

    client = sheets_client.get_client()
    spreadsheet = client.open_by_key(os.getenv("GOOGLE_SHEETS_ID"))
    worksheet = spreadsheet.worksheet(sheet_name)

    # Read all data including headers
    all_values = worksheet.get_all_values()
    if not all_values:
        return []

    headers = all_values[0]
    rows = []

    total_rows = len(all_values) - 1
    print(f"[read_sheet] Scanning {total_rows} rows in '{sheet_name}'...", file=sys.stderr)

    for row_idx, row_values in enumerate(all_values[1:], start=2):  # row 1 = header
        # Pad row to header length if needed
        while len(row_values) < len(headers):
            row_values.append("")

        row_dict = dict(zip(headers, row_values))
        row_dict["_row"] = row_idx  # actual sheet row number for updates

        if row_dict.get("Status", "").strip().upper() == "GO":
            rows.append(row_dict)
            if limit and len(rows) >= limit:
                break

    print(f"[read_sheet] Found {len(rows)} GO row(s) out of {total_rows} total.", file=sys.stderr)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Read GO rows from Pipeline sheet")
    parser.add_argument("--sheet", default=None, help="Sheet name (default: Pipeline test)")
    parser.add_argument("--limit", type=int, default=1, help="Max rows to return (default: 1)")
    args = parser.parse_args()

    rows = get_go_rows(sheet_name=args.sheet, limit=args.limit)
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
