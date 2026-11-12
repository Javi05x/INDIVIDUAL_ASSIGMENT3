# Individual Assignment 3: Parallel Matrix Multiplication and Optional Vectorisation

This project studies dense `float64` matrix multiplication in C11 with OpenMP.
The same `i-k-j` kernel is compiled in scalar and auto-vectorised variants.

The previous run was discarded because the laptop lid was closed while a game
was running. It is preserved as
`results/archive/DISCARDED_run1_lid_closed_gaming.csv` and must not be analysed.
The next coarse-timer run is preserved as
`results/archive/DISCARDED_run2_coarse_timer.csv` and must also not be analysed.
The latest preliminary data is preserved as
`results/archive/run3_preliminary.csv` and must not be analysed; the final
analysis must use one clean session only.
Run 1 teaches that the lid and background games invalidate timings. Run 2
teaches that the MinGW OpenMP timer was too coarse. Run 3 used an incorrect
process-level timeout for the whole repetition set and is also discarded.
This is a measurement-hygiene lesson: keep the laptop plugged in, the lid open
or sleep disabled, and all other heavy programs closed.

## Environment

The measured machine is a Windows 11 laptop with an Intel Core i5-13420H:
4 P-cores with Hyper-Threading and 4 E-cores (8 physical cores, 12 logical
processors). MSYS2 UCRT64 GCC 16.1.0 and Python 3.13 are used. The hybrid
topology means that static scheduling is limited by the slower E-cores.

Install MSYS2 UCRT64 GCC/OpenMP and Python packages `numpy pandas matplotlib
psutil` before running. The benchmark sets `OMP_NUM_THREADS`, `OMP_PROC_BIND=close`
and `OMP_PLACES=cores`. On this MinGW/libgomp Windows installation,
`--affinity-check` reported `Affinity not supported on this configuration` and
displayed an empty `OMP_PLACES`; therefore affinity cannot be claimed as
enforced and is a limitation of this experiment.

## Build

From an MSYS2 UCRT64 terminal:

```bash
python scripts/run_benchmarks.py --build-only
```

The four builds are:

```text
seq_scalar: -std=c11 -O3 -fno-tree-vectorize -fno-tree-slp-vectorize -ffp-contract=off
par_scalar: seq_scalar flags plus -fopenmp
seq_simd:   -std=c11 -O3 -march=native -ffp-contract=off
par_simd:   seq_simd flags plus -fopenmp
```

No BLAS, NumPy, fast-math, or optimised library is used in timed kernels.
GCC 16 spells the requested SLP-disable option `-fno-tree-slp-vectorize`;
this is the compiler's equivalent of `-fno-slp-vectorize`.
All variants use the same monotonic timer: `QueryPerformanceCounter` on
Windows and `clock_gettime(CLOCK_MONOTONIC)` elsewhere. Check its measured
resolution with:

```bash
python scripts/run_benchmarks.py --timer-resolution
```

## Correctness and evidence

```bash
python tests/test_correctness.py
python scripts/run_benchmarks.py --evidence-only
```

The tests cover identity, zero, a hand-computed 3x3 matrix, NumPy comparisons
for n=64, 128, and 256, and sequential/parallel checksum agreement.
The tolerance is `atol=rtol=1e-9`, appropriate for sums of at most 256
float64 products in [0,1).

## Benchmark

Do not run heavy programs concurrently; connect the laptop and select the
High performance power plan. The exact full command is:

```bash
python scripts/run_benchmarks.py --full
```

It tests n=256, 512, 1024, 2048, 4096 with threads 1, 2, 4, 6, 8, 12,
plus 24 only at n=1024. Sequential variants run only with threads=1;
parallel variants run with all listed thread counts. It performs two warm-ups and 30 measured repetitions for n <= 1024, one
warm-up and ten repetitions for n=2048, and one warm-up and three repetitions
at n=4096. At n=4096 it runs `seq_scalar`, `seq_simd`, and `par_simd` at
p=1, 4, 8, 12. `par_scalar` is attempted at p=1 and p=12 only if p=1 fits
the cap. The reduced n=2048 and n=4096 counts limit costly configurations
while retaining repeated measurements whose IQR is reported.
The n=4096 configurations are the largest attempted size; the largest size
meeting the 2 GB budget is reported separately. A run over 120 seconds is
recorded as `timeout` with its limit, never as an invented measurement.

Inputs are generated inside C using a fixed xorshift64 seed. Only the
multiplication is timed; allocation, generation, and zero-initialisation are
outside the timer. A checksum is computed after timing. `raw_measurements.csv`
keeps every measured row and timeout/skipped row. Every executable is run once
untimed at n=8 before measurements to reduce Windows Defender first-launch
effects. Configurations are interleaved by size, variant, and thread count,
with a five-second cooldown between configurations.
For n=256 and n=512, each timed sample is a batch of ten independent
multiplications and `time_s` is the time per multiplication; `batch_size`
records this value. Larger sizes use batch size one.
The per-multiplication cap is 120 seconds. The driver allows
`(warmups + repetitions + 1) * 120` seconds for the whole process, while the
C program stops a configuration when an individual measured multiplication
exceeds 120 seconds and flushes every completed repetition.

The smoke test also compares 30 repetitions of `seq_simd`, n=1024,
unaffinitized versus pinned to logical CPU 0 using
`psutil.Process.cpu_affinity`. If pinning reduces IQR by at least 20%,
sequential and p=1 runs are pinned in the final benchmark; otherwise they
remain unaffinitized. Parallel runs with p>1 remain unaffinitized.
In the latest smoke, unaffinitized median/IQR were 0.8546186/0.546658675 s
and CPU 0 pinned median/IQR were 0.46343405/0.212282175 s, so the final
decision is to pin sequential and p=1 runs to CPU 0. These measurements are
recorded in `results/pinning_test.md`.

The smoke test is:

```bash
python scripts/run_benchmarks.py --smoke
```

It uses n=256 and n=512, with three measured repetitions per configuration,
plus the 30-repetition pinning comparison.
Run it first and use its reported times to estimate the full run. The full
benchmark is intentionally not launched automatically.

## Analysis

After a real full run:

```bash
python scripts/analyze.py
```

This writes `results/summary.csv`, `results/results_tables.md`, and figures,
including `figures/gflops_vs_n.png`. Summary GFLOP/s is
`2*n^3/median_time/1e9`.
The driver also prints and saves `results/sanity_report.md`, flagging slow SIMD,
slow OpenMP p=1, superlinear speedups, high IQR, missing configurations, and
timeouts without deleting flagged data.
The theoretical storage is `3 * 8 * n^2` bytes; measured peak working set and
theoretical storage are different metrics.

## Limitations

- The CPU is hybrid: 4 P-cores with Hyper-Threading and 4 E-cores. Therefore
  p>6 mixes core types and static scheduling is affected by the slower E-cores.
- Sequential and p=1 runs are pinned to logical CPU 0 based on one n=1024
  pinning test. Runs with p>1 are not pinned. The CSV records this in
  `affinity`, and `results/pinning_test.md` records the evidence.
- On MinGW libgomp on Windows, `OMP_PROC_BIND=close` produced
  `Affinity not supported on this configuration` and `OMP_PLACES` was empty.
  The variables are set, but OpenMP affinity cannot be claimed as enforced.
- n=4096 uses only `seq_scalar`, `seq_simd`, `par_simd` p={1,4,8,12}, and
  `par_scalar` p={1,12}, with three repetitions because of the time budget.
- This is one machine and one clean session on Windows 11 with MSYS2 UCRT64
  GCC 16.1.0; thermal state and background activity were not fully controlled.
- The i-k-j kernel is not cache-blocked, so large-n results may be
  memory-bound; this was not tested directly.
- Peak memory uses Windows `GetProcessMemoryInfo` and
  `PeakWorkingSetSize` (or `ru_maxrss` on Unix). The theoretical metric is
  only `3 * 8 * n^2` bytes for the arrays; they are different quantities.

## AI usage disclosure

An AI coding agent (Google Antigravity) was used for code generation and
debugging. The student is responsible for running and validating the tests,
benchmarks, and reported results.
