# Update PhD Radar from v2.8 to v2.9

1. Open your current app and use **Settings → Export JSON backup** first.
2. Download and unzip v2.9.
3. In `bbkbhattarai/phd-tracker` on GitHub, replace `index.html`, `app.js`, `style.css`, `sw.js`, and `scripts/collect.py`.
4. Add the new file `scripts/search_profiles.json`.
5. **Replace `.github/workflows/search.yml`** with the version in this package. This one adds the essential GitHub Actions `push` trigger for profile configuration changes.
6. Do NOT overwrite `data/opportunities.json`; do not delete or overwrite your personal applications.
7. Commit to `main`. Run **Discover PhD opportunities** once, then refresh your app.
8. Visit **Settings → Adaptive search profiles**. Your default hearing sciences profile is preloaded.
9. To enable automatic publishing, generate a fine-grained GitHub token with **only `bbkbhattarai/phd-tracker` repository access** and **Contents: Read and write**. Enter it in the app and connect for this tab. Changes to profiles will then attempt automatic commits and initiate GitHub Actions searches. Reconnect after reopening the app.
10. For a no-token approach, use **Download JSON backup** and manually replace `scripts/search_profiles.json` on GitHub.

**Why the token is not remembered:** A public static website cannot safely hold a permanent GitHub write credential. Keeping a token out of localStorage and backups reduces exposure. A permanent login needs a separately built/authenticated backend or GitHub App.

If the publish status reports an error, your browser-local profile edits are retained. Check the token's repository access and scopes, refresh the page if another person edited the configuration, or export the JSON and update GitHub manually.

**Important:** Configuring new research terms changes matching against the existing source connectors, not the universe of sites being searched. FindAPhD, LinkedIn and any other blocked source remain outside automated retrieval.
