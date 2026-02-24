#!/usr/bin/env bash
# LeadPilot quick-run
# Usage:
#   ./go                         → test sheet, 1 row
#   ./go 5                       → test sheet, 5 rows
#   ./go 5 Pipeline              → production sheet, 5 rows

LIMIT=${1:-1}
SHEET=${2:-"Pipeline test"}

python Tools/run_pipeline.py --sheet "$SHEET" --limit "$LIMIT"
