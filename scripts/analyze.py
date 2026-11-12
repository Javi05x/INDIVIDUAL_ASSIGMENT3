import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
RAW = RESULTS / "raw_measurements.csv"


def median_iqr(values):
    median = statistics.median(values)
    iqr = (statistics.quantiles(values, n=4)[2] -
           statistics.quantiles(values, n=4)[0]) if len(values) > 1 else 0.0
    return median, iqr


raw = list(csv.DictReader(RAW.open(encoding="utf-8")))
groups = defaultdict(list)
for row in raw:
    if row["status"] == "ok":
        key = (row["variant"], int(row["n"]), int(row["threads"]))
        groups[key].append(row)

medians = {}
for key, rows in groups.items():
    times = [float(row["time_s"]) for row in rows]
    medians[key] = (*median_iqr(times), len(times))


def baseline_name(variant):
    return "seq_simd" if "simd" in variant else "seq_scalar"


summary = []
for (variant, n, threads), (median, iqr, repetitions) in sorted(medians.items()):
    same = medians.get((baseline_name(variant), n, 1))
    scalar = medians.get(("seq_scalar", n, 1))
    same_speedup = same[0] / median if same and variant.startswith("par_") else ""
    combined_speedup = scalar[0] / median if scalar and variant != "seq_scalar" else ""
    same_efficiency = same_speedup / threads if same_speedup != "" else ""
    combined_efficiency = combined_speedup / threads if combined_speedup != "" else ""
    summary.append({
        "variant": variant,
        "n": n,
        "threads": threads,
        "median_s": median,
        "iqr_s": iqr,
        "repetitions": repetitions,
        "speedup_same_level": same_speedup,
        "efficiency_same_level": same_efficiency,
        "speedup_combined_seq_scalar": combined_speedup,
        "efficiency_combined_seq_scalar": combined_efficiency,
        "gflops": 2 * n**3 / median / 1e9,
        "superlinear_same_level": bool(same_speedup != "" and same_speedup > threads),
    })


def row_for(variant, n, threads):
    return next((row for row in summary if row["variant"] == variant and
                 row["n"] == n and row["threads"] == threads), None)


def error_for(row, baseline=None):
    relative = row["iqr_s"] / row["median_s"] if row["median_s"] else 0
    if baseline:
        relative += baseline["iqr_s"] / baseline["median_s"]
    return row["median_s"] * relative


FIGURES.mkdir(exist_ok=True)

# Time versus n, with a readable subset of parallel thread counts.
plt.figure()
for variant in ("seq_scalar", "seq_simd", "par_scalar", "par_simd"):
    for threads in (1, 4, 12):
        if not any(r["variant"] == variant and r["threads"] == threads for r in summary):
            continue
        points = [r for r in summary if r["variant"] == variant and r["threads"] == threads]
        if not points:
            continue
        label = f"{variant}, p={threads}"
        plt.errorbar([r["n"] for r in points], [r["median_s"] for r in points],
                     yerr=[r["iqr_s"] for r in points], marker="o", capsize=3, label=label)
plt.xscale("log"); plt.yscale("log")
plt.xlabel("Matrix size n"); plt.ylabel("Time per multiplication (s)")
plt.title("Time versus matrix size (error bars = IQR; repetitions vary by n)")
plt.legend(fontsize="small", ncol=2); plt.grid(True, which="both", alpha=0.3)
plt.savefig(FIGURES / "time_vs_n.png", dpi=150, bbox_inches="tight")
plt.savefig(FIGURES / "time_vs_n.pdf", bbox_inches="tight"); plt.close()

# Speedup and efficiency by n.
for metric, ylabel, filename in (
    ("speedup_same_level", "Speedup", "speedup_vs_threads.png"),
    ("efficiency_same_level", "Efficiency", "efficiency_vs_threads.png"),
):
    sizes = sorted({r["n"] for r in summary})
    fig, axes = plt.subplots(2, 3, figsize=(10, 7), sharey=True)
    axes = axes.ravel()
    for axis, n in zip(axes, sizes):
        for variant in ("par_scalar", "par_simd"):
            points = [r for r in summary if r["variant"] == variant and r["n"] == n]
            if not points:
                continue
            errors = []
            for point in points:
                base = row_for(baseline_name(variant), n, 1)
                errors.append(error_for(point, base) / base["median_s"]
                              if metric == "speedup_same_level" else
                              error_for(point, base) / base["median_s"] / point["threads"])
            axis.errorbar([r["threads"] for r in points], [r[metric] for r in points],
                          yerr=errors, marker="o", capsize=3, label=variant)
        if metric == "speedup_same_level":
            axis.plot([1, 24], [1, 24], "k--", label="ideal")
        axis.axvline(8, color="gray", linestyle=":", label="physical=8")
        axis.axvline(12, color="black", linestyle="-.", label="logical=12")
        axis.set_title(f"n={n}")
        axis.set_xlabel("Threads p")
        axis.grid(True, alpha=0.3)
    for axis in axes[len(sizes):]:
        axis.set_visible(False)
    axes[0].set_ylabel(ylabel)
    axes[len(sizes) - 1].legend(fontsize="small")
    fig.suptitle(f"{ylabel} versus threads (same-level baseline; IQR; repetitions by n)")
    fig.tight_layout()
    fig.savefig(FIGURES / filename, dpi=150, bbox_inches="tight")
    fig.savefig(FIGURES / filename.replace(".png", ".pdf"), bbox_inches="tight"); plt.close(fig)

# GFLOP/s.
plt.figure()
for variant in ("seq_scalar", "seq_simd"):
    points = [r for r in summary if r["variant"] == variant and r["threads"] == 1]
    plt.errorbar([r["n"] for r in points], [r["gflops"] for r in points],
                 yerr=[r["gflops"] * r["iqr_s"] / r["median_s"] for r in points],
                 marker="o", capsize=3, label=variant)
plt.xlabel("Matrix size n"); plt.ylabel("GFLOP/s")
plt.title("Sequential throughput (median; error bars = propagated IQR)")
plt.legend(); plt.grid(True, alpha=0.3)
plt.savefig(FIGURES / "gflops_vs_n.png", dpi=150, bbox_inches="tight")
plt.savefig(FIGURES / "gflops_vs_n.pdf", bbox_inches="tight"); plt.close()

# 2x2 vectorisation view.
fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
for axis, n in zip(axes, (2048, 4096)):
    points = []
    labels = []
    for label, variant, threads in (
        ("scalar, p=1", "seq_scalar", 1),
        ("SIMD, p=1", "seq_simd", 1),
        ("scalar, p=12", "par_scalar", 12),
        ("SIMD, p=12", "par_simd", 12),
    ):
        row = row_for(variant, n, threads)
        if row:
            points.append(row); labels.append(label)
    axis.bar(labels, [r["median_s"] for r in points],
             yerr=[r["iqr_s"] for r in points], capsize=4)
    axis.set_title(f"n={n}"); axis.set_ylabel("Time per multiplication (s)")
    axis.tick_params(axis="x", rotation=35); axis.grid(axis="y", alpha=0.3)
fig.suptitle("Scalar/SIMD and one/many threads (median; IQR; repetitions by n)")
fig.tight_layout()
fig.savefig(FIGURES / "vectorisation_2x2.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES / "vectorisation_2x2.pdf", bbox_inches="tight"); plt.close(fig)

# OpenMP p=1 overhead.
fig, axis = plt.subplots(figsize=(8, 5))
for variant, base in (("par_scalar", "seq_scalar"), ("par_simd", "seq_simd")):
    points = [r for r in summary if r["variant"] == variant and r["threads"] == 1]
    axis.errorbar([r["n"] for r in points], [r["median_s"] for r in points],
                  yerr=[r["iqr_s"] for r in points], marker="o", capsize=3, label=variant)
    bases = [row_for(base, r["n"], 1)["median_s"] for r in points]
    axis.plot([r["n"] for r in points], bases, "--", label=f"{base}, no OpenMP")
axis.set_xlabel("Matrix size n"); axis.set_ylabel("Time per multiplication (s)")
axis.set_title("OpenMP p=1 overhead (median; IQR; repetitions by n)")
axis.legend(); axis.grid(True, alpha=0.3)
fig.savefig(FIGURES / "openmp_overhead.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES / "openmp_overhead.pdf", bbox_inches="tight"); plt.close(fig)

# Peak memory.
fig, axis = plt.subplots(figsize=(8, 5))
for variant in ("seq_scalar", "par_simd"):
    points = [r for r in summary if r["variant"] == variant and r["threads"] == 1]
    memories = []
    errors = []
    for point in points:
        source = [float(x["peak_mem_mb"]) for x in groups[(variant, point["n"], 1)]]
        median, iqr = median_iqr(source); memories.append(median); errors.append(iqr)
    axis.errorbar([r["n"] for r in points], memories, yerr=errors,
                  marker="o", capsize=3, label=f"{variant} measured")
theoretical = [3 * 8 * n * n / 1024**2 for n in sorted({r["n"] for r in summary})]
axis.plot(sorted({r["n"] for r in summary}), theoretical, "k--", label="theoretical arrays")
axis.set_xlabel("Matrix size n"); axis.set_ylabel("Memory (MiB)")
axis.set_title("Peak working set versus theoretical array storage (median; IQR)")
axis.legend(); axis.grid(True, alpha=0.3)
fig.savefig(FIGURES / "peak_memory_vs_n.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES / "peak_memory_vs_n.pdf", bbox_inches="tight"); plt.close(fig)

# Oversubscription at n=1024.
fig, axis = plt.subplots(figsize=(6, 4))
for variant in ("par_scalar", "par_simd"):
    base = row_for(baseline_name(variant), 1024, 1)
    p12 = row_for(variant, 1024, 12); p24 = row_for(variant, 1024, 24)
    if p12 and p24:
        axis.bar(f"{variant}\np=12 vs p=24",
                 p12["median_s"] / p24["median_s"],
                 yerr=error_for(p12, base) / p24["median_s"], capsize=4)
axis.axhline(1, color="black", linestyle="--")
axis.set_ylabel("Relative speedup (T12 / T24)")
axis.set_title("Oversubscription at n=1024 (IQR; 30 repetitions)")
axis.grid(axis="y", alpha=0.3)
fig.savefig(FIGURES / "oversubscription_1024.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES / "oversubscription_1024.pdf", bbox_inches="tight"); plt.close(fig)

fields = list(summary[0]) if summary else ["variant"]
with (RESULTS / "summary.csv").open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader(); writer.writerows(summary)

table = "# Results tables\n\nGenerated only from `results/raw_measurements.csv`.\n\n"
table += "| " + " | ".join(fields) + " |\n"
table += "| " + " | ".join("---" for _ in fields) + " |\n"
for row in summary:
    table += "| " + " | ".join(str(row[field]) for field in fields) + " |\n"
(RESULTS / "results_tables.md").write_text(table, encoding="utf-8")
print(f"Analysed {len(raw)} final-session rows into {len(summary)} configurations.")
