"""Generate identical seeded graphs, certify MSFs, then run algorithm-only timings."""
import gzip
import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from oracles import certify_msf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from run import build

OUTPUT = ROOT / "tests" / "results"
SEED = 252904


def graph(n, m):
    rng = random.Random(SEED + n)
    edges = [[v - 1, v, rng.randint(-1000000000, 1000000000)] for v in range(1, n)]
    edges.extend([rng.randrange(n), rng.randrange(n), rng.randint(-1000000000, 1000000000)]
                 for _ in range(m - len(edges)))
    rng.shuffle(edges)
    return {"n": n, "edges": edges}


def encode(requests):
    return "".join(json.dumps(x, separators=(",", ":")) + "\n" for x in requests)


def main():
    OUTPUT.mkdir(exist_ok=True)
    build("Java")  # Excluded from timings.
    subprocess.run(["javac", "--release", "17", "-encoding", "UTF-8",
                    "-cp", str(ROOT / ".build/Java"), "-d", str(ROOT / ".build/Java"),
                    str(ROOT / "tests/Benchmark.java")], check=True)
    requests = [graph(n, 4 * n) for n in (1000, 10000, 50000)]
    original = encode(requests)
    with gzip.open(OUTPUT / "benchmark_inputs.jsonl.gz", "wt", encoding="utf-8") as stream:
        stream.write(original)
    command = ["java", "-Xms128m", "-Xmx384m", "-cp", str(ROOT / ".build/Java"), "Benchmark"]
    verification = subprocess.run(command + ["--verify"], input=original, text=True,
                                  capture_output=True, check=True, timeout=60)
    verified = [json.loads(line) for line in verification.stdout.splitlines()]
    assert len(verified) == len(requests)
    with gzip.open(OUTPUT / "benchmark_forests.jsonl.gz", "wt", encoding="utf-8") as stream:
        stream.write(verification.stdout)
    # Independent path-maximum optimality checks BEFORE measuring either method.
    for request, result in zip(requests, verified):
        for task in ("kruskal", "prim"):
            certify_msf(request["n"], request["edges"], result[task])
        assert result["kruskal"]["cost"] == result["prim"]["cost"]
        assert result["kruskal"]["components"] == result["prim"]["components"] == 1
        request["expected_cost"] = result["kruskal"]["cost"]
        print(f"PASS certified both forests: n={request['n']}, m={len(request['edges'])}", flush=True)
    measured = subprocess.run(command, input=encode(requests), text=True,
                              capture_output=True, check=True, timeout=60)
    rows = [json.loads(line) for line in measured.stdout.splitlines()]
    assert len(rows) == 3
    for request, row in zip(requests, rows):
        row["seed"] = SEED + request["n"]
        row["sha256_edges"] = hashlib.sha256(json.dumps(request["edges"],
            separators=(",", ":")).encode()).hexdigest()
        for task in ("kruskal", "prim"):
            row[task + "_ms"] = [t / 1000000 for t in row[task + "_ns"]]
            row[task + "_median_ms"] = statistics.median(row[task + "_ms"])
        print(json.dumps({key: row[key] for key in
              ("n", "m", "kruskal_median_ms", "prim_median_ms")}), flush=True)
    cpu = "unknown"
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        cpu = next((line.split(":", 1)[1].strip() for line in cpuinfo.read_text().splitlines()
                    if line.startswith("model name")), cpu)
    result = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": "python tests/benchmark.py",
        "base_seed": SEED, "generator": "Python random.Random(base_seed+n); weighted chain, random extra edges, shuffle",
        "python": platform.python_version(), "os": platform.platform(), "cpu": cpu,
        "logical_cpus": os.cpu_count(),
        "timer": "System.nanoTime, elapsed nanoseconds",
        "jvm_flags": ["-Xms128m", "-Xmx384m"],
        "warmup": "8 calls per method per size; alternate first method",
        "samples": "7 calls per method per size; alternate first method",
        "included": "Method-local allocation, edge-ID sorting/adjacency creation, algorithm and result object",
        "excluded": "Compilation, JVM startup, input generation, JSON parsing, typed input conversion, validation, serialization and I/O",
        "preflight": "Both forests independently certified by feasibility and path-maximum cycle optimality",
        "graphs": rows}
    (OUTPUT / "benchmark.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS benchmark complete")


if __name__ == "__main__":
    main()
