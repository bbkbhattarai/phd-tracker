# Update existing GitHub Pages app to v2.7

1. Open your current app and **Settings → Export JSON backup**.
2. Unzip the v2.7 package.
3. In `bbkbhattarai/phd-tracker`, replace these files in their existing directories:
   - `index.html`, `app.js`, `style.css`, `sw.js`
   - `scripts/sources.json`
   - `README.md` (optional)
4. **Keep** the existing `scripts/collect.py`, `scripts/requirements.txt` and `.github/workflows/search.yml`, unless you deliberately want to replace them with the identical included versions. Their behaviour does not need to change for LinkedIn search shortcuts and monitored pages.
5. **Do not overwrite** `data/opportunities.json`. The ZIP intentionally omits it.
6. Commit to `main`, reopen the app, and open **Sources → LinkedIn: PhD recruitment searches**.
7. In GitHub Actions, manually run **Discover PhD opportunities** once to check the newly added universities. Then use **Refresh feed** in the app.

**Important**: LinkedIn searches are opened manually; no scraping is performed. New university sources are monitored for page changes, not automatically claimed as job adverts. Future dedicated extraction connectors may be added for institutions with accessible project listings.
