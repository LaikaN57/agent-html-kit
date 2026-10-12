#!/usr/bin/env bash
# Full benchmark: 4 scenarios x 4 formats x 3 runs, then implement, edit, count, summary.
set -e
cd "$(dirname "$0")/.."
for s in report diagram board plan; do
  py -I bench/run.py gen --scenario "$s" --runs 3 --jobs 4
done
py -I bench/run.py implement --runs 3 --jobs 4
py -I bench/run.py edit --runs 3 --jobs 4
py -I bench/run.py count
py -I bench/run.py summary
