# Agent Instructions

You're working inside the **WAT framework** (Workflows, Agents, Tools) for the **LeadPilot** project — AiBoostly's cold outreach pipeline. This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The Project

**LeadPilot** generates premium Dutch preview websites for local businesses (plumbers, electricians, auto shops, etc.), deploys them live, and writes the URL back to a Google Sheet. The business model: show the owner a better website than they have → convert to paying client.

Pipeline: `Google Sheet (Status=GO) → scrape site → fetch Google reviews+photos → Claude generates HTML → Netlify deploy → write URL back`

Run: `python Tools/run_pipeline.py --sheet "Pipeline test" --limit 1`

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `Workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example: If you need to pull data from a website, don't attempt it directly. Read `Workflows/scrape_website.md`, figure out the required inputs, then execute `Tools/scrape_website.py`

**Layer 3: Tools (The Execution)**
- Python scripts in `Tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## Key Tools

| Script | Purpose |
|--------|---------|
| `Tools/run_pipeline.py` | Main orchestrator — runs GO rows through all stages |
| `Tools/read_sheet.py` | Reads Pipeline rows with Status=GO |
| `Tools/update_sheet.py` | Writes status/URL back to sheet |
| `Tools/scrape_website.py` | Firecrawl multi-page scrape with fallback |
| `Tools/fetch_reviews.py` | Google Places API — real reviews + photos |
| `Tools/build_website.py` | Claude Opus streaming — generates single-file HTML |
| `Tools/deploy_netlify.py` | 3-step file digest deploy to Netlify |
| `Tools/setup_google_auth.py` | One-time Google OAuth setup (Codespaces-compatible) |

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `Tools/` based on what your workflow requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message and trace
- Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
- Document what you learned in the workflow (rate limits, timing quirks, unexpected behavior)
- Example: You get rate-limited on an API, so you dig into the docs, discover a batch endpoint, refactor the tool to use it, verify it works, then update the workflow so this never happens again

**3. Keep workflows current**
Workflows should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the workflow. That said, don't create or overwrite workflows without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

## Critical Technical Rules

**Claude API (build_website.py):**
- Always use `claude-opus-4-6` — Sonnet produces noticeably lower quality
- Always use streaming (`client.messages.stream()`) — non-streaming hangs indefinitely at `_receive_response_headers`
- **NEVER combine `thinking` + `web_search_20250305`** — this causes the API to never return headers, confirmed through testing
- Use `web_search` alone (no thinking parameter) — it's the bigger quality lever
- HTML is always in the **last `text` block** — iterate `reversed(response.content)`
- 529 (overloaded): retry 3× with 20s/40s backoff

**Netlify deployment:**
- MUST use file digest method — ZIP uploads serve HTML as `text/plain`, file digest serves as `text/html`
- Three API calls: create site → SHA1 manifest → upload raw bytes
- SHA1 must be of the raw UTF-8 bytes, not the Python string

**Google Sheets auth (Codespaces):**
- `run_local_server()` won't work — browser redirects to localhost on your machine, not the Codespace
- Use `setup_google_auth.py` — copy-paste flow that prints an auth URL, you paste the redirect URL
- Token stored as `token.pickle` (not token.json)
- Find columns by header name (not hardcoded index) — headers can shift

**Scraping:**
- Firecrawl handles JS-rendered sites and bot protection
- Multi-page crawl first (maxDepth=1, limit=5), fall back to single-page scrape, then continue without if both fail
- Output truncated to 8000 chars before sending to Claude

## The Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the workflow with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

## File Structure

**What goes where:**
- **Deliverables**: Final outputs go to cloud services (Google Sheets, Netlify) where the user can access them directly
- **Intermediates**: Temporary processing files in `.tmp/` that can be regenerated

**Directory layout:**
```
.tmp/                  # Temporary files (generated HTML, debug output). Regenerated as needed.
Tools/                 # Python scripts for deterministic execution
Workflows/             # Markdown SOPs defining what to do and how
.env                   # API keys and environment variables (NEVER store secrets anywhere else)
credentials.json       # Google OAuth app credentials (gitignored)
token.pickle           # Google OAuth user token (gitignored) — generate with setup_google_auth.py
Project.md             # Full business/technical knowledge base — read this first
```

**Core principle:** Local files are just for processing. Anything the user needs to see lives in cloud services (Google Sheet, Netlify URL). Everything in `.tmp/` is disposable.

## Bottom Line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

Stay pragmatic. Stay reliable. Keep learning.
