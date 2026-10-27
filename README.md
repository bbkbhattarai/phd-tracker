# PhD Research Radar v2.6: UK & Scotland Research Sources

This is a **drop-in update** to the working v2.5 static GitHub Pages app. It keeps the same local browser storage key (`phdradar_clean_v2`) and its JSON feed format (`schema_version: 2`).

## Newly monitored sources

- British Academy of Audiology (BAA): PhD Opportunities directory, individual original-project link verification; BAA professional vacancies watched for updates.
- University of Nottingham: official studentship vacancies index (`jobslive.nottingham.ac.uk/vacancies.aspx?cat=213`), restricted to hearing-relevant doctoral advertisements.
- Strathclyde: postgraduate research index and a nature-inspired acoustic sensors doctoral advertisement (broader than clinical audiology; fit is labelled).
- University of Edinburgh Acoustics and Audio Group: PhD recruitment enquiries with availability and funding unconfirmed.
- RNID: PhD studentship **funding scheme** (normally supervisor-applied); monitored for updates, never automatically displayed as a student-level job.
- British Society of Audiology (BSA): small grants, research funding and PhD top-ups; monitored only, not a full-funded PhD vacancy feed.
- British Cochlear Implant Group (BCIG): professional vacancy page; monitored for changes, not automatically treated as PhD recruitment.
- Nottingham NIHR Biomedical Research Centre Hearing theme, Queen Margaret University funded PhDs and CASL, Edinburgh Neuroscience, and Scottish university opportunities: monitored for changes.

Additional references: jobs.ac.uk, Postgraduate Studentships, BNA, UCL funded PhDs, Manchester project finder, Edinburgh Neuroscience listings, QMU PhD pathways, and Nottingham's hearing research team.

## Why some sources only show in Sources

Funding bodies and societies publish grants and clinical jobs as well as research recruitment, and degree directories are not open jobs. To prevent the earlier issue with irrelevant results, these are checked for content changes and shown in the Sources diagnostics, not represented as open PhD positions. A changed research page means **review required**, not an opening confirmed.

The index collectors parse eligible individual links, then attempt to read the original advert. If the original listing denies automated access, this is reported as an error rather than invented data. BAA's directory includes older projects and links to FindAPhD, which may still deny automated requests with HTTP 403.

## Scottish coverage

Scotland has its own regional filter when Scottish listings exist. The **UK** filter also includes Scotland. University of Nottingham is in England; Scottish sources are provided separately.

## Deploy to existing GitHub Pages

1. Open your existing app and **Settings > Export JSON backup**.
2. Download and unzip this update.
3. Replace `app.js`, `index.html`, `style.css`, `sw.js`, `scripts/collect.py` and `scripts/sources.json` with the matching files in this package. The package includes the other unchanged website assets and workflow for convenience.
4. **Keep the live `data/opportunities.json`.** This ZIP deliberately does not contain it, so historical records and source-change comparisons survive.
5. Keep your working `.github/workflows/search.yml` (it already installs requirements before calling `collect.py`).
6. Commit the files to `main`. Open the website and refresh; **Sources** should show the expanded catalogue immediately.
7. Run **Discover PhD opportunities** once in GitHub Actions and **Refresh feed** inside the app to see search results and per-source status.

Browser-installed PWAs may cache static files until an update; this release bumps the service worker cache to `phd-radar-rebuild-v2.6`.

## Validation

Offline extraction and pipeline regression tests, Python bytecode compilation, JavaScript syntax checking, browser UI smoke test (when available), and ZIP integrity verification. Live automated visits from GitHub Actions are **not** guaranteed: each monitored source reports success, no matching adverts, an extraction problem, or an HTTP/access error.
