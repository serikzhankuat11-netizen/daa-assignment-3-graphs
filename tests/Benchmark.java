import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

/** Algorithm-only timing harness. Compilation, parsing and graph generation are excluded. */
public final class Benchmark {
    private static volatile long sink;

    private static Map<String, Object> solve(boolean prim, int n, int[][] edges) {
        return prim ? Algorithms.prim(n, edges) : Algorithms.kruskal(n, edges);
    }

    private static long timed(boolean prim, int n, int[][] edges, long expectedCost) {
        long start = System.nanoTime();
        Map<String, Object> result = solve(prim, n, edges);
        long elapsed = System.nanoTime() - start;
        long cost = ((Number) result.get("cost")).longValue();
        if (cost != expectedCost || ((Number) result.get("components")).intValue() != 1) {
            throw new AssertionError("Incorrect benchmark result");
        }
        sink ^= cost + ((java.util.List<?>) result.get("edge_ids")).size();
        return elapsed;
    }

    public static void main(String[] args) throws Exception {
        boolean verify = args.length == 1 && args[0].equals("--verify");
        BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String line;
        while ((line = input.readLine()) != null) {
            Map<String, Object> request = Json.parseRequest(line);
            int n = Input.vertexCount(request);
            int[][] edges = Input.edges(request);
            if (verify) {
                System.out.println(Json.write(Map.of("n", n, "m", edges.length,
                        "kruskal", Algorithms.kruskal(n, edges), "prim", Algorithms.prim(n, edges))));
                continue;
            }
            long expectedCost = ((Number) request.get("expected_cost")).longValue();
            // Same graph and symmetric warm-up. Alternate which method goes first.
            for (int round = 0; round < 8; round++) {
                timed(round % 2 == 1, n, edges, expectedCost);
                timed(round % 2 == 0, n, edges, expectedCost);
            }
            long[] kruskal = new long[7];
            long[] prim = new long[7];
            for (int round = 0; round < 7; round++) {
                if (round % 2 == 0) {
                    kruskal[round] = timed(false, n, edges, expectedCost);
                    prim[round] = timed(true, n, edges, expectedCost);
                } else {
                    prim[round] = timed(true, n, edges, expectedCost);
                    kruskal[round] = timed(false, n, edges, expectedCost);
                }
            }
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("n", n);
            row.put("m", edges.length);
            row.put("cost", expectedCost);
            row.put("kruskal_ns", kruskal);
            row.put("prim_ns", prim);
            row.put("java_version", System.getProperty("java.version"));
            row.put("java_vm", System.getProperty("java.vm.name"));
            row.put("max_heap_bytes", Runtime.getRuntime().maxMemory());
            row.put("available_processors", Runtime.getRuntime().availableProcessors());
            System.out.println(Json.write(row));
        }
    }
}
