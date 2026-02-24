#!/usr/bin/env python3
"""
Scrape a business website using Firecrawl API.

Uses Firecrawl's crawl endpoint to scrape the homepage + key subpages
(services, about, team, contact) for richer context.

Falls back to single-page scrape if crawl fails or times out.

Usage:
    python Tools/scrape_website.py --url https://example.com [--max-chars 8000]

Output: clean markdown to stdout. Exits cleanly on failure so the pipeline continues.
"""

import sys
import re
import argparse
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MAX_CHARS = 8000
FIRECRAWL_API = "https://api.firecrawl.dev/v1"
CRAWL_POLL_INTERVAL = 3  # seconds between status checks
CRAWL_TIMEOUT = 45       # max seconds to wait for crawl


def _get_headers():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _scrape_single(url: str, max_chars: int) -> str:
    """Fallback: scrape just the homepage."""
    response = requests.post(
        f"{FIRECRAWL_API}/scrape",
        headers=_get_headers(),
        json={
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("success"):
        return ""

    text = data.get("data", {}).get("markdown", "")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:max_chars] + "..." if len(text) > max_chars else text


def _crawl_site(url: str, max_chars: int) -> str:
    """Crawl homepage + subpages, return combined markdown."""
    r = requests.post(
        f"{FIRECRAWL_API}/crawl",
        headers=_get_headers(),
        json={
            "url": url,
            "maxDepth": 1,
            "limit": 5,
            "scrapeOptions": {
                "formats": ["markdown"],
                "onlyMainContent": True,
            },
        },
        timeout=30,
    )
    r.raise_for_status()
    crawl_id = r.json().get("id")
    if not crawl_id:
        raise RuntimeError("No crawl ID returned")

    print(f"[scrape_website] Crawl started: {crawl_id}", file=sys.stderr)

    # Poll for completion
    deadline = time.time() + CRAWL_TIMEOUT
    while time.time() < deadline:
        time.sleep(CRAWL_POLL_INTERVAL)
        r = requests.get(
            f"{FIRECRAWL_API}/crawl/{crawl_id}",
            headers=_get_headers(),
            timeout=15,
        )
        r.raise_for_status()
        result = r.json()
        status = result.get("status")

        if status == "completed":
            pages = result.get("data", [])
            print(f"[scrape_website] Crawl done: {len(pages)} page(s)", file=sys.stderr)

            sections = []
            for page in pages:
                page_url = page.get("metadata", {}).get("sourceURL", "")
                md = page.get("markdown", "").strip()
                if md:
                    sections.append(f"--- PAGE: {page_url} ---\n{md}")

            combined = "\n\n".join(sections)
            combined = re.sub(r"\n{3,}", "\n\n", combined).strip()
            return combined[:max_chars] + "..." if len(combined) > max_chars else combined

        if status == "failed":
            raise RuntimeError(f"Crawl failed: {result}")

    raise TimeoutError(f"Crawl timed out after {CRAWL_TIMEOUT}s")


def scrape(url: str, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """
    Scrape url via Firecrawl crawl (multi-page) with single-page fallback.
    Returns empty string on any error — pipeline continues without scraped content.
    """
    if not url or not url.startswith("http"):
        return ""

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("[scrape_website] FIRECRAWL_API_KEY not set, skipping scrape", file=sys.stderr)
        return ""

    # Try multi-page crawl first
    try:
        text = _crawl_site(url, max_chars)
        print(f"[scrape_website] Crawled {len(text)} chars from {url}", file=sys.stderr)
        return text
    except Exception as e:
        print(f"[scrape_website] Crawl failed ({e}), falling back to single-page scrape", file=sys.stderr)

    # Fallback to single-page scrape
    try:
        text = _scrape_single(url, max_chars)
        print(f"[scrape_website] Single-page scraped {len(text)} chars from {url}", file=sys.stderr)
        return text
    except Exception as e:
        print(f"[scrape_website] Firecrawl failed for {url}: {e}", file=sys.stderr)
        return ""


def main():
    parser = argparse.ArgumentParser(description="Scrape website via Firecrawl")
    parser.add_argument("--url", required=True, help="URL to scrape")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    args = parser.parse_args()

    text = scrape(args.url, args.max_chars)
    print(text)


if __name__ == "__main__":
    main()
