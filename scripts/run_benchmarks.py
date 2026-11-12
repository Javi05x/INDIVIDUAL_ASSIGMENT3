import argparse
import csv
import os
import re
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
import psutil

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "matmul.c"
BUILD = ROOT / "build"
RESULTS = ROOT / "results"
SEED = 123456789
TIMEOUT_S = 120
MEMORY_BUDGET_MB = 2048
COOLDOWN_S = 5
VARIANTS = {
    "seq_scalar": ["-O3", "-fno-tree-vectorize", "-fno-tree-slp-vectorize"],
    "par_scalar": ["-O3", "-fno-tree-vectorize", "-fno-tree-slp-vectorize", "-fopenmp"],
    "seq_simd": ["-O3", "-march=native"],
    "par_simd": ["-O3", "-march=native", "-fopenmp"],
}
COMMON = ["-std=c11", "-ffp-contract=off"]
LINK = ["-lpsapi"] if os.name == "nt" else []
FIELDS = [
    "variant", "n", "threads", "oversubscription", "batch_size", "repetition", "time_s",
    "peak_mem_mb", "theoretical_mem_mb", "checksum", "status", "status_reason",
    "affinity", "warmup_runs",
    "seed", "dtype", "compiler_flags", "timeout_limit_s",
]


def build():
    BUILD.mkdir(exist_ok=True)
    for name, flags in VARIANTS.items():
        executable = BUILD / f"{name}.exe"
        command = ["gcc", *COMMON, *flags, str(SRC), "-o", str(executable), *LINK]
        print("+", " ".join(command))
        subprocess.run(command, check=True)


def warm_binary(variant):
    env = os.environ.copy()
    env.update({"OMP_NUM_THREADS": "1", "OMP_PROC_BIND": "close", "OMP_PLACES": "cores"})
    subprocess.run(
        [str(BUILD / f"{variant}.exe"), "--n", "8", "--warmups", "0", "--reps", "1"],
        env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def warm_binaries():
    print("Untimed Windows Defender warm-up: executing every binary once at n=8.")
    for variant in VARIANTS:
        warm_binary(variant)


def affinity_check():
    env = os.environ.copy()
    env.update({
        "OMP_NUM_THREADS": "2", "OMP_PROC_BIND": "close",
        "OMP_PLACES": "cores", "OMP_DISPLAY_ENV": "TRUE",
    })
    result = subprocess.run(
        [str(BUILD / "par_scalar.exe"), "--n", "32", "--warmups", "0", "--reps", "1"],
        env=env, text=True, capture_output=True, check=True,
    )
    print(result.stderr or result.stdout)


def parse_measurements(output, variant, n, threads, batch, warmups, affinity):
    theoretical = 3 * 8 * n * n / 1024**2
    pattern = re.compile(
        r"time_s=([0-9.eE+-]+) checksum=([0-9.eE+-]+) "
        r"peak_mem_mb=([0-9.eE+-]+)"
    )
    rows = []
    for repetition, line in enumerate(output.splitlines(), start=1):
        if "status=timeout" in line:
            rows.append(base_row(variant, n, threads, batch, warmups, "timeout",
                                 theoretical, affinity, "single multiplication exceeded 120 s"))
            break
        match = pattern.search(line)
        if match:
            row = base_row(variant, n, threads, batch, warmups, "ok",
                           theoretical, affinity)
            row.update({
                "repetition": repetition,
                "time_s": float(match.group(1)),
                "peak_mem_mb": float(match.group(3)),
                "checksum": float(match.group(2)),
            })
            rows.append(row)
    return rows


def pinning_test():
    results = {}
    for label, cpu in (("unaffinitized", None), ("cpu0", 0)):
        env = os.environ.copy()
        env.update({"OMP_NUM_THREADS": "1", "OMP_PROC_BIND": "false", "OMP_PLACES": ""})
        command = [
            str(BUILD / "seq_simd.exe"), "--n", "1024", "--warmups", "2",
            "--reps", "30", "--batch", "1",
        ]
        process = subprocess.Popen(command, env=env, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if cpu is not None:
            psutil.Process(process.pid).cpu_affinity([cpu])
        stdout, stderr = process.communicate(timeout=31 * TIMEOUT_S)
        if process.returncode:
            raise RuntimeError(stderr)
        values = [float(row["time_s"]) for row in
                  parse_measurements(stdout, "seq_simd", 1024, 1, 1, 2, label)
                  if row["status"] == "ok"]
        iqr = statistics.quantiles(values, n=4)[2] - statistics.quantiles(values, n=4)[0]
        results[label] = (statistics.median(values), iqr)
    pinned, unpinned = results["cpu0"], results["unaffinitized"]
    pin = pinned[1] < 0.8 * unpinned[1]
    report = (
        "# Pinning test\n\n"
        "seq_simd, n=1024, 2 warm-ups, 30 measured repetitions.\n\n"
        f"- Unaffinitized: median={unpinned[0]:.9g} s, IQR={unpinned[1]:.9g} s\n"
        f"- CPU 0 pinned: median={pinned[0]:.9g} s, IQR={pinned[1]:.9g} s\n"
        f"- Decision: {'pin sequential and p=1 runs to CPU 0' if pin else 'do not pin'} "
        "(clear reduction means pinned IQR < 80% of unaffinitized IQR).\n"
    )
    (RESULTS / "pinning_test.md").write_text(report, encoding="utf-8")
    print(report)
    return pin


def base_row(variant, n, threads, batch, warmups, status, theoretical,
             affinity="unaffinitized", reason=""):
    return {
        "variant": variant, "n": n, "threads": threads,
        "oversubscription": "yes" if threads > 12 else "no",
        "batch_size": batch,
        "repetition": "", "time_s": "", "peak_mem_mb": "",
        "theoretical_mem_mb": theoretical, "checksum": "", "status": status,
        "status_reason": reason, "affinity": affinity,
        "warmup_runs": warmups, "seed": SEED, "dtype": "float64",
        "compiler_flags": " ".join(COMMON + VARIANTS[variant]),
        "timeout_limit_s": TIMEOUT_S,
    }


def run_one(variant, n, threads, warmups, reps, batch, affinity="unaffinitized"):
    theoretical = 3 * 8 * n * n / 1024**2
    if theoretical > MEMORY_BUDGET_MB:
        return [base_row(variant, n, threads, batch, warmups, "skipped", theoretical,
                         affinity, "theoretical memory exceeds 2 GB budget")]
    env = os.environ.copy()
    env.update({
        "OMP_NUM_THREADS": str(threads),
        "OMP_PROC_BIND": "close",
        "OMP_PLACES": "cores",
    })
    command = [
        str(BUILD / f"{variant}.exe"), "--n", str(n),
        "--warmups", str(warmups), "--reps", str(reps), "--batch", str(batch),
    ]
    process_timeout = (warmups + reps + 1) * TIMEOUT_S
    process = subprocess.Popen(command, env=env, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if affinity == "cpu0":
        psutil.Process(process.pid).cpu_affinity([0])
    try:
        stdout, stderr = process.communicate(timeout=process_timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        print(f"{variant} n={n} threads={threads}: PROCESS TIMEOUT")
        rows = parse_measurements(stdout or "", variant, n, threads, batch, warmups, affinity)
        rows.append(base_row(
            variant, n, threads, batch, warmups, "timeout", theoretical, affinity,
            "process timeout; per-multiplication cap was not exceeded",
        ))
        return rows
    if process.returncode not in (0, 124):
        raise RuntimeError(stderr)
    rows = []
    pattern = re.compile(
        r"time_s=([0-9.eE+-]+) checksum=([0-9.eE+-]+) "
        r"peak_mem_mb=([0-9.eE+-]+)"
    )
    rows = parse_measurements(stdout, variant, n, threads, batch, warmups, affinity)
    timed_out = any(row["status"] == "timeout" for row in rows)
    if timed_out:
        print(f"{variant} n={n} threads={threads}: TIMEOUT for one multiplication")
        return rows
    if len(rows) != reps:
        raise RuntimeError(
            f"{variant} n={n} threads={threads} returned {len(rows)} "
            f"measurements, expected {reps}"
        )
    median = statistics.median(float(row["time_s"]) for row in rows)
    print(f"{variant:10} n={n:4} threads={threads:2}: median={median:.6f}s")
    return rows


def expected_configurations(full, smoke):
    sizes = [256, 512] if smoke else [256, 512, 1024, 2048, 4096]
    configurations = []
    for n in sizes:
        for variant in VARIANTS:
            if n == 4096:
                if variant == "par_simd":
                    configurations.extend((variant, n, p) for p in (1, 4, 8, 12))
                elif variant in ("seq_simd", "seq_scalar"):
                    configurations.append((variant, n, 1))
                elif variant == "par_scalar":
                    configurations.extend((variant, n, p) for p in (1, 12))
                continue
            if variant.startswith("seq_"):
                configurations.append((variant, n, 1))
            else:
                parallel = (1, 2) if smoke else (1, 2, 4, 6, 8, 12)
                if full and n == 1024:
                    parallel += (24,)
                configurations.extend((variant, n, p) for p in parallel)
    return configurations


def write_sanity_report(rows, expected):
    groups = defaultdict(list)
    for row in rows:
        if row["status"] == "ok":
            groups[(row["variant"], int(row["n"]), int(row["threads"]))].append(
                float(row["time_s"])
            )
    flags = []
    speedup_details = []
    for key, values in sorted(groups.items()):
        median = statistics.median(values)
        iqr = (statistics.quantiles(values, n=4)[2] -
               statistics.quantiles(values, n=4)[0]) if len(values) > 1 else 0
        if median and iqr > 0.2 * median:
            flags.append(f"IQR > 20% of median: {key}, median={median:.9g}, IQR={iqr:.9g}")

    def median_iqr(values):
        median = statistics.median(values)
        iqr = (statistics.quantiles(values, n=4)[2] -
               statistics.quantiles(values, n=4)[0]) if len(values) > 1 else 0
        return median, iqr

    for n in sorted({key[1] for key in groups}):
        scalar = groups.get(("seq_scalar", n, 1))
        simd = groups.get(("seq_simd", n, 1))
        if scalar and simd and median_iqr(simd)[0] > median_iqr(scalar)[0]:
            flags.append(f"seq_simd slower than seq_scalar at n={n}")
        for parallel, sequential in (("par_scalar", "seq_scalar"), ("par_simd", "seq_simd")):
            p1 = groups.get((parallel, n, 1))
            base = groups.get((sequential, n, 1))
            if p1 and base and median_iqr(p1)[0] > 1.25 * median_iqr(base)[0]:
                flags.append(f"{parallel} p=1 >25% slower than {sequential} at n={n}")
            if p1 and base:
                overhead = median_iqr(p1)[0] / median_iqr(base)[0]
                speedup_details.append(
                    f"OpenMP overhead {parallel} p=1 vs {sequential} at n={n}: "
                    f"speedup={1 / overhead:.6g}, efficiency={1 / overhead:.6g}"
                )
        for variant in ("par_scalar", "par_simd"):
            for (candidate, candidate_n, p), values in groups.items():
                if candidate == variant and candidate_n == n:
                    baseline_name = "seq_simd" if variant == "par_simd" else "seq_scalar"
                    baseline = groups.get((baseline_name, n, 1))
                    scalar_baseline = groups.get(("seq_scalar", n, 1))
                    if baseline and scalar_baseline:
                        speedup = median_iqr(baseline)[0] / median_iqr(values)[0]
                        combined_speedup = median_iqr(scalar_baseline)[0] / median_iqr(values)[0]
                        uncertainty = speedup * (
                            median_iqr(baseline)[1] / median_iqr(baseline)[0] +
                            median_iqr(values)[1] / median_iqr(values)[0]
                        )
                        speedup_details.append(
                            f"{variant} n={n} p={p}: same-level baseline={baseline_name}, "
                            f"speedup={speedup:.6g}, efficiency={speedup / p:.6g}; "
                            f"combined baseline=seq_scalar, speedup={combined_speedup:.6g}"
                        )
                        if speedup / p > 1.05:
                            flags.append(
                                f"Efficiency > 1.05: {variant}, n={n}, p={p}; "
                                f"efficiency={speedup / p:.6g}, baseline IQR="
                                f"{median_iqr(baseline)[1]:.6g}"
                            )
                        if speedup > p and speedup - p > uncertainty:
                            flags.append(
                                f"Possible superlinear speedup: {variant}, n={n}, p={p}; "
                                f"baseline={baseline_name}, speedup={speedup:.6g}, "
                                f"uncertainty={uncertainty:.6g}"
                            )
                        elif speedup > p:
                            flags.append(
                                f"Within noise (not superlinear): {variant}, n={n}, p={p}; "
                                f"baseline={baseline_name}, speedup={speedup:.6g}, "
                                f"uncertainty={uncertainty:.6g}"
                            )

    actual = {(row["variant"], int(row["n"]), int(row["threads"])) for row in rows}
    for configuration in expected:
        if configuration not in actual:
            flags.append(f"Missing configuration: {configuration}")
    for row in rows:
        if row["status"] == "timeout":
            flags.append(f"Timeout configuration: {(row['variant'], row['n'], row['threads'])}")
    report = "# Sanity report\n\n"
    report += (
        "Flags are warnings; no data was removed. Same-level speedups use "
        "seq_scalar for par_scalar and seq_simd for par_simd. Combined speedups "
        "always use seq_scalar. Superlinear tests use only same-level speedups; "
        "the threshold is p plus the sum of relative baseline and candidate IQRs.\n\n"
    )
    report += "## Speedups and p=1 overhead\n\n"
    report += "\n".join(f"- {detail}" for detail in speedup_details) or "- No comparable configurations.\n"
    report += "\n\n## Flags\n\n"
    report += "\n".join(f"- {flag}" for flag in flags) if flags else "- No flags.\n"
    (RESULTS / "sanity_report.md").write_text(report + "\n", encoding="utf-8")
    print("\n" + report)


def write_csv(rows):
    RESULTS.mkdir(exist_ok=True)
    with (RESULTS / "raw_measurements.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--evidence-only", action="store_true")
    parser.add_argument("--affinity-check", action="store_true")
    parser.add_argument("--timer-resolution", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=10)
    args = parser.parse_args()
    build()
    if args.build_only:
        return
    if args.affinity_check:
        affinity_check()
        return
    if args.timer_resolution:
        result = subprocess.run(
            [str(BUILD / "seq_scalar.exe"), "--timer-resolution"],
            text=True, capture_output=True, check=True,
        )
        print(result.stdout.strip())
        return
    if args.evidence_only:
        evidence = RESULTS / "vectorisation_evidence"
        evidence.mkdir(parents=True, exist_ok=True)
        for name in VARIANTS:
            flags = COMMON + VARIANTS[name] + [
                f"-fopt-info-vec-all={evidence / (name + '.vec-all.txt')}"
            ]
            subprocess.run(
                ["gcc", *flags, str(SRC), "-o", str(BUILD / f"{name}.exe"), *LINK],
                check=True,
            )
            with (evidence / f"{name}.objdump.txt").open("w") as output:
                subprocess.run(
                    ["objdump", "-d", str(BUILD / f"{name}.exe")],
                    stdout=output, check=True,
                )
        return
    if not (args.smoke or args.full):
        parser.error("choose --build-only, --evidence-only, --affinity-check, --timer-resolution, --smoke, or --full")

    print(
        "\nBenchmark reminder: plug in the laptop, select High performance, "
        "keep the lid open or disable sleep, and close other programs."
    )
    print(f"Starting in {args.wait_seconds} seconds; use Ctrl+C to cancel.")
    time.sleep(args.wait_seconds)
    warm_binaries()
    smoke = args.smoke
    pin_sequential = pinning_test()
    rows = []
    configurations = expected_configurations(args.full, smoke)
    if smoke:
        smoke_reps = 3
    else:
        smoke_reps = 30
    par_scalar_4096_p1_timeout = False
    for index, (variant, n, threads) in enumerate(configurations):
        warmups, reps = (2, smoke_reps)
        if n == 2048:
            warmups, reps = (1, 10)
        if n == 4096:
            warmups, reps = (1, 3)
        batch = 10 if n <= 512 else 1
        if args.full and n == 4096 and variant == "par_scalar" and threads == 12 and par_scalar_4096_p1_timeout:
            rows.append(base_row(
                variant, n, threads, batch, warmups, "skipped",
                3 * 8 * n * n / 1024**2, "unaffinitized",
                "p=1 exceeded the per-multiplication cap",
            ))
            continue
        affinity = "cpu0" if pin_sequential and (variant.startswith("seq_") or threads == 1) else "unaffinitized"
        result = run_one(variant, n, threads, warmups, reps, batch, affinity)
        rows.extend(result)
        if args.full and n == 4096 and variant == "par_scalar" and threads == 1:
            par_scalar_4096_p1_timeout = any(row["status"] == "timeout" for row in result)
        if index + 1 < len(configurations):
            time.sleep(COOLDOWN_S)
    write_csv(rows)
    write_sanity_report(rows, configurations)
    print(f"Wrote {len(rows)} rows to {RESULTS / 'raw_measurements.csv'}")


if __name__ == "__main__":
    main()
