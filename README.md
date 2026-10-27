# PhD Research Radar v2.2 | Recruitment discovery test build

An update to the working GitHub Pages PhD Radar 2.0, focused on **actual doctoral recruitment** in hearing sciences, audiology, auditory neuroscience, psychoacoustics, cochlear implants, and hearing technology.

## New in v2.2

- **AUDITORY announcements collector:** Monitors publicly posted, dated PhD recruitment announcements in the AUDITORY archive (`mhonarc/2026/threads.html`), with a backup archive endpoint. Does not treat general mailing-list posts as vacancies.
- **Direct studentship monitoring:** Adds a University College London studentship project in deaf children and cochlear implants, with explicit deadline extraction.
- **More lab recruitment sources:** Adds UT Dallas Neuroaudiology, Duke Auditory & Communication Systems, and UConn Audette Lab, in addition to prior lab sources.
- **Better cards:** Highlights recruitment evidence, intended intake, supervisor/contact where extractable, announcement date, and explicitly uncertain deadlines.
- **Safer date handling:** Does not invent a year for an archive announcement saying only “apply by December 15.” This is shown as a note requiring confirmation.
- **Stronger source diagnostics:** Sources blocked by HTTP 403 or failures are recorded. Existing non-expired records are retained when a source is temporarily unavailable.
- **App data compatibility:** Continues using the `phdradar_clean_v2` browser-storage key. No migration necessary from v2.0 or v2.1.

## Known limitations

1. FindAPhD currently returns HTTP 403 to the GitHub Action collector. That is a **blocked source**, not zero vacancies. The app does not bypass that restriction.
2. Not all 125 references have direct vacancy parsers. The Sources tab distinguishes monitored sources from references.
3. A lab invitation without a future application deadline remains in **Needs review**. Funding eligibility and intake must be confirmed at the original institution.
4. Monitoring the AUDITORY archive may be temporarily unavailable; source diagnostics will show any failure.
5. GitHub Actions schedules are not exact, and the website Refresh button only retrieves the last published feed.
6. Personal application history is held in the current browser. Export regular JSON backups.

## Deploy to an EXISTING GitHub Pages repository

1. From the running app, open **Settings** and **Export JSON backup** first.
2. Unzip the update. Upload or replace files into the **root of your existing repository**, not a nested folder. Preserve paths under `scripts/`, `assets/`, and `.github/workflows/`.
3. **Do not delete or replace `data/opportunities.json`.** The update ZIP intentionally excludes it. GitHub Actions will refresh it.
4. Commit files to `main`.
5. Open **Actions → Discover PhD opportunities → Run workflow** and verify all steps completed successfully.
6. Open `/data/opportunities.json` on the GitHub Pages site to confirm a new `generated_at` value. Inspect `source_health` and `review_queue`.
7. Reopen the app and select **Refresh feed**. Force-reload if your browser retains old static files.

## Expected test outcomes

- `opportunities`: source-confirmed deadline positions (such as UCL, if still open and accessible).
- `review_queue`: genuine lab recruitment calls and published PhD announcements whose current availability or deadline requires confirmation.
- `source_health`: one entry per monitored source, showing successes, 403 errors, and other failures.
- The FindAPhD sources may continue to show 403 errors; this should not stop the other collectors.

The updated code was tested offline using fixtures, including an end-to-end run with source blocking, one future-deadline studentship, and two unverified recruitment records. Live GitHub Actions execution and access to remote sites must be verified after deployment.

## Project files

- `.github/workflows/search.yml`: scheduled and manual collector; installs dependencies.
- `scripts/collect.py`: site monitors and eligibility / deadline parsing.
- `scripts/sources.json`: centralized monitored and reference source configuration.
- `app.js`, `index.html`, `style.css`: PWA interface and local application records.
- `sw.js`: versioned service worker.
- `tests/`: offline regression checks.
