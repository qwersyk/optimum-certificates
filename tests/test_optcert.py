import json
import random
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

import verify
from optcert import Matroid, Problem, bruteforce, graphic, uniform
from optcert.__main__ import load
from optcert.cover import minimum_cover

ROOT = Path(__file__).resolve().parent.parent


def test_two_items():
    # The cheaper of two items. `a` can never cost more than `b`, so nothing
    # has to be queried to know that `a` is a right choice; but they may tie
    # at 3, and one query is needed to rule that out.
    problem = Problem(uniform("ab", 1), {"a": 2, "b": 4}, {"a": (1, 3), "b": (3, 5)})
    assert problem.certificate("basis").queries == frozenset()
    assert problem.certifies([], "basis") and not problem.certifies([], "family")
    assert problem.certifies("a", "family") and problem.certifies("b", "family")
    assert problem.certificate("family").cost == 1


def test_network_example():
    problem = load(ROOT / "examples" / "network.json")
    basis, family = problem.certificate("basis"), problem.certificate("family")
    assert basis.basis == family.basis == {"AB", "BC", "CD"}
    assert basis.queries == {"AB", "CD"} and basis.required == {"CD"}
    assert family.queries == family.required == {"AB", "AC", "CD", "DA"}


def test_costs_change_the_choice():
    areas = {"a": (1, 3), "b": (3, 5)}
    problem = Problem(uniform("ab", 1), {"a": 2, "b": 4}, areas, {"a": 5, "b": 2})
    assert problem.certificate("family").queries == {"b"}
    problem = Problem(uniform("ab", 1), {"a": 2, "b": 4}, areas, {"a": 0, "b": 2})
    assert problem.certificate("family") == (frozenset("a"), 0, frozenset("a"), frozenset())


def test_tied_bases_differ_in_cost():
    # Both items weigh 1. `a` cannot weigh less and `b` cannot weigh more, so
    # `a` is certified for free, while certifying `b` takes both queries.
    problem = Problem(uniform("ab", 1), {"a": 1, "b": 1}, {"a": (1, 2), "b": (0, 1)}, sense="max")
    assert problem.optimal_bases() == {frozenset("a"), frozenset("b")}
    assert problem.certificate("basis") == (frozenset(), 0, frozenset("a"), frozenset())
    assert problem.certificate("basis", basis="b").queries == {"a", "b"}
    assert problem.certifies([], "basis") and not problem.certifies([], "basis", basis="b")
    assert problem.certificate("family").queries == {"a", "b"}


def test_gaps_in_areas():
    # Only the ends of an area matter for either question.
    whole = Problem(uniform("ab", 1), {"a": 1, "b": 9}, {"a": (0, 5), "b": (4, 10)})
    split = Problem(uniform("ab", 1), {"a": 1, "b": 9},
                    {"a": [(0, 1), (5, 5)], "b": [(4, 4), (8, 10)]})
    for mode in ("basis", "family"):
        assert whole.certificate(mode).queries == split.certificate(mode).queries != frozenset()


def test_known_weights_need_no_query():
    problem = Problem(graphic({1: "xy", 2: "xy", 3: "yz"}), {1: 1, 2: 1, 3: 4}, {})
    assert problem.uncertain == frozenset()
    assert problem.certificate("family") == (frozenset(), 0, problem.optimal_basis(), frozenset())
    assert len(problem.optimal_bases()) == 2


def test_exact_arithmetic():
    third = Fraction(1, 3)
    problem = Problem(uniform("ab", 1), {"a": third, "b": "1/3"}, {"a": (0, third)}, sense="max")
    assert problem.certificate("family").queries == {"a"}  # an exact tie
    assert problem.certificate("basis").queries == frozenset()  # `b` is never beaten


def test_custom_matroid():
    # At most one element of each colour.
    colour = {"r1": "red", "r2": "red", "g1": "green"}
    matroid = Matroid(colour, lambda s: len({colour[e] for e in s}) == len(s))
    problem = Problem(matroid, {"r1": 1, "r2": 5, "g1": 3},
                      {"r1": (0, 6), "r2": (2, 7), "g1": (0, 9)}, sense="max")
    found = problem.certificate("basis")
    # Once r1 is known to be 1 it cannot beat r2, which is at least 2.
    assert found.basis == {"r2", "g1"} and found.queries == {"r1"}
    assert not problem.certifies({"r2", "g1"}, "basis")


@pytest.mark.parametrize("campaign", [verify.finite, verify.intervals])
def test_matches_the_definitions(campaign):
    rng = random.Random(campaign.__name__)
    stats = {"instances": 0, "with several optimal bases": 0, "answers compared": 0}
    for _ in range(300):
        campaign(rng, stats)
    assert stats["with several optimal bases"] > 10 and stats["answers compared"] > 3000


def test_family_certificates_are_basis_certificates():
    rng = random.Random(7)
    for _ in range(300):
        matroid = verify.random_matroid(rng, 7)
        areas = {e: tuple(sorted(rng.sample(range(8), 2))) for e in matroid.ground}
        weights = {e: rng.randint(*areas[e]) for e in areas}
        problem = Problem(matroid, weights, areas, sense=rng.choice(("min", "max")))
        family = problem.certificate("family")
        assert problem.certifies(family.queries, "basis")
        assert problem.certificate("basis").cost <= family.cost


def test_minimum_cover():
    rng = random.Random(3)
    for _ in range(300):
        left, right = range(rng.randint(1, 4)), "abcd"[:rng.randint(1, 4)]
        edges = [(l, r) for l in left for r in right if rng.random() < 0.4]
        cost = {v: rng.choice((0, 1, 2, Fraction(5, 2))) for v in (*left, *right)}
        cover = minimum_cover(left, right, edges, cost)
        assert all(l in cover or r in cover for l, r in edges)
        best = min(sum(cost[v] for v in choice)
                   for choice in verify.subsets((*left, *right))
                   if all(l in choice or r in choice for l, r in edges))
        assert sum(cost[v] for v in cover) == best


def test_bruteforce_reads_the_definitions():
    bases = [frozenset("a"), frozenset("b")]
    values, actual = {"a": {0, 1}, "b": {0, 1}}, {"a": 1, "b": 0}
    # Knowing `a` picks an optimal item for either reply; it does not tell
    # whether the two tie.
    assert bruteforce.certifies(bases, values, actual, {"a"}, "basis")
    assert not bruteforce.certifies(bases, values, actual, {"a"}, "family")
    assert bruteforce.certificates(bases, values, actual, "family") == [frozenset("ab")]


def test_rejects_bad_input():
    matroid = uniform("ab", 1)
    with pytest.raises(ValueError, match="outside its area"):
        Problem(matroid, {"a": 4, "b": 1}, {"a": (1, 3)})
    with pytest.raises(ValueError, match="empty interval"):
        Problem(matroid, {"a": 2, "b": 1}, {"a": (3, 1)})
    with pytest.raises(ValueError, match="negative cost"):
        Problem(matroid, {"a": 2, "b": 1}, {"a": (1, 3)}, {"a": -1})
    with pytest.raises(ValueError, match="sense"):
        Problem(matroid, {"a": 2, "b": 1}, {}, sense="largest")
    problem = Problem(matroid, {"a": 2, "b": 1}, {"a": (1, 3)})
    with pytest.raises(ValueError, match="uncertain"):
        problem.certifies("b")
    with pytest.raises(ValueError, match="mode"):
        problem.certificate("all")
    with pytest.raises(ValueError, match="distinct"):
        Matroid("aa", lambda s: True)
    with pytest.raises(ValueError, match="is empty"):
        Problem(matroid, {"a": 2, "b": 1}, {"a": []})


@pytest.mark.parametrize("basis", ["a", "ab", ""])
def test_rejects_a_basis_that_is_not_optimal(basis):
    problem = Problem(uniform("ab", 1), {"a": 2, "b": 1}, {"a": (1, 3)})
    assert problem.optimal_basis() == {"b"}
    for mode in ("basis", "family"):
        with pytest.raises(ValueError, match="not an optimal basis"):
            problem.certificate(mode, basis=basis)
        with pytest.raises(ValueError, match="not an optimal basis"):
            problem.certifies([], mode, basis=basis)


def test_family_does_not_depend_on_the_basis():
    rng = random.Random(11)
    for _ in range(200):
        matroid = verify.random_matroid(rng, 7)
        areas = {e: tuple(sorted(rng.sample(range(4), 2))) for e in matroid.ground}
        weights = {e: rng.randint(*areas[e]) for e in areas}
        problem = Problem(matroid, weights, areas)
        costs = {problem.certificate("family", basis=b).cost for b in problem.optimal_bases()}
        assert len(costs) == 1


def test_many_tied_bases():
    # 12,870 optimal bases; none of them is enumerated.
    items = range(16)
    problem = Problem(uniform(items, 8), dict.fromkeys(items, 1), {e: (0, 2) for e in items})
    assert problem.certificate("basis").queries == set(items)
    assert not problem.certifies(range(15), "basis")
    # With weights at the ends of their areas, taking the ones that cannot
    # weigh less and leaving the ones that cannot weigh more costs nothing.
    areas = {e: (1, 2) if e < 8 else (0, 1) for e in items}
    problem = Problem(uniform(items, 8), dict.fromkeys(items, 1), areas, sense="max")
    assert problem.certificate("basis") == (frozenset(), 0, frozenset(range(8)), frozenset())


def test_basis_choice_matches_trying_every_optimal_basis():
    rng = random.Random(13)
    for _ in range(300):
        matroid = verify.random_matroid(rng, 9)
        areas = {e: tuple(sorted(rng.sample(range(4), 2))) for e in matroid.ground}
        weights = {e: rng.choice(areas[e]) for e in areas}
        costs = {e: rng.randint(0, 3) for e in areas}
        problem = Problem(matroid, weights, areas, costs, rng.choice(("min", "max")))
        bases = problem.optimal_bases()
        assert problem.certificate("basis").cost == \
            min(problem.certificate("basis", basis=b).cost for b in bases)
        queries = {e for e in problem.uncertain if rng.random() < 0.6}
        assert problem.certifies(queries, "basis") == \
            any(problem.certifies(queries, "basis", basis=b) for b in bases)


def test_too_many_optimal_bases():
    problem = Problem(uniform(range(12), 6), dict.fromkeys(range(12), 1), {0: (0, 2)})
    with pytest.raises(ValueError, match="more than 100"):
        problem.optimal_bases(limit=100)


def test_command_line():
    done = subprocess.run([sys.executable, "-m", "optcert", "examples/network.json"],
                          cwd=ROOT, capture_output=True, text=True, check=True)
    assert done.stdout.splitlines() == [
        "to certify one optimal solution: query AB, CD (cost 2)",
        "to certify all optimal solutions: query AB, AC, CD, DA (cost 4)",
    ]


def test_readme_reports_the_stored_results():
    results = json.loads((ROOT / "results.json").read_text())
    readme = (ROOT / "README.md").read_text()
    for campaign in ("finite", "intervals"):
        for count in results[campaign].values():
            assert f"{count:,}" in readme
