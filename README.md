# PhD Research Radar 2.3 (navigation and McGill-origin AUDITORY source clarification)

This is a UI-only update built on the working 2.2 collector. No collector settings or previously saved browser data are reset.

## Why the review leads were hard to see

The old dashboard showed `Opportunities 0` even though it mixed some laboratory review leads into the opportunities panel. Version 2.3 fixes this:

- **Opportunities** displays only `opportunities[]`, and its count matches that list.
- **Needs review** displays `review_queue[]`, and its count matches that list.
- When a refreshed feed has zero confirmed opportunities but one or more review leads, the app opens **Needs review** automatically.
- A prominent **View leads needing review** button appears whenever there are review leads.
- AUDITORY is already represented in the source catalogue and collection workflow. Its mailing list was founded by Professor Albert Bregman at McGill University. Non-recruitment posts (workshops, conferences, etc.) should not appear as opportunities.

## Deploy to the same GitHub Pages repository

1. Export your local data backup using the app's Settings tab.
2. Upload replacement files `index.html`, `app.js`, `style.css`, `sw.js` to the repository root. The other files in this ZIP are unchanged, and may be left as they are.
3. Do **not** replace `data/opportunities.json`. It is not included in this ZIP.
4. Let GitHub Pages publish the update and reload the app. If the old UI persists, do a hard refresh or open a private tab.
5. The 3 lab leads should be visible under **Needs review** without running the search again.

This patch does not fix the five FindAPhD 403 errors or add an independent second McGill listserv. If a different list is intended, its exact archive URL/name is needed.
