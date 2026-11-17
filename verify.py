"""Compare the library with the definitions on random small instances.

    python verify.py [instances] [seed]

For every instance and every set of queries, the library's answer to "is this
a certificate?" must equal the answer obtained by enumerating the worlds, for
both modes, and the minimum costs must agree. Two campaigns, written to
results.json:

finite     Every area is a finite set of points, so the enumeration covers
           every world.
intervals  Areas are unions of intervals. Worlds are enumerated on a grid
           made of all end points and the points halfway between them.

The matroids are cycle matroids of random multigraphs, uniform matroids and
binary matroids (random vectors over GF(2)).
"""

import json
import random
import sys
from fractions import Fraction
from itertools import chain, combinations

from optcert import Matroid, Problem, bruteforce, graphic, uniform

MODES = ("basis", "family")
COUNT = 5000


def subsets(items):
    return chain.from_iterable(combinations(items, k) for k in range(len(items) + 1))


def binary(vectors):
    """The matroid of linear independence over GF(2). `vectors` maps an
    element to an integer read as a bit vector."""
    def independent(names):
        reduced = []
        for name in names:
            v = vectors[name]
            for r in reduced:  # decreasing, with distinct leading bits
                v = min(v, v ^ r)
            if v == 0:
                return False
            reduced.append(v)
            reduced.sort(reverse=True)
        return True

    return Matroid(vectors, independent)


def random_matroid(rng, largest):
    kind = rng.choice(("graphic", "graphic", "uniform", "binary"))
    size = rng.randint(1, largest)
    if kind == "uniform":
        return uniform(range(size), rng.randint(0, size))
    if kind == "binary":
        return binary({k: rng.randrange(16) for k in range(size)})
    vertices = rng.randint(2, 5)
    return graphic({k: (rng.randrange(vertices), rng.randrange(vertices)) for k in range(size)})


def check(matroid, values, actual, areas, cost, sense, stats):
    """`values` are the worlds to enumerate; `areas` is what the library is told."""
    problem = Problem(matroid, actual, areas, cost, sense)
    sign = -1 if sense == "min" else 1
    values = {e: {sign * x for x in values[e]} for e in values}
    world = {e: sign * actual[e] for e in actual}
    bases = matroid.bases()
    optimal = bruteforce.optimal_family(bases, world)
    assert problem.optimal_bases() == set(optimal)
    stats["instances"] += 1
    stats["with several optimal bases"] += len(optimal) > 1
    for mode in MODES:
        truth = set(bruteforce.certificates(bases, values, world, mode))
        for queries in subsets(sorted(problem.uncertain)):
            stats["answers compared"] += 1
            assert problem.certifies(queries, mode) == (frozenset(queries) in truth), \
                (mode, sense, areas, actual, queries)
        found = problem.certificate(mode)
        assert found.queries in truth
        assert found.cost == min(sum(cost[e] for e in q) for q in truth)


def finite(rng, stats):
    matroid = random_matroid(rng, 7)
    top = rng.choice((1, 2, 3, 5))
    values = {e: set(rng.sample(range(top + 1), rng.randint(1, min(3, top + 1))))
              for e in matroid.ground}
    actual = {e: rng.choice(sorted(values[e])) for e in values}
    areas = {e: [(x, x) for x in sorted(values[e])] for e in values}
    cost = {e: rng.choice((0, 1, 1, 2, 3, Fraction(1, 2))) for e in values}
    check(matroid, values, actual, areas, cost, rng.choice(("min", "max")), stats)


def intervals(rng, stats):
    matroid = random_matroid(rng, 5)
    areas = {}
    for e in matroid.ground:
        points = sorted(rng.sample(range(6), rng.choice((1, 2, 2, 4))))
        areas[e] = [(points[0], points[0])] if len(points) == 1 else \
            list(zip(points[0::2], points[1::2]))
    ends = sorted({x for parts in areas.values() for part in parts for x in part})
    grid = [Fraction(x) for x in ends] + [Fraction(a + b, 2) for a, b in zip(ends, ends[1:])]
    values = {e: {x for x in grid if any(a <= x <= b for a, b in areas[e])} for e in areas}
    actual = {e: rng.choice(sorted(values[e])) for e in areas}
    cost = {e: rng.randint(0, 3) for e in areas}
    check(matroid, values, actual, areas, cost, rng.choice(("min", "max")), stats)


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else COUNT
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    results = {"seed": seed}
    for campaign in (finite, intervals):
        rng = random.Random(f"{seed}/{campaign.__name__}")
        stats = {"instances": 0, "with several optimal bases": 0, "answers compared": 0}
        for _ in range(count):
            campaign(rng, stats)
        results[campaign.__name__] = stats
        print(campaign.__name__, stats, flush=True)
    with open("results.json", "w") as out:
        json.dump(results, out, indent=1)
        out.write("\n")


if __name__ == "__main__":
    main()
