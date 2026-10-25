# Student tests

Run from the repository root with Python 3.12+ and JDK 17+:

```sh
python tools/run.py --setup
python tools/run.py --check
python tests/run_tests.py
python tests/benchmark.py
```

On Windows, replace `python` with `py -3` if necessary. The Python scripts
compile and run the Java solution; Python is only the test driver.
No third-party packages are required. A shorter development run is
`python tests/run_tests.py --quick`.

## Inputs, expected answers and actual results

| File | Contents |
|---|---|
| `my_cases.jsonl` | 392 inputs: 32 named boundaries and 360 seeded random cases |
| `expected.jsonl` | One independently computed expected answer per input line |
| `case_manifest.json` | Case name and justification, keyed by 1-based input line |
| `results/small_actual.jsonl` | 784 actual answers: input file order, then reversed input file order, all in one JVM |
| `results/witness_checks.json` | Five alternative valid answers and five deliberately invalid witnesses, with checker results |
| `results/route_actual.jsonl` | Nine direct Java helper tests, including actual routes and edge IDs |
| `results/scale_inputs.jsonl.gz` | Complete 17 large input requests, compressed JSON Lines |
| `results/scale_expected.jsonl.gz` | Corresponding expected outputs |
| `results/scale_actual.jsonl.gz` | Complete actual outputs, not truncated summaries |
| `results/scale_summary.json` | Scale case names, dimensions, elapsed seconds and mathematical justification |
| `results/summary.json` | Test counts and completion status |
| `results/benchmark_inputs.jsonl.gz` | The exact three benchmark graphs |
| `results/benchmark_forests.jsonl.gz` | Both actual forests before timing |
| `results/benchmark.json` | Environment, seeds, graph digests, 42 raw timings and medians |

Read compressed evidence with Python's built-in `gzip` module. For example,
inspect the first stored full-limit input:

```sh
python -c "import gzip,json; f=gzip.open('tests/results/scale_inputs.jsonl.gz','rt'); x=json.loads(next(f)); print(x['task'],x['n'],len(x['operations']))"
```

To run the small input file without comparison:

```sh
python tools/run.py --input tests/my_cases.jsonl
```

## Independent expectations

`oracles.py` uses graph search on each DSU prefix, exhaustive spanning-subset
enumeration for small forests, transitive closure for SCCs, Kahn's indegree
algorithm for cycles, and Bellman-Ford relaxation for DAG distances. These
oracles do not call the submitted algorithms. The fixed cases have additional
mathematical explanations in `case_manifest.json`.

We reuse the unmodified supplied semantic witness checker instead of comparing
non-unique arrays literally. In addition, all small MSFs and benchmark forests
are certified independently: selected edges must form a spanning forest, and
every input edge must be at least as heavy as the maximum edge on its forest
path. Binary lifting makes this certificate practical for the benchmark sizes.

`witness_tests()` demonstrates that different optimal edge IDs, arbitrary SCC
labels, a different topological ordering, and tied/parallel shortest-path
parents are accepted. Repeated selected IDs, missing condensation pairs,
backwards topological precedence and a parent edge ending at the wrong vertex
are rejected.

## Full-limit construction

All nonempty scale cases use `n=100000` and `m/q=250000`.
The expected answers follow directly from the construction:

- DSU: first connect the chain, then repeat unions inside the connected set.
- MSF: only the chain edges connect distinct vertices; all remaining edges
  are loops. Test both positive and negative 1,000,000,000 weights.
- SCC: a chain has singleton SCCs; adding a closing arc creates one giant SCC.
- Topo: a directed chain and high-degree star are acyclic; a ring is cyclic.
- DAG: repeated chain arcs give distance `v * weight`; an unreachable ring
  must still make the whole request cyclic.
- Four additional cases contain 100000 isolated vertices and no edges.

The complete scale requests and answers are stored, not only the generators.
The elapsed scale times include JSON transport and JVM startup and are
separate from the algorithm-only Kruskal/Prim benchmark.

## Direct route helper tests

`RouteTests.java` calls `Algorithms.reconstructRoute` directly and checks
vertices, incoming edge direction and summed edge weight. Cases cover
reachable, source, unreachable, tied routes, parallel edges, a nonzero source,
invalid direction, a parent cycle, and a route of 100000 vertices.
These tests use explicit assertions that run without Java's `-ea` flag.

The original `Public checks` workflow is unchanged. A separate
`Student tests` workflow runs this suite on pushes and pull requests.
