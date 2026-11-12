# Sanity report

Flags are warnings; no data was removed. Same-level speedups use seq_scalar for par_scalar and seq_simd for par_simd. Combined speedups always use seq_scalar. Superlinear tests use only same-level speedups; the threshold is p plus the sum of relative baseline and candidate IQRs.

## Speedups and p=1 overhead

- OpenMP overhead par_scalar p=1 vs seq_scalar at n=256: speedup=0.96631, efficiency=0.96631
- OpenMP overhead par_simd p=1 vs seq_simd at n=256: speedup=1.01432, efficiency=1.01432
- par_scalar n=256 p=1: same-level baseline=seq_scalar, speedup=0.96631, efficiency=0.96631; combined baseline=seq_scalar, speedup=0.96631
- par_scalar n=256 p=2: same-level baseline=seq_scalar, speedup=1.75289, efficiency=0.876447; combined baseline=seq_scalar, speedup=1.75289
- par_scalar n=256 p=4: same-level baseline=seq_scalar, speedup=3.80297, efficiency=0.950743; combined baseline=seq_scalar, speedup=3.80297
- par_scalar n=256 p=6: same-level baseline=seq_scalar, speedup=4.00706, efficiency=0.667844; combined baseline=seq_scalar, speedup=4.00706
- par_scalar n=256 p=8: same-level baseline=seq_scalar, speedup=4.91855, efficiency=0.614818; combined baseline=seq_scalar, speedup=4.91855
- par_scalar n=256 p=12: same-level baseline=seq_scalar, speedup=5.99638, efficiency=0.499698; combined baseline=seq_scalar, speedup=5.99638
- par_simd n=256 p=1: same-level baseline=seq_simd, speedup=1.01432, efficiency=1.01432; combined baseline=seq_scalar, speedup=3.30796
- par_simd n=256 p=2: same-level baseline=seq_simd, speedup=1.93369, efficiency=0.966845; combined baseline=seq_scalar, speedup=6.30629
- par_simd n=256 p=4: same-level baseline=seq_simd, speedup=3.83751, efficiency=0.959379; combined baseline=seq_scalar, speedup=12.5152
- par_simd n=256 p=6: same-level baseline=seq_simd, speedup=3.5388, efficiency=0.5898; combined baseline=seq_scalar, speedup=11.541
- par_simd n=256 p=8: same-level baseline=seq_simd, speedup=3.11814, efficiency=0.389768; combined baseline=seq_scalar, speedup=10.1691
- par_simd n=256 p=12: same-level baseline=seq_simd, speedup=3.49621, efficiency=0.291351; combined baseline=seq_scalar, speedup=11.4021
- OpenMP overhead par_scalar p=1 vs seq_scalar at n=512: speedup=1.00786, efficiency=1.00786
- OpenMP overhead par_simd p=1 vs seq_simd at n=512: speedup=1.00217, efficiency=1.00217
- par_scalar n=512 p=1: same-level baseline=seq_scalar, speedup=1.00786, efficiency=1.00786; combined baseline=seq_scalar, speedup=1.00786
- par_scalar n=512 p=2: same-level baseline=seq_scalar, speedup=1.97792, efficiency=0.98896; combined baseline=seq_scalar, speedup=1.97792
- par_scalar n=512 p=4: same-level baseline=seq_scalar, speedup=4.0546, efficiency=1.01365; combined baseline=seq_scalar, speedup=4.0546
- par_scalar n=512 p=6: same-level baseline=seq_scalar, speedup=4.1776, efficiency=0.696267; combined baseline=seq_scalar, speedup=4.1776
- par_scalar n=512 p=8: same-level baseline=seq_scalar, speedup=5.19817, efficiency=0.649771; combined baseline=seq_scalar, speedup=5.19817
- par_scalar n=512 p=12: same-level baseline=seq_scalar, speedup=6.3882, efficiency=0.53235; combined baseline=seq_scalar, speedup=6.3882
- par_simd n=512 p=1: same-level baseline=seq_simd, speedup=1.00217, efficiency=1.00217; combined baseline=seq_scalar, speedup=2.12946
- par_simd n=512 p=2: same-level baseline=seq_simd, speedup=2.25783, efficiency=1.12891; combined baseline=seq_scalar, speedup=4.79754
- par_simd n=512 p=4: same-level baseline=seq_simd, speedup=4.14298, efficiency=1.03574; combined baseline=seq_scalar, speedup=8.80321
- par_simd n=512 p=6: same-level baseline=seq_simd, speedup=4.90702, efficiency=0.817837; combined baseline=seq_scalar, speedup=10.4267
- par_simd n=512 p=8: same-level baseline=seq_simd, speedup=5.35733, efficiency=0.669667; combined baseline=seq_scalar, speedup=11.3835
- par_simd n=512 p=12: same-level baseline=seq_simd, speedup=6.94144, efficiency=0.578454; combined baseline=seq_scalar, speedup=14.7495
- OpenMP overhead par_scalar p=1 vs seq_scalar at n=1024: speedup=0.995278, efficiency=0.995278
- OpenMP overhead par_simd p=1 vs seq_simd at n=1024: speedup=0.97694, efficiency=0.97694
- par_scalar n=1024 p=1: same-level baseline=seq_scalar, speedup=0.995278, efficiency=0.995278; combined baseline=seq_scalar, speedup=0.995278
- par_scalar n=1024 p=2: same-level baseline=seq_scalar, speedup=1.8681, efficiency=0.93405; combined baseline=seq_scalar, speedup=1.8681
- par_scalar n=1024 p=4: same-level baseline=seq_scalar, speedup=3.45092, efficiency=0.862729; combined baseline=seq_scalar, speedup=3.45092
- par_scalar n=1024 p=6: same-level baseline=seq_scalar, speedup=4.06507, efficiency=0.677511; combined baseline=seq_scalar, speedup=4.06507
- par_scalar n=1024 p=8: same-level baseline=seq_scalar, speedup=4.92629, efficiency=0.615786; combined baseline=seq_scalar, speedup=4.92629
- par_scalar n=1024 p=12: same-level baseline=seq_scalar, speedup=6.68672, efficiency=0.557227; combined baseline=seq_scalar, speedup=6.68672
- par_scalar n=1024 p=24: same-level baseline=seq_scalar, speedup=6.45407, efficiency=0.26892; combined baseline=seq_scalar, speedup=6.45407
- par_simd n=1024 p=1: same-level baseline=seq_simd, speedup=0.97694, efficiency=0.97694; combined baseline=seq_scalar, speedup=1.87023
- par_simd n=1024 p=2: same-level baseline=seq_simd, speedup=2.05564, efficiency=1.02782; combined baseline=seq_scalar, speedup=3.93526
- par_simd n=1024 p=4: same-level baseline=seq_simd, speedup=4.11752, efficiency=1.02938; combined baseline=seq_scalar, speedup=7.88248
- par_simd n=1024 p=6: same-level baseline=seq_simd, speedup=4.26179, efficiency=0.710298; combined baseline=seq_scalar, speedup=8.15867
- par_simd n=1024 p=8: same-level baseline=seq_simd, speedup=5.38362, efficiency=0.672952; combined baseline=seq_scalar, speedup=10.3063
- par_simd n=1024 p=12: same-level baseline=seq_simd, speedup=6.4003, efficiency=0.533358; combined baseline=seq_scalar, speedup=12.2526
- par_simd n=1024 p=24: same-level baseline=seq_simd, speedup=6.46871, efficiency=0.269529; combined baseline=seq_scalar, speedup=12.3835
- OpenMP overhead par_scalar p=1 vs seq_scalar at n=2048: speedup=1.00367, efficiency=1.00367
- OpenMP overhead par_simd p=1 vs seq_simd at n=2048: speedup=0.997128, efficiency=0.997128
- par_scalar n=2048 p=1: same-level baseline=seq_scalar, speedup=1.00367, efficiency=1.00367; combined baseline=seq_scalar, speedup=1.00367
- par_scalar n=2048 p=2: same-level baseline=seq_scalar, speedup=1.62556, efficiency=0.812782; combined baseline=seq_scalar, speedup=1.62556
- par_scalar n=2048 p=4: same-level baseline=seq_scalar, speedup=3.0314, efficiency=0.757851; combined baseline=seq_scalar, speedup=3.0314
- par_scalar n=2048 p=6: same-level baseline=seq_scalar, speedup=3.66452, efficiency=0.610753; combined baseline=seq_scalar, speedup=3.66452
- par_scalar n=2048 p=8: same-level baseline=seq_scalar, speedup=4.52386, efficiency=0.565482; combined baseline=seq_scalar, speedup=4.52386
- par_scalar n=2048 p=12: same-level baseline=seq_scalar, speedup=5.56167, efficiency=0.463472; combined baseline=seq_scalar, speedup=5.56167
- par_simd n=2048 p=1: same-level baseline=seq_simd, speedup=0.997128, efficiency=0.997128; combined baseline=seq_scalar, speedup=1.41907
- par_simd n=2048 p=2: same-level baseline=seq_simd, speedup=1.70995, efficiency=0.854977; combined baseline=seq_scalar, speedup=2.43354
- par_simd n=2048 p=4: same-level baseline=seq_simd, speedup=3.22218, efficiency=0.805546; combined baseline=seq_scalar, speedup=4.58568
- par_simd n=2048 p=6: same-level baseline=seq_simd, speedup=3.88128, efficiency=0.646881; combined baseline=seq_scalar, speedup=5.52368
- par_simd n=2048 p=8: same-level baseline=seq_simd, speedup=4.1774, efficiency=0.522175; combined baseline=seq_scalar, speedup=5.94511
- par_simd n=2048 p=12: same-level baseline=seq_simd, speedup=4.91175, efficiency=0.409313; combined baseline=seq_scalar, speedup=6.9902
- OpenMP overhead par_scalar p=1 vs seq_scalar at n=4096: speedup=1.03586, efficiency=1.03586
- OpenMP overhead par_simd p=1 vs seq_simd at n=4096: speedup=0.99752, efficiency=0.99752
- par_scalar n=4096 p=1: same-level baseline=seq_scalar, speedup=1.03586, efficiency=1.03586; combined baseline=seq_scalar, speedup=1.03586
- par_scalar n=4096 p=12: same-level baseline=seq_scalar, speedup=3.95533, efficiency=0.329611; combined baseline=seq_scalar, speedup=3.95533
- par_simd n=4096 p=1: same-level baseline=seq_simd, speedup=0.99752, efficiency=0.99752; combined baseline=seq_scalar, speedup=1.46384
- par_simd n=4096 p=4: same-level baseline=seq_simd, speedup=3.05813, efficiency=0.764534; combined baseline=seq_scalar, speedup=4.48776
- par_simd n=4096 p=8: same-level baseline=seq_simd, speedup=2.8792, efficiency=0.3599; combined baseline=seq_scalar, speedup=4.22518
- par_simd n=4096 p=12: same-level baseline=seq_simd, speedup=2.92932, efficiency=0.24411; combined baseline=seq_scalar, speedup=4.29873

## Flags

- IQR > 20% of median: ('par_simd', 256, 12), median=0.000646, IQR=0.0002310925
- Within noise (not superlinear): par_simd, n=256, p=1; baseline=seq_simd, speedup=1.01432, uncertainty=0.205042
- Within noise (not superlinear): par_scalar, n=512, p=1; baseline=seq_scalar, speedup=1.00786, uncertainty=0.0707201
- Within noise (not superlinear): par_scalar, n=512, p=4; baseline=seq_scalar, speedup=4.0546, uncertainty=0.353595
- Within noise (not superlinear): par_simd, n=512, p=1; baseline=seq_simd, speedup=1.00217, uncertainty=0.0637423
- Efficiency > 1.05: par_simd, n=512, p=2; efficiency=1.12891, baseline IQR=0.000779735
- Within noise (not superlinear): par_simd, n=512, p=2; baseline=seq_simd, speedup=2.25783, uncertainty=0.268052
- Within noise (not superlinear): par_simd, n=512, p=4; baseline=seq_simd, speedup=4.14298, uncertainty=0.253725
- Within noise (not superlinear): par_simd, n=1024, p=2; baseline=seq_simd, speedup=2.05564, uncertainty=0.315556
- Within noise (not superlinear): par_simd, n=1024, p=4; baseline=seq_simd, speedup=4.11752, uncertainty=0.713484
- Within noise (not superlinear): par_scalar, n=2048, p=1; baseline=seq_scalar, speedup=1.00367, uncertainty=0.0552298
- Within noise (not superlinear): par_scalar, n=4096, p=1; baseline=seq_scalar, speedup=1.03586, uncertainty=0.0538077
