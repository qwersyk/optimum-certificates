"""Matroids given by an independence oracle."""

from itertools import combinations


class Matroid:
    """A matroid on the elements `ground`, in a fixed order."""

    def __init__(self, ground, independent):
        self.ground = tuple(ground)
        if len(set(self.ground)) != len(self.ground):
            raise ValueError("elements must be distinct")
        self._independent = independent

    def independent(self, elements):
        return self._independent(frozenset(elements))

    def greedy(self, key):
        """The basis built by taking elements in decreasing order of key."""
        basis = set()
        for e in sorted(self.ground, key=key, reverse=True):
            if self.independent(basis | {e}):
                basis.add(e)
        return frozenset(basis)

    def exchanges(self, basis):
        """All pairs (i, j) with i in the basis and j outside it such that
        replacing i by j gives another basis."""
        basis = frozenset(basis)
        return [(i, j) for j in self.ground if j not in basis
                for i in self.ground if i in basis
                and self.independent(basis - {i} | {j})]

    def bases(self):
        """Every basis, by enumeration. For small matroids only."""
        rank = len(self.greedy(lambda e: 0))
        return [frozenset(c) for c in combinations(self.ground, rank)
                if self.independent(c)]


def graphic(edges):
    """The cycle matroid of a graph. `edges` maps an edge name to its two
    end vertices; parallel edges and loops are allowed. Bases are the
    spanning forests."""
    edges = dict(edges)

    def independent(names):
        parent = {}

        def find(v):
            while parent.setdefault(v, v) != v:
                parent[v] = parent[parent[v]]
                v = parent[v]
            return v

        for name in names:
            a, b = (find(v) for v in edges[name])
            if a == b:
                return False
            parent[a] = b
        return True

    return Matroid(edges, independent)


def uniform(ground, rank):
    """The uniform matroid: every set of at most `rank` elements is independent."""
    return Matroid(ground, lambda s: len(s) <= rank)

