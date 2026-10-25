import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;

/**
 * Graph algorithms for Assignment 3.
 * All mutable state is allocated per call; the supplied JSON adapter is unchanged.
 */
public final class Algorithms {
    private Algorithms() {
    }

    /** Path compression plus union by size. */
    static final class DisjointSet {
        private final int[] parent;
        private final int[] size;
        int components;
        int largest;

        DisjointSet(int n) {
            parent = new int[n];
            size = new int[n];
            components = n;
            largest = n == 0 ? 0 : 1;
            for (int v = 0; v < n; v++) {
                parent[v] = v;
                size[v] = 1;
            }
        }

        int find(int v) {
            int root = v;
            while (root != parent[root]) {
                root = parent[root];
            }
            while (v != root) {
                int next = parent[v];
                parent[v] = root;
                v = next;
            }
            return root;
        }

        boolean union(int u, int v) {
            int a = find(u);
            int b = find(v);
            if (a == b) {
                return false;
            }
            if (size[a] < size[b]) {
                int temp = a;
                a = b;
                b = temp;
            }
            parent[b] = a;
            size[a] += size[b];
            components--;
            largest = Math.max(largest, size[a]);
            return true;
        }
    }

    static Map<String, Object> dsu(Map<String, Object> input) {
        int n = Input.vertexCount(input);
        int[][] operations = Input.operations(input);
        DisjointSet sets = new DisjointSet(n);
        int[][] states = new int[operations.length][2];
        for (int i = 0; i < operations.length; i++) {
            sets.union(operations[i][0], operations[i][1]);
            states[i][0] = sets.components;
            states[i][1] = sets.largest;
        }
        return Map.of("states", states);
    }

    static Map<String, Object> kruskal(Map<String, Object> input) {
        return kruskal(Input.vertexCount(input), Input.edges(input));
    }

    /** The typed overload also allows benchmarking without JSON parsing. */
    static Map<String, Object> kruskal(int n, int[][] edges) {
        Integer[] ids = new Integer[edges.length];
        for (int i = 0; i < edges.length; i++) {
            ids[i] = i;
        }
        Arrays.sort(ids, Comparator.<Integer>comparingInt(id -> edges[id][2])
                .thenComparingInt(id -> id));
        DisjointSet sets = new DisjointSet(n);
        List<Integer> selected = new ArrayList<>();
        long cost = 0;
        for (int id : ids) {
            int[] edge = edges[id];
            if (sets.union(edge[0], edge[1])) {
                selected.add(id);
                cost += (long) edge[2];
            }
        }
        return Map.of("cost", cost, "edge_ids", selected, "components", sets.components);
    }

    /**
     * Compressed adjacency lists. Neighbours of v occupy [offset[v], offset[v+1]).
     * Each arc keeps its original input edge ID, including in the transpose.
     */
    private static final class Graph {
        final int n;
        final int[] offset;
        final int[] to;
        final int[] edgeId;

        Graph(int n, int[][] edges, boolean undirected, boolean transpose) {
            this.n = n;
            offset = new int[n + 1];
            for (int[] edge : edges) {
                int u = transpose ? edge[1] : edge[0];
                int v = transpose ? edge[0] : edge[1];
                offset[u + 1]++;
                if (undirected) {
                    offset[v + 1]++;
                }
            }
            for (int v = 0; v < n; v++) {
                offset[v + 1] += offset[v];
            }
            to = new int[offset[n]];
            edgeId = new int[offset[n]];
            int[] next = offset.clone();
            for (int id = 0; id < edges.length; id++) {
                int u = transpose ? edges[id][1] : edges[id][0];
                int v = transpose ? edges[id][0] : edges[id][1];
                int at = next[u]++;
                to[at] = v;
                edgeId[at] = id;
                if (undirected) {
                    at = next[v]++;
                    to[at] = u;
                    edgeId[at] = id;
                }
            }
        }
    }

    private record Candidate(int vertex, int edgeId, int weight) {
    }

    static Map<String, Object> prim(Map<String, Object> input) {
        return prim(Input.vertexCount(input), Input.edges(input));
    }

    /** Lazy-heap Prim; a fresh root starts each component, including isolates. */
    static Map<String, Object> prim(int n, int[][] edges) {
        Graph graph = new Graph(n, edges, true, false);
        boolean[] visited = new boolean[n];
        PriorityQueue<Candidate> queue = new PriorityQueue<>(
                Comparator.comparingInt(Candidate::weight).thenComparingInt(Candidate::edgeId));
        List<Integer> selected = new ArrayList<>();
        long cost = 0;
        int components = 0;
        for (int start = 0; start < n; start++) {
            if (visited[start]) {
                continue;
            }
            components++;
            visited[start] = true;
            addFrontier(start, graph, edges, visited, queue);
            while (!queue.isEmpty()) {
                Candidate edge = queue.remove();
                int v = edge.vertex();
                if (visited[v]) {
                    continue; // A cheaper edge has already reached this vertex.
                }
                visited[v] = true;
                selected.add(edge.edgeId());
                cost += (long) edge.weight();
                addFrontier(v, graph, edges, visited, queue);
            }
        }
        return Map.of("cost", cost, "edge_ids", selected, "components", components);
    }

    private static void addFrontier(int u, Graph graph, int[][] edges,
                                    boolean[] visited, PriorityQueue<Candidate> queue) {
        for (int p = graph.offset[u]; p < graph.offset[u + 1]; p++) {
            int v = graph.to[p];
            if (!visited[v]) {
                int id = graph.edgeId[p];
                queue.add(new Candidate(v, id, edges[id][2]));
            }
        }
    }

    /**
     * Iterative DFS with 0=unvisited, 1=active, 2=finished.
     * A cursor remembers each suspended vertex's next arc, so no list is rescanned.
     * Returns increasing finish order, or null if rejectCycles and a back edge exists.
     */
    private static int[] finishOrder(Graph graph, boolean rejectCycles) {
        byte[] state = new byte[graph.n];
        int[] next = graph.offset.clone();
        int[] stack = new int[graph.n];
        int[] finish = new int[graph.n];
        int count = 0;
        for (int start = 0; start < graph.n; start++) {
            if (state[start] != 0) {
                continue;
            }
            int depth = 0;
            stack[depth++] = start;
            state[start] = 1;
            while (depth > 0) {
                int u = stack[depth - 1];
                if (next[u] == graph.offset[u + 1]) {
                    depth--;
                    state[u] = 2;
                    finish[count++] = u;
                    continue;
                }
                int v = graph.to[next[u]++];
                if (state[v] == 0) {
                    state[v] = 1;
                    stack[depth++] = v;
                } else if (rejectCycles && state[v] == 1) {
                    return null;
                }
            }
        }
        return finish;
    }

    static Map<String, Object> scc(Map<String, Object> input) {
        int n = Input.vertexCount(input);
        int[][] edges = Input.edges(input);
        Graph graph = new Graph(n, edges, false, false);
        int[] finish = finishOrder(graph, false);
        Graph transpose = new Graph(n, edges, false, true);
        int[] component = new int[n];
        Arrays.fill(component, -1);
        int[] stack = new int[n];
        int label = 0;
        for (int i = n - 1; i >= 0; i--) {
            int start = finish[i];
            if (component[start] != -1) {
                continue;
            }
            int depth = 0;
            stack[depth++] = start;
            component[start] = label;
            while (depth > 0) {
                int u = stack[--depth];
                for (int p = transpose.offset[u]; p < transpose.offset[u + 1]; p++) {
                    int v = transpose.to[p];
                    if (component[v] == -1) {
                        component[v] = label; // Mark on push to avoid duplicate stack entries.
                        stack[depth++] = v;
                    }
                }
            }
            label++;
        }
        Set<Long> seen = new HashSet<>();
        List<int[]> condensation = new ArrayList<>();
        for (int[] edge : edges) {
            int a = component[edge[0]];
            int b = component[edge[1]];
            long pair = ((long) a << 32) | (b & 0xffffffffL);
            if (a != b && seen.add(pair)) {
                condensation.add(new int[]{a, b});
            }
        }
        return Map.of("component", component, "condensation", condensation);
    }

    private static int[] topologicalOrder(Graph graph) {
        int[] order = finishOrder(graph, true);
        if (order != null) {
            for (int left = 0, right = order.length - 1; left < right; left++, right--) {
                int temp = order[left];
                order[left] = order[right];
                order[right] = temp;
            }
        }
        return order;
    }

    static Map<String, Object> topo(Map<String, Object> input) {
        Graph graph = new Graph(Input.vertexCount(input), Input.edges(input), false, false);
        int[] order = topologicalOrder(graph);
        return Map.of("acyclic", order != null, "order", order == null ? new int[0] : order);
    }

    static Map<String, Object> dag(Map<String, Object> input) {
        int n = Input.vertexCount(input);
        int source = Input.source(input);
        int[][] edges = Input.edges(input);
        Graph graph = new Graph(n, edges, false, false);
        int[] order = topologicalOrder(graph);
        if (order == null) {
            return Map.of("acyclic", false, "distance", new Long[0], "parent_edge", new int[0]);
        }
        Long[] distance = new Long[n];
        int[] parentEdge = new int[n];
        Arrays.fill(parentEdge, -1);
        distance[source] = 0L;
        for (int u : order) {
            if (distance[u] == null) {
                continue;
            }
            for (int p = graph.offset[u]; p < graph.offset[u + 1]; p++) {
                int v = graph.to[p];
                int id = graph.edgeId[p];
                long candidate = distance[u] + (long) edges[id][2];
                if (distance[v] == null || candidate < distance[v]) {
                    distance[v] = candidate;
                    parentEdge[v] = id;
                }
            }
        }
        return Map.of("acyclic", true, "distance", distance, "parent_edge", parentEdge);
    }

    /**
     * Reconstruct a route from a successful DAG result. Returns [] if unreachable
     * and [source] for the source. Parent IDs must belong to the supplied edges.
     * Invalid witnesses throw IllegalArgumentException instead of looping forever.
     * Time and auxiliary/output space: O(L) for a route with L vertices.
     */
    public static List<Integer> reconstructRoute(int source, int target,
                                                 int[][] edges, int[] parentEdge) {
        if (source < 0 || source >= parentEdge.length
                || target < 0 || target >= parentEdge.length) {
            throw new IllegalArgumentException("Invalid source or target");
        }
        if (target != source && parentEdge[target] == -1) {
            return List.of();
        }
        List<Integer> route = new ArrayList<>();
        int current = target;
        while (current != source) {
            if (route.size() >= parentEdge.length) {
                throw new IllegalArgumentException("Cycle in parent edges");
            }
            route.add(current);
            int id = parentEdge[current];
            if (id < 0 || id >= edges.length || edges[id][1] != current
                    || edges[id][0] < 0 || edges[id][0] >= parentEdge.length) {
                throw new IllegalArgumentException("Invalid incoming parent edge");
            }
            current = edges[id][0];
        }
        route.add(source);
        Collections.reverse(route);
        return route;
    }
}
