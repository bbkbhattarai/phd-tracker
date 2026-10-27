# PhD Research Radar v2.5: Source Diagnostics + UK University Monitoring

Incremental update to the working v2.4 GitHub Pages app. It leaves `data/opportunities.json` and all browser storage intact.

New: a dashboard **View source errors** button with detailed failed-source messages and links, full source health diagnostics, rejection statistics, JSON diagnostics export, and **Add an advert URL** on Needs review for blocked listings such as FindAPhD. The manually added records stay local to this browser.

Direct monitoring now includes the official Southampton *Attentive Ear* research studentship and a Southampton engineering PhD projects listing connector. Source: https://www.southampton.ac.uk/study/postgraduate-research/projects/the-attentive-ear-ai-to-decode-listening-fatigue-from .

FindAPhD is still returning HTTP 403 for automated GitHub Actions requests. This update does not circumvent access restrictions or pretend an unmonitored source has been searched. Instead, it adds direct original-university-page monitoring and a manual fallback.

**To deploy:** Export Settings backup. Replace `index.html`, `app.js`, `style.css`, `sw.js`, `scripts/collect.py`, and `scripts/sources.json` with these versions, preserving their paths. Keep your existing `data/opportunities.json` and working `.github/workflows/search.yml`. Commit to main, check site, run the Discover PhD opportunities workflow, and Refresh feed.

**Caution:** A direct vacancy listing can be accessible in a browser but blocked for GitHub Actions. Error diagnostics will reveal this; the source will not be silently treated as zero vacancies. The official Southampton listing says 'competition funded'; this is not guaranteed full funding.
