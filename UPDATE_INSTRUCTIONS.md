# Updating the existing GitHub Pages site to v2.6

Back up in-app data in Settings first. Then replace these six files in the existing `bbkbhattarai/phd-tracker` repository:

- `app.js`
- `index.html`
- `style.css`
- `sw.js`
- `scripts/collect.py`
- `scripts/sources.json`

**Do not overwrite** `data/opportunities.json` (not included). **Keep** the working `.github/workflows/search.yml` (it should run `python -m pip install -r scripts/requirements.txt` before the Python collection). No new dependencies are required.

Commit to `main`, check Sources in GitHub Pages, then run **Discover PhD opportunities** in GitHub Actions and **Refresh feed** in the app.

BAA and Nottingham student-vacancy directories are parsed for hearing-relevant PhD advertisements. RNID, BSA, BCIG and selected Nottingham/Scottish research pages are *content-change monitored* and do not generate an open studentship card without an actual verifiable individual advertisement. Grant calls that require a supervisor's application are not student job vacancies.
