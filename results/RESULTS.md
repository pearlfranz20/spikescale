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

## Gate 2 on synthetic data: failing

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

## E3 and E3b on Allen VISp, session 732592105 (27 Oct 2026, rerun with quantized pyramid and three decoders)

Brain Observatory 1.1, natural scenes, 118 images, 50 repeats each, 0 to 250 ms
from onset. 113 units pass the quality filters; 60 are subsampled per seed,
5 seeds, 60 epochs, time-blocked holdout (last 10 repeats of each image).
Chance is 0.008. Raw numbers: `e3_allen_732592105_VISp_n60.json`.

Four readouts: tokenizer codes (primary), tokenizer reconstruction, the
continuous pyramid (pooled log-counts, unbounded bits, a ceiling) and the
quantized pyramid (residual k-means on pooled log-counts at the tokenizer's
level lengths and codebook sizes, the matched-bits baseline gate 2 asks for).
Three decoders: plain L2 logistic on the level-k features (the decoder used in
the first run); PCA to 100 components then logistic; and PCA then logistic on
the concatenation of level-1 to level-k features ("cumulative"). The cumulative
decoder is the one to read per-level curves from, see below. Seeds agree to
within 0.02 (std) everywhere.

### Per-level accuracy, clean test set, plain logistic decoder

| readout | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| tokenizer codes | 0.06 | 0.11 | 0.16 | 0.17 | 0.16 | 0.17 |
| tokenizer reconstruction | 0.06 | 0.12 | 0.15 | 0.16 | 0.15 | 0.15 |
| quantized pyramid (matched bits) | 0.04 | 0.09 | 0.11 | 0.14 | 0.17 | 0.19 |
| continuous pyramid | 0.40 | 0.43 | 0.39 | 0.34 | 0.27 | 0.20 |
| cumulative bits (codes) | 5 | 17 | 47 | 117 | 292 | 642 |

### Per-level accuracy, clean test set, cumulative PCA decoder

| readout | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| tokenizer codes | 0.06 | 0.11 | 0.15 | 0.16 | 0.17 | 0.18 |
| tokenizer reconstruction | 0.06 | 0.11 | 0.14 | 0.15 | 0.15 | 0.15 |
| quantized pyramid (matched bits) | 0.04 | 0.09 | 0.10 | 0.13 | 0.15 | 0.16 |
| continuous pyramid | 0.40 | 0.41 | 0.41 | 0.39 | 0.37 | 0.35 |

**Gate 2 on real data: a tie.** At matched bits the learned codes and the
residual k-means codes are within 0.02 of each other at every level under the
cumulative decoder, and the tokenizer is ahead by 0.02 to 0.05 at L1 to L4
under the plain decoder while k-means is ahead by 0.02 at L6. Learned codes do
not beat plain quantization, but on real data they no longer lose to it
either (on synthetic data k-means won almost everywhere). Gate 2 as written
asks the tokenizer to beat the matched-bits baseline, so it is not met.

**Both discrete readouts discard most of the stimulus information.** The
continuous pyramid reaches 0.40 at 250 ms and 0.41 at 125 to 50 ms; neither
discrete readout passes 0.19 at any level, with 642 bits available by L6.
Codebooks are fully used (perplexity 26 of 32 at L1, 98 to 114 of 128 at L4
to L6), so this is not dead codes. Level 1 has 32 codes for 118 images, which
caps it at about 0.27 even if codes were pure, and both methods reach 0.04 to
0.06 there. The loss is in the bottleneck shape: one code of 32 to 128 entries
per time bin for a 60-unit population vector, learned or not, keeps a few
bits of a 60-dimensional count. Since k-means and the tokenizer land in the
same place, the remedy is not better training of this architecture; it is a
different bottleneck (per-unit or per-group codes, or far larger codebooks).

**The decoder matters for the per-level shape, not for the conclusion.** With
the plain decoder the continuous pyramid falls from 0.43 at L2 to 0.20 at L6.
Stronger L2 regularization or PCA on the level-k features alone does not
recover it (probed: C from 0.001 to 0.1, PCA 100 to 300, best 0.24 at L6),
because the coarse-count direction is spread over 25 to 50 standardized bins
at fine levels and the L2 penalty prices it accordingly. Concatenating levels
1 to k keeps the coarse counts as explicit features, and with PCA to 100 the
curve becomes 0.40, 0.41, 0.41, 0.39, 0.37, 0.35: flat to L3 and a 0.06
decline after, which is the remaining capacity cost. Read this as: no
decodable image information is added below 50 ms bins, and the decline at
finer levels is decoder noise, not lost information. The discrete readouts
hardly change between decoders (at most 0.02), because 100 PCs already cover
their low-dimensional features.

### E3b: jitter and PSTH-matched surrogates, cumulative PCA decoder

Continuous pyramid:

| test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 0.40 | 0.41 | 0.41 | 0.39 | 0.37 | 0.35 |
| jitter 5 ms | 0.40 | 0.41 | 0.41 | 0.39 | 0.37 | 0.35 |
| jitter 10 ms | 0.40 | 0.41 | 0.40 | 0.39 | 0.37 | 0.35 |
| jitter 25 ms | 0.40 | 0.41 | 0.40 | 0.38 | 0.36 | 0.34 |
| PSTH surrogate | 0.34 | 0.36 | 0.38 | 0.37 | 0.37 | 0.35 |

Tokenizer codes:

| test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 0.06 | 0.11 | 0.15 | 0.16 | 0.17 | 0.18 |
| jitter 25 ms | 0.06 | 0.11 | 0.15 | 0.15 | 0.16 | 0.16 |
| PSTH surrogate | 0.06 | 0.12 | 0.15 | 0.17 | 0.18 | 0.18 |

Jitter of 5 and 10 ms changes nothing in any readout. Jitter of 25 ms costs
the pyramid 0.01 at L3 to L6 (it cost 0.02 to 0.04 under the plain decoder,
so part of that earlier loss was the decoder's noise sensitivity) and the
codes 0.01 to 0.02 at L4 to L6. The quantized pyramid behaves like the codes.

**Little decodable timing information below 25 ms, and little between 25
and 50 ms.** Taken with the flat cumulative curve from L1 to L3, image
identity in VISp over 0 to 250 ms is carried at the 50 to 125 ms scale.

**Noise correlations help at coarse levels.** The PSTH-matched surrogate,
which keeps each unit's per-image PSTH but breaks trial-wise co-variation
across units, lowers L1 by 0.06, L2 by 0.05, L3 by 0.03, L4 by 0.02 and
leaves L5 and L6 alone. For the codes the surrogate slightly raises accuracy
(up to 0.01).

## Comparison with published VISp decoding (27 Oct 2026)

There is no benchmark for 118-image natural-scene decoding on Allen
Neuropixels. The closest published number is Table I of
[arXiv 2510.09451](https://arxiv.org/html/2510.09451v1): a linear SVM on
all VISp units of a session, 10-fold cross-validation, seven Brain
Observatory 1.1 sessions. The paper does not state its window or bin size
and calls the task 128-way, so treat it as a ballpark. `compare_external.py`
runs the continuous pyramid on this session under both protocols, with both
unit counts and all three decoders. Raw numbers: `external_allen_732592105_VISp.json`.

### Continuous pyramid, best level, this session

| units | split | decoder | best level | top-1 |
| --- | --- | --- | --- | --- |
| 60 | time-blocked | logistic | L2 (125 ms) | 0.43 |
| 60 | random 10-fold | logistic | L2 | 0.49 |
| 113 (all) | time-blocked | logistic | L2 | 0.54 |
| 113 (all) | random 10-fold | logistic | L2 | 0.59 |
| 113 (all) | random 10-fold | cumulative PCA | L3 (50 ms) | 0.56 |

### Published, same task

| source | setting | VISp top-1 |
| --- | --- | --- |
| arXiv 2510.09451, Table I | all units, SVM, 10-fold CV, 7 sessions | 0.45 +- 0.09 (range 0.31 to 0.55) |
| same paper, Table III | several areas pooled, 2 sessions | 0.88 to 0.96 |

Under the matching protocol (all units, random folds) this session reaches
0.59, above the best of the paper's seven sessions. So the extraction and the
plain count decoder are at least as good as the published single-area
baseline, and the gap between the tokenizer codes and the pyramid is not a
weak pipeline. Random folds add 0.05 over the time-blocked split at 60 units
and 113 units alike, which is the drift the blocked split is there to
exclude. Going from 60 to 113 units adds 0.11. The multi-region numbers pool
hundreds of units across areas and are not comparable to a single-area
readout.

The per-level shape agrees with the literature too.
[NeuroPixelHD](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10899419/)
(Frontiers in Cellular Neuroscience, 2024) decoded the same 118 images from
Allen Neuropixels at bin widths from milliseconds up and found that 125 ms bins
maximized accuracy across the brain, with the optimum shifting along the
sensory-to-associative hierarchy. Here the peak is at L2 (125 ms) for the
plain decoder and L2 to L3 (125 to 50 ms) for the cumulative decoder, in
every unit count and split. Together with the E3b jitter result (no loss
below 25 ms), VISp image identity in this window is a 50 to 125 ms code.

Not done: the paper's seven sessions were not downloaded (about 3 GB each),
so the comparison is one session against their distribution, not per session.

## Caveats

- Synthetic codes are easy (the continuous pyramid is at 1.00), so they test
  localization better than retention.
- 60 epochs on CPU, 2 synthetic seeds and 5 real-data unit subsamples. Not tuned.
- One Allen session, one area. The published comparison is against seven
  other sessions' distribution, not the same sessions.
- The cumulative PCA decoder was added after the first real-data run showed
  the plain decoder falling with level. It was chosen on the argument above
  and a probe of the continuous pyramid only; C stayed at 0.1 and was not
  tuned per level. All three decoders are in the JSON and the plain one is
  still reported.
- The remaining 0.06 decline from L3 to L6 under the cumulative decoder is
  attributed to capacity, not measured; a per-level inner-CV choice of C or
  PCA size would settle it.

## Suggested next steps

1. Gate 2 is not met and the matched-bits baseline shows why: the bottleneck
   shape, not the learning, limits both. If the tokenizer is to be kept, the
   change is architectural: per-unit or per-group codebooks (a code per unit
   per bin, or per small group) so the bit budget scales with the population,
   or codebooks in the thousands with product quantization. Otherwise reframe
   around the analysis, with the quantized pyramid as a drop-in tokenizer.
2. A second VISp session and one higher area (VISl or VISam) with the same
   pipeline, to see whether the 50 to 125 ms optimum shifts with the
   hierarchy as NeuroPixelHD reports.
3. Inner-CV choice of C and PCA size per level, so the per-level curve is
   capacity-matched by construction rather than by argument.
4. E4, the fixed-resolution ladder, is still open.
