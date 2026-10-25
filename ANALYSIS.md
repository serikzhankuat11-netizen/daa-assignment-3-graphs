# Assignment 3: Graph Algorithms

**Student:** Serik Zhankuat  
**Group:** SE-2520, Astana IT University  
**Language:** Java 17  
**Verification date:** 25 October 2026

## 1. Interface and design

The selected implementation is `src/Java/Algorithms.java`.
`submission.json` contains `{"language":"Java"}`. The template's entry point,
JSON adapter, input helpers, public cases and public checker are unchanged.
Other language directories are retained template files and are not the selected
solution.

Each input line is one independent request. Main prints exactly one JSON object
per line; the algorithms print nothing. Ping still returns `{"status":"ready"}`.
Each algorithm creates its own arrays, lists, sets and heaps. There are no static
mutable algorithm fields, and neither MST algorithm changes the supplied edges.
This prevents previous requests from affecting later ones.

Vertices and edge IDs use `int`; edge IDs always refer to positions in the
original edge array. Kruskal sorts an array of IDs, not the original edges.
Adjacency lists retain the original ID on every arc. Costs and distances use
`long`; unreachable distances use `Long[]` entries equal to `null`.
A simple forest/path contains at most 99999 edges, so its absolute total is at
most 99,999,000,000,000 under the limits, well inside signed 64-bit range.
Weight comparisons use comparators rather than subtracting weights.

The `Graph` helper stores adjacency in three arrays: `offset`, `to` and
`edgeId`. The neighbours of vertex v occupy
`[offset[v], offset[v+1])`. Two linear passes construct these arrays.
Undirected graphs store two arcs per edge. The transpose reverses arc direction.

## 2. DSU

**Steps.** Initially every vertex is its own root with size 1. Find follows parent
links to a root, then makes every visited vertex point directly to that root.
Union finds both roots, returns immediately if they are equal, and otherwise
attaches the smaller component below the larger. It updates the root's size,
the component count and the largest size. The output records these last two
values after every operation.

**Invariant.** Rooted trees partition the vertices exactly according to all
connections processed so far. Each root's size is its component cardinality;
`components` counts roots, and `largest` is the maximum root size.

**Correctness.** Initially the invariant holds for singleton components.
An operation inside one component changes no connectivity. An operation between
two roots joins exactly those two connected components, subtracts one from the
count, and adds their sizes. Path compression only changes the representation
of a component. Therefore the invariant and each reported state remain correct.

**Boundaries.** For n=0 there are no operations and no states. With n>0 and no
operations there are also no states. Self-unions and repeated unions leave both
reported values unchanged.

**Complexity.** Initialization is O(n). With path compression and union by size,
q unions take O(q alpha(n)) amortised time. Total time is
O(n + q alpha(n)); memory is O(n+q), including the returned states.

## 3. Kruskal minimum spanning forest

**Steps.** Sort original edge IDs by increasing weight, using ID as a deterministic
tie-breaker. Scan them once. Select an edge only if its endpoints belong to
different DSU components, then merge those components and add its weight.

**Invariant.** Selected edges form a forest that can be extended to a minimum
spanning forest; DSU describes exactly the connectivity of the selected edges.

**Correctness.** Consider a selected edge joining two current components.
No lighter edge crossing that cut was rejected: if one had previously joined
the cut's sides, they would already be connected. Thus this edge is a lightest
available crossing edge. By the cut/exchange argument, some optimal spanning
forest contains the previously selected edges and this edge. Selection never
creates a cycle. After scanning all edges, every input edge's endpoints are
connected in the selected forest, so every original component is spanned.
Consequently the final forest has minimum total cost.

**Boundaries.** Loops always fail union. Parallel edges compete normally, and
equal weights may admit multiple correct forests. Negative weights require no
special case. Isolates remain separate DSU components. The empty graph returns
cost 0, no IDs and 0 components. A forest has exactly n-components selected IDs.

**Complexity.** Sorting takes O(m log(m+1)); DSU contributes
O(n + m alpha(n)). The standard bound is O(n + m log(m+1)).
Memory, including IDs, DSU and result, is O(n+m).

## 4. Prim minimum spanning forest

**Steps.** Build undirected adjacency lists. Start at every vertex not yet
visited, incrementing the component count. Mark that root visited and put its
outgoing edges to unvisited vertices in a min-priority queue. Repeatedly remove
the lightest candidate. If its destination was already visited, discard it.
Otherwise select that edge, visit its destination and add its new frontier.
Finish the heap before starting the next component.

**Invariant.** The visited vertices of the current component form a tree.
The heap contains every edge crossing from this tree to an unvisited vertex,
possibly together with stale candidates.

**Correctness.** After stale candidates are skipped, the next candidate is a
minimum-weight edge crossing the visited/unvisited cut. The cut property makes
it safe to add. Its destination is new, so no cycle is introduced. If the heap
becomes empty, no edge leaves the visited set; the entire current component is
spanned. Restarting repeats this argument for all components. The sum of their
minimum tree costs is the minimum forest cost.

**Boundaries.** An isolated root still counts as one component. A loop never
enters the frontier because its destination is already visited. Parallel and
negative edges work with the ordinary comparator. Stale edges are ignored.
The n=0 case returns the empty forest.

**Complexity.** Adjacency construction is O(n+m). Each undirected edge becomes
at most one heap candidate, so the lazy heap performs O(m) insertions/removals.
Time is O(n + m log(m+1)); memory is O(n+m).
Prim does not call Kruskal or DSU.

## 5. Kosaraju SCC and condensation

**Steps.** Run iterative DFS on the original graph, appending each vertex when
it finishes. Build the transpose. In decreasing first-pass finish order,
start a transpose DFS at every unlabelled vertex; label all vertices reached in
that search with one new component ID. Finally scan original edges, omitting
internal edges and deduplicating ordered component pairs in a hash set.

**Invariant.** The first pass appends a vertex only after all its DFS descendants
finish. In the second pass, completed searches are entire SCCs, and the next
search cannot leave its SCC for another unlabelled SCC.

**Correctness.** Contract SCCs into a DAG. For an edge from one SCC to another,
the source SCC has a larger maximum first-pass finishing time than the target.
The greatest remaining finish time therefore belongs to a source SCC in the
remaining condensation. In the transpose this SCC has no edge to another
unprocessed SCC. Its search reaches every vertex inside it, since reversing
edges preserves strong connectivity, and no new SCC outside it. Induction
proves that the labels describe exactly the maximal mutually reachable sets.
Scanning all original edges produces all and only cross-component pairs;
deduplication keeps each once.

**Boundaries.** Each isolate receives its own label. Self-loops stay internal.
Duplicate arcs do not create duplicate condensation pairs. For n=0, both arrays
are empty. Labels are consecutive in this implementation, but the checker
accepts any nonnegative labels with the same membership relation.

**Complexity.** Both graph constructions and both DFS passes take O(n+m).
Condensation deduplication takes expected O(m) under the usual hash-set
assumption; thus expected total time is O(n+m). Adversarial hash collisions can
increase hash-operation cost. Memory is O(n+m), including the condensation.

## 6. DFS topological ordering

**Steps.** Use states 0 (unvisited), 1 (active), and 2 (finished).
Push an unvisited root, and process one outgoing arc at a time. Push an
unvisited neighbour. An active neighbour is a back edge and makes the graph
cyclic. An edge to a finished neighbour is harmless. After all outgoing arcs
are processed, finish and pop the vertex. Check every vertex as a possible root
and reverse the finish sequence if no cycle was found.

**Invariant.** Active vertices are exactly the current DFS path. Each active
vertex remembers its next unprocessed arc. A finished vertex has had every
outgoing arc examined.

**Correctness.** An edge to an active ancestor closes a directed cycle,
including a self-loop. Conversely, DFS of a directed cycle must encounter an
edge to an active vertex before all vertices of that cycle finish.
When there is no cycle, every edge u->v has v finished before u: either DFS
discovers v from u or v is already finished. Reversing finish order therefore
puts u before v for every edge. Every vertex is output once, including isolates.

**Boundaries.** A cycle in any disconnected component returns false and [].
Repeated edges do not create a cycle by themselves. The empty graph returns
true and [].

**Complexity and depth.** Each vertex is pushed/popped once and each arc is
examined once: O(n+m) time and memory. The array `next[u]` retains progress,
so returning from a child never restarts scanning u's neighbours. Both DFS
passes and route reconstruction use explicit loops rather than recursion.
A 100000-vertex path therefore does not consume 100000 Java call frames.

## 7. DAG shortest paths and route reconstruction

**Steps.** First run the same three-state DFS cycle check over the entire graph.
A cycle anywhere returns false with two empty arrays. Otherwise initialize the
source distance to 0, other distances to null and every parent to -1.
Visit vertices in topological order. Skip unreachable vertices. For every
outgoing edge from a reachable vertex, replace the destination distance and
parent edge ID if the new distance is smaller.

**Invariant.** When a vertex is processed, its distance is the shortest source
distance, or null if no source path exists. Every finite non-source distance
has a parent chain forming a source path of exactly that weight.

**Correctness.** Every predecessor occurs earlier in topological order.
Therefore, by the time a vertex is processed, all incoming paths that could
improve it have been considered. Induction over that order proves the shortest
distances. This argument allows negative weights because no edge returns to an
earlier vertex. A parent is recorded only when extending an existing reachable
path, so it is an incoming original edge ID and its chain ends at the source.
Equal-cost alternatives need not replace a valid witness.

**Boundaries.** A cycle unreachable from the source still rejects the whole
graph. A finite distance of -1 is distinct from null. Unreachable vertices keep
parent -1. The source keeps distance 0 and parent -1: any reachable edge back
to it would imply a cycle. Arbitrary sources, negative weights, parallel edges,
ties and isolated vertices are supported. A DAG request always has n>=1.

**Complexity.** The cycle check, ordering and relaxation together take O(n+m)
time and memory.

### Helper contract and actual calls

The helper is
`Algorithms.reconstructRoute(source, target, edges, parentEdge)`.
Call it only with an acyclic result and the corresponding original edges.
It follows incoming edge IDs backwards, checks their direction, and reverses
the accumulated vertex list. An unreachable target returns []; the source
returns [source]. A malformed parent chain throws IllegalArgumentException.
The length guard prevents infinite traversal of an invalid parent cycle.
For a valid route of L vertices, time and output/auxiliary space are O(L);
there is no n-sized allocation inside the helper.

For
`E={{0,1,3},{0,2,8},{1,2,-7},{2,3,4}}`,
the actual parent array is `P={-1,0,2,3,-1}`.

| Actual call | Returned vertices | Selected edge IDs in route order | Weight |
|---|---|---|---|
| `reconstructRoute(0,3,E,P)` | [0,1,2,3] | [0,2,3] | 3-7+4 = 0 |
| `reconstructRoute(0,0,E,P)` | [0] | [] | 0 |
| `reconstructRoute(0,4,E,P)` | [] | [] | No route |

For the tied/parallel graph
`T={{0,1,2},{0,1,2},{0,2,2},{1,3,-1},{2,3,-1}}`,
the actual parent array is `Q={-1,0,2,4,-1}`.

| Actual call | Returned vertices | Selected edge IDs | Weight |
|---|---|---|---|
| `reconstructRoute(0,3,T,Q)` | [0,2,3] | [2,4] | 2-1 = 1 |
| `reconstructRoute(0,1,T,Q)` | [0,1] | [0] | 2 |

The alternative path [0,1,3], including the other equal-weight parallel edge,
is also valid. The semantic witness tests accept such an alternative.
`tests/RouteTests.java` executes these calls and checks the direction and sum
of every selected edge. It also tests source 2, rejects a wrong-direction
parent and a parent cycle, and reconstructs all 100000 vertices of a deep path.
Actual output is in `tests/results/route_actual.jsonl`.

## 8. Test evidence

The recorded run passed 36 public cases and the public two-batch state-reset
check. The student's suite passed:

| Coverage | Recorded result |
|---|---|
| Fixed edge/boundary cases | 32 passed |
| Seeded random cases | 360 passed |
| Mixed requests, including reverse-order replay in one JVM | 784 passed |
| Alternative valid witnesses | 5 accepted |
| Invalid witnesses | 5 rejected |
| Direct route-helper tests | 9 passed |
| Full-limit/deep/isolate cases | 17 passed |

The base seed is 252904. Small-graph reference answers are independent of the
submitted methods: graph search for DSU prefixes, exhaustive subsets for MSFs,
Boolean transitive closure for SCCs, Kahn for cycles, and Bellman-Ford for
distances. Non-unique outputs are checked semantically with the unchanged
public validator, not by literal edge IDs or label values.

Full-limit cases use n=100000 and m/q=250000, plus four cases with n=100000
and no edges. Their expectations follow from chains, rings, stars and isolates.
They cover both signs of 64-bit totals, a high-degree vertex, repeated unions,
parallel arcs and an unreachable cycle. Full inputs, expectations, actual
outputs and explanations are stored under `tests/`, including compressed
JSON Lines for the large cases. See `tests/README.md` for file mapping.

Passing these checks is evidence of behaviour on the tested inputs, not an
official grade or a claim that the private assessment has been run.

## 9. Kruskal-Prim benchmark

Run `python tests/benchmark.py`. The generator uses Python
`random.Random(252904+n)`. It creates a spanning chain, adds random endpoint
pairs until m=4n, assigns independent integer weights in [-1000000000,1000000000],
and shuffles the edge list. Loops and parallel edges are allowed. Each method
receives exactly the same unchanged `int[][]` for a given size.
The stored graphs and SHA-256 edge digests make the experiment reproducible.

Before timing, both returned forests are checked for acyclicity, spanning,
component count and weight. The independent optimality certificate verifies
that every non-loop input edge is at least as heavy as the maximum edge on its
selected forest path. If this property failed, exchanging that path edge
would reduce cost. If it holds for every edge, no improving exchange exists
and the forest is minimum. Both methods also agree on cost.

**Environment.** OpenJDK 17.0.20, OpenJDK 64-Bit Server VM;
Python 3.12.14; Linux 6.18.55 x86-64/glibc 2.39; AMD EPYC 7763.
The container exposed 9 logical CPUs to the OS and 8 processors to the JVM;
the algorithms use one thread. JVM flags: `-Xms128m -Xmx384m`.
Recorded on 25 October 2026. The test environment invokes the installed
JDK compiler module through a local javac launcher; a normal JDK installation
uses its regular javac executable.

**Timer and boundary.** `System.nanoTime()` measures one complete typed
algorithm call, including local allocation, ID sorting or adjacency construction,
heap/DSU work and construction of the result object. The same boundary applies
to both methods. It excludes compilation, JVM startup, graph generation, JSON
parsing, typed input conversion, correctness certification, serialization and
I/O. Results are consumed and costs checked after timing. No forced garbage
collection occurs.

**Warm-up and samples.** At each size, execute 8 warm-up calls per method.
Then collect 7 calls per method, alternating which method goes first in each
round. Compilation is completed before either phase.

All timings below are milliseconds; each median uses the seven unrounded values.

| n | m | Method | Seven timings (ms) | Median (ms) |
|---:|---:|---|---|---:|
| 1000 | 4000 | Kruskal | 2.483787, 2.197622, 2.357861, 2.237186, 2.296327, 2.156354, 1.967461 | 2.237186 |
| 1000 | 4000 | Prim | 2.294714, 2.257544, 2.228780, 2.187613, 2.368461, 1.972189, 1.787013 | 2.228780 |
| 10000 | 40000 | Kruskal | 13.272703, 13.186802, 13.660278, 13.426421, 13.208544, 13.292992, 13.328888 | 13.292992 |
| 10000 | 40000 | Prim | 15.171646, 16.500773, 14.056801, 16.103831, 15.189820, 14.968475, 14.807865 | 15.171646 |
| 50000 | 200000 | Kruskal | 154.243484, 134.626345, 155.940878, 133.628417, 126.793837, 163.338341, 178.105919 | 154.243484 |
| 50000 | 200000 | Prim | 145.237009, 140.025449, 183.279077, 192.749987, 158.918179, 147.489194, 158.769357 | 158.769357 |

| n | Seed | Certified optimum cost |
|---:|---:|---:|
| 1000 | 253904 | -701431711939 |
| 10000 | 262904 | -7070455311048 |
| 50000 | 302904 | -35287385527911 |

**Observations.** The smallest medians are nearly equal. Kruskal's median is
lower at the two larger sizes in this run. Both methods grow substantially as
the graph grows. This is compatible with their O(n + m log(m+1)) bounds, but
three sizes cannot establish a complexity law. Sorting, adjacency allocation,
heap comparisons, cache behaviour, JIT activity and garbage collection can
affect these implementation-level measurements.

**Limitations.** This is one connected sparse graph per size in a shared virtual
environment. It does not represent dense graphs, all graph families or other
machines. The largest samples show timing variability; all samples are retained.
The medians reduce the influence of individual slow runs but do not remove
system noise. The timing result is separate from the correctness proof and
asymptotic analysis. Exact nanoseconds, seeds, digests and preflight forests are
stored in `tests/results/benchmark.json` and the accompanying gzip files.

## 10. Build, run and test commands

From the repository root, with JDK 17+ and Python 3.12+ installed:

```sh
python tools/run.py --setup
python tools/run.py --check
python tools/run.py --input tests/my_cases.jsonl
python tests/run_tests.py
python tests/benchmark.py
python -m unittest discover -s tools -p "test_*.py"
```

On Windows, `py -3` can replace `python`. The scripts build the selected Java
files using `javac --release 17 -encoding UTF-8`. No network dependency is
required to compile or run the solution. Manual compilation and execution:

```sh
mkdir -p .build/Java
javac --release 17 -encoding UTF-8 -d .build/Java src/Java/*.java
java -Xmx384m -cp .build/Java Main < tests/my_cases.jsonl
```

The provided `Public checks` workflow and the added `Student tests` workflow
run on pushes. A local pass is not a GitHub Actions run; verify the workflow
status on the exact uploaded commit before submitting its URL.

## 11. Sources and AI assistance

- RZhaniya, [Assignment 3 template and specification](https://github.com/RZhaniya/daa-assignment-3-graphs),
  baseline commit `76c1d91daa90ceadcb225f5408d54d4bfcf397f9`.
  The template supplied the contracts, JSON transport, test runner, public
  validator, public cases and original workflow.
- The provided English assignment PDF was used to cross-check the deliverables.
- OpenAI ChatGPT/Codex substantially assisted with implementation, test/oracle
  design, debugging, benchmark tooling and this explanation. Automated tests
  and measurements reported here were actually executed in the development
  environment; they are not claimed to be the student's independent manual
  verification or official grading results.

The linked Moodle syllabus was not accessible from this environment, so its
AI-policy details and deadline were not independently verified. The student
must review that policy, understand the implementation and retain an accurate
assistance disclosure when submitting.
