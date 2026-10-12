# agent-html-kit

HTML pages from a coding agent at markdown token cost.

When an agent writes a freeform HTML page, most of the tokens go into design: CSS,
hand-placed SVG coordinates, and JavaScript nobody asked for. This kit moves all of
that into one script file (`kit/kit.js`). The agent writes only content, using a few
components, so an HTML report costs about the same as the markdown version.

The repo also contains the benchmark behind that claim: 72 real Claude Code runs,
every number taken from `claude -p --output-format json` usage receipts.

## Results

Model `claude-opus-5-5`, Claude Code on a clean config (no settings, skills, plugins
or MCP servers), 3 runs per cell, median shown. Run on 2026-10-12.

**Output tokens per job**

| Job | A · markdown | B · freeform HTML | C · HTML + kit | D · markdown + renderer |
|---|---:|---:|---:|---:|
| Weekly status report | 883 | 7,204 | 726 | 569 |
| Architecture diagram | 1,672 | 17,314 | 1,015 | 1,651 |
| Drag-and-drop triage board | 790 | 16,987 | 615 | 698 |
| Implementation plan | 8,599 | 25,376 | 8,911 | 9,086 |

**API time per job (seconds)**

| Job | A | B | C | D |
|---|---:|---:|---:|---:|
| Report | 7.5 | 55.5 | 5.9 | 4.9 |
| Diagram | 14.5 | 143.6 | 8.2 | 15.2 |
| Board | 7.9 | 136.7 | 5.1 | 6.2 |
| Plan | 70.2 | 197.8 | 74.3 | 77.0 |

**A second agent builds a module from each plan** (19 hidden tests it never sees)

| Plan format | Tests passed (3 runs) | Input tokens | Cost (USD, list price) |
|---|---|---:|---:|
| A · markdown | 19, 19, 19 | 85,954 | 0.126 |
| B · freeform HTML | 19, 19, 19 | 234,403 | 0.209 |
| C · HTML + kit | 19, 19, 19 | 83,887 | 0.092 |
| D · markdown + renderer | 19, 19, 19 | 66,500 | 0.077 |

Every build passed. The freeform HTML plan cost about two thirds more, because the
building agent re-reads the whole plan on every step.

**One small edit** ("CHK-102 is now done, update everything that depends on it"):
all 12 edits were correct. In the kit version the diff is two lines; in the freeform
version the same fact lives in six places (progress bar widths, legend, filter counts,
the row's status pill, its note, next week).

Full numbers: `bench/results/summary.json`. Generated files for every run sit next to
their receipts in `bench/results/<job>/`.

## Use the kit

Copy `kit/` next to your documents. An HTML document starts with one line, then content:

```html
<!doctype html><meta charset="utf-8"><script src="kit/kit.js" defer></script>
<rk-header title="Weekly Engineering Status" sub="Team Checkout, week 41"></rk-header>
<rk-stats>
23 | PRs merged | +5 vs last week
</rk-stats>
<rk-chart type="bar" title="PRs merged per day">
Mon: 3
Tue: 6
</rk-chart>
```

Components: `rk-header`, `rk-stats`, `rk-chart`, `rk-table`, `rk-callout`,
`rk-diagram`, `rk-steps`, `rk-board`, `rk-cols`. The full contract the agent gets is
`bench/contracts/html.txt` (634 input tokens per call). Examples are in `examples/`.

Prefer markdown? Write it with the fenced `chart`, `diagram`, `steps` and `board`
blocks and render it:

```bash
node kit/md2html.js report.md          # -> report.html with kit components
node kit/md2html.js report.md --plain  # -> plain GitHub-style render
```

## Claude Code skill

`skill/SKILL.md` teaches the agent the kit contract. Copy the `skill/` folder to
`.claude/skills/html-kit/` in your project (or `~/.claude/skills/html-kit/`).

## Run the benchmark yourself

Needs the Claude Code CLI and Python 3. The full run is 72 Claude Code calls and uses
real tokens on your account.

```bash
bash bench/run_all.sh                              # everything
python bench/run.py gen --scenario report --runs 3  # one job
python bench/run.py summary                         # rebuild summary.json
```

## Limits

- One model (Opus 5.5) and three runs per cell. Treat the numbers as directional.
- Dollar amounts are list prices from the receipts (`costBasis: "list"`). On a
  subscription you pay in usage limits instead.
- Writing a kit is not free. `kit/kit.js` measures 20,564 tokens, spent once. Each kit
  report saves about 6,478 output tokens against a freeform one (726 vs 7,204), so the
  kit pays for itself by the fourth report.
- The kit only knows its components. A page that needs something it doesn't have
  costs the freeform price.
- Raw `claude -p` event streams are not committed (they contain local paths and
  session ids). One build reply in `bench/results/implement/B-2.json` had a local
  temp path, redacted to `%TEMP%`.

## License

MIT
