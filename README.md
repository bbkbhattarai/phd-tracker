# PhD Research Radar 2.0 (clean rebuild)

A GitHub Pages-ready Progressive Web App for finding **actual advertised PhD positions** and **research labs explicitly recruiting doctoral students** in hearing sciences, audiology, auditory neuroscience, psychoacoustics, electrophysiology, hearing aids and cochlear implants.

This is a **new codebase**, not a patch to the prior Radar versions. It uses a new localStorage key (`phdradar_clean_v2`) and **does not remove or overwrite old local data**. Old data is available via Settings → Import previous app data if you install this on the same web origin and browser. Export a backup from your old version before deployment.

## Deploy to GitHub Pages

1. Back up current browser records through the existing app's Settings.
2. Download and extract this archive; copy **all** files to the root of a GitHub repository, including `.github/workflows/search.yml` and `.nojekyll`. Remove old `app.js`, `style.css`, `sw.js` and legacy files to prevent confusion.
3. GitHub → Settings → Pages → Deploy from branch → `main` / root.
4. GitHub → Actions → **Discover PhD opportunities** → Run workflow. Workflow needs contents: write (set in YAML, subject to repository/organization permissions).
5. Verify `data/opportunities.json` has a non-null `generated_at` timestamp; open the site and select **Refresh feed**.
6. On your existing browser, Settings → **Import previous app data**, verify records and export new backup.

The GitHub Action is scheduled daily at 07:17 UTC, but GitHub scheduled runs may be delayed or skipped. In-app Refresh downloads the *last published* data, not a new search.

## What is *actually monitored* in this first release

- **5 FindAPhD listing search pages:** extracts individual `/phds/project/` links, opens each project's page, screens for hearing relevance and evidence of doctoral recruitment, and extracts funding/deadline when evident.
- **4 laboratory recruiting pages:** checks recruiting-language patterns and sends promising leads to *Needs review*, not automatically confirmed. A lab page may stay online for years, so verify current recruitment and intake.
- A worldwide **source catalogue** includes additional university/programme/directory reference URLs, but **these are not all directly scraped**. A source appearing in the catalogue does not imply scheduled monitoring.
- **AUDITORY mailing list** is available as a reference source but archival announcements are **not automatically ingested** yet.

Other portals (jobs.ac.uk, EURAXESS, AcademicTransfer) are in the reference directory and require specific supported adapters before they can supply automated leads. Where a site blocks automated requests, Source Diagnostics displays the failure. Do not interpret zero accepted records as proof that no openings exist.

## Verified versus review

- **Opportunities**: PhD project page opened with a future deadline observed (not a guarantee that the university continues accepting applications). University project pages can contain stale data, and exact deadline/funding/eligibility should be checked before applying.
- **Needs review**: doctoral project page without a clear deadline, older leads that could not be rechecked, or lab page explicitly claiming to recruit PhD students. Never presented as confirmed open.
- Expired records fall out of active feeds. Saved local application records persist.
- No fabricated projects, no news-headline ingestion, no invented dates or funding guarantees.

## Data privacy and limitations

- GitHub hosts only public HTML/JS, source configuration and public results JSON.
- Bookmarks, notes, application status, seen markers, added personal source URLs are stored only within browser localStorage. They do not sync between browsers/devices. Do not store sensitive identity documents in notes.
- Source additions in the Sources screen do **not** automatically modify the scheduled GitHub collector. To add a scheduled source, update `scripts/sources.json` and add an appropriate parser if needed.
- Deadline reminders display while app is open; no notification service / background push.
- PWA static cache explicitly uses network-first asset loading and network-only (with optional existing cache fallback) for JSON feeds.
- Permission to access sites and reliability of HTML layouts vary. Respect robots rules, rate limits and website terms when extending adapters.

## Development / offline tests

```sh
python -m pip install -r scripts/requirements.txt
python tests/test_collector.py
python scripts/collect.py
python -m http.server 8000
```

Open `http://localhost:8000/`. Note that running the collector requires internet access; tests use offline sample fixtures only.
