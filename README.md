# PhD Research Radar v1.3: Vacancy-First Collector

This is a drop-in update for `bbkbhattarai/phd-tracker` hosted on GitHub Pages. **Do not clear browser local storage.** The local application database key is unchanged. Export a backup in Settings before updating.

## What changed

- Removes Google News RSS headline discovery. Searches the ordinary web index and **directly reads public vacancy listing pages**, then checks candidate original pages before publication.
- Prioritises actual advertised PhD studentships, doctoral researcher positions and applications over generic articles/programme descriptions. Postdocs, news, expired adverts and missing/ambiguous deadlines are excluded from the active feed.
- Accepts adverts with a clearly dated future application deadline or explicitly stated rolling intake. Does **not** infer funding or eligibility from a university's reputation.
- Extracts explicit deadlines, funding status, a region, original URL and last verification date. Rejects conflicting deadline information rather than guessing which applies.
- Reports `source_health`, `rejected_reasons`, `page_errors` and candidate totals in `data/opportunities.json`. Sources that block automated access remain visible as failed checks.
- Existing unverified Google News results are **not carried forward** into the refreshed public feed. Previously saved personal applications remain in browser storage.

## Important limitations

This is a **conservative beta**, not a guaranteed comprehensive live university vacancy database. HTML vacancy extraction can miss legitimate positions, websites may restrict bots, Bing RSS can rate-limit or fail, and multiple date formats may be ambiguous. No real-time live-source test was possible in this build environment. Always confirm vacancy status, funding eligibility and application deadline on the institution's own site. Direct source lists are selected high-value pages, not all 125 institutions; the full institution directory remains a reference catalogue. The collector does not directly scrape every institution.

## Installation

1. From your running app, **Settings → Export backup**.
2. Upload this package's files to the **root** of your existing GitHub repository, including `.github/workflows/search.yml`, `scripts/collect.py`, `scripts/sources.json`, `app.js`, and `sw.js`.
3. Do **not** upload or overwrite `data/opportunities.json` from an older ZIP. Leave the current public feed in place until the next workflow run overwrites it. The new collector will intentionally rebuild the feed from newly verified pages, removing old unverified/news results.
4. Commit to `main`.
5. **Actions → Refresh PhD opportunity leads → Run workflow**. Look for green collection and commit steps.
6. Open `https://bbkbhattarai.github.io/phd-tracker/data/opportunities.json`; check `schema_version: 3`, `source_health`, `rejected_reasons`, and `opportunities`. Then refresh the app. A short or empty feed is possible because strict verification rejects unconfirmed candidates.

## Adding directly monitored pages

Edit `scripts/sources.json`. Use `direct_sources` for public, accessible *listing pages* that link to individual current vacancies; `custom_vacancy_urls` for exact advertised vacancy URLs. Source pages recorded in the 125-institution directory are not automatically monitored. An entry saved in the app's Sources tab is local to that browser until also added to the JSON file. `max_candidate_pages` and `max_search_queries` control GitHub Actions resource usage.

## Test locally

```bash
python -m unittest discover -s tests -v
python scripts/collect.py
```

The second command requires internet access. The first uses built-in fixtures and does not.

## Data preservation and privacy

Personal tracked projects and notes stay in your browser's local storage. They are not committed by GitHub Actions. The public results feed in your repository is visible to anyone visiting the site. Different browsers/devices do not synchronize local records.
