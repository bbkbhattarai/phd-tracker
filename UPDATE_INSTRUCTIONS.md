# Upgrade from PhD Research Radar 2.0 / 2.1 to 2.2

**Important: do not overwrite `data/opportunities.json`.** The package excludes that file to preserve your currently published feed and collected leads.

Upload the ZIP contents into the root of `bbkbhattarai/phd-tracker` on GitHub. This is an update, not a second nested repository.

1. Export your local records from Settings first.
2. Replace `app.js`, `index.html`, `style.css`, `sw.js`, `scripts/collect.py`, `scripts/sources.json`, and other matching included files.
3. Check that `.github/workflows/search.yml` is present and unchanged if your current one already works. The ZIP has a working workflow with the dependency-installation step.
4. Run **Discover PhD opportunities** manually in GitHub Actions. Do not use the Pages deployment workflow as a substitute.
5. Open https://bbkbhattarai.github.io/phd-tracker/data/opportunities.json to inspect the new timestamp and source-health statuses.
6. Open https://bbkbhattarai.github.io/phd-tracker/ and click **Refresh feed**. Look in both **Opportunities** and **Needs review**.

The search is broader but still source-limited. FindAPhD's 403 restriction is not resolved by this update. Recruitment announcements without verified deadlines stay in Needs review, not Opportunities.
