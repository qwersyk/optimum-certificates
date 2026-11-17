"""Certificates for an optimal matroid basis when weights are uncertain.

Every element has a weight that is known to lie in an area, a finite union of
closed bounded intervals, and an actual weight inside it. Querying an element
reveals its actual weight. A set of queries is a certificate when what it
reveals settles the answer whatever the weights left unqueried turn out to
be. Two answers are supported:

"basis"   some basis is optimal for every possible value of the unqueried
          weights;
"family"  the set of all optimal bases is the same for every possible value
          of the unqueried weights.

Internally the objective is always maximised; a minimisation problem is
negated on the way in.
"""

from collections import namedtuple
from fractions import Fraction

from .cover import minimum_cover

Certificate = namedtuple("Certificate", "queries cost basis required")
Certificate.__doc__ = """A minimum-cost certificate.

queries   the elements to query
cost      their total cost
basis     an optimal basis that the certificate was computed from
required  the queries that belong to every certificate (for "basis": to every
          certificate of this basis)
"""


class Problem:
    def __init__(self, matroid, weights, areas, costs=None, sense="min"):
        """`weights` maps each element to its actual weight, `areas` to its
        area: a pair (lo, hi) or a list of such pairs. An element missing
        from `areas` is known exactly. `costs` maps elements to nonnegative
        query costs, 1 by default."""
        if sense not in ("min", "max"):
            raise ValueError("sense must be 'min' or 'max'")
        self.matroid, self.sense = matroid, sense
        sign = -1 if sense == "min" else 1
        self._value, self._lo, self._hi, self.costs = {}, {}, {}, {}
        for e in matroid.ground:
            weight = Fraction(weights[e])
            parts = areas.get(e, (weight, weight))
            if not parts:
                raise ValueError(f"the area of {e!r} is empty")
            if not isinstance(parts[0], (tuple, list)):
                parts = [parts]
            parts = [(Fraction(a), Fraction(b)) for a, b in parts]
            if any(a > b for a, b in parts):
                raise ValueError(f"empty interval in the area of {e!r}")
            if not any(a <= weight <= b for a, b in parts):
                raise ValueError(f"the weight of {e!r} is outside its area")
            ends = sorted(sign * x for part in parts for x in part)
            self._value[e], self._lo[e], self._hi[e] = sign * weight, ends[0], ends[-1]
            self.costs[e] = Fraction(1 if costs is None else costs.get(e, 1))
            if self.costs[e] < 0:
                raise ValueError(f"negative cost for {e!r}")
        #: The elements whose weight is not known exactly.
        self.uncertain = frozenset(e for e in matroid.ground if self._lo[e] < self._hi[e])

    # -- optimal bases -------------------------------------------------------

    def optimal_basis(self):
        return self.matroid.greedy(self._value.__getitem__)

    def optimal_bases(self, limit=10_000):
        """All optimal bases, found by exchanges that keep the weight."""
        found, queue = set(), [self.optimal_basis()]
        while queue:
            basis = queue.pop()
            if basis in found:
                continue
            found.add(basis)
            if len(found) > limit:
                raise ValueError(f"more than {limit} optimal bases")
            queue += [basis - {i} | {j} for i, j in self.matroid.exchanges(basis)
                      if self._value[i] == self._value[j]]
        return found

    def _preferred_basis(self, known=frozenset(), costs=None):
        """An optimal basis that has a cheapest certificate among all optimal
        bases, by the contraction and deletion rules of Diwan, Hellerstein,
        Megow and Schloter (Algorithm 1). Elements in `known` count as
        known exactly."""
        value, lo, hi = self._value, self._lo, self._hi
        independent = self.matroid.independent
        cost = (lambda e: 1) if costs is None else costs.__getitem__
        uncertain = self.uncertain - known
        chosen = set()

        def extend(elements):
            """`chosen` plus as many of the elements as stay independent."""
            out = set(chosen)
            for e in elements:
                if independent(out | {e}):
                    out.add(e)
            return out

        def replaceable(e, basis, others):
            return any(independent(basis - {e} | {x}) for x in others)

        for weight in sorted(set(value.values()), reverse=True):
            tied = [e for e in self.matroid.ground if value[e] == weight]
            while True:
                # An element spanned by what is chosen cannot be added.
                tied = [e for e in tied if e not in chosen and independent(chosen | {e})]
                if not tied:
                    break
                basis = extend(tied)
                others = [e for e in tied if e not in basis]
                forced = [e for e in tied if e in basis and not replaceable(e, basis, others)]
                low = [e for e in tied if e in uncertain and lo[e] == weight]
                high = [e for e in tied if e in uncertain and hi[e] == weight]
                if forced:  # in every optimal basis
                    chosen.update(forced)
                elif low:  # cannot weigh less: safe to take without a query
                    chosen.add(max(low, key=cost))
                elif high:  # cannot weigh more: safe to leave out without a query
                    tied.remove(max(high, key=cost))
                else:
                    known_exactly = [e for e in tied if e not in uncertain]
                    chosen.add((known_exactly or tied)[0])
        return frozenset(chosen)

    # -- the two characterisations ------------------------------------------

    def _family_constraints(self, basis):
        """(critical elements, residual edges) for the set of all optimal bases."""
        value, lo, hi = self._value, self._lo, self._hi
        pairs = self.matroid.exchanges(basis)
        critical = {i for i, j in pairs if value[j] >= lo[i]} \
            | {j for i, j in pairs if value[i] <= hi[j]}
        critical &= self.uncertain
        edges = [(i, j) for i, j in pairs if i not in critical and j not in critical
                 and value[i] > value[j] and lo[i] <= hi[j]]
        return critical, edges

    def _basis_constraints(self, basis):
        """(required elements, residual edges) for this basis to stay optimal."""
        value, lo, hi = self._value, self._lo, self._hi
        required, edges = set(), []
        for i, j in self.matroid.exchanges(basis):
            if lo[i] >= hi[j]:
                continue
            i_alone, j_alone = value[i] >= hi[j], lo[i] >= value[j]
            if i_alone and j_alone:
                edges.append((i, j))
            else:
                required |= {e for e, other_alone in ((i, j_alone), (j, i_alone))
                             if not other_alone}
        return required, [(i, j) for i, j in edges if i not in required and j not in required]

    def _constraints(self, mode, basis):
        if mode == "family":
            return self._family_constraints(basis)
        if mode == "basis":
            return self._basis_constraints(basis)
        raise ValueError("mode must be 'basis' or 'family'")

    def _reference(self, basis):
        """The basis to work from: the given one, which must be optimal, or
        the greedy one."""
        if basis is None:
            return self.optimal_basis()
        basis = frozenset(basis)
        if not (self.matroid.independent(basis) and len(basis) == len(self.optimal_basis())
                and all(self._value[i] >= self._value[j]
                        for i, j in self.matroid.exchanges(basis))):
            raise ValueError("not an optimal basis")
        return basis

    def certifies(self, queries, mode="basis", basis=None):
        """Whether the queries are a certificate. For "basis", whether they
        certify the given optimal basis, or any optimal basis if none is
        given."""
        queries = set(queries)
        if not queries <= self.uncertain:
            raise ValueError("only elements with uncertain weight can be queried")
        if mode == "basis" and basis is None:
            # With the queried weights known, some basis needs no further
            # query exactly when the preferred one needs none.
            return self._certifies(queries, mode, self._preferred_basis(frozenset(queries)))
        return self._certifies(queries, mode, self._reference(basis))

    def _certifies(self, queries, mode, basis):
        required, edges = self._constraints(mode, basis)
        return required <= queries and all(i in queries or j in queries for i, j in edges)

    def certificate(self, mode="basis", basis=None):
        """A minimum-cost certificate. For "basis" the minimum is taken over
        all optimal bases unless one of them is given."""
        if mode == "basis" and basis is None:
            return self._certificate(mode, self._preferred_basis(costs=self.costs))
        return self._certificate(mode, self._reference(basis))

    def _certificate(self, mode, basis):
        required, edges = self._constraints(mode, basis)
        cover = minimum_cover([i for i, _ in edges], [j for _, j in edges], edges, self.costs)
        queries = frozenset(required | cover)
        return Certificate(queries, sum(self.costs[e] for e in queries), basis,
                           frozenset(required))
