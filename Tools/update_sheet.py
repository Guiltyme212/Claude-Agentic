#!/usr/bin/env python3
"""
Update specific columns in a Pipeline sheet row.

Usage:
    python Tools/update_sheet.py --sheet "Pipeline test" --row 5 --updates '{"Status":"DEPLOYING","Preview URL":"https://..."}'

Finds each column by header name, updates only the specified cells.
"""

import sys
import json
import argparse
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))
import sheets_client


def update_row(sheet_name: str, row_num: int, updates: dict) -> None:
    """Update specific columns in a sheet row. updates = {column_header: value}."""
    client = sheets_client.get_client()
    spreadsheet = client.open_by_key(os.getenv("GOOGLE_SHEETS_ID"))
    worksheet = spreadsheet.worksheet(sheet_name)

    # Read headers (row 1)
    headers = worksheet.row_values(1)

    # Build batch update list
    batch = []
    for col_name, value in updates.items():
        if col_name not in headers:
            print(f"[update_sheet] WARNING: column '{col_name}' not found in headers, skipping", file=sys.stderr)
            continue
        col_idx = headers.index(col_name) + 1  # gspread is 1-indexed
        col_letter = _col_index_to_letter(col_idx)
        a1 = f"{col_letter}{row_num}"
        batch.append({"range": a1, "values": [[str(value)]]})

    if batch:
        worksheet.batch_update(batch, value_input_option="RAW")
        print(f"[update_sheet] Updated row {row_num}: {list(updates.keys())}", file=sys.stderr)


def _col_index_to_letter(idx: int) -> str:
    """Convert 1-indexed column number to A1 letter notation (supports AA, AB, etc)."""
    result = ""
    while idx > 0:
        idx, remainder = divmod(idx - 1, 26)
        result = chr(65 + remainder) + result
    return result


def main():
    parser = argparse.ArgumentParser(description="Update columns in a Pipeline sheet row")
    parser.add_argument("--sheet", required=True, help="Sheet name")
    parser.add_argument("--row", type=int, required=True, help="1-indexed row number")
    parser.add_argument("--updates", required=True, help='JSON dict of {column: value}')
    args = parser.parse_args()

    updates = json.loads(args.updates)
    update_row(args.sheet, args.row, updates)


if __name__ == "__main__":
    main()
