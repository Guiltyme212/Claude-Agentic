# Workflow: Build Website with Claude API

## Objective
Generate a complete, mobile-responsive single-file HTML website in Dutch for a local business using Claude with web_search and extended thinking.

## Tool
`Tools/build_website.py`

## Inputs
- `business_data`: dict of all sheet columns for this row
- `scraped_text`: plain text from the business's current site (can be empty)

## Steps

1. Build user prompt including all business_data fields + scraped_text
2. Instruct Claude to use web_search to research the business
3. Call Claude API with:
   - Model: `claude-opus-4-6`
   - Extended thinking: `budget_tokens: 10000`
   - Web search tool: `web_search_20250305`
   - Timeout: 180s
   - max_tokens: 16000
4. Extract HTML from the **last `text` block** in response.content
5. Strip any markdown fences (` ```html ... ``` `)
6. Validate output starts with `<!DOCTYPE html>` or `<html`

## Output
HTML string. Also saved to `.tmp/{business_name}.html` for inspection.

## Failure Handling
- **529 overloaded**: retry 3× with 20s/40s wait
- **No text block**: raises RuntimeError — escalates to ERROR in sheet
- **Non-HTML output**: raises RuntimeError — Claude sometimes returns explanations if the prompt is ambiguous; check system prompt if this recurs

## Response Structure (with web_search + thinking)
Claude returns mixed content blocks:
```
[thinking block] [tool_use: web_search] [tool_result] [thinking block] [text: HTML]
```
Always take the **last text block**.

## Quality Levers
- **More web_search results** = richer, more accurate sites
- **Higher thinking budget** = better layout and copy decisions
- **Longer scraped text** = better branding/tone matching (more chars → more tokens → more cost)
- If quality is low: check that scraped text and Outscraper data are populated

## Known Issues
- Opus with web_search + thinking: 60-120s typical, up to 180s
- Sonnet is faster/cheaper but noticeably lower design quality
- Dutch UTF-8 in business names: json.dumps with ensure_ascii=False handles this correctly

## CLI Usage
```bash
python Tools/build_website.py \
  --data '{"Business Name":"Loodgieter de Vries","City":"Utrecht","Phone":"+31612345678"}' \
  --scraped-text "Wij zijn een familiebedrijf..." \
  --out .tmp/test.html
```
