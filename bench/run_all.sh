#!/usr/bin/env bash
# Full benchmark: 4 scenarios x 4 formats x 3 runs, then implement, edit, count, summary.
# Writes into a new folder (default bench/results-local), never into the committed bench/results.
# Re-running the script resumes: receipts already in that folder are skipped.
set -e
cd "$(dirname "$0")/.."
export AHK_RESULTS="${AHK_RESULTS:-bench/results-local}"
# python3 on macOS/Linux, python or the py launcher on Windows; override with PYTHON=...
PY="${PYTHON:-$(command -v python3 || command -v python || command -v py)}"
for s in report diagram board plan; do
  "$PY" -I bench/run.py gen --scenario "$s" --runs 3 --jobs 4
done
"$PY" -I bench/run.py implement --runs 3 --jobs 4
"$PY" -I bench/run.py edit --runs 3 --jobs 4
"$PY" -I bench/run.py count
"$PY" -I bench/run.py summary
echo "results: $AHK_RESULTS"
