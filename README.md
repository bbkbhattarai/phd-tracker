# PhD Research Radar v1.5: diagnostic repair

The previous collector rejected every candidate with missing or conflicting deadlines and discarded all old feed entries if they were not revisited. This version:

- Displays verified opportunities in Active Feed.
- Places plausible original PhD vacancy pages missing a reliable deadline into Review Queue. These are NOT confirmed open and must be checked manually.
- Retains previously verified unexpired opportunities, visibly marked as needing recheck, rather than silently deleting them on a single unsuccessful discovery run.
- Continues excluding news, generic degree lists, expired positions, and postdocs.
- Preserves local application data storage key and sources.

**Deploy:** backup using Settings, replace project files except existing `data/opportunities.json`, commit changes, manually run GitHub Action, and hard refresh the website. The workflow will populate `review_candidates` in addition to `opportunities`. Do not upload an empty JSON file over your live feed.

**Important:** This improves visibility and diagnostics, not coverage guarantees. If `candidate_pages` remains 0, the issue is discovery/blocked search services and the next step is dedicated feeds and parsers.

# PhD Research Radar v1.4: Global Monitoring + Application Reminders

**Drop-in update for `bbkbhattarai/phd-tracker`.** Keep your existing `data/opportunities.json` and any browser storage. Export a backup in the app first.

## Fix for empty dashboard while feed is populated

The app now has an **Active Feed** view showing *all current feed records*, not only never-reviewed leads. **New** displays only never-reviewed opportunities. A feed diagnostic above the results confirms count and publication date. The client accepts the `opportunities` array regardless of `schema_version`, and does not exclude entries solely because of a missing `verification` marker. A record in the feed is **not thereby confirmed open**: verify the university vacancy page before applying.

The app fetches `data/opportunities.json` when opened and via **Check for new leads**. A PWA cache version change makes the browser update its old code. If an old install persists, close all app tabs and reload twice.

## Phase 3: Global research monitoring

- Existing direct job listing pages still checked and verified through `scripts/collect.py`.
- Rotating site-index queries check 12 non-portal institutions from the 125-source global catalogue per daily run, in addition to topic-based discovery. These are **search-engine indexed discovery checks, not dedicated direct integrations**. Site-index queries may miss ads, especially where university sites restrict bots.
- Direct vacancy URLs can be specified in `scripts/sources.json` under `custom_vacancy_urls`.
- Sources remain browseable and user-added sources remain local to the device; to include them in scheduled GitHub Actions searches, add them to the repo config/catalogue.
- The resulting public feed reports `source_health`, `institution_sources_checked`, `candidate_pages`, `rejected_reasons`, and `page_errors`. Failed searches cannot support a claim of no open vacancies.

## Phase 4: Deadline / application management

- Upcoming deadlines shown at top of listings for saved or active applications. Settings lets you choose 3/7/14/30-day reminder windows.
- Closing dates remove expired opportunities from **Active Feed** and **New**, while saved/tracked opportunities remain in **Saved/Applications** for historical follow-up.
- Application stages and user-entered verified deadline overrides stay in local browser storage; not synced to GitHub.
- **Notifications are in-app only while you are using the browser app**. No push notifications when closed, no cross-device sync.

## Publish to GitHub Pages

1. Open the existing app and **Settings → Export backup**.
2. Upload this ZIP's extracted files to repo `bbkbhattarai/phd-tracker` root, including hidden `.github` workflow directory. Preserve the existing `data/opportunities.json` (not shipped in ZIP).
3. Commit to `main`. Wait until Pages deployment finishes.
4. Open the app and use **Active Feed**. It should load the *currently published* JSON even before running the collector.
5. Go to GitHub **Actions → Refresh PhD opportunity leads → Run workflow** to refresh worldwide results, then return to the app and click **Check for new leads**.
6. Open the feed URL to verify the `opportunities` array and diagnostics. If the list appears in JSON but not the app, check the app's Feed Status banner, browser console and service worker cache.

## Constraints

No guaranteed scraping for all 125 institutions. Full direct connectors are not yet present for every university, and the Bing RSS/site discovery can miss valid openings. Funding text is extracted heuristically and deadlines from page text; they require manual confirmation at the application source. Deployment to the GitHub account is not performed by creating this ZIP.

## Tests

Run `python -m unittest discover -s tests -v` and `node --check app.js`. Live scraping wasn't validated in this environment.
