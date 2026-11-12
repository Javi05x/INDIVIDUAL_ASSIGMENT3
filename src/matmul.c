#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#ifdef _WIN32
#include <malloc.h>
#include <windows.h>
#include <psapi.h>
#else
#include <sys/resource.h>
#include <time.h>
#endif
#ifdef _OPENMP
#include <omp.h>
#endif

#ifndef ALIGNMENT
#define ALIGNMENT 64
#endif

static void *aligned_alloc64(size_t bytes) {
#ifdef _WIN32
    return _aligned_malloc(bytes, ALIGNMENT);
#else
    void *p = NULL;
    return posix_memalign(&p, ALIGNMENT, bytes) == 0 ? p : NULL;
#endif
}
static void aligned_free64(void *p) {
#ifdef _WIN32
    _aligned_free(p);
#else
    free(p);
#endif
}

static uint64_t next_random(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13; x ^= x >> 7; x ^= x << 17;
    *state = x;
    return x;
}
static double random_unit(uint64_t *state) {
    return (double)(next_random(state) >> 11) * (1.0 / 9007199254740992.0);
}
static double monotonic_seconds(void) {
#ifdef _WIN32
    static LARGE_INTEGER frequency;
    static int initialised = 0;
    LARGE_INTEGER counter;
    if (!initialised) {
        QueryPerformanceFrequency(&frequency);
        initialised = 1;
    }
    QueryPerformanceCounter(&counter);
    return (double)counter.QuadPart / (double)frequency.QuadPart;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + 1e-9 * ts.tv_nsec;
#endif
}

static void multiply(const double *a, const double *b, double *c, size_t n) {
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (size_t i = 0; i < n; ++i) {
        for (size_t k = 0; k < n; ++k) {
            double aik = a[i * n + k];
            for (size_t j = 0; j < n; ++j)
                c[i * n + j] += aik * b[k * n + j];
        }
    }
}

static double checksum(const double *c, size_t count) {
    double sum = 0.0;
    for (size_t i = 0; i < count; ++i) sum += c[i];
    return sum;
}
static double peak_memory_mb(void) {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS counters;
    if (GetProcessMemoryInfo(GetCurrentProcess(), &counters, sizeof(counters)))
        return (double)counters.PeakWorkingSetSize / (1024.0 * 1024.0);
    return -1.0;
#else
    struct rusage usage;
    if (getrusage(RUSAGE_SELF, &usage) == 0) return usage.ru_maxrss / 1024.0;
    return -1.0;
#endif
}

static int self_test(void) {
    const size_t n = 3;
    double *a = aligned_alloc64(n * n * sizeof(double));
    double *b = aligned_alloc64(n * n * sizeof(double));
    double *c = aligned_alloc64(n * n * sizeof(double));
    if (!a || !b || !c) return 1;
    memset(c, 0, n * n * sizeof(double));
    for (size_t i = 0; i < n; ++i)
        for (size_t j = 0; j < n; ++j) {
            a[i*n+j] = i == j ? 1.0 : 0.0;
            b[i*n+j] = (double)(i*n+j+1);
        }
    multiply(a, b, c, n);
    for (size_t i = 0; i < n*n; ++i) if (c[i] != b[i]) return 2;
    memset(a, 0, n*n*sizeof(double)); memset(c, 0, n*n*sizeof(double));
    multiply(a, b, c, n);
    for (size_t i = 0; i < n*n; ++i) if (c[i] != 0.0) return 3;
    double expected[9] = {30,36,42,66,81,96,102,126,150};
    double left[9] = {1,2,3,4,5,6,7,8,9};
    memcpy(a, left, sizeof(left)); memcpy(b, left, sizeof(left));
    memset(c, 0, sizeof(left)); multiply(a, b, c, n);
    for (size_t i = 0; i < n*n; ++i) if (c[i] != expected[i]) return 4;
    aligned_free64(a); aligned_free64(b); aligned_free64(c);
    puts("self-tests: PASS (identity, zero, hand-computed 3x3)");
    return 0;
}

int main(int argc, char **argv) {
    size_t n = 64, warmups = 2, reps = 1, batch = 1;
    uint64_t seed = 123456789;
    const char *dump = NULL;
    double single_timeout = 0.0;
    int test = 0, resolution = 0;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--test")) test = 1;
        else if (!strcmp(argv[i], "--timer-resolution")) resolution = 1;
        else if (!strcmp(argv[i], "--n") && i+1 < argc) n = (size_t)strtoull(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "--warmups") && i+1 < argc) warmups = (size_t)strtoull(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "--reps") && i+1 < argc) reps = (size_t)strtoull(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "--batch") && i+1 < argc) batch = (size_t)strtoull(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "--single-timeout") && i+1 < argc) single_timeout = strtod(argv[++i], NULL);
        else if (!strcmp(argv[i], "--seed") && i+1 < argc) seed = strtoull(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "--dump") && i+1 < argc) dump = argv[++i];
        else { fprintf(stderr, "unknown argument: %s\n", argv[i]); return 2; }
    }
    if (test) return self_test();
    if (resolution) {
        double minimum = 1.0;
        double previous = monotonic_seconds();
        for (int i = 0; i < 100000; ++i) {
            double current = monotonic_seconds();
            if (current > previous && current - previous < minimum) minimum = current - previous;
            previous = current;
        }
        printf("timer=%s resolution_s=%.12g\n",
#ifdef _WIN32
               "QueryPerformanceCounter",
#else
               "clock_gettime(CLOCK_MONOTONIC)",
#endif
               minimum);
        return 0;
    }
    if (batch == 0) { fprintf(stderr, "batch must be positive\n"); return 2; }
    size_t bytes = n * n * sizeof(double);
    double *a = aligned_alloc64(bytes), *b = aligned_alloc64(bytes);
    double **results = calloc(batch, sizeof(*results));
    if (results) for (size_t r = 0; r < batch; ++r) results[r] = aligned_alloc64(bytes);
    if (!a || !b || !results) { fprintf(stderr, "allocation failed\n"); return 3; }
    uint64_t state = seed;
    for (size_t i = 0; i < n*n; ++i) { a[i] = random_unit(&state); b[i] = random_unit(&state); }
    for (size_t r = 0; r < warmups; ++r)
        for (size_t q = 0; q < batch; ++q) { memset(results[q], 0, bytes); multiply(a, b, results[q], n); }
    for (size_t r = 0; r < reps; ++r) {
        for (size_t q = 0; q < batch; ++q) memset(results[q], 0, bytes);
        double start = monotonic_seconds();
        for (size_t q = 0; q < batch; ++q) multiply(a, b, results[q], n);
        double elapsed = (monotonic_seconds() - start) / (double)batch;
        double result_checksum = 0.0;
        for (size_t q = 0; q < batch; ++q) result_checksum += checksum(results[q], n*n);
        if (single_timeout > 0.0 && batch == 1 && elapsed > single_timeout) {
            printf("status=timeout time_s=%.12g peak_mem_mb=%.6f n=%zu threads=%d limit_s=%.6g\n",
                   elapsed, peak_memory_mb(), n,
#ifdef _OPENMP
                   omp_get_max_threads(),
#else
                   1,
#endif
                   single_timeout);
            fflush(stdout);
            return 124;
        }
        printf("time_s=%.12g checksum=%.17g peak_mem_mb=%.6f n=%zu threads=%d\n",
               elapsed, result_checksum, peak_memory_mb(), n,
#ifdef _OPENMP
               omp_get_max_threads()
#else
               1
#endif
        );
        fflush(stdout);
    }
    if (dump) {
        FILE *f = fopen(dump, "wb");
        if (!f || fwrite(results[0], sizeof(double), n*n, f) != n*n) { fprintf(stderr, "dump failed\n"); return 4; }
        fclose(f);
    }
    aligned_free64(a); aligned_free64(b);
    for (size_t r = 0; r < batch; ++r) aligned_free64(results[r]);
    free(results);
    return 0;
}
