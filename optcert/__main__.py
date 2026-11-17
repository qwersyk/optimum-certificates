"""Command line: python -m optcert problem.json

The file gives "weights", "areas" and optionally "costs" and "sense", and
either "edges" (edge name -> two vertices, for spanning trees) or "ground"
and "rank" (choose `rank` of the listed elements).
"""

import json
import sys

from . import Problem, graphic, uniform


def load(path):
    with open(path) as source:
        data = json.load(source)
    matroid = graphic(data["edges"]) if "edges" in data else \
        uniform(data["ground"], data["rank"])
    return Problem(matroid, data["weights"], data["areas"], data.get("costs"),
                   data.get("sense", "min"))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    problem = load(sys.argv[1])
    for mode, goal in (("basis", "one optimal solution"), ("family", "all optimal solutions")):
        found = problem.certificate(mode)
        queries = ", ".join(sorted(map(str, found.queries))) or "nothing"
        print(f"to certify {goal}: query {queries} (cost {found.cost})")


if __name__ == "__main__":
    main()
