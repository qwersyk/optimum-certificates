# Certificates for an optimal basis and for the set of optimal bases

This note states what the library computes and proves it. Section 2 restates
known results. Section 3 is a variation of the same argument for a stronger
question; it has not been reviewed by anyone else, and no claim is made that
it is new.

## 1. Setting

$M$ is a matroid on a finite set $E$ with bases $\mathcal B$. Every element
$e$ has an area $A_e \subset \mathbb R$, a finite union of closed bounded
intervals, with least and greatest points $L_e \le U_e$, and an actual weight
$w_e \in A_e$. An element is *uncertain* if $L_e < U_e$. Weights are
maximised; minimisation is the same problem with all numbers negated.

For weights $v$, let $\mathcal F(v)$ be the set of bases of maximum weight.
A set $Q$ of uncertain elements is a set of queries. A *world consistent
with* $Q$ is any $v$ with $v_e \in A_e$ for all $e$ and $v_e = w_e$ for
$e \in Q$. Write

```math
\ell_e(Q) = \begin{cases} w_e & e \in Q \\ L_e & e \notin Q \end{cases}
\qquad
u_e(Q) = \begin{cases} w_e & e \in Q \\ U_e & e \notin Q \end{cases}
```

for the least and greatest weight of $e$ in such a world. Because the areas
are independent, any combination of these extremes is itself a consistent
world.

$Q$ is a

- **basis certificate** if some basis belongs to $\mathcal F(v)$ for every
  consistent $v$;
- **family certificate** if $\mathcal F(v) = \mathcal F(w)$ for every
  consistent $v$.

Every family certificate is a basis certificate. The converse fails. Let the
task be to pick the lighter of two items, $a \in [1, 3]$ and $b \in [3, 5]$.
Then $a$ is a correct answer without any query, but whether $b$ is one as
well depends on the weights.

Fix a basis $B \in \mathcal F(w)$. An *exchange* is a pair $(i, j)$ with
$i \in B$, $j \notin B$ and $B - i + j \in \mathcal B$. A basis is optimal
exactly when $v_i \ge v_j$ for all of its exchanges.

## 2. One optimal basis (known)

$Q$ certifies that $B$ stays optimal if and only if
$\ell_i(Q) \ge u_j(Q)$ for every exchange $(i, j)$. This is Lemma 8 of
Diwan et al. [2]. Only the ends of the areas enter, so the answer is the same
for open intervals. For one exchange with $L_i < U_j$ there are four cases:

| $w_i \ge U_j$ | $L_i \ge w_j$ | constraint on $Q$ |
|---|---|---|
| yes | yes | $i \in Q$ or $j \in Q$ |
| yes | no | $i \in Q$ |
| no | yes | $j \in Q$ |
| no | no | $i \in Q$ and $j \in Q$ |

The certificates of $B$ are therefore the sets that contain the forced
elements and cover the remaining pairs, which form a bipartite graph between
$B$ and $E \setminus B$; the cheapest one is the forced elements plus a
minimum-cost vertex cover. This is the construction of Erlebach and
Hoffmann [1] for spanning trees and of [2] for matroids.

When several bases are optimal, their cheapest certificates can differ in cost
(Figure 2 of [2]). The library chooses the basis as Algorithm 1 of [2] does.
Going through the weights from the heaviest, among tied elements it first
takes those that every optimal basis must contain. Then it prefers to take an
element whose weight is at the lower end of its area, and to leave out one
whose weight is at the upper end, the costlier first: such an element needs
no query on its own account. That a basis chosen this way has a cheapest
certificate is Theorem 14 of [2]. The rules were implemented here from the
paper's description, in the mirrored form for maximisation, and the outcome
is compared with trying every optimal basis (Section 4).

## 3. The set of all optimal bases

**Lemma.** For any weights $v$: $\mathcal F(v) = \mathcal F(w)$ if and only
if $v_i - v_j$ and $w_i - w_j$ have the same sign (positive or zero) for every
exchange $(i, j)$ of $B$.

*Proof.* Suppose the families are equal. Then $B$ is optimal for $v$, so
$v_i \ge v_j$. The basis $B - i + j$ is optimal for $w$ exactly when
$w_i = w_j$ and for $v$ exactly when $v_i = v_j$, so the signs agree.

Suppose the signs agree. All $v_i - v_j$ are nonnegative, so $B$ is optimal
for $v$. Let $X \in \mathcal F(w)$; we show $X \in \mathcal F(v)$ by induction
on $|X \setminus B|$. If $X \ne B$, take $i \in B \setminus X$. By the
symmetric exchange property there is $j \in X \setminus B$ such that
$B - i + j$ and $X' = X - j + i$ are bases. Their weights under $w$ add up to
twice the optimum and neither exceeds it, so both are optimal and
$w_i = w_j$. Then $X' \in \mathcal F(v)$ by induction, and $v_i = v_j$ gives
$X$ the same weight under $v$. So $\mathcal F(w) \subseteq \mathcal F(v)$.
The assumption is symmetric in $v$ and $w$, and $B$ is optimal for both, so
the reverse inclusion follows in the same way. ∎

By the lemma, $Q$ is a family certificate if and only if for every exchange
$(i, j)$

- when $w_i = w_j$: both weights are fixed, that is, each of $i$, $j$ that is
  uncertain is in $Q$;
- when $w_i > w_j$: the difference stays positive, $\ell_i(Q) > u_j(Q)$.

Let $C$ be the set of uncertain elements that some exchange forces:

```math
i \in C \iff L_i \le w_j \text{ for some exchange } (i, j), \qquad
j \in C \iff w_i \le U_j \text{ for some exchange } (i, j).
```

Let $H$ be the bipartite graph on the remaining elements with an edge for
every exchange $(i, j)$, $i, j \notin C$, with $L_i \le U_j$.

**Theorem.** $Q$ is a family certificate if and only if $C \subseteq Q$ and
$Q$ contains an end of every edge of $H$. The minimum cost of a family
certificate is the cost of $C$ plus the minimum cost of a vertex cover of
$H$.

*Proof.* Let $i \in C$ with $L_i \le w_j$, and suppose $i \notin Q$. The
world that differs from $w$ only in giving $i$ the weight $L_i$ is consistent
with $Q$ and has $v_i \le v_j$. This changes the sign, except when
$L_i = w_i = w_j$; in that case give $i$ any other weight from its area.
So $i$ must be queried. The case of $j$ is symmetric, with $U_j$ in place of
$L_i$. Hence $C \subseteq Q$ is necessary.

Assume $C \subseteq Q$ and take an exchange $(i, j)$. If $w_i = w_j$, each
uncertain end is in $C$, so the difference is fixed. Let $w_i > w_j$. If both
ends are queried the difference is unchanged. If $j \notin Q$ then
$j \notin C$, so $w_i > U_j$; if $i \notin Q$ then $L_i > w_j$. So a single
queried end keeps the difference positive, and with neither queried the
smallest difference is $L_i - U_j$, which is positive exactly when $(i, j)$
is not an edge of $H$. ∎

Unlike in Section 2, the result does not depend on which optimal basis $B$ is
used, since the definition does not mention one. The exchanges of one basis
are found with $|B| \cdot |E \setminus B|$ calls of the independence oracle,
and the vertex cover by one maximum flow.

The areas enter only through $L_e$, $U_e$ and whether $e$ is uncertain, so
gaps inside an area do not matter. Closedness does: if an end of an area is
not attained, a tie at that end cannot occur, and the conditions above change
from $\le$ to $<$ for that end. The library assumes closed areas.

## 4. Checks

`verify.py` enumerates, for random small matroids, every world and every set
of queries, evaluates both definitions directly, and compares the outcome
with the library: the answer for each set of queries, and the minimum cost.
The minimum cost found by enumeration is over all optimal bases, so it also
checks the choice of basis in Section 2.
For areas that are finite sets the enumeration is complete. For intervals it
runs over a grid of all end points and midpoints, which contains the worlds
used in the proofs above but is not by itself a proof for interval areas.
Counts are in `results.json`.

## References

1. T. Erlebach, M. Hoffmann. Minimum spanning tree verification under
   uncertainty. WG 2014, LNCS 8747.
2. H. Diwan, L. Hellerstein, N. Megow, J. Schlöter. Optimal verification of a
   minimum-weight basis in an uncertainty matroid. STACS 2026, LIPIcs 364,
   32:1–32:20. [arXiv:2512.17116](https://arxiv.org/abs/2512.17116)
3. A. Merino, J. A. Soto. The minimum cost query problem on matroids with
   uncertainty areas. ICALP 2019.
   [arXiv:1904.11668](https://arxiv.org/abs/1904.11668)
4. C. Dürr, A. Merino, J. A. Soto, J. Verschae. Set selection with uncertain
   weights: non-adaptive queries and thresholds.
   [arXiv:2404.17214](https://arxiv.org/abs/2404.17214)
