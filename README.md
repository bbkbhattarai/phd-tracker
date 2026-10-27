# PhD Research Radar | GitHub Pages PWA

A personal PhD lead discovery and application tracker for hearing sciences. **Private records are stored only in the browser localStorage**; they are not sent to GitHub. The public discovery feed is committed to the repository.

## Publish on GitHub Pages

1. Create a **public** GitHub repository named `phd-radar`.
2. Upload **all contents of this folder**, including `.github/workflows/search.yml` (GitHub's upload web interface can handle nested folders when dragging folder contents, but check hidden files; Git command line or GitHub Desktop is more reliable).
3. In repository **Settings > Pages**, set **Build and deployment > Deploy from a branch**, select `main` and `/ (root)`, and Save.
4. In **Actions > Refresh PhD opportunity leads > Run workflow**, start the first collection. If prompted, enable workflows.
5. Visit `https://YOUR-GITHUB-USERNAME.github.io/phd-radar/`. To install on mobile, use Safari Share > Add to Home Screen (iOS), or browser menu > Install app / Add to Home Screen (Android). Desktop install availability varies by browser.
6. If Actions cannot push, check repository **Settings > Actions > General > Workflow permissions** and enable read/write permissions (subject to your repo/org policies).

## Add more search sources

- **App > Sources > Add a source** stores a private local bookmark plus a one-click targeted web search.
- For automatic daily searches, add query phrases or custom domain names in `scripts/sources.json` **in the GitHub repository**, then commit. E.g. `"custom_sites":["ucl.ac.uk","nottingham.ac.uk"]`.
- The app cannot automatically write to your GitHub repository from a static webpage. The configuration is deliberately separate for privacy and security.

## Important boundaries

- Search uses Google News public RSS as an initial discovery mechanism, not direct scraping of all PhD portals. This is incomplete, and some sources block indexing or never appear in news results. The workflow reports errors and can be extended with source-specific permitted APIs/feeds.
- A 'lead' is **not a verified open PhD position**; funding and closing dates must be verified at the linked institution. Unknown dates are not removed as 'expired'. Leads older than 120 days are removed from the **public feed**, but local saved application records are not exported to GitHub. To retain past feed items offline, export local backups.
- In-app deadline reminders show while the app is open, not push notifications while it is closed. Scheduled GitHub Action runs may be delayed or skipped.
- Data does **not** automatically sync across browsers, devices or private/incognito sessions. Clear-site-data actions may wipe local records. Export a JSON backup regularly.
- Google News result URLs may point to secondary articles and may not resolve directly to a university listing.
- GitHub Pages hosts public static files. Never commit application notes, personal information or exported backup files.


## Worldwide geography update
The scheduled collector now uses worldwide search queries and additional regional institutional searches. The user interface shows a region selector only for regions represented in the currently displayed results. Unknown institutions appear as **Location unspecified** rather than being assigned incorrectly. Google News RSS cannot guarantee comprehensive worldwide monitoring or reliable live vacancy status. Additional universities in the Sources tab are reference links; to add domains to the scheduled worldwide collector, edit `scripts/sources.json` in GitHub.

### Upgrade existing GitHub Pages site
Upload these files in place of the originals, preserving their paths, including the hidden `.github` directory. Your personal applications and seen/saved state use the existing `phdradar-state-v2` browser storage key and are not reset. Before upgrading, use Settings > Export backup. After uploading, run the Refresh PhD opportunity leads workflow once, then reload the web app (a hard reload may help).
