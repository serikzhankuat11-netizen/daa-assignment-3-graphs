import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Direct helper calls; deliberately separate from the six JSON tasks. */
public final class RouteTests {
    private static void verify(String name, String json, int target, List<Integer> expected) {
        Map<String, Object> request = Json.parseRequest(json);
        Map<String, Object> result = Algorithms.dag(request);
        if (!Boolean.TRUE.equals(result.get("acyclic"))) {
            throw new AssertionError("Expected a DAG");
        }
        int source = Input.source(request);
        int[][] edges = Input.edges(request);
        int[] parent = (int[]) result.get("parent_edge");
        Long[] distance = (Long[]) result.get("distance");
        List<Integer> route = Algorithms.reconstructRoute(source, target, edges, parent);
        if (!route.equals(expected)) {
            throw new AssertionError(name + ": " + route);
        }
        List<Integer> selected = new ArrayList<>();
        long cost = 0;
        for (int i = 1; i < route.size(); i++) {
            int id = parent[route.get(i)];
            if (edges[id][0] != route.get(i - 1) || edges[id][1] != route.get(i)) {
                throw new AssertionError("Wrong direction");
            }
            selected.add(id);
            cost += (long) edges[id][2];
        }
        if (!route.isEmpty() && (distance[target] == null || cost != distance[target])) {
            throw new AssertionError("Wrong route weight");
        }
        if (route.isEmpty() && distance[target] != null) {
            throw new AssertionError("Missing reachable route");
        }
        System.out.println(Json.write(Map.of(
                "case", name, "source", source, "target", target, "route", route,
                "selected_edge_ids", selected, "weight", route.isEmpty() ? "no route" : cost,
                "status", "PASS")));
    }

    private static void reject(String name, int[][] edges, int[] parents) {
        try {
            Algorithms.reconstructRoute(0, 2, edges, parents);
            throw new AssertionError("Accepted invalid parent witness");
        } catch (IllegalArgumentException expected) {
            System.out.println(Json.write(Map.of("case", name, "status", "PASS")));
        }
    }

    public static void main(String[] args) {
        String graph = """
                {"task":"dag","n":5,"source":0,
                 "edges":[[0,1,3],[0,2,8],[1,2,-7],[2,3,4]]}
                """;
        verify("reachable", graph, 3, List.of(0, 1, 2, 3));
        verify("source", graph, 0, List.of(0));
        verify("unreachable", graph, 4, List.of());
        String tied = """
                {"task":"dag","n":5,"source":0,
                 "edges":[[0,1,2],[0,1,2],[0,2,2],[1,3,-1],[2,3,-1]]}
                """;
        verify("tied_parallel", tied, 3, List.of(0, 2, 3));
        verify("parallel_edge", tied, 1, List.of(0, 1));
        String nonzeroSource = """
                {"task":"dag","n":4,"source":2,
                 "edges":[[2,1,-1],[1,0,5],[3,2,8]]}
                """;
        verify("nonzero_source", nonzeroSource, 0, List.of(2, 1, 0));
        reject("wrong_direction_rejected", new int[][]{{0, 1, 1}, {2, 1, 1}},
                new int[]{-1, 0, 1});
        reject("parent_cycle_rejected", new int[][]{{1, 2, 0}, {2, 1, 0}},
                new int[]{-1, 1, 0});

        int n = 100000;
        int[][] edges = new int[n - 1][3];
        int[] parents = new int[n];
        parents[0] = -1;
        for (int v = 1; v < n; v++) {
            edges[v - 1] = new int[]{v - 1, v, -1000000000};
            parents[v] = v - 1;
        }
        List<Integer> route = Algorithms.reconstructRoute(0, n - 1, edges, parents);
        if (route.size() != n) {
            throw new AssertionError("Truncated deep route");
        }
        for (int v = 0; v < n; v++) {
            if (route.get(v) != v) {
                throw new AssertionError("Wrong deep route");
            }
        }
        System.out.println(Json.write(Map.of("case", "deep_route", "vertices", route.size(),
                "first", route.get(0), "last", route.get(n - 1), "status", "PASS")));
    }
}
