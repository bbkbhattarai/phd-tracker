# PhD Research Radar v2.4: Worldwide vacancy and lab expansion

This is a **targeted update** for your existing GitHub Pages repository:
`https://github.com/bbkbhattarai/phd-tracker`

## Replace these files

- `scripts/collect.py`
- `scripts/sources.json`
- `app.js`
- `index.html`
- `style.css`
- `sw.js`

Upload folder contents to the **repository root**, preserving the `scripts` directory.

**Do NOT delete or replace `data/opportunities.json`.** This ZIP intentionally excludes the feed. The GitHub Actions collector updates it on the next run.

**Do NOT replace `.github/workflows/search.yml`.** Your existing working **Discover PhD opportunities** workflow can continue to run `python scripts/collect.py` and commit the updated feed. The Python requirements are unchanged.

## Steps

1. In the current app, open Settings and export a JSON backup of your local application data.
2. Replace the six files listed above in the existing repository and commit to `main`.
3. In Actions, manually run **Discover PhD opportunities** once to generate an updated feed.
4. Check `data/opportunities.json`: `generated_at`, `opportunities`, `review_queue` and `source_health`.
5. Open `https://bbkbhattarai.github.io/phd-tracker/` and select **Refresh feed**. A hard refresh may be needed on a previously installed PWA.
6. Check both **Opportunities** (future deadlines) and **Needs review** (recruitment leads or adverts with unconfirmed deadlines), and use the regional dropdown in each view.

## Monitoring and limitations

- 31 configured scheduled discovery sources, including **5 FindAPhD URLs known to return HTTP 403 from GitHub Actions**. These blocked sources are *not* claimed as searched successfully.
- 8 direct individual advertised PhD pages, 3 institutional vacancy indexes, 14 recruiting laboratory pages and the AUDITORY recruitment archive.
- 46 research / programme reference pages. Reference listings are useful links, but they are not individually scanned for vacancies.
- Geographical coverage of directly monitored pages: UK, continental Europe, USA, Canada, Australia, New Zealand and Hong Kong. The wider Asian research directory is reference-only until audited vacancy connectors are built.
- No new listings are fabricated or manually hardcoded into the feed. Every displayed record must come from an accessible original page during a successful collection, or be a previously collected record carried forward as needing recheck.
- The collector can misinterpret complex website layouts and date statements. Check the original vacancy before applying, especially funding terms and eligibility. A blocked page means **unknown**, never “no vacancies”.
- In-app custom source links are private local settings; adding them **does not** automatically schedule GitHub Actions crawling. For scheduled monitoring, add an appropriate adapter to `scripts/sources.json` and collector logic.
- Your saved applications and notes remain in local browser storage under the **same key** used by v2.3. GitHub hosts only public feed data and app code. Back up periodically, especially before browser resets.

## Validation

- Collector Python syntax compiles.
- 21 offline pytest cases pass, including UK/EU/Australian dates, Canadian/NZ/HK lab recruitment, index parsing, closed lab rejection and mock end-to-end pipeline.
- JavaScript syntax checks pass.
- **Live GitHub Actions checks have not been run in this environment.** Some institutional sites may return 403, 404, timeouts or unfamiliar layouts; review source diagnostics after deployment.
