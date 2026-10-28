# Results so far, 27 Oct 2026

Sections up to the E3b pipeline check are on synthetic data: 60 units, 16 stimuli, 100 trials each, time-blocked
holdout, 2 seeds. Chance is 0.06. Figure: `e2.png`. Raw numbers: `e2.json`.

## Gate 1 (E2): 6 of 7 pass, 1 fails

Gate: code-based accuracy reaches 90% of its final value at the level whose bin
width matches the planted precision, plus or minus one level. The 2 ms control
stays unresolved.

| planted code | expected | tokenizer | quantized pyramid | continuous pyramid | verdict |
| --- | --- | --- | --- | --- | --- |
| rate | L1 | L1 | L1 | L1 | pass |
| shape, 125 ms | L2 | L3 | L6 | L2 | pass (weak) |
| timing, 50 ms | L3 | L5 | L3 | L3 | **fail** |
| timing, 25 ms | L4 | L4 | L4 | L4 | pass |
| timing, 10 ms | L5 | L5 | L5 | L5 | pass |
| timing, 5 ms | L6 | L6 | L6 | L6 | pass |
| mixed | L5 | L5 | L5 | L5 | descriptive |
| control, 2 ms | none | none | none | none | pass |

**Localization works.** In every condition, information first appears at the
planted level and never before it, and the control stays at chance.

**Retention is the weakness.** The 50 ms code jumps from 0.06 to 0.61 at L3,
which is the correct level, but keeps climbing to 0.76 by L6, so the 90% rule
is met only at L5. The 125 ms shape code reaches only about 0.34 (ceiling 0.95).
Both codes have the fewest events per unit (1 and 2), so their signal is the
smallest share of reconstruction variance.

The failure is reported against the criterion as written. The criterion has
not been changed after seeing the data.

## Preview of gate 2: currently failing

The quantized pyramid (residual k-means on pooled log-counts, same levels and
codebook sizes, no learning) matches or beats the tokenizer almost everywhere:

| code | tokenizer, final | quantized pyramid, final |
| --- | --- | --- |
| rate | 0.89 | 1.00 |
| shape, 125 ms | 0.32 | 0.69 |
| timing, 50 ms | 0.76 | 0.99 |
| timing, 25 ms | 0.97 | 1.00 |
| timing, 10 ms | 1.00 | 1.00 |
| timing, 5 ms | **1.00** | 0.84 |

The tokenizer wins only at the finest scale. As built, the learned codes add
little over plain binning at matched bits on these data.

## E3b pipeline check (10 ms timing code, 40 units)

| test set | codes, L5 to L6 | pyramid, L5 to L6 |
| --- | --- | --- |
| clean | 0.99, 1.00 | 1.00, 1.00 |
| jittered 10 ms | 0.32, 0.41 | 0.73, 0.65 |
| PSTH-matched surrogate | 1.00, 1.00 | 1.00, 1.00 |

Jitter destroys the planted code as intended. The surrogate leaves it intact,
which is correct here because synthetic units are independent. Codes are more
fragile to jitter than counts.

## E3 and E3b on Allen VISp, session 732592105 (27 Oct 2026)

Brain Observatory 1.1, natural scenes, 118 images, 50 repeats each, 0 to 250 ms
from onset. 113 units pass the quality filters; 60 are subsampled per repeat,
5 repeats, 60 epochs, time-blocked holdout (last 10 repeats of each image).
Chance is 0.008. Raw numbers: `e3_allen_732592105_VISp_n60.json`.

### Per-level accuracy, clean test set (mean of 5 repeats)

| readout | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| tokenizer codes | 0.06 | 0.11 | 0.16 | 0.17 | 0.16 | 0.17 |
| tokenizer reconstruction | 0.06 | 0.12 | 0.15 | 0.16 | 0.15 | 0.15 |
| continuous pyramid | 0.40 | 0.43 | 0.39 | 0.34 | 0.27 | 0.20 |
| cumulative bits (codes) | 5 | 17 | 47 | 117 | 292 | 642 |

Repeats agree to within about 0.03 everywhere.

**The codes keep far less than the counts.** Plain 250 ms counts decode the
image at 0.40, the codes at 0.06. Level 1 has only 32 codes for 118 images,
which caps it, but the gap stays at 0.2 or more at every level and the codes
plateau at 0.17 from L4 on while 117 to 642 bits are available. The quantized
pyramid is not part of the E3 script, so the matched-bits comparison from gate
2 was not rerun here, but the continuous pyramid already shows the learned
codes discard most of the stimulus information on real data. All codebooks are
fully used (perplexity 26 of 32 at L1, 98 to 114 of 128 at L4 to L6), so this
is not dead codes.

**The pyramid curve falls with level.** 0.43 at L2 down to 0.20 at L6. The
decoder sees 60 x 50 = 3000 features at L6 with 40 training trials per image,
so this is decoder overfitting, not evidence that fine bins carry less
information. On real data the pyramid curve is therefore not a clean per-level
information measure, which the synthetic runs (at ceiling everywhere) did not
reveal.

### E3b: jitter and PSTH-matched surrogates (pyramid readout)

| test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 0.40 | 0.43 | 0.39 | 0.34 | 0.27 | 0.20 |
| jitter 5 ms | 0.40 | 0.43 | 0.39 | 0.34 | 0.26 | 0.20 |
| jitter 10 ms | 0.40 | 0.43 | 0.38 | 0.33 | 0.25 | 0.20 |
| jitter 25 ms | 0.40 | 0.42 | 0.37 | 0.30 | 0.23 | 0.18 |
| PSTH surrogate | 0.34 | 0.38 | 0.36 | 0.33 | 0.26 | 0.21 |

Codes behave the same way at a lower level: jitter of 5 and 10 ms changes them
by at most 0.01, and 25 ms jitter costs 0.01 to 0.02 at L3 to L6.

**Little decodable timing information below 25 ms.** Jitter at 5 and 10 ms
leaves every readout unchanged. Jitter at 25 ms costs the pyramid 0.02 to 0.04
at L3 to L6, so image identity depends on spike timing only at the 25 ms scale
and coarser, with this decoder and unit count.

**Noise correlations help at coarse levels.** The PSTH-matched surrogate, which
keeps each unit's per-image PSTH but breaks trial-wise co-variation across
units, lowers L1 and L2 accuracy by 0.05 to 0.06 and leaves L4 to L6 alone. For
the codes the surrogate slightly raises accuracy (0.17 to 0.18 at L6).

## Caveats

- Synthetic codes are easy (the continuous pyramid is at 1.00), so they test
  localization better than retention.
- 60 epochs on CPU, 2 synthetic seeds and 5 real-data unit subsamples. Not tuned.
- One Allen session, one area. The fixed logistic decoder overfits at fine
  levels on real data (40 training trials per image), so per-level curves
  there mix information with decoder capacity.

## Suggested next steps

1. Decide whether gate 2 can still be met. Real data widens the gap: codes
   retain 0.17 of a possible 0.43. Options: longer training, codebooks fit to
   the quantized-pyramid init, or reframing the project around the analysis
   (E3b with the quantized pyramid as the tokenizer).
2. Add the quantized pyramid to E3 so the matched-bits comparison exists on
   real data.
3. Use a decoder that does not overfit at fine levels (stronger regularization
   or PCA before the classifier) so the real-data pyramid curve measures
   information, not capacity.
