# Workflow: Draft Cold Outreach Email

## Objective
Generate a short, personal cold email from Dan (AiBoostly) to a Dutch local business owner, linking to the preview website already built and deployed by the pipeline.

## Tool
`Tools/draft_email.py`

## Inputs
- `business_data` (dict): all columns from the Google Sheet row
- `live_url` (str): deployed Netlify preview URL
- `scraped_text` (str, optional): Firecrawl output from their existing website
- `reviews_text` (str, optional): formatted Google reviews

## Steps
1. Extract key fields from business_data (name, contact, city, category, rating)
2. Build user prompt with structured fields (not raw JSON)
3. Call Claude Opus 4.6 via streaming (no web_search needed)
4. Extract email body from last text block in response
5. Return plain text email body

## Output
Plain text email body (6-8 lines). No subject line — body only.

## Email Structure
- Line 1: personal opening (contact name or "Hoi")
- Lines 2-3: what was built + preview link
- Lines 4-5: one specific benefit from their data
- Line 6: soft CTA
- Sign-off: "Groet, Dan" or "Groeten, Dan"

## Skip Conditions
- If `Email Status` is `BLACKLISTED` or `INVALID` → skip (handled in run_pipeline.py)

## Failure Handling
- 529 overloaded → retry 3x with 20s/40s backoff
- No text block → raise RuntimeError (caught by pipeline, logged as ERROR)
- Any other API error → bubble up to pipeline error handler

## Quality Levers
- More scraped content → more specific emails
- Google reviews data → social proof angle
- Contact Name present → personal salutation vs generic "Hoi"

## CLI Usage
```bash
python Tools/draft_email.py \
  --data '{"Business Name":"Loodgieter Jansen","Contact Name":"Jan","City":"Amsterdam","Category":"Loodgieter","Rating":"4.8","Reviews":"23"}' \
  --live-url 'https://loodgieter-jansen-1234567890.netlify.app'
```
