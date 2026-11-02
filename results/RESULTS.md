# Results so far, 1 Nov 2026

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

## E3 and E3b on Allen VISp, session 732592105 (28 Oct 2026, rerun with the nested-C cumulative decoder)

Brain Observatory 1.1, natural scenes, 118 images, 50 repeats each, 0 to 250 ms
from onset. 113 units pass the quality filters; 60 are subsampled per seed,
5 seeds, 60 epochs, time-blocked holdout (last 10 repeats of each image).
Chance is 0.008. Figure: `e3_allen_732592105_VISp_n60.png` (A: the four
readouts, B: the pyramid under the four decoders, C and D: E3b test sets).
Raw numbers: `e3_allen_732592105_VISp_n60.json`.

Four readouts: tokenizer codes (primary), tokenizer reconstruction, the
continuous pyramid (pooled log-counts, unbounded bits, a ceiling) and the
quantized pyramid (residual k-means on pooled log-counts at the tokenizer's
level lengths and codebook sizes, the matched-bits baseline gate 2 asks for).
Four decoders, all L2 logistic: on the concatenation of level-1 to level-k
features ("cumulative") with C chosen per level on an inner time-blocked
split of the training set (primary, chosen in `notes/decoder_bakeoff.md`
from twelve candidates); cumulative features through PCA to 100 then fixed
C = 0.1 (secondary, the primary of the 27 Oct run); and, for continuity,
plain and PCA-100 logistic on the level-k features alone at C = 0.1. The
cumulative decoders are the ones to read per-level curves from: the
concatenation keeps the coarse counts as explicit features, so a level
cannot score below the levels above it for reasons of decoder geometry, and
the per-level C matches capacity across levels. Seeds agree to within 0.02
(std) everywhere. Chosen C falls with level in every readout: 0.03 to 0.1 at
L1, 0.001 at L5 to L6 for the pyramid (the grid runs 0.001 to 1; a probe
below 0.001 lost accuracy).

### Per-level accuracy, clean test set, nested-C cumulative decoder (primary)

| readout | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| tokenizer codes | 0.06 | 0.11 | 0.16 | 0.19 | 0.21 | 0.23 |
| tokenizer reconstruction | 0.06 | 0.12 | 0.15 | 0.18 | 0.19 | 0.20 |
| quantized pyramid (matched bits) | 0.04 | 0.09 | 0.12 | 0.16 | 0.18 | 0.20 |
| continuous pyramid | 0.40 | 0.45 | 0.47 | 0.45 | 0.41 | 0.37 |
| cumulative bits (codes) | 5 | 17 | 47 | 117 | 292 | 642 |

### Per-level accuracy, clean test set, cumulative PCA-100 decoder, C = 0.1 (secondary)

| readout | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| tokenizer codes | 0.06 | 0.11 | 0.15 | 0.16 | 0.17 | 0.18 |
| tokenizer reconstruction | 0.06 | 0.11 | 0.14 | 0.15 | 0.15 | 0.15 |
| quantized pyramid (matched bits) | 0.04 | 0.09 | 0.10 | 0.13 | 0.15 | 0.16 |
| continuous pyramid | 0.40 | 0.41 | 0.41 | 0.39 | 0.37 | 0.35 |

### Per-level accuracy, clean test set, plain logistic on level-k features, C = 0.1

| readout | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| tokenizer codes | 0.06 | 0.11 | 0.16 | 0.17 | 0.16 | 0.17 |
| tokenizer reconstruction | 0.06 | 0.12 | 0.15 | 0.16 | 0.15 | 0.15 |
| quantized pyramid (matched bits) | 0.04 | 0.09 | 0.11 | 0.14 | 0.17 | 0.19 |
| continuous pyramid | 0.40 | 0.43 | 0.39 | 0.34 | 0.27 | 0.20 |

**Gate 2 on real data: a small, consistent edge for the learned codes, short
of the gate.** Under the primary decoder the tokenizer codes beat the
quantized pyramid at every level, by 0.02 at L1 to L2, 0.03 to 0.04 at L3
to L5 and 0.02 at L6 (paired per seed: ahead in 29 of 30 seed-level pairs,
the one exception by 0.004 at L1). Seed std is 0.01 to 0.02, so the edge is
real but modest; the 27 Oct PCA-100 decoder had compressed it to a tie.
Learned codes beat plain quantization by a few points at matched bits on
real data (on synthetic data k-means won almost everywhere). Gate 2 asked
for a clear win, so it is not met; the codes carry about 0.03 more
decodable information per 60 units than residual k-means on the same bits.

**Both discrete readouts discard most of the stimulus information.** The
continuous pyramid reaches 0.47 at L3; neither discrete readout passes 0.23
at any level, with 642 bits available by L6. Codebooks are fully used
(perplexity 26 of 32 at L1, 98 to 114 of 128 at L4 to L6), so this is not
dead codes. Level 1 has 32 codes for 118 images, which caps it at about 0.27
even if codes were pure, and both methods reach 0.04 to 0.06 there. The loss
is in the bottleneck shape: one code of 32 to 128 entries per time bin for a
60-unit population vector, learned or not, keeps a few bits of a
60-dimensional count. Since k-means and the tokenizer land within 0.04 of
each other, the remedy is not better training of this architecture; it is a
different bottleneck (per-unit or per-group codes, or far larger codebooks).

**The decoder matters for the per-level shape, not for the conclusion.** With
the plain decoder the continuous pyramid falls from 0.43 at L2 to 0.20 at L6.
Concatenating levels 1 to k and choosing C per level gives 0.40, 0.45, 0.47,
0.45, 0.41, 0.37: a gain of 0.06 to 0.07 from L1 to L3 in every seed, then a
decline of 0.09 to 0.11 to L6. The 27 Oct PCA-100 decoder had flattened the
L1 to L3 gain away (0.40, 0.41, 0.41), so its "flat to L3" reading was a
decoder artefact; the nested-C decoder is 0.04 to 0.06 more accurate than it
at L2 to L4. The L3 to L6 decline survives every decoder in the bake-off
(0.11 for the best, 0.07 for trial-averaged PCA) and the extended C grid, so
with 40 training trials per image it is a floor on the capacity cost of
linear decoders at 10 and 5 ms, not a measurement of information lost. Read
the curve as: 125 and 50 ms structure adds 0.07 over whole-window counts,
and no decodable image information is added below 50 ms bins. The discrete
readouts change by at most 0.05 between decoders (codes 0.18 to 0.23 at L6).

### E3b: jitter and PSTH-matched surrogates, nested-C cumulative decoder

Continuous pyramid:

| test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 0.40 | 0.45 | 0.47 | 0.45 | 0.41 | 0.37 |
| jitter 5 ms | 0.40 | 0.45 | 0.47 | 0.45 | 0.41 | 0.37 |
| jitter 10 ms | 0.40 | 0.45 | 0.46 | 0.44 | 0.40 | 0.36 |
| jitter 25 ms | 0.40 | 0.44 | 0.46 | 0.42 | 0.39 | 0.34 |
| PSTH surrogate | 0.35 | 0.42 | 0.45 | 0.46 | 0.44 | 0.39 |

Tokenizer codes:

| test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 0.06 | 0.11 | 0.16 | 0.19 | 0.21 | 0.23 |
| jitter 10 ms | 0.06 | 0.11 | 0.16 | 0.19 | 0.21 | 0.22 |
| jitter 25 ms | 0.06 | 0.11 | 0.15 | 0.17 | 0.20 | 0.21 |
| PSTH surrogate | 0.06 | 0.12 | 0.17 | 0.20 | 0.24 | 0.26 |

Jitter of 5 ms changes nothing in any readout. Jitter of 10 ms costs the
pyramid 0.01 at L3 to L6. Jitter of 25 ms costs it 0.01 at L2 to L3 and
0.02 to 0.03 at L4 to L6 (in every seed), and the codes 0.01 to 0.02 at L3
to L6. The quantized pyramid behaves like the codes. So there is a small
amount of decodable timing structure between 10 and 25 ms, worth about 0.03
at the levels fine enough to see it, but the best level (L3, 50 ms bins)
loses only 0.01 to 25 ms jitter.

**Image identity in VISp over 0 to 250 ms is carried at the 50 to 125 ms
scale.** Levels 2 and 3 add 0.07 over whole-window counts, finer levels add
nothing, and 25 ms jitter costs the best level 0.01.

**Noise correlations help at coarse levels and hurt slightly at fine ones.**
The PSTH-matched surrogate, which keeps each unit's per-image PSTH but breaks
trial-wise co-variation across units, lowers the pyramid's L1 by 0.05, L2 by
0.03 and L3 by 0.01 (every seed below clean at L1 to L2), and raises L4 to
L6 by 0.01 to 0.03 (every seed above clean at L4 to L6). For the codes the
surrogate raises accuracy by 0.01 to 0.03 at L3 to L6. Under the PCA-100
decoder the surrogate had only lowered accuracy; the fine-level gain is
visible once the decoder is strong enough to use the fine features.

## Comparison with published VISp decoding (27 Oct 2026, nested-C decoder added 1 Nov)

There is no benchmark for 118-image natural-scene decoding on Allen
Neuropixels. The closest published number is Table I of
[arXiv 2510.09451](https://arxiv.org/html/2510.09451v1): a linear SVM on
all VISp units of a session, 10-fold cross-validation, seven Brain
Observatory 1.1 sessions. The paper does not state its window or bin size
and calls the task 128-way, so treat it as a ballpark. `compare_external.py`
runs the continuous pyramid on this session under both protocols, with both
unit counts and all four E3 decoders. Raw numbers: `external_allen_732592105_VISp.json`.

### Continuous pyramid, best level, this session

| units | split | decoder | best level | top-1 |
| --- | --- | --- | --- | --- |
| 60 | time-blocked | nested-C cumulative (primary) | L2 to L3 (125 to 50 ms) | 0.45 |
| 60 | random 10-fold | nested-C cumulative | L3 (50 ms) | 0.52 |
| 113 (all) | time-blocked | nested-C cumulative | L3 | 0.59 |
| 113 (all) | random 10-fold | nested-C cumulative | L3 | 0.63 |
| 60 | time-blocked | plain logistic, C = 0.1 | L2 (125 ms) | 0.43 |
| 60 | random 10-fold | plain logistic | L2 | 0.49 |
| 113 (all) | time-blocked | plain logistic | L2 | 0.54 |
| 113 (all) | random 10-fold | plain logistic | L2 | 0.59 |
| 113 (all) | random 10-fold | cumulative PCA-100, C = 0.1 | L1 to L3 | 0.56 |

Full per-level curves for the primary decoder (fold std 0.01 to 0.02 under
random folds):

| units | split | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | time-blocked | 0.39 | 0.45 | 0.45 | 0.44 | 0.39 | 0.35 |
| 60 | random 10-fold | 0.44 | 0.50 | 0.52 | 0.50 | 0.46 | 0.42 |
| 113 | time-blocked | 0.53 | 0.58 | 0.59 | 0.57 | 0.53 | 0.48 |
| 113 | random 10-fold | 0.58 | 0.62 | 0.63 | 0.62 | 0.58 | 0.54 |

### Published, same task

| source | setting | VISp top-1 |
| --- | --- | --- |
| arXiv 2510.09451, Table I | all units, SVM, 10-fold CV, 7 sessions | 0.45 +- 0.09 (range 0.31 to 0.55) |
| same paper, Table III | several areas pooled, 2 sessions | 0.88 to 0.96 |

Under the matching protocol (all units, random folds) this session reaches
0.63 with the primary decoder and 0.59 with plain logistic on whole-window
counts, both above the best of the paper's seven sessions. So the extraction
and the count decoders are at least as good as the published single-area
baseline, and the gap between the tokenizer codes and the pyramid is not a
weak pipeline. The nested-C decoder adds 0.02 to 0.04 over plain logistic
in every unit count and split, the same margin as in the bake-off. Random
folds add 0.04 to 0.06 over the time-blocked split at 60 units and 113 units
alike, which is the drift the blocked split is there to exclude. Going from
60 to 113 units adds 0.11 to 0.14. The chosen C falls with level here as in
E3 (median 0.1 or 0.03 at L1, 0.001 at L6). The multi-region numbers pool
hundreds of units across areas and are not comparable to a single-area
readout.

The per-level shape agrees with the literature too.
[NeuroPixelHD](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10899419/)
(Frontiers in Cellular Neuroscience, 2024) decoded the same 118 images from
Allen Neuropixels at bin widths from milliseconds up and found that 125 ms bins
maximized accuracy across the brain, with the optimum shifting along the
sensory-to-associative hierarchy. Here the peak is at L2 (125 ms) for the
plain decoder and L3 (50 ms, with L2 within 0.01 at 60 units) for the
cumulative decoders, in every unit count and split. Together with the E3b jitter result (no loss
below 25 ms), VISp image identity in this window is a 50 to 125 ms code.

Not done: the paper's seven sessions were not downloaded (about 3 GB each),
so the comparison is one session against their distribution, not per session.

## Unique information per scale: decoding from each level's detail alone (1 Nov 2026)

The cumulative curve says the 125 and 50 ms levels add information over
whole-window counts, but not whether that information is unique to each
scale or a re-expression of coarser structure. `scripts/residual_levels.py`
splits every unit's 5 ms count vector (sqrt-transformed) into six orthogonal
pieces, the level-k detail being the part of levels 1 to k that is orthogonal
to levels 1 to k-1 (1, 1, 4, 4, 20 and 20 dimensions per unit; the level
lengths do not all nest, so the pieces come from Gram-Schmidt on the pooling
bases rather than Haar differences). Each detail is decoded alone with the
primary nested-C decoder, same split and unit subsets as E3. The control is
the same detail after the 5 ms bins of every trial and unit are permuted,
which keeps each unit's count and destroys all timing: it measures how much
a detail can be decoded from the size of the fluctuations alone. Raw numbers:
`residual_allen_732592105_VISp.json` and `residual_<code>.json` for the
synthetic checks.

Synthetic checks (60 units, 16 stimuli, chance 0.06, one seed): the rate
code decodes at 1.00 from the L1 detail and at chance from every other
detail; the 25 ms timing code is at chance for L1 to L3 and 1.00 from the L4
detail; the 10 ms code is at chance except 1.00 from the L5 detail. The
shuffled control is at chance everywhere. So a detail scores only when its
scale carries the code.

### Allen VISp, detail of level k alone, nested-C logistic

| units | readout | L1 (250) | L2 (125) | L3 (50) | L4 (25) | L5 (10) | L6 (5 ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 60, 5 seeds | detail alone | 0.41 | 0.21 | 0.17 | 0.07 | 0.05 | 0.03 |
| 60, 5 seeds | time-shuffled control | 0.41 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| 60, 5 seeds | details 1 to k, cumulative | 0.41 | 0.45 | 0.39 | 0.35 | 0.25 | 0.19 |
| 113 (all) | detail alone | 0.55 | 0.30 | 0.24 | 0.11 | 0.06 | 0.03 |
| 113 (all) | time-shuffled control | 0.55 | 0.02 | 0.02 | 0.02 | 0.01 | 0.02 |
| 113 (all) | details 1 to k, cumulative | 0.55 | 0.57 | 0.51 | 0.46 | 0.34 | 0.28 |

Chance is 0.008. Seed std is at most 0.02. Detail minus control per seed
(60 units): 0.17 to 0.22 at L2, 0.14 to 0.17 at L3, 0.04 to 0.06 at L4, 0.02
to 0.03 at L5, and -0.01 to 0.02 at L6.

**Image identity is multiplexed over three scales, and each is unique.** The
125 ms detail is one number per unit, the difference between the first and
second half of the window, and on its own it identifies the image at 0.21
(60 units) or 0.30 (all units), 25 to 35 times chance, with the whole-window
count removed by construction. The 50 ms detail adds 0.17 or 0.24 on its
own, orthogonal to both the count and the 125 ms shape. The 25 ms detail is
worth 0.05 to 0.09 and the 10 ms detail 0.03 to 0.04, both above the control
in every seed. At 5 ms the detail is within the control's range. The
control stays at 0.02, so none of this is fluctuation size masquerading as
timing. This is the same ordering the cumulative curve and the jitter test
gave, now with each scale's contribution separated: rate carries most, the
125 ms temporal shape and the 50 ms shape each carry a large independent
share, and there is a small but real component between 10 and 25 ms.

Two caveats. Orthogonality is in time, not in statistics: a detail can be
decodable because its shape covaries with rate across images, and the
control only rules out the size of fluctuations, not their shape. And the
cumulative detail readout is linear in near-raw counts (sqrt of 0 or 1
spikes per 5 ms bin), so it falls below the log1p pooled pyramid from L3 on
(0.39 against 0.47 at L3, 60 units); the pyramid's per-level log transform
is worth up to 0.08 at fine levels. Read the detail rows against each other
and against the control, not against the pyramid.

## Caveats

- Synthetic codes are easy (the continuous pyramid is at 1.00), so they test
  localization better than retention.
- 60 epochs on CPU, 2 synthetic seeds and 5 real-data unit subsamples. Not tuned.
- One Allen session, one area. The published comparison is against seven
  other sessions' distribution, not the same sessions.
- The primary decoder was chosen on 28 Oct after the first real-data run,
  from a bake-off on the continuous pyramid only (`notes/decoder_bakeoff.md`),
  and then applied to all four readouts. All four decoders are in the JSON
  and the earlier ones are still reported. The published comparison was
  rerun with it on 1 Nov; the fixed-C rows are kept.
- Per-level C is chosen inside the training set, so the per-level curve is
  capacity-matched within the L2 logistic family. The remaining L3 to L6
  decline is the best any linear decoder tested can do with 40 training
  trials per image; whether a nonlinear or trial-pooled decoder would recover
  it is not tested.
- The per-scale detail analysis uses a sqrt transform on 5 ms bins and a
  single session; the synthetic checks cover planted codes of one kind at a
  time, not mixtures.

## Suggested next steps

1. Gate 2 is not met and the matched-bits baseline shows why: the bottleneck
   shape, not the learning, limits both, with the learned codes about 0.03
   ahead. If the tokenizer is to be kept, the change is architectural:
   per-unit or per-group codebooks (a code per unit per bin, or per small
   group) so the bit budget scales with the population, or codebooks in the
   thousands with product quantization. Otherwise reframe around the
   analysis, with the quantized pyramid as a drop-in tokenizer.
2. A higher area from the same session (VISal has 89 quality units, VISpm
   68, VISrl 66), then a second VISp session (794812542 has 131 VISp, 105
   VISl and 114 VISam units), with the same pyramid, jitter and per-scale
   detail pipeline, to see whether the 50 to 125 ms optimum shifts with the
   hierarchy as NeuroPixelHD reports.
3. The detail analysis's first caveat is testable: regress each level's
   detail on the whole-window count per unit before decoding, to separate
   temporal shape that covaries with rate from shape that does not.
