# PhD Research Radar v2.8

This is a **drop-in GitHub Pages update** for the existing `bbkbhattarai/phd-tracker` site. It does not reset or include `data/opportunities.json`, and it keeps the existing localStorage key (`phdradar_clean_v2`).

## New in v2.8

### Editable search criteria

The **Settings → Search criteria** panel lets you:

- add, remove, and review research phrases that identify relevant PhD opportunities;
- optionally add excluded phrases;
- save draft changes locally, without changing any personal application record;
- download or copy a valid `search_terms.json` configuration;
- open the configuration file in GitHub's editor.

**Important sync boundary:** A public GitHub Actions job cannot read private browser localStorage. New terms **do not change scheduled discovery** until you replace `scripts/search_terms.json` in GitHub, commit to `main`, and run the discovery workflow. Once published, these literal phrases are used by the Python collector to match candidates from its configured sources. Adding a term does not automatically add university websites or unlock restricted sites such as FindAPhD.

Manual LinkedIn search shortcuts additionally include the first 16 research phrases in the current browser draft. LinkedIn remains **manual only**.

### Added UK sources

- **University of Warwick**: Life Sciences funded studentships, Medical School fully funded research projects, and WMG doctoral vacancies. These are `monitor_only_sources`: page checks and change notices, **not** automatic creation of PhD listings from general funding pages.
- **Postgraduate Studentships**: the doctoral-funding listings index is now an `institution_indexes` source using the `postgraduate_funding` adapter. It follows only individual `/opportunity/<slug>/<id>` links that match a configured research phrase. Each linked page is read and further screened for a real PhD opening. Generic degree promotions are rejected. A broader funding index is monitored for changes.

The Postgraduate Studentships site advertises a mixture of Masters, doctoral programmes, general scholarships, and promotional material. Not every item is a research vacancy. The collector may return `no_vacancies_parsed`, `no_current_vacancy`, or a source error if relevant advertisements aren't present or access is restricted.

## Deploy the update

1. Open PhD Radar → Settings and **Export JSON backup**.
2. Upload the contents of this ZIP to your **existing repository**, preserving relative paths:
   - root: `index.html`, `app.js`, `style.css`, `sw.js`
   - scripts: `collect.py`, `sources.json`, **new** `search_terms.json`
3. Do **not** overwrite your current `data/opportunities.json` or your working `.github/workflows/search.yml`.
4. Commit all changes to the `main` branch.
5. Open GitHub Actions → **Discover PhD opportunities** → **Run workflow**.
6. Once the new feed is published, open your web app and click **Refresh feed**. Check Sources diagnostics for Warwick and Postgraduate Studentships.

## Change search topics in the future

1. Open **Settings → Search criteria**.
2. Add or remove phrases; click × to remove. The draft is saved to **this browser** automatically.
3. Click **Copy JSON** or **Download search_terms.json**.
4. Open `scripts/search_terms.json` in GitHub (link provided inside the app). Click **Edit**, replace its full content with the copied JSON, and **Commit changes**. You may also upload the downloaded JSON to the `scripts/` directory to replace the existing file.
5. Start **Discover PhD opportunities** in GitHub Actions, or let the daily scheduled workflow run. When finished, refresh the feed in the app.

If you update only the local browser draft, scheduled discovery stays unchanged. When the GitHub file is updated but GitHub Actions hasn't rerun yet, the app displays **Published, next search pending** when comparing the current feed with the published configuration.

## What remains unchanged

- Application notes, saved leads, statuses and browser-only data.
- The existing date/funding checks, review queue, and source diagnostics.
- Existing LinkedIn searches are manual shortcuts; no scraping is performed.
- The FindAPhD 403 restriction is not bypassed.

## Testing

Eight offline Python tests passed, including term validation, literal matching, date filtering, and Postgraduate Studentships-style listing extraction. JavaScript and Python syntax checks passed. A browser UI test using mocked local JSON confirmed adding/removing phrases, exporting JSON, and saving an opportunity. Live Warwick and Postgraduate Studentships collector runs on GitHub Actions have **not yet been validated**.
