"""Markdown vs HTML token benchmark, measured with real Claude Code runs.

Every number comes from `claude -p --output-format json` usage, on a clean config
(no settings, MCP servers, skills or plugins), so the overhead is a few thousand tokens.

Formats
  A  plain markdown (GitHub-flavored)
  B  freeform HTML (self-contained, inline CSS + SVG + JS)
  C  HTML with the kit (components, no CSS/SVG written by the agent)
  D  markdown for the kit renderer (fenced chart/diagram/board blocks)

Commands
  python bench/run.py gen --scenario report --runs 3 --jobs 4
  python bench/run.py implement --runs 3      # an agent implements each plan, hidden tests score it
  python bench/run.py edit --runs 3           # an agent updates one status in each report
  python bench/run.py count                   # token size of artifacts, kit and contracts as input
  python bench/run.py summary

Existing receipts in the results folder are skipped, so an interrupted run resumes. Set
AHK_RESULTS=bench/results-mine to measure into a new folder instead of bench/results.
"""
import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCEN = ROOT / "scenarios"
# Results folder. The committed measurements live in bench/results; run_all.sh writes a fresh run
# elsewhere (AHK_RESULTS) so nothing is skipped as "cached" and the two never mix.
RES = Path(os.environ.get("AHK_RESULTS") or ROOT / "results").resolve()
CONTRACTS = ROOT / "contracts"
WORK = Path(tempfile.gettempdir()) / "ahk-bench"
MODEL = "claude-opus-5-5"
FORMATS = ["A", "B", "C", "D"]
EXT = {"A": "md", "B": "html", "C": "html", "D": "md"}
NAMES = {"A": "markdown", "B": "freeform HTML", "C": "HTML + kit", "D": "markdown + renderer"}
CLEAN = ["--setting-sources", "", "--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence"]

SUFFIX = "Output only the file content: no preamble, no commentary, no code fence around the whole file."


def format_instruction(f):
    if f == "A":
        return "Format: GitHub-flavored Markdown. No raw HTML."
    if f == "B":
        return ("Format: one self-contained HTML file that opens in the browser. Make it polished: inline CSS, "
                "real SVG for any chart or diagram, styled tables, and JavaScript where interaction is needed. "
                "No external resources.")
    if f == "C":
        return "Format: HTML using our kit. Follow this contract exactly:\n\n" + (CONTRACTS / "html.txt").read_text("utf-8")
    if f == "D":
        return "Format: Markdown for our renderer. Follow this contract exactly:\n\n" + (CONTRACTS / "markdown.txt").read_text("utf-8")
    raise ValueError(f)


def claude(prompt, cwd, tools="", extra=(), max_turns=1, raw_path=None):
    exe = shutil.which("claude") or "claude"
    cmd = [exe, "-p", "--output-format", "json", "--model", MODEL, "--max-turns", str(max_turns), "--tools", tools, *CLEAN, *extra]
    t0 = time.time()
    p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    wall = time.time() - t0
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"bad json (exit {p.returncode}): {p.stdout[:300]} {p.stderr[:300]}")
    if raw_path:
        Path(raw_path).write_text(json.dumps(data, indent=1), "utf-8")
    events = data if isinstance(data, list) else [data]
    # An agent that runs a background task gets woken again when it finishes, and each wake-up
    # ends in its own result event. Each result's usage covers only its own turn, so sum them.
    results = [x for x in events if x.get("type") == "result"]
    if not results:
        raise RuntimeError(f"no result event (exit {p.returncode}): {p.stderr[:300]}")
    last = results[-1]
    if last.get("is_error"):
        raise RuntimeError(f"claude error: {str(last.get('result'))[:300]}")
    s = lambda key: sum((r["usage"].get(key) or 0) for r in results)
    out = s("output_tokens")
    thinking = sum(((r["usage"].get("output_tokens_details") or {}).get("thinking_tokens") or 0) for r in results)
    inp, cw, cr = s("input_tokens"), s("cache_creation_input_tokens"), s("cache_read_input_tokens")
    rec = {
        "model": MODEL,
        "output_tokens": out,
        "thinking_tokens": thinking,
        "artifact_tokens": out - thinking,
        "input_tokens": inp,
        "cache_creation_tokens": cw,
        "cache_read_tokens": cr,
        "total_input_tokens": inp + cw + cr,
        "cost_usd": last.get("total_cost_usd"),  # already cumulative for the whole session
        "duration_ms": sum(r.get("duration_ms") or 0 for r in results),
        "duration_api_ms": sum(r.get("duration_api_ms") or 0 for r in results),
        "wall_s": round(wall, 1),
        "num_turns": sum(r.get("num_turns") or 0 for r in results),
        "result_events": len(results),
    }
    return rec, last.get("result") or ""


def strip_fence(text):
    t = text.strip()
    m = re.match(r"^```[\w-]*\n(.*)\n```$", t, re.S)
    return (m.group(1), True) if m else (t, False)


def with_retry(fn, tries=3):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # rate limits, transient API errors
            if i == tries - 1:
                raise
            print(f"  retry after error: {e}", flush=True)
            time.sleep(20 * (i + 1))


def gen_one(scenario, f, i):
    out = RES / scenario
    out.mkdir(parents=True, exist_ok=True)
    meta = out / f"{f}-{i}.json"
    if meta.exists():
        return f"{scenario} {f}-{i} cached"
    task = (SCEN / scenario / "task.txt").read_text("utf-8").strip()
    data = (SCEN / scenario / "data.txt").read_text("utf-8").strip()
    prompt = f"{task}\n\n{format_instruction(f)}\n\n{SUFFIX}\n\n{data}\n"
    cwd = WORK / "gen" / f"{scenario}-{f}-{i}"
    cwd.mkdir(parents=True, exist_ok=True)
    rec, result = with_retry(lambda: claude(prompt, cwd))
    body, fenced = strip_fence(result)
    (out / f"{f}-{i}.{EXT[f]}").write_text(body, "utf-8")
    rec.update(scenario=scenario, format=f, run=i, fenced=fenced, chars=len(body))
    meta.write_text(json.dumps(rec, indent=2), "utf-8")
    return f"{scenario} {f}-{i}: artifact {rec['artifact_tokens']} tok, thinking {rec['thinking_tokens']}, {rec['duration_api_ms']/1000:.0f}s"


IMPLEMENT = ("Implement the plan in {file} in this folder: create pricing.py exactly as the plan describes. "
             "The plan is your only source of requirements. Work on your own and do not ask questions. "
             "When pricing.py is done, reply with one line saying so.")


def implement_one(f, i):
    out = RES / "implement"
    out.mkdir(parents=True, exist_ok=True)
    meta = out / f"{f}-{i}.json"
    if meta.exists():
        return f"implement {f}-{i} cached"
    plan = RES / "plan" / f"{f}-{i}.{EXT[f]}"
    cwd = WORK / "implement" / f"{f}-{i}"
    if cwd.exists():
        shutil.rmtree(cwd)
    cwd.mkdir(parents=True)
    name = f"plan.{EXT[f]}"
    shutil.copy(plan, cwd / name)
    rec, result = with_retry(lambda: claude(
        IMPLEMENT.format(file=name), cwd, tools="Read,Write,Edit,Bash", max_turns=40, raw_path=out / f"{f}-{i}.raw.json",
        extra=["--permission-mode", "acceptEdits", "--allowedTools", "Read", "Write", "Edit",
               "Bash(python:*)", "Bash(py:*)", "Bash(python3:*)"]))
    test = subprocess.run([sys.executable, "-I", str(SCEN / "plan" / "hidden_test.py"), str(cwd)],
                          capture_output=True, text=True, encoding="utf-8")
    score = json.loads(test.stdout.strip().splitlines()[-1])
    if (cwd / "pricing.py").exists():
        shutil.copy(cwd / "pricing.py", out / f"{f}-{i}.pricing.py")
    rec.update(scenario="implement", format=f, run=i, tests=score, reply=result[:300])
    meta.write_text(json.dumps(rec, indent=2), "utf-8")
    return f"implement {f}-{i}: {score['passed']}/{score['total']} tests, in {rec['total_input_tokens']} out {rec['output_tokens']}, turns {rec['num_turns']}"


EDIT = ("Update {file} in this folder: CHK-102 Address autocomplete is now done, it shipped on Thursday. "
        "Update its status and everything in the file that depends on it (counts, summaries, status visuals, next week). "
        "Change nothing else. Reply with one line when done.")


def edit_one(f, i):
    out = RES / "edit"
    out.mkdir(parents=True, exist_ok=True)
    meta = out / f"{f}-{i}.json"
    if meta.exists():
        return f"edit {f}-{i} cached"
    src = RES / "report" / f"{f}-{i}.{EXT[f]}"
    cwd = WORK / "edit" / f"{f}-{i}"
    if cwd.exists():
        shutil.rmtree(cwd)
    cwd.mkdir(parents=True)
    name = f"report.{EXT[f]}"
    shutil.copy(src, cwd / name)
    rec, result = with_retry(lambda: claude(
        EDIT.format(file=name), cwd, tools="Read,Edit,Write", max_turns=20, raw_path=out / f"{f}-{i}.raw.json",
        extra=["--permission-mode", "acceptEdits"]))
    shutil.copy(cwd / name, out / f"{f}-{i}.{EXT[f]}")
    rec.update(scenario="edit", format=f, run=i, reply=result[:300])
    meta.write_text(json.dumps(rec, indent=2), "utf-8")
    return f"edit {f}-{i}: in {rec['total_input_tokens']} out {rec['output_tokens']}, turns {rec['num_turns']}"


COUNT_WRAP = "Reply with just OK. Ignore everything between the markers.\n<<<\n{text}\n>>>"


def count_tokens(text, cwd):
    rec, _ = with_retry(lambda: claude(COUNT_WRAP.format(text=text), cwd))
    return rec["total_input_tokens"]


def cmd_count(_):
    cwd = WORK / "count"
    cwd.mkdir(parents=True, exist_ok=True)
    path = RES / "counts.json"
    counts = json.loads(path.read_text("utf-8")) if path.exists() else {}
    if "_baseline" not in counts:
        counts["_baseline"] = count_tokens("", cwd)
    base = counts["_baseline"]
    targets = {
        "kit/kit.js": ROOT.parent / "kit" / "kit.js",
        "contracts/html.txt": CONTRACTS / "html.txt",
        "contracts/markdown.txt": CONTRACTS / "markdown.txt",
    }
    for scen in ["report", "diagram", "board", "plan"]:
        for f in FORMATS:
            p = RES / scen / f"{f}-1.{EXT[f]}"
            if p.exists():
                targets[f"{scen}/{f}-1"] = p
    todo = [k for k in targets if k not in counts]

    def work(k):
        return k, count_tokens(targets[k].read_text("utf-8"), cwd) - base

    with ThreadPoolExecutor(4) as ex:
        for k, n in ex.map(work, todo):
            counts[k] = n
            print(f"{k}: {n} tokens", flush=True)
    path.write_text(json.dumps(counts, indent=2), "utf-8")


def run_jobs(jobs, n):
    with ThreadPoolExecutor(n) as ex:
        for msg in ex.map(lambda j: j(), jobs):
            print(msg, flush=True)


def cmd_gen(a):
    fs = a.formats or FORMATS
    jobs = [lambda s=a.scenario, f=f, i=i: gen_one(s, f, i) for i in range(1, a.runs + 1) for f in fs]
    run_jobs(jobs, a.jobs)


def cmd_implement(a):
    fs = a.formats or FORMATS
    run_jobs([lambda f=f, i=i: implement_one(f, i) for i in range(1, a.runs + 1) for f in fs], a.jobs)


def cmd_edit(a):
    fs = a.formats or FORMATS
    run_jobs([lambda f=f, i=i: edit_one(f, i) for i in range(1, a.runs + 1) for f in fs], a.jobs)


def cmd_summary(_):
    rows = []
    for scen in ["report", "diagram", "board", "plan", "implement", "edit"]:
        d = RES / scen
        if not d.exists():
            continue
        for f in FORMATS:
            recs = [json.loads(p.read_text("utf-8")) for p in sorted(d.glob(f"{f}-*.json"))]
            recs = [r for r in recs if "output_tokens" in r]
            if not recs:
                continue
            med = lambda k: statistics.median([r[k] or 0 for r in recs])
            row = {
                "scenario": scen, "format": f, "name": NAMES[f], "runs": len(recs),
                "artifact_tokens": med("artifact_tokens"), "thinking_tokens": med("thinking_tokens"),
                "output_tokens": med("output_tokens"), "total_input_tokens": med("total_input_tokens"),
                "cost_usd": round(med("cost_usd"), 4), "api_s": round(med("duration_api_ms") / 1000, 1),
                "turns": med("num_turns"),
                "min_out": min(r["output_tokens"] for r in recs), "max_out": max(r["output_tokens"] for r in recs),
            }
            if scen == "implement":
                row["tests"] = [r["tests"]["passed"] for r in recs]
            rows.append(row)
    for scen in dict.fromkeys(r["scenario"] for r in rows):
        group = [r for r in rows if r["scenario"] == scen]
        base = next((r for r in group if r["format"] == "A"), None)
        print(f"\n== {scen}")
        for r in group:
            x = f"{r['output_tokens'] / base['output_tokens']:.1f}x" if base else ""
            extra = f" tests {r['tests']}" if "tests" in r else ""
            print(f"  {r['format']} {r['name']:22s} out {r['output_tokens']:7.0f} ({x:>6s}) artifact {r['artifact_tokens']:7.0f} "
                  f"think {r['thinking_tokens']:6.0f} in {r['total_input_tokens']:8.0f} ${r['cost_usd']:<7} {r['api_s']:6.1f}s "
                  f"turns {r['turns']} range {r['min_out']}-{r['max_out']}{extra}")
    (RES / "summary.json").write_text(json.dumps(rows, indent=2), "utf-8")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--scenario", required=True)
    for p in [g, sub.add_parser("implement"), sub.add_parser("edit")]:
        p.add_argument("--runs", type=int, default=3)
        p.add_argument("--jobs", type=int, default=4)
        p.add_argument("--formats", nargs="*")
    sub.add_parser("count")
    sub.add_parser("summary")
    a = ap.parse_args()
    {"gen": cmd_gen, "implement": cmd_implement, "edit": cmd_edit, "count": cmd_count, "summary": cmd_summary}[a.cmd](a)


if __name__ == "__main__":
    main()
