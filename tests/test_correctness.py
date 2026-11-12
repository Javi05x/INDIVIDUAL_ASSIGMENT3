import struct, subprocess, tempfile, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "scripts/run_benchmarks.py", "--build-only"], cwd=ROOT, check=True)

def run_test(exe):
    subprocess.run([str(ROOT / "build" / exe), "--test"], check=True, cwd=ROOT)

for executable in ("seq_scalar.exe", "par_scalar.exe", "seq_simd.exe", "par_simd.exe"):
    run_test(executable)

def generated(n, seed=123456789):
    state = seed
    a = np.empty((n, n)); b = np.empty((n, n))
    mask = (1 << 64) - 1
    for i in range(n*n):
        state ^= (state << 13) & mask
        state ^= state >> 7
        state ^= (state << 17) & mask
        a.flat[i] = (state >> 11) / 9007199254740992.0
        state ^= (state << 13) & mask
        state ^= state >> 7
        state ^= (state << 17) & mask
        b.flat[i] = (state >> 11) / 9007199254740992.0
    return a, b

for n in (64, 128, 256):
    a, b = generated(n)
    expected = a @ b
    checksums = []
    with tempfile.TemporaryDirectory() as directory:
        for executable in ("seq_scalar.exe", "par_scalar.exe", "seq_simd.exe", "par_simd.exe"):
            output = Path(directory) / f"{executable}.bin"
            subprocess.run([str(ROOT / "build" / executable), "--n", str(n),
                            "--warmups", "0", "--reps", "1", "--dump", str(output)],
                           check=True, cwd=ROOT, stdout=subprocess.PIPE)
            actual = np.fromfile(output, dtype=np.float64).reshape(n, n)
            np.testing.assert_allclose(actual, expected, atol=1e-9, rtol=1e-9)
            checksums.append(float(actual.sum()))
    assert max(checksums) - min(checksums) == 0.0, f"checksum mismatch at n={n}"

print("numpy comparisons: PASS (n=64, 128, 256; atol=rtol=1e-9)")
print("sequential/parallel checksums: PASS")
