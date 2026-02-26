#!/usr/bin/env python3
"""
Generate a premium HTML website for a Dutch local business using Claude API.

Uses:
- claude-opus-4-6 (best quality)
- web_search tool (Claude researches the business)
- Font Awesome 6 icons (no emojis)

Usage:
    python Tools/build_website.py --data '{"Business Name":"..."}' [--scraped-text "..."] [--out output.html]

Output: HTML written to --out file (default: .tmp/website.html) and path printed to stdout.
"""

import sys
import os
import re
import json
import time
import argparse
from dotenv import load_dotenv

load_dotenv()
import anthropic

SYSTEM_PROMPT = """You are an expert web designer building premium preview websites for Dutch local businesses (loodgieters, elektriciens, autowerkplaatsen, kappers, fysiotherapeuten, etc).

Your output must be a COMPLETE, READY-TO-DEPLOY single HTML file. Nothing else — no explanations, no markdown fences, no comments outside the HTML. Just the raw HTML starting with <!DOCTYPE html>.

HARD RULES (non-negotiable):
1. Single file: all CSS in <style> tags, all JS inline in <script> if needed. Google Fonts via @import or <link> is fine.
2. Dutch: every word visible to the user must be in Dutch.
3. Real data only: if information is missing, skip that section entirely. NEVER invent services, staff names, testimonials, statistics, review quotes, hours, or anything else not in the provided data.
4. Footer: must include the text "Website gemaakt door AiBoostly" as a clickable link to https://aiboostly.com
5. Call CTA: must have a prominent click-to-call button (href="tel:..."). No contact forms — tradespeople don't fill out forms.
6. Mobile-first responsive design — these owners read on their phones between jobs.
7. No empty links: never output href="". If a social URL is missing from the data, don't render that icon/link.
8. No fake maps: never render a grey placeholder. Use a real Google Maps iframe or make the address a clickable Maps link.
9. Phone links: tel: href must strip all spaces (tel:+31201234567). Display version keeps spaces.
10. Email: if "Email Status" is "BLACKLISTED" or "INVALID", do NOT show the email.
11. No emojis anywhere — ever. Not in headings, buttons, lists, or body text. Use Font Awesome 6 icons instead: load via <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"> and use <i class="fas fa-phone"></i>, <i class="fas fa-map-marker-alt"></i>, <i class="fas fa-star"></i>, etc. Icons should feel intentional and premium, not decorative clutter.

DESIGN PHILOSOPHY:
- Be creative. Choose colors, fonts, and layout that match the business personality and type.
- An electrician site should feel different from a chiropractor's or a plumber's.
- Aim for "holy shit this looks better than what I have" within 3 seconds on mobile.
- Use the business category, scraped branding cues, and your design judgment.
- Modern, premium, obviously better than typical WordPress templates.
- Add subtle CSS animations: fade-in on scroll (IntersectionObserver), hover effects on cards and buttons.
- Use natural Dutch section headings, not corporate uppercase ("Wat we voor u doen" not "ONZE DIENSTEN").

SECTIONS (include only if you have the data):
- Hero: business name, city/location, primary CTA (call button)
- Services: from Subtypes/Services field and scraped website content
- About/Trust: company description, contact person, years in business if found. "About" field is a JSON string — parse it.
- Social proof: Google rating + review count (from "Rating" and "Reviews" fields), link to Google reviews. Never invent review quotes.
- Opening hours: parse "Monday,9am,5pm|Tuesday,9am,5pm|..." format
- Features/amenities: from About JSON (wheelchair access, payment methods, etc)
- Contact: phone, email, full address, Google Maps link/embed, social media links (only if URLs exist in data)
- Strong closing CTA: business-specific, not generic. Include phone number again.
- Footer: AiBoostly credit with link, nav links to sections, © year

OUTPUT: raw HTML only. No markdown. No explanation. Start with <!DOCTYPE html>."""


def build_website(business_data: dict, scraped_text: str = "", reviews_text: str = "") -> str:
    """Call Claude API via streaming and return generated HTML string."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    business_name = business_data.get("Business Name", "dit bedrijf")
    city = business_data.get("City", "")

    user_prompt = f"""Build a premium Dutch preview website for this local business.

BUSINESS DATA:
{json.dumps(business_data, ensure_ascii=False, indent=2)}

CURRENT WEBSITE CONTENT (scraped from their existing site):
{scraped_text[:6000] if scraped_text else "Niet beschikbaar"}

{reviews_text if reviews_text else ""}

INSTRUCTIONS:
1. First use web_search to research "{business_name} {city}" — look for any additional context about the business, but do NOT invent testimonials, statistics, or review quotes from search results.
2. Then generate the complete single-file HTML website following all rules in your system prompt.
3. Before outputting, verify every fact on the page traces back to the BUSINESS DATA or SCRAPED CONTENT above. Remove anything you can't trace.

Output the raw HTML only. Nothing else."""

    messages = [{"role": "user", "content": user_prompt}]

    # Streaming keeps the connection alive and shows real progress.
    # Without streaming, the request hangs silently for minutes waiting for headers.
    last_error = None
    for attempt in range(3):
        try:
            print(f"[build_website] Streaming from Claude (attempt {attempt+1}/3)...", file=sys.stderr)
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=30000,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=messages,
            ) as stream:
                for event in stream:
                    event_type = getattr(event, "type", "")
                    if event_type == "content_block_start":
                        block_type = getattr(getattr(event, "content_block", None), "type", "")
                        if block_type == "thinking":
                            print("[build_website] Thinking...", file=sys.stderr)
                        elif block_type == "tool_use":
                            print("[build_website] Web searching...", file=sys.stderr)
                        elif block_type == "text":
                            print("[build_website] Generating HTML...", file=sys.stderr)
                response = stream.get_final_message()
            break
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 2:
                wait = 20 * (attempt + 1)
                print(f"[build_website] Claude overloaded (529), waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                last_error = e
                continue
            raise
    else:
        raise last_error

    # Extract HTML from the last text block
    html = None
    for block in reversed(response.content):
        if getattr(block, "type", None) == "text":
            html = block.text
            break

    if not html:
        raise RuntimeError("Claude returned no text content block")

    # Strip markdown fences if present
    html = re.sub(r"^```html?\s*\n?", "", html, flags=re.IGNORECASE)
    html = re.sub(r"\n?```\s*$", "", html)
    html = html.strip()

    if not html.lower().startswith("<!doctype") and not html.lower().startswith("<html"):
        raise RuntimeError(f"Claude output doesn't look like HTML. First 200 chars: {html[:200]}")

    print(f"[build_website] Generated {len(html)} chars of HTML for '{business_name}'", file=sys.stderr)
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate HTML website via Claude API")
    parser.add_argument("--data", required=True, help="JSON string of business data")
    parser.add_argument("--scraped-text", default="", help="Scraped website text")
    parser.add_argument("--out", default=".tmp/website.html", help="Output file path")
    args = parser.parse_args()

    business_data = json.loads(args.data)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    html = build_website(business_data, args.scraped_text)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    print(args.out)  # stdout: path to the output file


if __name__ == "__main__":
    main()
