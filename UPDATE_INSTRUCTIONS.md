# v2.1 small diagnostic correction

The live feed confirms that all five FindAPhD requests returned HTTP 403; this cannot be solved by changing dashboard filters. FindAPhD data will require an authorized feed/API or another permitted recruitment source.

## Fix
- The collector now rejects lab pages explicitly stating no positions are open, even when the page contains archived PhD titles.
- Rejected explicitly closed labs are not automatically restored from the previous feed.
- The `review_queue` entries for UT Dallas, Illinois and Indiana are still expected to be displayed under **Needs review** because no verified deadline was extracted.

## Deploy
Replace only `scripts/collect.py` in your GitHub repository. The rest of the ZIP is included for reference, not required for this hotfix. Run **Discover PhD opportunities**, then open the JSON feed and refresh the app. Do not reset browser storage.

## Important
This hotfix does not add new permitted vacancy integrations. It corrects one false positive and makes the existing results more accurate.
