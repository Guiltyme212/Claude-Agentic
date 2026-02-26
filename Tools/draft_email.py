#!/usr/bin/env python3
"""
Draft a cold outreach email for a Dutch local business using Claude API.

Uses:
- claude-opus-4-6 (best quality for natural Dutch)
- Streaming (required for Opus)
- No web_search (all data already available from pipeline)

Usage:
    python Tools/draft_email.py --data '{"Business Name":"..."}' --live-url 'https://...'

Output: Email body printed to stdout.
"""

import sys
import os
import json
import time
import argparse
from dotenv import load_dotenv

load_dotenv()
import anthropic

SYSTEM_PROMPT = """Je bent Dan, een jonge AI-specialist die net zijn eigen bureau AiBoostly is gestart.
Je schrijft korte, eerlijke cold emails aan lokale Nederlandse ondernemers.

═══ WIE JE BENT ═══
- Jong, technisch, nuchter
- Je hebt NET een preview-website gebouwd voor dit bedrijf — ongevraagd, als demo
- Je bent geen verkoper. Je bent een vakman die zijn werk laat zien
- Je schrijft zoals je praat: direct, zonder poespas

═══ EMAILSTRUCTUUR (STRIKT) ═══
Regel 1:     Korte persoonlijke opening (gebruik hun naam als beschikbaar)
Regels 2-3:  Wat je voor ze gebouwd hebt + de link
Regels 4-5:  Eén concreet voordeel gebaseerd op HUN bedrijfsdata
Regel 6:     Zachte CTA ("neem gerust een kijkje", "benieuwd wat je ervan vindt")
Afsluiting:  "Groet, Dan" of "Groeten, Dan"

Maximaal 6-8 regels totaal. Elk woord moet er toe doen.

═══ TOON ═══
- Schrijf alsof je een bekende een appje stuurt — maar dan net iets netter
- Wees specifiek: noem hun bedrijfsnaam, hun stad, hun branche
- Als ze goede reviews hebben: noem dat als kracht, niet als verkooptruc
- Eén link, naar de preview-site. Geen andere links
- Geen "Beste heer/mevrouw" — gewoon hun naam, of "Hoi" als je geen naam hebt

═══ VERBODEN ═══
- Woorden: "innovatief", "uniek", "beste", "exclusief", "cutting-edge", "baanbrekend", "toonaangevend"
- Lange alinea's (max 2 zinnen per blok)
- Meer dan één link
- Nepurgentie ("alleen vandaag!", "beperkt aanbod!")
- Specifieke beloftes met cijfers ("300% meer klanten")
- Opsommingen met bullets
- Formele aanhef ("Geachte", "Beste heer/mevrouw")
- Engelse woorden (behalve technische termen die in het Nederlands gangbaar zijn)

═══ HET GEHEIM ═══
De preview-site IS je pitch. Je hoeft niet te verkopen.
Laat het werk spreken. De email is alleen de uitnodiging om te kijken."""


def draft_email(business_data: dict, live_url: str, scraped_text: str = "", reviews_text: str = "") -> str:
    """Call Claude API via streaming and return the email body string."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    business_name = business_data.get("Business Name", "dit bedrijf")
    contact_name = business_data.get("Contact Name", "")
    city = business_data.get("City", "")
    category = business_data.get("Category", "")
    services = business_data.get("Subtypes / Services", "")
    rating = business_data.get("Rating", "")
    reviews_count = business_data.get("Reviews", "")
    phone = business_data.get("Phone", "")

    user_prompt = f"""Schrijf een cold email voor dit bedrijf.

BEDRIJFSGEGEVENS:
Naam: {business_name}
Contactpersoon: {contact_name or "onbekend"}
Stad: {city}
Branche: {category}
Services: {services}
Rating: {rating} ({reviews_count} reviews)
Telefoon: {phone}

PREVIEW WEBSITE:
{live_url}

GESCRAPETE WEBSITE-INHOUD:
{scraped_text[:3000] if scraped_text else "Niet beschikbaar"}

GOOGLE REVIEWS:
{reviews_text[:2000] if reviews_text else "Geen reviews beschikbaar"}

Schrijf NUR de email. Geen uitleg, geen opties, geen markdown."""

    messages = [{"role": "user", "content": user_prompt}]

    last_error = None
    for attempt in range(3):
        try:
            print(f"[draft_email] Streaming from Claude (attempt {attempt+1}/3)...", file=sys.stderr)
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=2000,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                for event in stream:
                    event_type = getattr(event, "type", "")
                    if event_type == "content_block_start":
                        block_type = getattr(getattr(event, "content_block", None), "type", "")
                        if block_type == "thinking":
                            print("[draft_email] Thinking...", file=sys.stderr)
                        elif block_type == "text":
                            print("[draft_email] Drafting email...", file=sys.stderr)
                response = stream.get_final_message()
            break
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < 2:
                wait = 20 * (attempt + 1)
                print(f"[draft_email] Claude overloaded (529), waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                last_error = e
                continue
            raise
    else:
        raise last_error

    # Extract email from the last text block
    email_text = None
    for block in reversed(response.content):
        if getattr(block, "type", None) == "text":
            email_text = block.text
            break

    if not email_text:
        raise RuntimeError("Claude returned no text content block")

    email_text = email_text.strip()
    print(f"[draft_email] Generated {len(email_text)} chars for '{business_name}'", file=sys.stderr)
    return email_text


def main():
    parser = argparse.ArgumentParser(description="Draft cold outreach email via Claude API")
    parser.add_argument("--data", required=True, help="JSON string of business data")
    parser.add_argument("--live-url", required=True, help="Netlify preview URL")
    parser.add_argument("--scraped-text", default="", help="Scraped website text")
    parser.add_argument("--reviews-text", default="", help="Formatted reviews text")
    args = parser.parse_args()

    business_data = json.loads(args.data)
    email = draft_email(business_data, args.live_url, args.scraped_text, args.reviews_text)
    print(email)


if __name__ == "__main__":
    main()
