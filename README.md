# PhD Research Radar v2.9 | Adaptive Search Profiles

This is a **drop-in update** for the existing GitHub Pages repository `bbkbhattarai/phd-tracker`, not a new hosting service. Personal application records, notes, saved opportunities and reviewed flags remain browser-local under the **unchanged** `phdradar_clean_v2` storage key.

## New: reusable profiles and relevance levels

In **Settings → Adaptive search profiles**, create up to 12 independent research profiles. Each has:

- Name and enable/disable control.
- **Focused**: exact literal phrase matching against Level 1 core phrases.
- **Related**: core plus Level 2 phrases.
- **Exploratory**: core, related and Level 3 phrases.
- Excluded phrases, geographical scope, and opportunity categories (advertised PhD / recruiting PhD lab).

All enabled profiles are combined by the scheduled collector, and accepted records include `profile_matches` and `relevance_score`. An additional **Research profile** dropdown on the main Opportunities screen filters records by profile. A disabled second example profile shows how to add other disciplines without changing the existing hearing-science profile.

**Search breadth is a deterministic phrase rule, not AI relevance inference.** Profiles change filtering and evaluation of candidates on already integrated sources; they cannot make unsupported sites searchable, turn general articles into recruitable positions, or bypass FindAPhD's HTTP 403 access restrictions. The collector still screens for PhD or doctoral recruitment. New qualification levels, job types and true dynamic source discovery would require separate extensions.

## New: automatic GitHub publication while connected

To avoid copying JSON manually, v2.9 can publish configuration edits directly to GitHub using the official repository Contents API:

1. Create a **fine-grained GitHub personal access token** with **only** `bbkbhattarai/phd-tracker` selected under *Repository access* and **Contents: Read and write** under *Repository permissions*. Use a short expiration date. No `Workflows` permission is necessary because the app never edits workflow files.
2. In **Settings → Automatic GitHub synchronization**, paste it and select **Connect for this session**.
3. Add/remove a phrase, toggle a region, change the research profile level, or create a new profile. The browser saves the new profile locally and, while connected, attempts to commit `scripts/search_profiles.json` automatically after a short debounce. If the commit fails, the edit remains local and the app shows an error; use **Publish changes now** to retry.
4. The included `.github/workflows/search.yml` now listens for **pushes to `scripts/search_profiles.json`** as well as the existing scheduled/manual events. A successful authorized GitHub configuration commit therefore starts the collector automatically. When the workflow finishes, refresh the public feed in the app.

**Security model:** The token remains in JavaScript memory for the open page only. It is never stored in localStorage, included in backups, added to published configuration, or passed to the Python collector. Reloading or closing the tab disconnects it; you must connect again next session. This is a deliberate limitation of a static-only website. For a genuinely permanent, one-time connection across sessions, the project would need a carefully configured **GitHub App or OAuth backend** (e.g. a restricted Cloudflare Worker) that stores credentials server-side and authenticates the owner. Do **not** put a GitHub token in code, `search_profiles.json`, GitHub Actions YAML, or a public source file.

The client-side sync is implemented and tested with **simulated** GitHub API responses. It has **not been tested against your authenticated GitHub account**, so actual browser permissions, token policy and network CORS behavior must be verified after deployment. A failed connection does not modify the remote repository.

## Files to deploy

Upload/update these paths in the existing repository, keeping the same folders:

- `index.html`, `app.js`, `style.css`, `sw.js`
- `scripts/collect.py`
- **New:** `scripts/search_profiles.json`
- **Update:** `.github/workflows/search.yml` (this is required to react to profile changes)

Leave these as they are unless you need to restore them: `scripts/sources.json`, `scripts/requirements.txt`, `data/opportunities.json`, `manifest.webmanifest`, `assets/`. In particular, **do not overwrite the current populated `data/opportunities.json`**. The update package deliberately excludes the feed.

After committing v2.9, manually trigger **Discover PhD opportunities** once to test the new collector configuration. Subsequent browser-edited profile commits, when GitHub synchronization is connected, will cause new runs automatically.

### Optional manual backup

The Settings screen can export `search_profiles.json` if you don't want to connect GitHub. You can still upload the JSON yourself. The existing personal backup/restore mechanism is independent and preserved.

## Known limitations

- Browser-only saved applications/notes do not sync across devices.
- FindAPhD pages previously returned HTTP 403 and remain blocked by their access control.
- LinkedIn posts are manual search shortcuts, not a scheduled scraper.
- Source discovery still depends on the maintained `sources.json` connectors. Editing a profile doesn't install new scrapers or add unsupported sites.
- The collector continues to look for doctoral recruiting evidence. Configuring unrelated subjects works on existing accessible recruiting pages, but supporting other qualification levels (e.g. Masters, postdoc, faculty jobs) will require new category-specific verification rules.
- Changing profiles doesn't alter past personal saved records. Old public records may remain in the review queue pending re-check.
- GitHub Actions schedules can be delayed. New search results become visible after the Actions collector commits the feed and Pages serves it.

## Validation performed

- Python collector compilation and eleven offline unit tests, including all three profile matching levels, region/category restrictions and profile-specific exclusions.
- JavaScript syntax and offline Chromium browser UI checks for editing, switching profiles, export and preserving saved listings.
- Simulated GitHub API browser test: token connection, automatic Contents API PUT after a change, JSON payload, and absence of token in browser-local storage.
- ZIP integrity validation.

No live source crawling or authenticated GitHub write was run as part of this package build.
