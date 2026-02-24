# Workflow: LeadPilot Full Pipeline

## Objective
Process one or more rows from the Pipeline Google Sheet (Status=GO) through the full website generation pipeline and return live Netlify URLs.

## Required Inputs
- Sheet name: "Pipeline test" (safe default) or "Pipeline" (production)
- Row limit: how many GO rows to process in this run (default: 1)

## Steps

### 1. Check for existing tools
Before doing anything, verify the tools exist: `read_sheet.py`, `update_sheet.py`, `scrape_website.py`, `build_website.py`, `deploy_netlify.py`.

### 2. Verify credentials
Ensure `.env` is present and `token.pickle` exists (Google OAuth). If `token.pickle` is missing, run `Tools/setup_google_auth.py` first.

### 3. Run the pipeline
```bash
python Tools/run_pipeline.py --sheet "Pipeline test" --limit 1
```

For production:
```bash
python Tools/run_pipeline.py --sheet "Pipeline" --limit 5
```

### 4. Monitor output
The pipeline logs each stage to stderr. The final live URL is written back to the sheet's "Preview URL" column.

Status progression:
```
GO → SCRAPING → BUILDING → DEPLOYING → DEPLOYED
                                      → ERROR (with Notes)
```

### 5. On ERROR status
- Read the Notes column in the sheet for the error message
- Diagnose: was it scraping failure, Claude 529, Netlify API issue?
- Fix the underlying tool, verify fix, then reset Status to GO and re-run

## Edge Cases
- **No GO rows**: pipeline exits cleanly with a message
- **SSL errors on scraping**: scrape_website.py catches these and continues without scraped content — pipeline still runs
- **Claude 529**: build_website.py retries 3× with 20s/40s backoff before failing
- **Netlify name collision**: timestamp suffix on slug prevents this
- **Missing columns in sheet**: update_sheet.py warns and skips unknown column names

## Notes
- Always test on "Pipeline test" before running on production "Pipeline"
- .tmp/ stores intermediate HTML files for inspection — safe to delete anytime
- Never edit Workflows without asking first
