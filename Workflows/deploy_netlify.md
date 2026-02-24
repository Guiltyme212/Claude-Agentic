# Workflow: Deploy to Netlify

## Objective
Deploy a single HTML file to Netlify via the file digest API method and return a live HTTPS URL.

## Tool
`Tools/deploy_netlify.py`

## Why File Digest (not ZIP)
ZIP uploads serve HTML as `text/plain` — the browser downloads instead of renders.
File digest method correctly serves `text/html`. This is the only method that works.

## API Flow (3 calls)

### 1. Create site
```
POST https://api.netlify.com/api/v1/sites
Body: { "name": "loodgieter-de-vries-1234567890" }
→ Returns: site_id, site URL
```

### 2. Create deploy with SHA1 manifest
```
POST https://api.netlify.com/api/v1/sites/{site_id}/deploys
Body: { "files": { "/index.html": "<sha1-hex-of-html>" } }
→ Returns: deploy_id
```

### 3. Upload the file
```
PUT https://api.netlify.com/api/v1/deploys/{deploy_id}/files/index.html
Content-Type: application/octet-stream
Body: raw HTML bytes
→ Deploy goes live
```

## Site Naming
- Slug from business name: lowercase, hyphens, max 40 chars
- Strip legal suffixes: B.V., N.V., V.O.F.
- Normalize Dutch characters: ë→e, é→e, ö→o (via NFD + ASCII encode)
- Append Unix timestamp: prevents name collisions
- Final: `{slug}-{timestamp}` (max ~51 chars, well within Netlify limit)

## Output
Live URL: `https://{site-name}.netlify.app`

## Failure Handling
- HTTP errors from Netlify API raise immediately (no retry — Netlify API is reliable)
- If site name is taken: timestamp suffix prevents this in practice

## CLI Usage
```bash
python Tools/deploy_netlify.py --html .tmp/test.html --name "Loodgieter de Vries B.V."
# Output: https://loodgieter-de-vries-1234567890.netlify.app
```

## Credentials
`NETLIFY_TOKEN` from `.env` — passed as `Authorization: Bearer {token}` header.
