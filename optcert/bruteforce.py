"""The definitions, evaluated by enumeration. Used to test the library;
nothing here relies on exchange arguments or on vertex covers.

Worlds are enumerated over a finite set of values per element, so the result
is exact when every area is a finite set of points.
"""

from fractions import Fraction
from itertools import chain, combinations, product


def optimal_family(bases, value):
    """The set of maximum-weight bases."""
    total = {b: sum(value[e] for e in b) for b in bases}
    best = max(total.values())
    return frozenset(b for b, t in total.items() if t == best)


def completions(values, actual, queries):
    """Every world that agrees with the actual one on the queried elements.
    `values` maps each element to the finite set of values it may take."""
    names = list(values)
    choices = [[actual[e]] if e in queries else sorted(values[e]) for e in names]
    for combo in product(*choices):
        yield dict(zip(names, combo))


def certifies(bases, values, actual, queries, mode):
    families = [optimal_family(bases, world) for world in completions(values, actual, queries)]
    if mode == "family":
        return all(f == families[0] for f in families)
    return bool(frozenset.intersection(*families))


def certificates(bases, values, actual, mode):
    """Every certificate, as a list of frozensets."""
    uncertain = [e for e in values if len(values[e]) > 1]
    subsets = chain.from_iterable(combinations(uncertain, k) for k in range(len(uncertain) + 1))
    return [frozenset(q) for q in subsets if certifies(bases, values, actual, q, mode)]


def minimum_cost(bases, values, actual, cost, mode):
    return min(sum((Fraction(cost[e]) for e in q), Fraction(0))
               for q in certificates(bases, values, actual, mode))
