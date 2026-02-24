#!/usr/bin/env python3
"""
Fetch real Google reviews and photos for a business using the Places API.

Single API call returns both reviews and photo references.
Photo URLs are constructed as direct Google image links.

Usage:
    python Tools/fetch_reviews.py --place-id ChIJa7Jk9JftyEcRj7xCUSjEG_0

Output: JSON with 'reviews' and 'photos' keys.
"""

import sys
import json
import argparse
import os
import requests
from dotenv import load_dotenv

load_dotenv()

PLACES_API = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTO_BASE = "https://maps.googleapis.com/maps/api/place/photo"


def fetch(place_id: str, max_reviews: int = 5, max_photos: int = 6) -> dict:
    """
    Fetch reviews and photos for a Google Place ID in a single API call.
    Returns dict: { "reviews": [...], "photos": [...] }
    Returns empty dict on any error.
    """
    if not place_id or not place_id.strip():
        return {"reviews": [], "photos": []}

    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("[fetch_reviews] GOOGLE_MAPS_API_KEY not set, skipping", file=sys.stderr)
        return {"reviews": [], "photos": []}

    try:
        r = requests.get(
            PLACES_API,
            params={
                "place_id": place_id.strip(),
                "fields": "reviews,photos",
                "language": "nl",
                "reviews_sort": "most_relevant",
                "key": api_key,
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        if data.get("status") != "OK":
            print(f"[fetch_reviews] API status: {data.get('status')} — {data.get('error_message', '')}", file=sys.stderr)
            return {"reviews": [], "photos": []}

        result = data.get("result", {})

        # ── Reviews ────────────────────────────────────────────────────
        reviews = []
        for rev in result.get("reviews", [])[:max_reviews]:
            text = rev.get("text", "").strip()
            if not text:
                continue
            reviews.append({
                "author": rev.get("author_name", ""),
                "rating": rev.get("rating", 0),
                "text": text,
                "time_ago": rev.get("relative_time_description", ""),
            })

        # ── Photos ─────────────────────────────────────────────────────
        photos = []
        for photo in result.get("photos", [])[:max_photos]:
            ref = photo.get("photo_reference")
            if not ref:
                continue
            url = (
                f"{PHOTO_BASE}"
                f"?maxwidth=1200"
                f"&photo_reference={ref}"
                f"&key={api_key}"
            )
            photos.append(url)

        print(
            f"[fetch_reviews] Got {len(reviews)} review(s) and {len(photos)} photo(s) "
            f"for place_id={place_id}",
            file=sys.stderr,
        )
        return {"reviews": reviews, "photos": photos}

    except Exception as e:
        print(f"[fetch_reviews] Failed for place_id={place_id}: {e}", file=sys.stderr)
        return {"reviews": [], "photos": []}


def format_for_prompt(place_data: dict) -> str:
    """Format reviews and photos as a prompt block for Claude."""
    reviews = place_data.get("reviews", [])
    photos = place_data.get("photos", [])
    sections = []

    if reviews:
        lines = ["REAL GOOGLE REVIEWS (include these verbatim in the website):"]
        for r in reviews:
            stars = "★" * r["rating"] + "☆" * (5 - r["rating"])
            lines.append(f'\n{stars} {r["author"]} ({r["time_ago"]})')
            lines.append(f'"{r["text"]}"')
        sections.append("\n".join(lines))

    if photos:
        lines = ["REAL BUSINESS PHOTOS (use these as <img> src in the website):"]
        for i, url in enumerate(photos, 1):
            lines.append(f"Photo {i}: {url}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Fetch Google reviews and photos for a Place ID")
    parser.add_argument("--place-id", required=True, help="Google Place ID")
    args = parser.parse_args()

    data = fetch(args.place_id)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
