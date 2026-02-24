# Workflow: Scrape Business Website

## Objective
Extract plain text content from a business's current website to give Claude context about their services, tone, and branding.

## Tool
`Tools/scrape_website.py`

## Inputs
- `url`: The business's website URL (from sheet "Website" column)
- `max_chars`: Max chars to extract (default: 6000)

## Steps

1. HTTP GET with browser User-Agent (avoids 403s)
2. Parse HTML with lxml/html.parser
3. Remove noise: `<script>`, `<style>`, `<nav>`, `<footer>`, `<form>`, `<svg>`, `<img>`, `<button>`
4. Extract remaining text, collapse whitespace
5. Truncate to max_chars

## Output
Plain text string to stdout. Empty string on failure.

## Failure Handling
The tool **never raises** — it catches all exceptions and returns empty string. The pipeline continues without scraped content because Claude has:
- Outscraper data (business name, address, services, reviews, hours)
- Web search capability (researches business online during site generation)

## Known Issues & Fixes
- **SSL certificate errors**: tool retries with `verify=False` as fallback
- **Timeout**: set to 15s — most slow sites fail within this window
- **Bot detection / 403**: nothing we can do; return empty, Claude handles it
- **WordPress/Elementor sites**: often have useful text buried in blocks; BeautifulSoup gets it fine

## CLI Usage
```bash
python Tools/scrape_website.py --url https://example.nl
python Tools/scrape_website.py --url https://example.nl --max-chars 8000
```
