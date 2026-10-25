"""Run reproducible student tests. Requires Python 3.12+ and JDK 17+."""
import argparse
import gzip
import json
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from run import build, execute
from public_validate import check
from oracles import expected, certify_msf

SEED = 252904
RESULTS = ROOT / "tests" / "results"


def write_jsonl(path, values):
    with path.open("w", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, separators=(",", ":")) + "\n")


def small_cases():
    cases = []

    def add(name, request, reason):
        cases.append({"name": name, "input": request, "output": expected(request),
                      "justification": reason})

    add("ping", {"task": "ping"}, "The transport contract requires status=ready.")
    for task in ("dsu", "kruskal", "prim", "scc", "topo"):
        key = "operations" if task == "dsu" else "edges"
        add(task + "_empty", {"task": task, "n": 0, key: []}, "The empty graph has no vertices or edges.")
        add(task + "_isolates", {"task": task, "n": 6, key: []},
            "Six independent vertices; no forest edges or condensation edges.")
    add("dsu_merge_repeat_self", {"task": "dsu", "n": 6,
        "operations": [[0, 1], [2, 3], [1, 2], [3, 0], [4, 4], [4, 5], [0, 5]]},
        "Prefix connected-component search gives (5,2),(4,2),(3,4),(3,4),(3,4),(2,4),(1,6).")
    forest = [[0, 0, -1000000000], [0, 1, 9], [0, 1, -4], [1, 2, -1],
              [0, 2, 10], [3, 4, 7], [3, 4, 7]]
    for task in ("kruskal", "prim"):
        add(task + "_disconnected_loops_parallel", {"task": task, "n": 6, "edges": forest},
            "Choose weights -4,-1,7: total 2; vertex 5 is isolated, so 3 components.")
        for sign in (-1, 1):
            add(task + "_long_" + str(sign), {"task": task, "n": 5,
                "edges": [[v, v + 1, sign * 1000000000] for v in range(4)]},
                "The unique chain has four edges; its cost is sign * 4,000,000,000.")
        add(task + "_ties", {"task": task, "n": 4,
            "edges": [[0, 1, 2], [1, 2, 2], [2, 3, 2], [0, 3, 2], [0, 2, 2]]},
            "Any three edges that form a spanning tree cost 6.")
    add("scc_exact_condensation", {"task": "scc", "n": 7,
        "edges": [[0, 1], [1, 0], [1, 2], [0, 2], [1, 2], [2, 3], [3, 2],
                  [3, 4], [4, 4], [5, 6], [6, 5]]},
        "SCCs are {0,1},{2,3},{4},{5,6}; only the first-to-second and second-to-third pairs exist.")
    for name, edges in (("finished_cross_edge", [[0, 1], [0, 2], [2, 1]]),
                         ("self_loop", [[3, 3]]), ("disconnected_cycle", [[0, 1], [2, 3], [3, 2]])):
        add("topo_" + name, {"task": "topo", "n": 5, "edges": edges},
            "Independent Kahn removal detects exactly whether all five vertices can be removed.")
    dag_cases = [
        ("singleton", 1, 0, []),
        ("negative_unreachable", 6, 0, [[0, 1, -1], [1, 2, 0], [2, 3, -3], [4, 5, -99]]),
        ("unreachable_cycle", 6, 0, [[0, 1, 1], [2, 3, -1], [3, 2, 1]]),
        ("self_loop", 3, 0, [[2, 2, 0]]),
        ("ties_parallel", 5, 0, [[0, 1, 2], [0, 1, 2], [0, 2, 2], [1, 3, -1], [2, 3, -1]]),
        ("nonzero_source", 5, 3, [[4, 3, -2], [3, 1, -1], [1, 0, 3], [3, 2, 9], [2, 0, -8]]),
        ("long_positive", 5, 0, [[v, v + 1, 1000000000] for v in range(4)]),
        ("long_negative", 5, 0, [[v, v + 1, -1000000000] for v in range(4)]),
    ]
    for name, n, source, edges in dag_cases:
        add("dag_" + name, {"task": "dag", "n": n, "source": source, "edges": edges},
            "Kahn checks the whole graph; independent repeated Bellman-Ford relaxation computes finite distances.")
    fixed_count = len(cases)
    rng = random.Random(SEED)
    for trial in range(60):
        n = rng.randint(1, 7)
        m = rng.randint(0, 10)
        weighted = [[rng.randrange(n), rng.randrange(n), rng.randint(-8, 8)] for _ in range(m)]
        operations = [[rng.randrange(n), rng.randrange(n)] for _ in range(rng.randint(0, 12))]
        add(f"random_{trial}_dsu", {"task": "dsu", "n": n, "operations": operations},
            "Expected states come from graph search on every operation prefix, without DSU.")
        for task in ("kruskal", "prim"):
            add(f"random_{trial}_{task}", {"task": task, "n": n, "edges": weighted},
                "All subsets of size n-components are enumerated; the cheapest spanning subset is optimal.")
        directed = [e[:2] for e in weighted]
        add(f"random_{trial}_scc", {"task": "scc", "n": n, "edges": directed},
            "Floyd-Warshall Boolean transitive closure defines mutual reachability.")
        add(f"random_{trial}_topo", {"task": "topo", "n": n, "edges": directed},
            "Kahn's indegree removal is independent of the submitted DFS.")
        # Half of the requests are guaranteed DAGs with randomly permuted vertex IDs.
        if trial % 2 == 0:
            permutation = list(range(n))
            rng.shuffle(permutation)
            weighted = [[permutation[min(u, v)], permutation[max(u, v)], w]
                        for u, v, w in weighted if u != v]
        add(f"random_{trial}_dag", {"task": "dag", "n": n, "source": rng.randrange(n),
                                  "edges": weighted},
            "Kahn's whole-graph cycle result plus Bellman-Ford distances; parents checked semantically.")
    return cases, fixed_count


def witness_tests():
    """Demonstrate alternative witnesses accepted and invalid witnesses rejected."""
    records = []
    mst_input = {"task": "kruskal", "n": 3, "edges": [[0, 1, 1], [1, 2, 1], [0, 2, 1]]}
    examples = [
        ("kruskal", mst_input, {"cost": 2, "components": 1, "edge_ids": [0, 2]},
         {"cost": 2, "components": 1, "edge_ids": [0, 0]}),
        ("prim", dict(mst_input, task="prim"), {"cost": 2, "components": 1, "edge_ids": [1, 2]},
         {"cost": 2, "components": 1, "edge_ids": [1, 1]}),
        ("scc", {"task": "scc", "n": 3, "edges": [[0, 1], [1, 0], [1, 2]]},
         {"component": [40, 40, 99], "condensation": [[40, 99]]},
         {"component": [40, 40, 99], "condensation": []}),
        ("topo", {"task": "topo", "n": 3, "edges": [[0, 2], [1, 2]]},
         {"acyclic": True, "order": [1, 0, 2]}, {"acyclic": True, "order": [2, 0, 1]}),
        ("dag", {"task": "dag", "n": 4, "source": 0,
                 "edges": [[0, 1, 1], [0, 1, 1], [0, 2, 1], [1, 3, 1], [2, 3, 1]]},
         {"acyclic": True, "distance": [0, 1, 1, 2], "parent_edge": [-1, 1, 2, 4]},
         {"acyclic": True, "distance": [0, 1, 1, 2], "parent_edge": [-1, 1, 2, 0]}),
    ]
    for name, request, alternative, invalid in examples:
        reference = expected(request)
        assert check(request, alternative, reference), (name, "valid alternative rejected")
        assert not check(request, invalid, reference), (name, "invalid witness accepted")
        records.append({"name": name, "input": request, "reference": reference,
                        "alternative": alternative, "invalid": invalid,
                        "accepted_alternative": True, "rejected_invalid": True})
    return records


def scale_cases():
    n, m = 100000, 250000
    operations = [[v - 1, v] for v in range(1, n)]
    operations += [[0, i % n] for i in range(m - len(operations))]
    states = [[n - i - 1, i + 2] for i in range(n - 1)] + [[1, n]] * (m - n + 1)
    yield ("dsu_full_limits", {"task": "dsu", "n": n, "operations": operations},
           {"states": states}, "The first n-1 unions extend one chain; the remaining unions change nothing.")
    del operations, states
    for sign in (1, -1):
        edges = [[v - 1, v, sign * 1000000000] for v in range(1, n)]
        edges += [[i % n, i % n, -1000000000] for i in range(m - len(edges))]
        reference = {"cost": sign * (n - 1) * 1000000000,
                     "components": 1, "edge_ids": list(range(n - 1))}
        for task in ("kruskal", "prim"):
            yield (f"{task}_full_{sign}", {"task": task, "n": n, "edges": edges}, reference,
                   "The only non-loop edges form a chain, so all n-1 chain edges are required.")
    chain = [[v - 1, v] for v in range(1, n)]
    chain += [[i % (n - 1), i % (n - 1) + 1] for i in range(m - len(chain))]
    yield ("scc_deep_full", {"task": "scc", "n": n, "edges": chain},
           {"component": list(range(n)), "condensation": [[v - 1, v] for v in range(1, n)]},
           "A one-way chain has n singleton SCCs and exactly n-1 distinct condensation pairs.")
    yield ("topo_deep_full", {"task": "topo", "n": n, "edges": chain},
           {"acyclic": True, "order": list(range(n))},
           "Every edge increases the vertex number; duplicates do not change precedence.")
    for sign in (1, -1):
        weighted = [[u, v, sign * 1000000000] for u, v in chain]
        yield (f"dag_deep_full_{sign}", {"task": "dag", "n": n, "source": 0, "edges": weighted},
               {"acyclic": True, "distance": [v * sign * 1000000000 for v in range(n)],
                "parent_edge": [-1] + list(range(n - 1))},
               "All source-to-v routes have v equal-weight steps, hence distance=v*weight.")
    cycle = chain[:-1] + [[n - 1, 0]]
    yield ("scc_giant_full", {"task": "scc", "n": n, "edges": cycle},
           {"component": [0] * n, "condensation": []}, "The closing arc makes every vertex mutually reachable.")
    yield ("topo_cycle_full", {"task": "topo", "n": n, "edges": cycle},
           {"acyclic": False, "order": []}, "The n-vertex directed ring is a cycle.")
    del cycle, chain
    fan = [[0, 1 + i % (n - 1)] for i in range(m)]
    yield ("topo_high_degree_full", {"task": "topo", "n": n, "edges": fan},
           {"acyclic": True, "order": list(range(n))},
           "Only vertex 0 has outgoing arcs; it must precede all other vertices.")
    cycle = [[1 + i % (n - 1), 1 + (i + 1) % (n - 1), 0] for i in range(m)]
    yield ("dag_unreachable_cycle_full", {"task": "dag", "n": n, "source": 0, "edges": cycle},
           {"acyclic": False, "distance": [], "parent_edge": []},
           "Source 0 is isolated; vertices 1..n-1 form an unreachable directed cycle.")
    for task in ("kruskal", "prim", "scc", "topo"):
        result = ({"cost": 0, "edge_ids": [], "components": n} if task in ("kruskal", "prim")
                  else {"component": list(range(n)), "condensation": []} if task == "scc"
                  else {"acyclic": True, "order": list(range(n))})
        yield (task + "_maximum_isolates", {"task": task, "n": n, "edges": []}, result,
               "All 100000 vertices are isolated; each is its own component.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="skip the full-limit cases")
    args = parser.parse_args()
    RESULTS.mkdir(exist_ok=True)
    command = build("Java")
    cases, fixed_count = small_cases()
    write_jsonl(ROOT / "tests" / "my_cases.jsonl", [c["input"] for c in cases])
    write_jsonl(ROOT / "tests" / "expected.jsonl", [c["output"] for c in cases])
    (ROOT / "tests" / "case_manifest.json").write_text(json.dumps([
        {"line": i + 1, "name": c["name"], "justification": c["justification"]}
        for i, c in enumerate(cases)], indent=2) + "\n", encoding="utf-8")
    # Exact same cases repeated in reverse task order within the SAME JVM.
    repeated = cases + list(reversed(cases))
    answers = execute(command, [c["input"] for c in repeated])
    for case, answer in zip(repeated, answers):
        assert check(case["input"], answer, case["output"]), (case["name"], answer, case["output"])
        if case["input"]["task"] in ("kruskal", "prim"):
            certify_msf(case["input"]["n"], case["input"]["edges"], answer)
    write_jsonl(RESULTS / "small_actual.jsonl", answers)
    witness = witness_tests()
    (RESULTS / "witness_checks.json").write_text(json.dumps(witness, indent=2) + "\n", encoding="utf-8")
    print(f"PASS {fixed_count} fixed + {len(cases)-fixed_count} random cases; {len(repeated)} mixed requests in one JVM")
    print(f"PASS {len(witness)} alternative witnesses accepted and {len(witness)} invalid witnesses rejected")
    subprocess.run(["javac", "--release", "17", "-encoding", "UTF-8", "-cp", str(ROOT / ".build/Java"),
                    "-d", str(ROOT / ".build/Java"), str(ROOT / "tests/RouteTests.java")], check=True)
    routes = subprocess.run(["java", "-Xmx384m", "-cp", str(ROOT / ".build/Java"), "RouteTests"],
                            text=True, capture_output=True, check=True, timeout=20)
    (RESULTS / "route_actual.jsonl").write_text(routes.stdout, encoding="utf-8")
    route_count = len(routes.stdout.splitlines())
    print(f"PASS {route_count} direct route helper cases")
    scale_summary = []
    if not args.quick:
        with gzip.open(RESULTS / "scale_inputs.jsonl.gz", "wt", encoding="utf-8") as inputs, \
             gzip.open(RESULTS / "scale_expected.jsonl.gz", "wt", encoding="utf-8") as reference, \
             gzip.open(RESULTS / "scale_actual.jsonl.gz", "wt", encoding="utf-8") as actual:
            for name, request, exp, reason in scale_cases():
                start = time.perf_counter()
                answer = execute(command, [request])[0]
                seconds = time.perf_counter() - start
                assert check(request, answer, exp), name
                for stream, obj in ((inputs, request), (reference, exp), (actual, answer)):
                    stream.write(json.dumps(obj, separators=(",", ":")) + "\n")
                record = {"name": name, "n": request["n"],
                          "m_or_q": len(request.get("edges", request.get("operations", []))),
                          "seconds": round(seconds, 6), "justification": reason, "status": "PASS"}
                scale_summary.append(record)
                print(f"PASS {name}: n={record['n']}, m/q={record['m_or_q']}, {seconds:.3f} s", flush=True)
        (RESULTS / "scale_summary.json").write_text(json.dumps(scale_summary, indent=2) + "\n", encoding="utf-8")
    summary = {"seed": SEED, "fixed_cases": fixed_count, "random_cases": len(cases)-fixed_count,
               "mixed_requests_one_jvm": len(repeated), "route_cases": route_count,
               "alternative_witnesses_accepted": len(witness), "invalid_witnesses_rejected": len(witness),
               "scale_cases": len(scale_summary), "status": "PASS"}
    (RESULTS / ("quick_summary.json" if args.quick else "summary.json")).write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("PASS all student tests")


if __name__ == "__main__":
    main()
