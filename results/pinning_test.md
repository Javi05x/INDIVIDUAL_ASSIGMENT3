# Pinning test

seq_simd, n=1024, 2 warm-ups, 30 measured repetitions.

- Unaffinitized: median=0.284604 s, IQR=0.036152375 s
- CPU 0 pinned: median=0.25952855 s, IQR=0.01692295 s
- Decision: pin sequential and p=1 runs to CPU 0 (clear reduction means pinned IQR < 80% of unaffinitized IQR).
