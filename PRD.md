# AiBoostly — Product Requirements Document (PRD)

> **Single source of truth for all AiBoostly development.**
> Notion version: https://www.notion.so/3185346b7d3f81cfa476dfff8ef0d14c
> Last updated: March 3, 2026

---

## Product Overview

**AiBoostly** is an AI-native agency that automatically generates and delivers premium websites to Dutch small businesses *before they request them* — then converts those into recurring AI automation retainers.

Aligned with Y Combinator's Spring 2026 RFS: *"AI-native agencies that deliver finished work upfront to win business before the contract is signed."*

> We don't sell software to help businesses build websites — we build the website and sell it to them. Software margins on agency revenue.

---

## Business Model

**Revenue Streams:**
- **EUR 390 one-time** — AI-generated website (foot-in-the-door)
- **EUR 149/month** — AI automation retainer (chatbot, booking, auto-replies, analytics)
- **Custom pricing** — Enterprise/premium clients

**Unit Economics:**
- Cost per site (AI generation): ~EUR 0.50
- Margin: 99.9%
- One retainer client = EUR 2,778 first year
- 50 retainer clients = EUR 7,450 MRR

**Target Market:**
- 3.5M+ Dutch SMEs with bad or no website
- Focus: plumbers, electricians, auto repair, cleaning companies, chiropractors
- Expansion: restaurants, salons, dentists

---

## System Architecture

### Three Core Systems

| System | What It Does | Where It Lives |
|---|---|---|
| **AiBoostly Website** | Landing page + admin dashboard + payment | Lovable > aiboostly.com |
| **LeadPilot Pipeline** | Auto-generates websites & sends emails | Python > Railway (24/7) |
| **Google Sheet** | Lead database + status tracker + API backend | Google Sheets + Apps Script |

### How They Connect

```
+---------------------+                       +----------------------+
|   LOVABLE WEBSITE   | <===================> |    GOOGLE SHEET      |
|  aiboostly.com      |   (Apps Script API)   |  lead database       |
|  /admin dashboard   |                       |  status tracking     |
+---------------------+                       +----------+-----------+
                                                         |
                                              reads GO > | < writes status
                                                         |
                                              +----------v-----------+
                                              |  RAILWAY PIPELINE    |
                                              |  LeadPilot (Python)  |
                                              |  polls every 2 min   |
                                              +----------------------+
```

---

## System 1: AiBoostly Website (Lovable)

**URL:** aiboostly.com
**Built with:** Lovable (React vibe-coding platform)
**Deployed on:** Lovable hosting

### Pages

| Page | Purpose | Status |
|---|---|---|
| `/` | Landing page — sells the service, builds trust | Live |
| `/admin` | Dashboard — shows pipeline status, lead tracking | Live |
| `/claim` | Payment page (planned) — Mollie checkout for prospects | Planned |

### Admin Dashboard (`/admin`)
- Reads from Google Sheet via Google Apps Script API
- Shows leads with color-coded status badges
- Statuses match the pipeline (see Status Flow below)
- Links to live Netlify preview sites
- CORS fixes applied and write-back working

### Current Work (separate Lovable Claude Code agent)
- Building out the dashboard functionality
- Connecting to Google Sheet for live status updates

---

## System 2: LeadPilot Pipeline (Railway)

**Repo:** Claude-Agentic (GitHub > Railway auto-deploy)
**Runtime:** Python 3.12 on Railway
**Entry point:** `railway_main.py`
**Polling:** Every 120 seconds for GO rows

### Pipeline Flow

| Step | What Happens | Tool | Sheet Status |
|---|---|---|---|
| 1. Scrape | Extract business website content | Firecrawl API (multi-page crawl, single-page fallback) | SCRAPING |
| 2. Reviews | Fetch real Google reviews + photos | Google Places API | (no status change) |
| 3. Generate | Create full single-file HTML website in Dutch | Claude Opus 4.6 + web_search + adaptive thinking | BUILDING |
| 4. Deploy | Push to Netlify via file digest | Netlify API (3-step: create site > SHA1 manifest > upload) | DEPLOYING > Deployed |
| 5. Draft Email | Write personalized cold email in Dutch | Claude Opus 4.6 + adaptive thinking | EMAILING > Email Draft Written |
| 6. Send Email | Send preview link to business owner | Microsoft 365 SMTP (multipart: plain + HTML) | SENDING > Email sent succesfully |

**Note:** Payment (Mollie) is NOT part of the automated pipeline. A payment link is included in the email, but payment processing is handled externally.

### Email skip conditions
- If `Email Status` is BLACKLISTED or INVALID: skip email entirely, stay at Deployed
- If no email address in sheet: skip send, stay at Email Draft Written

### Key Technical Details

**Website Generation (`Tools/build_website.py`):**
- Model: `claude-opus-4-6` with `web_search_20250305` tool + adaptive thinking (`thinking: {"type": "adaptive"}`)
- Max tokens: 30,000
- Output: Single-file HTML with inline CSS, Google Fonts, Font Awesome 6 icons (no emojis)
- Language: Dutch
- Design: Mobile-first, layout variety per business type, scroll animations, hover effects
- Reviews: Only verified Google reviews from Places API (no fabrication)
- Quality checklist enforced via system prompt
- Cost: ~EUR 0.50/site
- 529 retries: 3 attempts with 20s/40s backoff

**Email Drafting (`Tools/draft_email.py`):**
- Model: `claude-opus-4-6` with adaptive thinking (no web_search)
- Max tokens: 2,000
- Tone: Personal, informal Dutch — "Dan texting you" feel
- No marketing buzzwords, no bullet lists, max 6-8 lines
- 529 retries: same as website generation

**Email Sending (`Tools/send_email.py`):**
- SMTP: smtp.office365.com:587 with STARTTLS
- From: dan@aiboostly.com (Microsoft 365 via GoDaddy)
- Multipart/alternative: plain text + designed HTML template
- HTML template (`Tools/email_template.py`): table-based layout, CTA button to preview site, inline styles, Outlook-compatible
- SMTP retries: 3 attempts with 5s/10s/20s backoff
- Test mode: `SMTP_TEST_EMAIL` env var redirects all emails to test address

**Netlify Deploy (`Tools/deploy_netlify.py`):**
- Method: File digest (SHA1 hash > deploy manifest > octet-stream upload)
- NOT zip method (zip breaks content-type, serves as text/plain)
- Site slugs: lowercase, hyphens, strip B.V./N.V./V.O.F., max 40 chars, timestamp appended
- Auto SSL included

**Scraping (`Tools/scrape_website.py`):**
- Firecrawl multi-page crawl first (maxDepth=1, limit=5 pages)
- Falls back to single-page scrape if crawl fails/times out (45s timeout)
- Returns empty string on any error — pipeline continues without scraped content
- Output truncated to 8,000 chars

**Reviews & Photos (`Tools/fetch_reviews.py`):**
- Google Places API: single API call returns reviews + photo references
- Max 5 reviews, max 6 photos per business
- Photos: direct Google Maps photo URLs (maxwidth=1200)
- Language: Dutch (`language=nl`)
- Returns empty arrays on error — pipeline continues

**Error Handling:**
- Failed steps > Status = ERROR with details in Notes column (truncated to 500 chars)
- Pipeline continues to next row after an error
- Details logged to stderr (visible in Railway logs)
- Claude 529 errors retried automatically (3 attempts)
- SMTP errors retried automatically (3 attempts)

### Railway Configuration

**Entry:** `railway_main.py`
**Build:** Nixpacks (auto-detected from `requirements.txt`)
**Start:** `python railway_main.py` (defined in `railway.toml`)

**How `railway_main.py` works:**
1. Decodes `GOOGLE_TOKEN_PICKLE_B64` env var to `token.pickle` on disk
2. Imports `Tools/run_pipeline.py`
3. Polls in infinite loop: run pipeline > sleep `POLL_INTERVAL` seconds > repeat
4. Catches and logs exceptions without crashing

**Key files:**

| File | Purpose |
|---|---|
| `railway_main.py` | Polling worker entry point |
| `railway.toml` | Build/deploy config (nixpacks + start command) |
| `.python-version` | Python 3.12 |
| `Tools/run_pipeline.py` | Pipeline orchestrator (processes GO rows) |
| `Tools/scrape_website.py` | Firecrawl multi-page scrape with fallback |
| `Tools/fetch_reviews.py` | Google Places API (reviews + photos) |
| `Tools/build_website.py` | Claude Opus 4.6 streaming HTML generation |
| `Tools/deploy_netlify.py` | 3-step Netlify file digest deploy |
| `Tools/draft_email.py` | Claude Opus 4.6 email drafting |
| `Tools/send_email.py` | SMTP email sending with retry |
| `Tools/email_template.py` | HTML email template builder (table-based, Outlook-compatible) |
| `Tools/read_sheet.py` | Read GO rows from Google Sheet |
| `Tools/update_sheet.py` | Write status/URL/notes back to sheet (with color coding) |
| `Tools/sheets_client.py` | Shared Google Sheets auth (gspread + OAuth) |
| `Tools/setup_google_auth.py` | One-time Google OAuth setup (Codespaces copy-paste flow) |

### WAT Framework

The codebase follows the WAT (Workflows, Agents, Tools) architecture:

| Layer | What | Where |
|---|---|---|
| **Workflows** | Markdown SOPs (instructions) | `Workflows/*.md` |
| **Agents** | Claude (decision-making, orchestration) | `CLAUDE .md` |
| **Tools** | Python scripts (deterministic execution) | `Tools/*.py` |

Workflow files: `pipeline.md`, `scrape_website.md`, `build_website.md`, `deploy_netlify.md`, `draft_email.md`, `send_email.md`

---

## System 3: Google Sheet (Database)

**Sheet ID:** `1LbFulV5XzbCUHc1mn5uWo9Dt65T60fFJaH9yq4ZcvwY`

### Tabs

| Tab | Purpose | Rows |
|---|---|---|
| Pipeline | Production leads | ~1,994 |
| Pipeline test | Testing/dev | ~1,643 |
| Raw Data (Outscraper) | Outscraper exports | ~2,001 |

### Key Columns
- Business Name, Full Address, City, Street, Postal Code, Phone, Email, Website
- Google Place ID, Rating, Reviews, Reviews Link
- Category, Subtypes / Services
- Email Status (RECEIVING / BLACKLISTED / INVALID)
- Status (pipeline stage)
- Preview URL (Netlify link, filled after deploy)
- Email Draft (filled by draft_email step)
- Sent Date (filled after send)
- Notes (error details)
- Contact Name, Contact Title, Contact Phone, Contact LinkedIn
- Facebook, Instagram
- Working Hours, About (JSON string)
- Photo URL, Logo URL

### API Layer
- Google Apps Script deployed as web app
- Handles read/write from Lovable dashboard
- CORS-enabled for cross-origin requests

### Google Sheets Auth
- Uses `gspread` library with OAuth2 credentials
- `credentials.json` (OAuth Desktop App from Google Cloud Console) — gitignored
- `token.pickle` generated by `Tools/setup_google_auth.py` — gitignored
- Railway: `GOOGLE_TOKEN_PICKLE_B64` env var decoded to `token.pickle` at startup
- Auto-refresh of expired tokens via `sheets_client.py`

---

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API (Opus 4.6) | — |
| `GOOGLE_MAPS_API_KEY` | Google Places API for reviews + photos | — |
| `NETLIFY_TOKEN` | Netlify deploy API | — |
| `GOOGLE_SHEETS_ID` | Lead database sheet ID | — |
| `GOOGLE_TOKEN_PICKLE_B64` | Base64 of token.pickle for Sheets auth on Railway | — |
| `FIRECRAWL_API_KEY` | Web scraping API | — |
| `SMTP_HOST` | SMTP server | smtp.office365.com |
| `SMTP_PORT` | SMTP port | 587 |
| `SMTP_USER` | SMTP login email | — |
| `SMTP_PASSWORD` | Microsoft 365 password | — |
| `SMTP_FROM_NAME` | Display name in emails | Dan van AiBoostly |
| `SMTP_FROM_EMAIL` | From address (defaults to SMTP_USER) | — |
| `SMTP_TEST_EMAIL` | Test mode: redirect all emails to this address | — |
| `PIPELINE_SHEET` | Which sheet tab to process | Pipeline test |
| `PIPELINE_LIMIT` | Max leads per polling cycle | 5 |
| `POLL_INTERVAL` | Seconds between polling cycles | 120 |
| `GOOGLE_SHEETS_PIPELINE_TEST` | Default sheet name for local CLI runs | Pipeline test |

---

## Status Flow

```
GO > SCRAPING > BUILDING > DEPLOYING > Deployed > EMAILING > Email Draft Written > SENDING > Email sent succesfully
```

Each status has a color-coded background in the sheet (defined in `Tools/update_sheet.py`):

| Status | Color |
|---|---|
| GO | Light blue |
| SCRAPING | Yellow |
| BUILDING | Orange |
| DEPLOYING | Purple |
| Deployed | Green |
| EMAILING | Light cyan |
| Email Draft Written | Soft blue |
| SENDING | Light pink |
| Email sent succesfully | Bright green |
| ERROR | Red |

**Trigger:** Manually set a row to GO (or batch-set via dashboard)
**Automatic:** Everything after GO is fully automated by Railway pipeline
**Error:** Any step can fail > ERROR with details in Notes column

---

## Quality Standards

### Website Generation Rules
- Layout variety per business type (no identical templates)
- Only verified Google reviews (never fabricated)
- Human-sounding Dutch section headers ("Wat we voor u doen" not "ONZE DIENSTEN")
- Subtle CSS animations: fade-in on scroll (IntersectionObserver), hover effects on cards/buttons
- Mobile-first responsive design
- Font Awesome 6 icons throughout (no emojis anywhere)
- Real Google Maps links (no grey placeholder boxes)
- No invented statistics, services, staff, or review quotes
- Phone number formatting: `tel:+31302322221` for links, "030 - 232 2221" for display
- Image onerror fallback handlers
- Social media links validated (only render if URL exists in data)
- "Website gemaakt door AiBoostly" footer link to https://aiboostly.com
- Click-to-call CTA button (no contact forms)
- No empty `href=""` links
- If Email Status is BLACKLISTED/INVALID, email is not shown on site

### Quality Checklist
- Hero communicates WHO, WHAT, WHERE within 3 seconds on mobile
- Call button visible without scrolling on mobile
- No invented content — every fact traces back to business data or scraped content
- Layout looks different from typical AI card-grid template
- All animations subtle and fast (under 400ms)
- Site works with JavaScript disabled
- Google Maps is a real link, not a grey box
- Would a business owner think a human designer built this?

---

## Roadmap

### Phase 1-4: COMPLETE
- Business registered + domain + email
- Leads scraped and loaded via Outscraper
- Website generation engine with quality improvements
- Hackathon demo with live payments (Sjonnie Gitaar)
- Admin dashboard live at aiboostly.com/admin
- Google Apps Script API deployed

### Phase 5: Cloud Pipeline (IN PROGRESS)
- LeadPilot Python pipeline built
- Railway hosting selected + GitHub connected
- Railway deploy configured (start command working)
- Production env vars configured
- First cloud test run (GO > full flow)

### Phase 6: Launch & Scale (NEXT)
- Run 10 test leads end-to-end on Pipeline test sheet
- QA generated sites — verify layout variety + real data
- Switch to Pipeline sheet (production leads)
- Batch processing ramp-up: 50 leads/day
- Monitor email delivery rates

### Phase 7: Revenue & Conversion
- First EUR 390 website sale
- Follow-up email sequence for non-responders
- Phone follow-up script for warm leads
- Hit EUR 5K MRR milestone

### Phase 8: Growth & YC
- Case studies from first 10 paying clients
- Expand to new verticals
- Y Combinator application with live revenue
- Hit EUR 10K MRR
- First hire

---

## Proven Examples

| Business | Type | Preview URL | Status |
|---|---|---|---|
| Sjonnie Gitaar | Guitar shop | sjonniegitaar.netlify.app | Live + Mollie payment |
| KwikFit Utrecht | Auto repair | kwikfit-utrecht.netlify.app | Deployed |
| Van Kuilenburg | Auto repair | van-kuilenburg.netlify.app | Deployed |
| OnzeAuto | Auto repair | onzeauto.netlify.app | Deployed |
| Boerhof Accountants | Accounting | boerhof-accountants.netlify.app | Deployed |

---

## Key Decisions & Learnings

**Claude Code > n8n** — Python agent approach proved more reliable than n8n workflows. n8n workflow (ID: d7z4MtRCE4eyl0GR) still exists but is fragile.

**Direct SMTP > Instantly** — Instantly's API had persistent `not_sending_status` issues. Microsoft 365 SMTP just works.

**File digest > ZIP** — Netlify ZIP uploads broke content-type (served as text/plain). SHA1 file digest is reliable (serves as text/html).

**Quality > Speed** — Opus 4.6 at ~EUR 0.50/site beats cheaper models. 99.9% margin supports this.

**Real data > Fake data** — Google Places API reviews and photos eliminate fabrication risk. Pipeline skips sections with missing data rather than inventing content.

**Streaming required** — Non-streaming Claude API calls hang indefinitely waiting for response headers. Always use `client.messages.stream()`.

**Adaptive thinking + web_search** — The build_website tool uses both adaptive thinking and web_search together. The CLAUDE.md warns against combining explicit thinking with web_search (which caused hangs), but adaptive thinking mode works.

**Pipeline never dies** — Scraping and review fetching return empty results on error rather than raising exceptions. The pipeline continues with whatever data it has.
