name: Fetch SILSO daily (Sunspot-Daily)

on:
  schedule:
    - cron: '0 0 * * *'  # daily at 00:00 UTC
  workflow_dispatch: {}

jobs:
  fetch:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          persist-credentials: true
          fetch-depth: 0

      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install requests

      - name: Run fetch_silso.py script
        run: python ./Sunspot_Daily/scripts/fetch_silso.py
        env:
          ARCHIVE_DIR: data/archive
          TARGET_FILENAME: Sunspot-Daily
          SILSO_URL: https://www.sidc.be/silso/INFO/sndtotcsv.php

      - name: Commit and push updated CSV (if changed)
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/Sunspot-Daily.csv || true
          git add data/archive || true
          if git diff --staged --quiet; then
            echo "No changes to commit."
            exit 0
          fi
          git commit -m "chore(data): update Sunspot-Daily for $(date -u +%Y-%m-%d)"
          git push
