"""Minimum-cost vertex cover of a bipartite graph, by maximum flow."""

from collections import deque


def minimum_cover(left, right, edges, cost):
    """A minimum-cost set of vertices touching every edge. `edges` are pairs
    (l, r) with l in `left` and r in `right`; `cost` maps a vertex to a
    nonnegative number. Arithmetic is exact for exact costs."""
    left, right = list(dict.fromkeys(left)), list(dict.fromkeys(right))
    source, sink = object(), object()
    capacity = {}
    graph = {v: [] for v in [source, sink, *(("l", v) for v in left), *(("r", v) for v in right)]}

    def arc(a, b, c):
        for u, v, value in ((a, b, c), (b, a, 0)):
            if (u, v) not in capacity:
                capacity[u, v] = 0
                graph[u].append(v)
            capacity[u, v] += value

    unbounded = sum(cost[v] for v in left) + sum(cost[v] for v in right) + 1
    for v in left:
        arc(source, ("l", v), cost[v])
    for v in right:
        arc(("r", v), sink, cost[v])
    for l, r in edges:
        arc(("l", l), ("r", r), unbounded)

    def reachable():
        seen, queue = {source: None}, deque([source])
        while queue:
            u = queue.popleft()
            for v in graph[u]:
                if v not in seen and capacity[u, v] > 0:
                    seen[v] = u
                    queue.append(v)
        return seen

    while True:  # Edmonds-Karp
        seen = reachable()
        if sink not in seen:
            break
        path, v = [], sink
        while seen[v] is not None:
            path.append((seen[v], v))
            v = seen[v]
        push = min(capacity[a] for a in path)
        for u, v in path:
            capacity[u, v] -= push
            capacity[v, u] += push
    touched = {l for l, _ in edges} | {r for _, r in edges}
    return ({v for v in left if ("l", v) not in seen and v in touched}
            | {v for v in right if ("r", v) in seen})
