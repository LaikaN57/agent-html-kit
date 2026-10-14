---
name: html-kit
description: Write HTML documents (reports, architecture diagrams, plans, triage boards) with agent-html-kit components instead of hand-written CSS and SVG, at close to markdown token cost. Use when the user wants a document they will open in the browser, or asks for HTML output, a visual report, a diagram or an interactive board.
---

# agent-html-kit

The kit (`kit/kit.js`) holds all the design. You only write content, so an HTML file
costs about as many tokens as markdown. If the folder you write into has no `kit/kit.js`,
copy the `kit/` folder from this skill's directory next to the documents first; every
document loads it with one line.

## Writing an HTML document

Start the file with exactly this line, then write only content:
<!doctype html><meta charset="utf-8"><script src="kit/kit.js" defer></script>

Never write <style>, other <script> tags (except rk-diff's text/plain wrapper), style attributes, CSS or SVG. The kit draws everything.
Plain <h2> <h3> <p> <ul> <ol> <li> <b> <code> <a> are styled. In any text: **bold**, `code`,
status pills [done] [progress] [blocked] [todo] [warn], and IDs like ABC-123 are formatted.

<rk-header title="..." sub="..."></rk-header>           page hero
<rk-stats>                                              one stat per line: value | label | note
23 | PRs merged | +5 vs last week                       (note starting + is green, ! is red)
</rk-stats>
<rk-chart type="bar|line|hbar" title="..." unit="ms">   one point per line: Label: number (0 or more)
Mon: 3
</rk-chart>
<rk-table>                                              first line is the header, cells split by |
ID | Item | Status
CHK-1 | Apple Pay | [done]
</rk-table>
<rk-compare title="..." lower-is-better>                before/after, one per line: Label | before | after
p95 latency | 420ms | 310ms                             (kit computes the change; trailing | lower or | higher flips one row)
</rk-compare>
<rk-callout kind="risk|warn|note|ok" title="...">text</rk-callout>
<rk-diagram title="...">                                one edge per line: A -> B: label
Browser [user] -> API: HTTPS                            node kinds: [user] [svc] [db] [queue] [cache] [ext]
</rk-diagram>
<rk-sequence title="...">                               call order, one message per line: A -> B: call
Client [user] -> API: POST /pay                         B --> A: reply (dashed), A -> A: self call, note: text (band)
</rk-sequence>
<rk-steps>                                              numbered steps, one per line: Title | detail
Parse input | reject bad rows
</rk-steps>
<rk-progress title="..." good="80" bad="50">            one goal per line: Label | value | target (default 100)
Repos migrated | 34 | 50                                (kit computes %, colors and an overall row)
</rk-progress>
<rk-timeline title="...">                               dated milestones, one per line: date | title | detail
2026-10-01 | Cutover | [done]                           (YYYY-MM-DD, YYYY-MM or 14:05; sorted, dot = first pill)
</rk-timeline>
<rk-board title="..." columns="Now,Next,Later,Cut">     drag-and-drop board with markdown export
ID | title | column (optional, items start in Inbox)
</rk-board>
<rk-matrix title="..." y="Impact" x="Effort">           2x2 grid; quadrants="TL,TR,BL,BR" renames them
ID | title | y-level | x-level                          levels high|low, e.g. CHK-1 | Apple Pay | high | low
</rk-matrix>
<rk-diff title="...">                                   a unified diff, pasted as is (git diff output)
<script type="text/plain">diff --git ...</script>       use the script wrapper when the diff contains <
</rk-diff>
<rk-cols><div>...</div><div>...</div></rk-cols>         side-by-side columns
<rk-toc></rk-toc>                                       table of contents from the h2/h3 headings (depth="2": h2 only)
<rk-tabs><section title="Name">...</section></rk-tabs>   tabs, one section per tab; any content, components too
<details><summary>Title</summary>...</details>          collapsible card, closed until clicked

## Or write markdown and render it

When the reader is another agent or a repo, write markdown. To give a human the same
rendered page, use these extensions and run `node kit/md2html.js file.md`:

Write GitHub-flavored Markdown, no raw HTML. Our renderer adds:
- The first "# Title" becomes the page hero.
- A line "stats: value label | value label | ..." becomes stat cards.
- Status pills anywhere, including table cells: [done] [progress] [blocked] [todo] [warn].
- IDs like ABC-123 become chips.
- A line "[toc]" alone becomes a table of contents of the ## and ### headings.
- Blockquotes starting "Risk:", "Warning:", "Note:" or "OK:" become colored callouts.
- A line "+++ Title" opens a collapsible block and a line "+++" closes it; the content is
  normal markdown. Consecutive "+++ tab: Name" blocks become tabs.
- Fenced blocks by language:
  chart    optional header lines "title: ...", "type: bar|line|hbar", "unit: ms", then "Label: number" lines
  diagram  optional "title: ...", then one edge per line "A -> B: label";
           node kinds [user] [svc] [db] [queue] [cache] [ext], e.g. "Browser [user] -> API: HTTPS"
  compare  optional "title: ...", "lower: yes", then "Label | before | after" lines
           (e.g. "p95 latency | 420ms | 310ms"; add "| lower" or "| higher" to flip one row)
  sequence optional "title: ...", then one message per line: "A -> B: call", "B --> A: reply",
           "A -> A: self call", "note: text"; same node kinds as diagram
  steps    numbered steps, one per line "Title | detail"
  progress optional "title: ...", "good: 80", "bad: 50", then "Label | value | target" lines (target defaults to 100)
  timeline optional "title: ...", then "date | title | detail" lines; dates YYYY-MM-DD, YYYY-MM
           or 14:05 are sorted, a pill like [done] colors the dot
  board    "title: ...", "columns: Now,Next,Later,Cut", then "ID | title | column" lines;
           renders a drag-and-drop board with markdown export (items without a column start in Inbox)
  matrix   optional "title:", "y: Impact", "x: Effort", "quadrants: A,B,C,D", then "ID | title | y-level | x-level"
           lines with levels high|low; renders a 2x2 grid (default quadrants Quick wins, Big bets, Fill-ins, Avoid)
  diff     optional "title: ...", then a unified diff as is (git diff output)

## Rules

- Use only the data you were given. The kit computes summaries (status bar, chart
  average, peak bar) itself; do not write them out.
- If you need something the kit does not have, write plain HTML for that one part
  and keep the rest in components.
