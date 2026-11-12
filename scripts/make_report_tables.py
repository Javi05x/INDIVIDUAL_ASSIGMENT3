import csv
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
TABLES = REPORT / "tables"
TABLES.mkdir(exist_ok=True)

raw = list(csv.DictReader((ROOT / "results/raw_measurements.csv").open(encoding="utf-8")))
summary = list(csv.DictReader((ROOT / "results/summary.csv").open(encoding="utf-8")))


def esc(value):
    return str(value).replace("_", r"\_")


def write_table(name, caption, headers, rows):
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\scriptsize",
        r"\caption{" + caption + "}",
        r"\begin{tabular}{@{}" + "l" * len(headers) + r"@{}}",
        r"\toprule",
        " & ".join(esc(h) for h in headers) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(esc(x) for x in row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    (TABLES / name).write_text("\n".join(lines), encoding="utf-8")


def f(value, digits=4):
    return f"{float(value):.{digits}g}"


configs = sorted({(r["variant"], r["n"], r["threads"], r["repetitions"])
                   for r in summary},
                 key=lambda x: (int(x[1]), x[0], int(x[2])))
write_table(
    "configurations.tex",
    "Configurations represented in the final clean session.",
    ["Variant", "$n$", "$p$", "Repetitions"],
    configs,
)

runtime_rows = []
for r in summary:
    if r["threads"] in ("1", "8", "12") and (
        r["variant"].startswith("seq_") or r["n"] != "4096"
    ):
        runtime_rows.append((r["variant"], r["n"], r["threads"],
                             f(r["median_s"]), f(r["iqr_s"]), r["repetitions"]))
write_table(
    "runtime.tex",
    "Representative median runtime per multiplication in seconds; IQR and repetitions are shown. Sequential variants use $p=1$.",
    ["Variant", "$n$", "$p$", "Median (s)", "IQR (s)", "$r$"],
    runtime_rows,
)

speed_rows = []
for r in summary:
    if r["variant"].startswith("par_"):
        speed_rows.append((r["variant"], r["n"], r["threads"],
                           f(r["speedup_same_level"]), f(r["efficiency_same_level"]),
                           f(r["speedup_combined_seq_scalar"])))
write_table(
    "speedup_efficiency.tex",
    "Parallel speedup and efficiency. The same-level baseline is $seq\\_scalar$ for scalar and $seq\\_simd$ for SIMD; the combined baseline is always $seq\\_scalar$.",
    ["Variant", "$n$", "$p$", "$S(p)$", "$E(p)$", "Combined $S$"],
    speed_rows,
)

overhead_rows = []
for r in summary:
    if r["variant"] in ("par_scalar", "par_simd") and r["threads"] == "1":
        overhead_rows.append((r["variant"], r["n"], f(r["speedup_same_level"]),
                              f(r["efficiency_same_level"]), f(r["iqr_s"]),
                              r["repetitions"]))
write_table(
    "overhead.tex",
    "OpenMP $p=1$ overhead relative to the matching sequential baseline.",
    ["Variant", "$n$", "$S(1)$", "$E(1)$", "IQR (s)", "$r$"],
    overhead_rows,
)

vector_rows = []
for r in summary:
    if r["n"] in ("2048", "4096") and r["threads"] in ("1", "12") and (
        r["variant"] in ("seq_scalar", "seq_simd", "par_scalar", "par_simd")
    ):
        vector_rows.append((r["variant"], r["n"], r["threads"],
                            f(r["median_s"]), f(r["iqr_s"]), r["repetitions"]))
write_table(
    "vectorisation.tex",
    "The scalar/SIMD and one/many-thread values used in the 2x2 comparison.",
    ["Variant", "$n$", "$p$", "Median (s)", "IQR (s)", "$r$"],
    vector_rows,
)

gflops_rows = []
for r in summary:
    if r["variant"] in ("seq_scalar", "seq_simd"):
        gflops_rows.append((r["variant"], r["n"], f(r["gflops"]), r["repetitions"]))
write_table(
    "gflops.tex",
    "Sequential throughput calculated as $2n^3/T_{seq}$ in GFLOP/s.",
    ["Variant", "$n$", "GFLOP/s", "$r$"],
    gflops_rows,
)

oversub_rows = []
for variant in ("par_scalar", "par_simd"):
    p12 = next(r for r in summary if r["variant"] == variant and r["n"] == "1024" and r["threads"] == "12")
    p24 = next(r for r in summary if r["variant"] == variant and r["n"] == "1024" and r["threads"] == "24")
    oversub_rows.append((variant, f(float(p12["median_s"]) / float(p24["median_s"])),
                         f(p12["median_s"]), f(p24["median_s"])))
write_table(
    "oversubscription.tex",
    "Comparison of $p=12$ and oversubscribed $p=24$ at $n=1024$; the ratio is $T_{12}/T_{24}$.",
    ["Variant", "$T_{12}/T_{24}$", "$T_{12}$ (s)", "$T_{24}$ (s)"],
    oversub_rows,
)

memory_groups = defaultdict(list)
for r in raw:
    if r["status"] == "ok" and r["variant"] == "seq_scalar" and r["threads"] == "1":
        memory_groups[int(r["n"])].append(float(r["peak_mem_mb"]))
memory_rows = []
for n, values in sorted(memory_groups.items()):
    median = statistics.median(values)
    iqr = statistics.quantiles(values, n=4)[2] - statistics.quantiles(values, n=4)[0]
    theoretical = 3 * 8 * n * n / 1024**2
    memory_rows.append((str(n), f(median), f(iqr), f(theoretical)))
write_table(
    "memory.tex",
    "Measured peak working set and theoretical storage for the sequential scalar process.",
    ["$n$", "Peak median (MiB)", "Peak IQR (MiB)", "Theoretical (MiB)"],
    memory_rows,
)

print(f"Generated {len(list(TABLES.glob('*.tex')))} tables from final CSV outputs.")
