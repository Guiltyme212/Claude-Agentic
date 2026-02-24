# LeadPilot — Project Knowledge Base

## What This Is

LeadPilot is the cold outreach engine behind **AiBoostly**, an AI automation agency in Arnhem, Netherlands. It generates premium preview websites for Dutch local businesses using their real data, deploys them to live URLs, then sends cold emails showing the business owner "here's what your website could look like."

The business model is a trojan horse: the €390 website gets them in the door, the €149/month AI automation services are the real revenue.

## The Pipeline (What It Does)

```
Google Sheet row (business data from Outscraper)
  → Scrape their current website for extra content
  → Feed everything to Claude API (with web search to research the business)
  → Claude generates a complete single-file HTML website
  → Deploy to Netlify via file digest API
  → Write live URL back to sheet
  → (Later) Send cold email with preview link
```

Each business gets a live `.netlify.app` URL they can click and see immediately.

## Data Source

Outscraper scrapes Google Maps for Dutch local businesses (plumbers, electricians, auto repair, cleaning companies, chiropractors, etc). Raw data lands in the "Raw Data (Outscraper)" sheet (112 columns), then gets processed into the "Pipeline" sheet for the website builder.

### Pipeline Sheet — Columns That Matter

These are the columns you'll actually use (the sheet has 90 columns but most are Netlify deploy response junk from columns 37+):

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

### Raw Data (Outscraper) — Extra Fields Available

The raw sheet has richer data if needed: `reviews_per_score` (breakdown by 1-5 stars), `photos_count`, `verified` status, `business_status`, `owner_title`, `latitude`/`longitude`, `company_insights` (LinkedIn data like employee count, founded year, industry). These can be pulled in if useful for richer websites.

### Google Sheet ID

Spreadsheet: `1LbFulV5XzbCUHc1mn5uWo9Dt65T60fFJaH9yq4ZcvwY`
- Production sheet: "Pipeline" (1994 rows)
- Test sheet: "Pipeline test" (1643 rows)
- Raw data: "Raw Data (Outscraper)" (2001 rows)

The `Status` column drives the pipeline. Set to `GO` → pipeline picks it up → updates through stages → ends at `DEPLOYED` with live URL or `ERROR` with notes.

## The Generated Websites — Design Philosophy

The goal is to make each business owner think "holy shit, this looks better than my current site" within 3 seconds of opening the preview link. These are cold leads — they didn't ask for this. The site has to be so good they can't ignore it.

**You have creative freedom on design.** Choose colors, layout, typography, and animations that best fit the business type. An electrician's site should feel different from a chiropractor's. A premium auto shop should look different from a neighborhood plumber. Use the business category, their current branding (scraped from their site), and your judgment. The only visual constant: it should feel modern, premium, and obviously better than whatever WordPress template they're currently running.

**Hard constraints (non-negotiable):**
- Single HTML file, ALL CSS in `<style>` tag — no external CSS files (Google Fonts via @import or link is fine)
- Mobile-first responsive — these people read on their phones between jobs
- ALL visible text in Dutch
- ONLY real data — NEVER invent services, reviews, team members, or anything else. If a field is missing, skip that section entirely.
- Footer must include: "Website gemaakt door AiBoostly" linking to https://aiboostly.com
- Must have a click-to-call CTA button (not a contact form — tradespeople don't fill out forms)

**Sections to include (skip any that lack data):**
- Hero with business name, location, primary CTA
- Services/specialties (from Subtypes/Services + scraped website content)
- About/trust section (description, contact person, years active if found)
- Social proof (Google rating + review count if available, link to reviews)
- Opening hours (parsed from `Monday,8am,5pm|Tuesday,8am,5pm|...` format)
- Features/amenities from About field (JSON with wheelchair access, payment methods, etc)
- Contact details (phone, email, address, Google Maps link, social media)
- Footer

**What makes a preview site convert (trigger the business owner to respond):**
- It loads fast and looks polished on mobile
- It immediately shows THEIR real business name, address, phone — personal, not generic
- The design is clearly better than their current site
- It includes real Google reviews/rating — they see their reputation showcased
- The CTA works (tap to call)
- It feels like a finished product, not a mockup

## Netlify Deployment — File Digest Method

**This is the only method that works correctly.** We tried ZIP uploads — they serve HTML as `text/plain` instead of rendering it. File digest serves as `text/html`.

Three API calls:

```
1. POST /api/v1/sites              → creates site, returns site_id
2. POST /api/v1/sites/{id}/deploys → SHA1 manifest of files, returns deploy_id
3. PUT  /api/v1/deploys/{id}/files/index.html → upload actual HTML as octet-stream
```

**Critical details:**
- Step 2 body: `{ "files": { "/index.html": "<sha1-hex>" } }` — the SHA1 is of the HTML content
- Step 3: Content-Type must be `application/octet-stream`, body is raw HTML bytes
- Site name slug: lowercase, hyphens, no spaces, max ~50 chars, add timestamp suffix to prevent duplicates
- Token: stored in `.env` as `NETLIFY_TOKEN`

## Claude API — What Works

**Model:** `claude-opus-4-6` produces the best websites. `claude-sonnet-4-20250514` is faster/cheaper but noticeably lower quality in design decisions and copy.

**Web Search:** Adding `tools: [{ type: 'web_search_20250305', name: 'web_search' }]` lets Claude research the business (Google reviews, KvK registration, reputation, extra services). This is a massive quality lever — sites built with research context are richer, more accurate, and feel personalized rather than template-generated.

**Extended Thinking:** `thinking: { type: 'enabled', budget_tokens: 10000 }` improves layout decisions and code quality. Compatible with web_search.

**System prompt strategy:** Don't hardcode a fixed design spec. Give Claude the hard constraints (single HTML file, Dutch text, real data only, AiBoostly footer), the business data, and tell it to choose a design that fits the business type. Include the scraped website content so Claude can pick up on existing branding, colors, and tone.

**Response handling:** With web_search and thinking enabled, the response contains mixed content blocks (`thinking`, `tool_use`, `tool_result`, `text`). The HTML is always in the **last `text` block**. Filter for `type === 'text'` and take the last one.

**Markdown fences:** Claude sometimes wraps HTML in ` ```html ... ``` ` — strip these before deploying.

**529 errors:** Opus gets overloaded regularly. Implement retry with backoff (3 attempts, 15-20s wait between). Sonnet almost never 529s.

**Timeouts:** Opus with web_search + thinking can take 60-120 seconds. Set HTTP timeout to at least 180s.

**Tokens:** stored in `.env` as `ANTHROPIC_API_KEY`

## Scraping the Business Website

Before calling Claude, scrape the business's current website to extract text content. This gives Claude context about their services, team, and tone.

- Simple HTTP GET with a browser User-Agent
- Strip `<script>`, `<style>` tags, then all HTML tags
- Collapse whitespace, truncate to ~5000-8000 chars (saves tokens)
- If scrape fails (SSL errors, timeouts, no website), continue anyway — Claude has Outscraper data + web_search

## Lessons Learned the Hard Way

**n8n-specific (if relevant to your tooling choice):**
- `fetch()` does NOT exist in n8n Code tool sandbox — must use `this.helpers.httpRequest()`
- n8n Code nodes have 60-second execution timeout — too short for Opus with web_search
- n8n HTTP Request nodes respect custom timeouts (set to 120-180s for Claude)
- `$fromAI()` parameter passing to HTTP Request tools is unreliable — Code tools with `query.param` work better
- Agent/langchain nodes add complexity for zero benefit when a single API call does the job
- Google Sheets "appendOrUpdate" nodes break when columns change — fragile

**General pipeline gotchas:**
- Some business websites have SSL certificate errors → handle gracefully, skip scraping
- Working Hours format varies: `Monday,8am,5pm|Tuesday,8am,5pm` is the Outscraper standard
- About field is sometimes JSON, sometimes plain text — handle both
- Photo URLs are Google streetview thumbnails — they work as hero backgrounds with dark overlay
- Logo URLs are sometimes broken or low-res — always have a fallback (just text)
- Business names can contain BV, B.V., parentheses — strip these from URL slugs
- Dutch UTF-8 characters (ë, é, ö, etc) need `normalize('NFD')` before slugifying

## API Credentials

All stored in `.env` — never hardcoded anywhere else:
```
ANTHROPIC_API_KEY=       # Claude API (sk-ant-api03-...)
NETLIFY_TOKEN=           # Netlify deploy (nfp_...)
GOOGLE_SHEETS_ID=1LbFulV5XzbCUHc1mn5uWo9Dt65T60fFJaH9yq4ZcvwY
```

**Google Sheets:** Uses OAuth2 credentials (`credentials.json` / `token.json`). Production sheet: "Pipeline", test sheet: "Pipeline test".

## The Current n8n Implementation (Reference)

There's a working n8n workflow (`LeadPilot Website Builder`, ID `d7z4MtRCE4eyl0GR`) on `aiboostly.app.n8n.cloud` that does this pipeline. It works but is fragile — n8n has limitations with long-running AI tasks, Google Sheets column changes break nodes, and the fixed dark-theme design spec produces samey-looking sites. The flow:

```
Sheet Trigger → Filter GO → First Row → Status: SCRAPING
  → Fetch Website (HTTP GET) → Extract Text Content (strip HTML)
  → Status: BUILDING → Prepare Claude Request (build JSON body)
  → Claude API (HTTP POST, 120s timeout) → Extract HTML (last text block)
  → Status: DEPLOYING → Build SHA1 hash → Netlify Create Site
  → Merge Site Info → Deploy file digest → Status: DEPLOYED + URL
  
  Error path: On Error → Fetch Execution Data → Extract Error → Status: ERROR
```

The goal of this repo is to replicate — and improve — this pipeline outside of n8n, where we have full control over execution time, retry logic, and error handling.

## Target Audience Context

These websites target Dutch tradespeople: plumbers, electricians, HVAC installers, auto repair shops, cleaning companies, chiropractors. They're reading on mobile between jobs. The generated sites and any outreach must:

- Be in Dutch (all visible text)
- Use zero jargon — speak their language
- Show real data only — fake testimonials or invented services destroy trust
- Load fast and look premium on mobile
- Have clear CTAs (call button, not a contact form)

## What Success Looks Like

1. Feed a business name/data into the pipeline
2. Get a live, beautiful, mobile-responsive preview website at `{slug}.netlify.app`
3. The site uses real data, researched reviews, and looks premium
4. The URL gets written back for the outreach step
5. The whole thing runs reliably without manual intervention