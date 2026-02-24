#!/usr/bin/env python3
"""
Deploy an HTML file to Netlify using the file digest method.

The only method that serves HTML correctly (ZIP uploads serve as text/plain).
Three API calls: create site → file digest deploy → upload file.

Usage:
    python Tools/deploy_netlify.py --html path/to/index.html --name "Loodgieter Jansen"

Output: live URL printed to stdout (e.g. https://loodgieter-jansen-1234567890.netlify.app)
"""

import sys
import os
import re
import time
import hashlib
import unicodedata
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

NETLIFY_API = "https://api.netlify.com/api/v1"


def slugify(name: str) -> str:
    """Convert business name to a URL-safe slug."""
    # Strip legal suffixes
    name = re.sub(r"\b(b\.?v\.?|n\.?v\.?|v\.?o\.?f\.?|bvba|ltd|gmbh)\b", "", name, flags=re.IGNORECASE)
    # Normalize Dutch/accented characters to ASCII
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    # Lowercase, replace anything non-alphanumeric with hyphens
    name = re.sub(r"[^a-z0-9]+", "-", name.lower())
    name = name.strip("-")
    return name[:40]


def deploy(html: str, business_name: str) -> str:
    """
    Deploy HTML string to Netlify.
    Returns the live HTTPS URL.
    """
    token = os.getenv("NETLIFY_TOKEN")
    if not token:
        raise RuntimeError("NETLIFY_TOKEN not set in .env")

    auth_headers = {"Authorization": f"Bearer {token}"}
    html_bytes = html.encode("utf-8")
    sha1 = hashlib.sha1(html_bytes).hexdigest()
    timestamp = int(time.time())
    slug = slugify(business_name)
    site_name = f"{slug}-{timestamp}"

    # Step 1: Create site
    r = requests.post(
        f"{NETLIFY_API}/sites",
        headers={**auth_headers, "Content-Type": "application/json"},
        json={"name": site_name},
        timeout=30,
    )
    r.raise_for_status()
    site_data = r.json()
    site_id = site_data["id"]
    site_url = site_data.get("ssl_url") or site_data.get("url") or f"https://{site_name}.netlify.app"
    print(f"[deploy_netlify] Created site: {site_url}", file=sys.stderr)

    # Step 2: Create deploy with file digest manifest
    r = requests.post(
        f"{NETLIFY_API}/sites/{site_id}/deploys",
        headers={**auth_headers, "Content-Type": "application/json"},
        json={"files": {"/index.html": sha1}},
        timeout=30,
    )
    r.raise_for_status()
    deploy_id = r.json()["id"]
    print(f"[deploy_netlify] Deploy created: {deploy_id}", file=sys.stderr)

    # Step 3: Upload the actual HTML file
    r = requests.put(
        f"{NETLIFY_API}/deploys/{deploy_id}/files/index.html",
        headers={**auth_headers, "Content-Type": "application/octet-stream"},
        data=html_bytes,
        timeout=60,
    )
    r.raise_for_status()
    print(f"[deploy_netlify] File uploaded. Live at: {site_url}", file=sys.stderr)

    return site_url


def main():
    parser = argparse.ArgumentParser(description="Deploy HTML to Netlify")
    parser.add_argument("--html", required=True, help="Path to HTML file")
    parser.add_argument("--name", required=True, help="Business name (used for URL slug)")
    args = parser.parse_args()

    with open(args.html, "r", encoding="utf-8") as f:
        html = f.read()

    url = deploy(html, args.name)
    print(url)  # stdout: the live URL


if __name__ == "__main__":
    main()
