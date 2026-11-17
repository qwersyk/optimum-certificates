"""Draw docs/example.svg from examples/network.json.

    python -m docs.figure
"""

import json
from pathlib import Path

from optcert.__main__ import load

ROOT = Path(__file__).resolve().parent.parent
PLACE = {"A": (80, 40), "B": (260, 40), "C": (260, 220), "D": (80, 220)}
# Where along the edge its label sits, and how far it is pushed off the line.
LABEL = {"AB": (0.5, 0, -12), "BC": (0.5, 36, 4), "CD": (0.5, 0, 22),
         "DA": (0.5, -36, 4), "AC": (0.3, 32, 0), "BD": (0.7, 32, 10)}
WIDTH, HEIGHT, GAP = 340, 292, 20

STYLE = """
  text { font: 12px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: #57606a; }
  .title { font-size: 13px; }
  .node { fill: #ffffff; stroke: #57606a; stroke-width: 1.2; }
  .edge { stroke: #afb8c1; stroke-width: 1.5; }
  .tree { stroke: #24292f; stroke-width: 3; }
  .query { stroke: #cf222e; }
  .asked { fill: #cf222e; font-weight: 600; }
  @media (prefers-color-scheme: dark) {
    text { fill: #8b949e; }
    .node { fill: #0d1117; stroke: #8b949e; }
    .edge { stroke: #484f58; }
    .tree { stroke: #e6edf3; }
    .query { stroke: #f85149; }
    .asked { fill: #f85149; }
  }
"""


def panel(problem, data, mode, title, shift):
    found = problem.certificate(mode)
    out = [f'<g transform="translate({shift} 0)">',
           f'<text class="title" x="{WIDTH / 2}" y="{HEIGHT - 14}" text-anchor="middle">{title}</text>']
    for name, (a, b) in data["edges"].items():
        (x1, y1), (x2, y2) = PLACE[a], PLACE[b]
        kinds = ["edge"] + ["tree"] * (name in found.basis) + ["query"] * (name in found.queries)
        out.append(f'<line class="{" ".join(kinds)}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
    for name, (a, b) in data["edges"].items():
        (x1, y1), (x2, y2) = PLACE[a], PLACE[b]
        t, dx, dy = LABEL[name]
        lo, hi = data["areas"][name]
        asked = ' class="asked"' if name in found.queries else ""
        out.append(f'<text{asked} x="{x1 + t * (x2 - x1) + dx:g}" y="{y1 + t * (y2 - y1) + dy:g}" '
                   f'text-anchor="middle">{data["weights"][name]} ({lo}–{hi})</text>')
    for name, (x, y) in PLACE.items():
        out.append(f'<circle class="node" cx="{x}" cy="{y}" r="11"/>'
                   f'<text x="{x}" y="{y + 4}" text-anchor="middle">{name}</text>')
    return out + ["</g>"]


def main():
    path = ROOT / "examples" / "network.json"
    data, problem = json.loads(path.read_text()), load(path)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {2 * WIDTH + GAP} {HEIGHT}" '
           f'width="{2 * WIDTH + GAP}" height="{HEIGHT}" role="img" aria-label="A network with '
           'uncertain edge costs, its cheapest spanning tree, and the edges that must be measured">',
           f"<style>{STYLE}</style>"]
    for shift, mode, goal in ((0, "basis", "the tree is cheapest"),
                              (WIDTH + GAP, "family", "it is the only cheapest tree")):
        count = len(problem.certificate(mode).queries)
        out += panel(problem, data, mode, f"to certify that {goal}: {count} queries", shift)
    (ROOT / "docs" / "example.svg").write_text("\n".join(out + ["</svg>"]) + "\n")


if __name__ == "__main__":
    main()
