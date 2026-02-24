# LeadPilot — Project Knowledge Base

## What This Is

LeadPilot is the cold outreach engine behind **AiBoostly**, an AI automation agency in Arnhem, Netherlands. It generates premium preview websites for Dutch local businesses using their real data, deploys them to live URLs, then sends cold emails showing the business owner "here's what your website could look like."

The business model is a trojan horse: the €390 website gets them in the door, the €149/month AI automation services are the real revenue.

## The Pipeline (What It Does)

```
Google Sheet row (business data from Outscraper)
  → Firecrawl scrapes their current website (multi-page crawl, markdown output)
  → Google Places API fetches real reviews + photos (via Google Place ID)
  → Claude Opus 4-6 API (streaming + web_search) generates a single-file HTML website
  → Deploy to Netlify via file digest API → live .netlify.app URL
  → Write URL + status back to sheet
  → (Next) Send cold email with preview link
```

Run the pipeline:
```bash
python Tools/run_pipeline.py --sheet "Pipeline test" --limit 1   # test
python Tools/run_pipeline.py --sheet "Pipeline" --limit 10        # production
```

## Data Sources

Three data sources feed every website generation:

1. **Outscraper sheet** — primary source (business name, address, phone, hours, rating, etc.)
2. **Firecrawl** — scrapes their existing website, returns clean markdown of all pages
3. **Google Places API** — pulls up to 5 real reviews + 6 real photos using the Google Place ID

### Pipeline Sheet — Columns That Matter

| Column | Type | Example |
|--------|------|---------|
| **Status** | Workflow state | GO → SCRAPING → BUILDING → DEPLOYING → DEPLOYED / ERROR |
| **Business Name** | String | Installatiebedrijf Piso B.V. |
| **Website** | URL | https://www.pisoinstallatie.nl/ |
| **CMS / Generator** | String | Elementor 3.33.0-dev4 |
| **City** | String | Heeg |
| **Full Address** | String | Harinxmastrjitte 22, 8621 BL Heeg |
| **Street** | String | Harinxmastrjitte 22 |
| **Postal Code** | String | 8621 BL |
| **Phone** | String | +31 515 442 202 |
| **Email** | String | info@pisoinstallatie.nl |
| **Email Status** | String | RECEIVING / BLACKLISTED / INVALID |
| **Category** | String (Dutch) | Installatiebedrijf, Elektricien, Autobedrijf/Garage |
| **Subtypes / Services** | Comma-separated | Plumber, Electrical installation service, HVAC contractor |
| **Rating** | Number | 4.6 |
| **Reviews** | Number | 13 |
| **Website Description** | String | (scraped meta description) |
| **Company Description** | String | (from Google profile) |
| **Working Hours** | Pipe-delimited CSV | Monday,9am,5pm\|Tuesday,9am,6pm\|... |
| **About** | JSON string | {"Service options": {"On-site services": true}, "Accessibility": {...}} |
| **Photo URL** | URL | Google streetview/profile photo |
| **Logo URL** | URL | Google business profile logo |
| **Contact Name** | String | Seef El Shimy |
| **Contact Title** | String | eigenaar |
| **Contact Phone** | String | (personal/mobile number) |
| **Contact LinkedIn** | URL | LinkedIn profile |
| **Facebook** | URL | Facebook page |
| **Instagram** | URL | Instagram profile |
| **Google Place ID** | String | ChIJa7Jk9JftyEcRj7xCUSjEG_0 |
| **Google Maps Link** | URL | Google Maps place link |
| **Reviews Link** | URL | Direct link to Google reviews |
| **Preview URL** | URL | (filled after deploy) |
| **Email Draft** | String | (filled by email generation step) |
| **Notes** | String | (error messages, manual notes) |
| **Website's need for change** | String | (lead scoring assessment) |

### Google Sheet ID

Spreadsheet: `1LbFulV5XzbCUHc1mn5uWo9Dt65T60fFJaH9yq4ZcvwY`
- Production sheet: "Pipeline" (1994 rows)
- Test sheet: "Pipeline test" (1643 rows)
- Raw data: "Raw Data (Outscraper)" (2001 rows)

The `Status` column drives the pipeline. Set to `GO` → pipeline picks it up → updates through stages → ends at `DEPLOYED` with live URL or `ERROR` with notes.

## The Generated Websites — Design Philosophy

The goal is to make each business owner think "holy shit, this looks better than my current site" within 3 seconds of opening the preview link. These are cold leads — they didn't ask for this. The site has to be so good they can't ignore it.

**Creative freedom on design.** Choose colors, layout, typography, and animations that fit the business type. An electrician's site should feel different from a chiropractor's. Use the business category, scraped branding, and real photos from the Places API.

**Hard constraints (non-negotiable):**
- Single HTML file, ALL CSS in `<style>` tag — no external CSS files (Google Fonts via @import is fine)
- Mobile-first responsive — these people read on their phones between jobs
- ALL visible text in Dutch
- ONLY real data — NEVER invent services, reviews, team members, or anything else. If a field is missing, skip that section entirely.
- Footer must include: "Website gemaakt door AiBoostly" linking to https://aiboostly.com
- Click-to-call CTA button (not a contact form — tradespeople don't fill out forms)
- No empty `href=""` links — if a social URL is missing, don't render that icon
- Phone `tel:` links must strip all spaces
- If `Email Status` is BLACKLISTED or INVALID, do not show the email

**Sections to include (skip any that lack data):**
- Hero with business name, location, primary CTA
- Services/specialties (from Subtypes/Services + scraped website content)
- About/trust section (description, contact person, years active if found)
- Social proof — show real Google reviews verbatim if provided (Places API), plus rating + review count
- Real business photos from Places API as hero background or gallery
- Opening hours (parsed from `Monday,8am,5pm|Tuesday,8am,5pm|...` format)
- Features/amenities from About JSON field
- Contact details (phone, email, address, Google Maps embed/link, social media)
- Strong closing CTA with phone number again
- Footer with AiBoostly credit, nav links, © year

## Netlify Deployment — File Digest Method

**This is the only method that works correctly.** ZIP uploads serve HTML as `text/plain`. File digest serves as `text/html`.

Three API calls:
```
1. POST /api/v1/sites              → creates site, returns site_id
2. POST /api/v1/sites/{id}/deploys → SHA1 manifest, returns deploy_id
3. PUT  /api/v1/deploys/{id}/files/index.html → upload raw HTML bytes
```

**Critical details:**
- Step 2 body: `{ "files": { "/index.html": "<sha1-hex>" } }` — SHA1 of the HTML content
- Step 3: Content-Type must be `application/octet-stream`, body is raw bytes
- Site name slug: lowercase, hyphens, strip legal suffixes (B.V., N.V., V.O.F.), normalize Dutch chars via NFD, add timestamp suffix

## Claude API — What Works

**Model:** `claude-opus-4-6` — always. Sonnet produces noticeably lower quality design.

**Web Search:** `tools: [{ type: 'web_search_20250305', name: 'web_search' }]` — massive quality lever. Claude researches the business online during generation.

**Streaming is required.** Non-streaming calls hang indefinitely at the HTTP header receive phase (no timeout fires). Use `client.messages.stream()` context manager. The stream immediately opens the connection and delivers chunks as Claude works.

**Thinking + web_search = HANG. Do not combine them.** `thinking: { type: 'adaptive' }` combined with `web_search_20250305` causes the Anthropic API to never return headers. Confirmed through testing. Use web_search alone — it's the bigger quality lever anyway.

**Response handling:** With web_search, the response contains mixed blocks (`server_tool_use`, `web_search_tool_result`, `text`). The HTML is always in the **last `text` block**. Use `stream.get_final_message()` then iterate `reversed(response.content)`.

**Markdown fences:** Claude sometimes wraps HTML in ` ```html ... ``` ` — strip before deploying.

**529 errors:** Opus gets overloaded. Retry 3× with 20s/40s backoff.

**Timing:** Opus with web_search takes 30-90 seconds per site with streaming.

## Scraping — Firecrawl

Firecrawl replaces raw HTTP/BeautifulSoup scraping. It handles JS-rendered sites, bot protection, and returns clean markdown.

**Two-tier approach:**
1. Try multi-page crawl first (`/v1/crawl`, maxDepth=1, limit=5 pages) — gets services, about, team subpages
2. Fall back to single-page scrape (`/v1/scrape`) if crawl fails or times out (45s)
3. If both fail, continue without scraped text — Claude still has Outscraper data + web_search

Result is truncated to 8000 chars before being sent to Claude.

## Google Places API — Reviews & Photos

Uses `Google Place ID` (already in every Pipeline row) to fetch in a single API call:
- Up to 5 real reviews (Dutch language preferred): author, star rating, full text, time ago
- Up to 6 real business photos: direct URL with `maxwidth=1200`

Reviews are included verbatim in the Claude prompt. Photos are passed as direct `<img src>` URLs.

`language=nl` returns Dutch-language reviews where available.

## Lessons Learned the Hard Way

**Claude API:**
- `thinking: adaptive` + `web_search_20250305` hangs indefinitely — never combine them
- Non-streaming Opus calls hang at `_receive_response_headers` — always use streaming
- `thinking.adaptive.budget_tokens` is not a valid parameter — adaptive sets its own budget
- HTML always in last `text` block — iterate `reversed(response.content)`

**Codespaces / OAuth:**
- `run_local_server()` opens a local port; browser redirects to `localhost:8080` which hits the user's machine, not the Codespace
- Fix: use `flow.authorization_url()` + manual redirect URL paste + `flow.fetch_token(code=...)`
- Token stored as `token.pickle` (pickle, not json)

**Google Sheets:**
- `gspread.batch_update()` with A1 notation is faster than `update_cell()` for multiple fields
- Find columns by header name, not hardcoded index — headers can shift
- `update_row()` in `Tools/update_sheet.py` handles this dynamically

**Netlify:**
- File digest: SHA1 must be of the raw UTF-8 bytes, not the string
- Site name collisions prevented by appending Unix timestamp to slug
- Strip B.V., N.V., V.O.F. and normalize Dutch UTF-8 chars (NFD + ASCII encode) before slugifying

**General:**
- About field is sometimes JSON, sometimes plain text — Claude handles both
- Working Hours: `Monday,8am,5pm|Tuesday,8am,5pm` is the Outscraper standard
- Email Status BLACKLISTED/INVALID → don't show email in website

## API Credentials

All stored in `.env` — never hardcoded:
```
ANTHROPIC_API_KEY=        # Claude API
FIRECRAWL_API_KEY=        # Firecrawl website scraping
NETLIFY_TOKEN=            # Netlify deploy
GOOGLE_MAPS_API_KEY=      # Google Places API (reviews + photos)
GOOGLE_SHEETS_ID=         # 1LbFulV5XzbCUHc1mn5uWo9Dt65T60fFJaH9yq4ZcvwY
GOOGLE_SHEETS_PIPELINE=   # Pipeline
GOOGLE_SHEETS_PIPELINE_TEST= # Pipeline test
```

**Google Sheets auth:** OAuth2 via `credentials.json` (Desktop App from Google Cloud Console). Run `python Tools/setup_google_auth.py` once to generate `token.pickle`. In Codespaces: copy-paste flow (no local server).

## Target Audience Context

Dutch tradespeople: plumbers, electricians, HVAC installers, auto repair shops, cleaning companies, chiropractors. Reading on mobile between jobs.

- All visible text in Dutch
- Zero jargon — speak their language
- Real data only — fake testimonials destroy trust instantly
- Fast-loading, premium on mobile
- Clear CTAs (call button, not a form)

## What Success Looks Like

1. Set a row to `GO` in the sheet
2. `python Tools/run_pipeline.py --sheet "Pipeline test" --limit 1` completes without error
3. Live site at `{slug}.netlify.app` loads fast, looks premium, shows real business data
4. Real Google reviews and photos appear on the site
5. Status in sheet updated to `DEPLOYED` with the URL
6. The whole thing runs in under 2 minutes per business
