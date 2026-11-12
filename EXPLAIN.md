# Design explanation

## Algorithm and variants

The program multiplies two dense row-major n by n matrices of `double`.
Matrices are one-dimensional, aligned to 64 bytes, and generated inside C
with a fixed xorshift64 seed. The kernel uses loop order `i-k-j`:

```text
for each row i
  for each k
    for each column j
      C[i,j] += A[i,k] * B[k,j]
```

The j loop accesses a contiguous row of B and C, so it is the natural loop
for auto-vectorisation. The parallel builds add only
`parallel for schedule(static)` to the i loop. Each thread owns different
rows of C, so there is no race.

The four executables isolate two effects. `seq_scalar` disables GCC
vectorisation and OpenMP. `par_scalar` adds OpenMP. `seq_simd` enables
`-march=native` auto-vectorisation without OpenMP. `par_simd` combines both.
All builds use `-O3`, `-ffp-contract=off`, and no BLAS, NumPy, fast-math, or
library threading in the timed kernel.

## Timing and protocol

The timer is `QueryPerformanceCounter` on Windows and
`clock_gettime(CLOCK_MONOTONIC)` elsewhere. It includes only multiplication;
allocation, generation, clearing C, and checksum calculation are outside it.
Short n=256 and n=512 samples execute ten multiplications per batch and report
the average time per multiplication. The CSV stores `batch_size`.

The final session uses two warm-ups and 30 repetitions through n=1024,
one warm-up and 10 repetitions at n=2048, and one warm-up and three
repetitions at n=4096. A 120-second limit applies to each multiplication.
The process allowance is larger so it can finish all repetitions. Every
output line is flushed immediately. Sequential and p=1 processes are pinned
to CPU 0 after the pinning test; p>1 processes are not pinned.

## Correctness and metrics

Tests cover identity, zero, a hand-computed 3x3 product, NumPy reference
results for n=64, 128, and 256 with `atol=rtol=1e-9`, and checksums for all
variants. The fixed i-k-j summation order makes sequential and parallel
results bit-identical in the tested checks.

For each configuration, the reported time is the median and variability is
the IQR. Same-level speedup is `seq_scalar/Tp` for scalar or
`seq_simd/Tp` for SIMD. Combined speedup always uses `seq_scalar`.
Efficiency is speedup divided by p. GFLOP/s is `2*n^3/median_time/1e9`.
Peak working set is measured separately from theoretical array storage.

## Evidence

GCC vectorisation reports and `objdump` disassemblies are in
`results/vectorisation_evidence/`. The enabled builds report 32-byte
vectorised loops and contain SIMD instructions such as `vmulpd` and `vaddpd`;
the scalar-disabled disassemblies provide the comparison.
