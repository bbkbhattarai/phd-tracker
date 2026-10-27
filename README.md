# PhD Research Radar v2.4

International expansion for the **existing** GitHub Pages PhD Research Radar web app. It monitors genuine doctoral vacancy adverts and laboratories explicitly recruiting PhD students in hearing and auditory sciences, with a separate review queue for unverified recruitment.

There are 31 configured monitored sources (including known-blocked FindAPhD search URLs), and 46 reference sources. The new monitored sources include individual university PhD adverts in the UK, Spain/Belgium, and Australia, and lab recruitment pages in Canada, New Zealand and Hong Kong. Additional international research pages are available as a *reference directory only*, not falsely labelled as monitored.

See `UPDATE_INSTRUCTIONS.md` for precise deployment instructions. This is an incremental update that preserves the existing GitHub Actions workflow, previously published JSON feed, and browser storage key.

No server installs are needed for normal app use. The GitHub Actions collector requires Python `requests` and `beautifulsoup4`, as already installed by the existing workflow.
