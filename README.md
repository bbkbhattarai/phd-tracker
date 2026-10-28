# PhD Research Radar 2.7 | LinkedIn searches + UK universities

A drop-in update for https://bbkbhattarai.github.io/phd-tracker/ . The GitHub Pages PWA keeps personal application data in the same browser storage key as v2.6 (`phdradar_clean_v2`). The scheduled search collector still runs from `.github/workflows/search.yml`.

## New in 2.7

- **LinkedIn discovery shortcuts**: Ten keyword searches for PhD recruitment posts and LinkedIn Jobs. These open LinkedIn in a new tab. They are **manual, not automatic feed ingestion**. LinkedIn prohibits unauthorized scraping; this app does not request or parse LinkedIn pages from GitHub Actions. Use **Add a post I found** or the **Add an advert URL** button to save promising LinkedIn recruitment notices locally in the review list, with verification required.
- **15 added university/research-page monitors**: Glasgow, Aberdeen, University of the West of Scotland, Sheffield, Salford (LAURA and Sound Futures), Swansea, Leicester, University of Lancashire, Lancaster University and Manchester. These are checked for reachability/content changes. A changed page is reported in Sources diagnostics rather than automatically presented as a verified open position.
- **A more discoverable LinkedIn shortcut** on the Needs review screen.
- **Versioned service-worker cache** so updated code loads properly when GitHub Pages publishes.

### Why not auto-import LinkedIn posts?

LinkedIn's public User Agreement and Help Centre explicitly restrict third-party crawling and automated extraction. The project provides first-party LinkedIn search links and local manual capture. Using an approved API or explicit permission would be required for any future automated import.

### Monitoring levels

`listing_sources`, `direct_vacancies`, `institution_indexes`, `announcement_sources`, and confirmed `lab_sources` can create PhD records after validation. `monitor_only_sources` report page availability/changes **without** creating PhD records. `reference_sources` are directory links only. `linkedin_searches` are **manual search shortcuts**, not GitHub Actions sources.

Several university pages embed FindAPhD. Those do not give us authorized access to FindAPhD's 403-restricted listings, and are therefore monitored as pages without claims of vacancy extraction.

### Deployment

1. Back up your saved records from Settings.
2. Upload the replacement files to the *existing* `bbkbhattarai/phd-tracker` repository, preserving folder paths.
3. Do not replace the existing `data/opportunities.json` and do not reset browser site data.
4. Commit to `main`. Visit Sources to see the LinkedIn search panel and the new catalogue.
5. Run **Discover PhD opportunities** in GitHub Actions to get a fresh `source_health` report from the new university monitors. Then click **Refresh feed** in the app.

The configured monitors may return errors if the university blocks automation; source diagnostics will report those rather than claiming zero PhD opportunities. No automatic LinkedIn leads should be expected.

### Validation

- Python source compilation and JS syntax checks.
- Sources JSON verified, no duplicate IDs.
- HTML controls and links verified.
- Offline collector monitoring checks and package integrity.
- Live GitHub Actions and LinkedIn search availability are not validated by these tests.
