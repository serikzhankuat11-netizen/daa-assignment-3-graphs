"""Independent small-graph oracles and an MST optimality certificate.

No production algorithm is imported. Small MSFs are found by exhaustive subsets;
SCCs by transitive closure; cycle detection by Kahn; distances by Bellman-Ford.
"""
from collections import deque
from itertools import combinations


def labels_by_search(n, edges):
    adjacency = [[] for _ in range(n)]
    for edge in edges:
        u, v = edge[:2]
        adjacency[u].append(v)
        adjacency[v].append(u)
    labels = [-1] * n
    sizes = []
    for start in range(n):
        if labels[start] >= 0:
            continue
        label = len(sizes)
        labels[start] = label
        stack = [start]
        size = 0
        while stack:
            u = stack.pop()
            size += 1
            for v in adjacency[u]:
                if labels[v] < 0:
                    labels[v] = label
                    stack.append(v)
        sizes.append(size)
    return labels, sizes


def kahn(n, edges):
    adjacency = [[] for _ in range(n)]
    indegree = [0] * n
    for edge in edges:
        u, v = edge[:2]
        adjacency[u].append(v)
        indegree[v] += 1
    queue = deque(v for v in range(n) if indegree[v] == 0)
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in adjacency[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    return order if len(order) == n else None


def expected(request):
    task = request["task"]
    if task == "ping":
        return {"status": "ready"}
    n = request["n"]
    edges = request.get("edges", [])
    if task == "dsu":
        prefix, states = [], []
        for pair in request["operations"]:
            prefix.append(pair)
            _, sizes = labels_by_search(n, prefix)
            states.append([len(sizes), max(sizes, default=0)])
        return {"states": states}
    if task in ("kruskal", "prim"):
        _, sizes = labels_by_search(n, edges)
        count = len(sizes)
        best, best_ids = None, []
        for ids in combinations(range(len(edges)), n - count):
            chosen = [edges[i] for i in ids]
            _, parts = labels_by_search(n, chosen)
            # Exactly n-c edges and c components imply acyclicity and spanning.
            if len(parts) == count:
                cost = sum(e[2] for e in chosen)
                if best is None or cost < best:
                    best, best_ids = cost, list(ids)
        assert best is not None
        return {"cost": best, "edge_ids": best_ids, "components": count}
    if task == "scc":
        reach = [[u == v for v in range(n)] for u in range(n)]
        for u, v in edges:
            reach[u][v] = True
        for k in range(n):
            for u in range(n):
                for v in range(n):
                    reach[u][v] |= reach[u][k] and reach[k][v]
        labels = [min(v for v in range(n) if reach[u][v] and reach[v][u])
                  for u in range(n)]
        pairs = sorted({(labels[u], labels[v]) for u, v in edges if labels[u] != labels[v]})
        return {"component": labels, "condensation": [list(p) for p in pairs]}
    order = kahn(n, edges)
    if task == "topo":
        return {"acyclic": order is not None, "order": order or []}
    if order is None:
        return {"acyclic": False, "distance": [], "parent_edge": []}
    distance, parents = [None] * n, [-1] * n
    distance[request["source"]] = 0
    for _ in range(n - 1):
        changed = False
        for i, (u, v, weight) in enumerate(edges):
            if distance[u] is None:
                continue
            candidate = distance[u] + weight
            if distance[v] is None or candidate < distance[v]:
                distance[v], parents[v] = candidate, i
                changed = True
        if not changed:
            break
    return {"acyclic": True, "distance": distance, "parent_edge": parents}


def certify_msf(n, edges, answer):
    """Prove an MSF via feasibility and the cycle optimality condition.

    Every non-loop edge must weigh at least the maximum edge on its forest path.
    This certifies optimality without rerunning Kruskal or Prim.
    """
    ids = answer["edge_ids"]
    assert len(set(ids)) == len(ids)
    assert all(type(i) is int and 0 <= i < len(edges) for i in ids)
    assert answer["cost"] == sum(edges[i][2] for i in ids)
    adjacency = [[] for _ in range(n)]
    for i in ids:
        u, v, weight = edges[i]
        assert u != v
        adjacency[u].append((v, weight, i))
        adjacency[v].append((u, weight, i))
    levels = max(1, n.bit_length())
    ancestor = [[0] * n for _ in range(levels)]
    maximum = [[-(1 << 63)] * n for _ in range(levels)]
    depth, component = [0] * n, [-1] * n
    components = 0
    for start in range(n):
        if component[start] >= 0:
            continue
        component[start] = components
        ancestor[0][start] = start
        stack = [(start, -1)]
        while stack:
            u, parent_id = stack.pop()
            for v, weight, edge_id in adjacency[u]:
                if edge_id == parent_id:
                    continue
                assert component[v] == -1, "Selected edges contain a cycle"
                component[v] = components
                depth[v] = depth[u] + 1
                ancestor[0][v] = u
                maximum[0][v] = weight
                stack.append((v, edge_id))
        components += 1
    assert answer["components"] == components
    assert len(ids) == n - components
    for k in range(1, levels):
        for v in range(n):
            middle = ancestor[k - 1][v]
            ancestor[k][v] = ancestor[k - 1][middle]
            maximum[k][v] = max(maximum[k - 1][v], maximum[k - 1][middle])

    def path_max(u, v):
        result = -(1 << 63)
        if depth[u] < depth[v]:
            u, v = v, u
        difference = depth[u] - depth[v]
        for k in range(levels):
            if difference & (1 << k):
                result = max(result, maximum[k][u])
                u = ancestor[k][u]
        if u == v:
            return result
        for k in range(levels - 1, -1, -1):
            if ancestor[k][u] != ancestor[k][v]:
                result = max(result, maximum[k][u], maximum[k][v])
                u, v = ancestor[k][u], ancestor[k][v]
        return max(result, maximum[0][u], maximum[0][v])

    for u, v, weight in edges:
        assert component[u] == component[v], "Forest does not span an input component"
        if u != v:
            assert weight >= path_max(u, v), "A cheaper replacement edge exists"
