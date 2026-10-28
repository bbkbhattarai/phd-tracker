# Update to v2.8 (keep your existing site and data)

**Replace root files:** `index.html`, `app.js`, `style.css`, `sw.js`.

**Replace files inside `scripts/`:** `collect.py`, `sources.json`.

**Add this NEW file inside `scripts/`:** `search_terms.json`.

**Keep unchanged:** `data/opportunities.json`, `.github/workflows/search.yml`, `scripts/requirements.txt`, existing saved browser data.

Commit to the `main` branch, then run the existing **Discover PhD opportunities** GitHub Action. Refresh your browser's feed.

## Future term edits

Settings → Search criteria → add/remove phrase → **Copy JSON** → edit `scripts/search_terms.json` on GitHub → paste and commit → run discovery workflow. Browser-only edits do not reach GitHub Actions by themselves. This version is **not** a live server-side settings API.

## New monitoring

Warwick university research/studentship pages = monitored for changes and errors, not auto-vacancy extraction. Postgraduate Studentships PhD-funding index = candidate link extraction with topic matching and individual advert verification, subject to site access. Check source diagnostics after the first run.
