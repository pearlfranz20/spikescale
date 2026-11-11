# Results so far, 11 Nov 2026

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

## VISal from the same session: half the information, same scale (2 Nov 2026)

The published claim this tests is that the best bin width moves along the
sensory-to-associative hierarchy (NeuroPixelHD). Session 732592105 also has
90 VISal units passing the quality filters, so the whole pipeline (E3, E3b,
the random-CV comparison and the per-scale detail analysis) was run on them
with no new download: same window, same 118 images and 50 repeats, 60
units subsampled per seed, 5 seeds, time-blocked holdout. Chance is 0.008.
Figure: `e3_allen_732592105_VISal_n60.png`. Raw numbers:
`e3_allen_732592105_VISal_n60.json`, `external_allen_732592105_VISal.json`,
`residual_allen_732592105_VISal.json`. VISal units fire at 5.1 Hz on average
in the window against 8.5 Hz in VISp, and 24 of the 90 are below 1 Hz.

### Per-level accuracy, clean test set, nested-C cumulative decoder (VISp in brackets)

| readout | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| tokenizer codes | 0.04 [0.06] | 0.08 [0.11] | 0.11 [0.16] | 0.13 [0.19] | 0.14 [0.21] | 0.14 [0.23] |
| tokenizer reconstruction | 0.04 [0.06] | 0.08 [0.12] | 0.10 [0.15] | 0.12 [0.18] | 0.12 [0.19] | 0.11 [0.20] |
| quantized pyramid (matched bits) | 0.04 [0.04] | 0.07 [0.09] | 0.10 [0.12] | 0.12 [0.16] | 0.14 [0.18] | 0.15 [0.20] |
| continuous pyramid | 0.22 [0.40] | 0.27 [0.45] | 0.30 [0.47] | 0.30 [0.45] | 0.27 [0.41] | 0.23 [0.37] |

Seed std is 0.01 or less for the pyramid and the codes and 0.01 to 0.02 for
the quantized pyramid. Codebooks are fully used (perplexity 27 of 32 at L1,
86 to 102 of 128 at L4 to L6, slightly below VISp). Chosen C falls with
level as before (0.01 to 0.1 at L1, 0.001 at L5 to L6 for the pyramid).

**The scale is the same.** The continuous pyramid gains 0.08 to 0.09 from L1
to L3 in every seed (0.05 to 0.06 of it at L2), peaks at L3 (50 ms) with L4
within 0.01, and falls 0.05 to 0.09 to L6. That is the VISp curve at about
0.55 of the height: 0.30 against 0.47 at the peak, 0.22 against 0.40 on
whole-window counts. The relative gain from temporal structure is, if
anything, larger in VISal (L3 is 1.39 times L1, against 1.18 in VISp). The
optimum does not move to coarser bins between VISp and VISal in this session.

**Gate 2 is further from met.** The codes lead the quantized pyramid by 0.01
at L1, L2 and L4 and 0.02 at L3 (ahead in 17 of 20 seed-level pairs at L1
to L4), tie at L5 (ahead in 3 of 5) and trail by 0.01 at L6 (ahead in 2 of
5). Over all 30 seed-level pairs the codes are ahead in 22, against 29 in
VISp. The
edge the learned codes had in VISp is confined to the coarse levels here.
Both discrete readouts again keep well under half of what the continuous
pyramid decodes (0.14 against 0.30).

### E3b on VISal, continuous pyramid, nested-C cumulative decoder

| test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| clean | 0.22 | 0.27 | 0.30 | 0.30 | 0.27 | 0.23 |
| jitter 5 ms | 0.22 | 0.27 | 0.30 | 0.30 | 0.28 | 0.23 |
| jitter 10 ms | 0.22 | 0.27 | 0.31 | 0.30 | 0.27 | 0.23 |
| jitter 25 ms | 0.22 | 0.27 | 0.29 | 0.28 | 0.25 | 0.21 |
| PSTH surrogate | 0.20 | 0.25 | 0.30 | 0.29 | 0.26 | 0.21 |

Tokenizer codes: clean 0.04, 0.08, 0.11, 0.13, 0.14, 0.14; jitter 25 ms
0.04, 0.08, 0.11, 0.12, 0.13, 0.13; PSTH surrogate 0.05, 0.09, 0.12, 0.14,
0.16, 0.16.

Jitter of 5 or 10 ms changes nothing (per-seed differences of either sign
within 0.015). Jitter of 25 ms costs the pyramid 0.01 to 0.02 at L3 in four
seeds of five and about 0.02 on average at L4 to L6 (every seed loses at
L6), the same pattern and size as VISp. The PSTH-matched surrogate lowers the pyramid at L1 (0.00 to 0.04)
and L2 (0.01 to 0.03, every seed), as in VISp, but the fine-level gain VISp
showed (L4 to L6 up by 0.01 to 0.03 in every seed) is absent here: L4 to L6
move by -0.02 to +0.03 with no consistent sign. For the codes the surrogate
raises L4 to L6 by 0.01 to 0.03 in every seed, as in VISp.

### Random folds and all units (the published-comparison protocol)

Continuous pyramid, nested-C cumulative decoder (VISp in brackets):

| units | split | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | time-blocked | 0.22 [0.39] | 0.28 [0.45] | 0.31 [0.45] | 0.30 [0.44] | 0.26 [0.39] | 0.22 [0.35] |
| 60 | random 10-fold | 0.25 [0.44] | 0.31 [0.50] | 0.33 [0.52] | 0.33 [0.50] | 0.31 [0.46] | 0.27 [0.42] |
| 90 (all) | time-blocked | 0.27 [0.53] | 0.33 [0.58] | 0.37 [0.59] | 0.36 [0.57] | 0.32 [0.53] | 0.29 [0.48] |
| 90 (all) | random 10-fold | 0.31 [0.58] | 0.37 [0.62] | 0.39 [0.63] | 0.39 [0.62] | 0.36 [0.58] | 0.32 [0.54] |

Plain logistic on level-k features peaks at L2 to L3 (0.27 at 60 units
blocked, 0.31 at 90 units) and falls to 0.09 to 0.14 at L6, as in VISp. The
best level is L3 in every unit count and split, random folds add 0.02 to
0.05 over the blocked split, and going from 60 to 90 units adds 0.05 to
0.07. arXiv 2510.09451 reports no single-area VISal number to set beside
this.

### Detail of level k alone, nested-C logistic (VISp in brackets)

| units | readout | L1 (250) | L2 (125) | L3 (50) | L4 (25) | L5 (10) | L6 (5 ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 60, 5 seeds | detail alone | 0.22 [0.41] | 0.12 [0.21] | 0.11 [0.17] | 0.04 [0.07] | 0.02 [0.05] | 0.02 [0.03] |
| 60, 5 seeds | time-shuffled control | 0.22 | 0.02 | 0.01 | 0.02 | 0.01 | 0.02 |
| 60, 5 seeds | details 1 to k, cumulative | 0.22 | 0.26 | 0.25 | 0.23 | 0.14 | 0.11 |
| 90 (all) | detail alone | 0.29 [0.55] | 0.15 [0.30] | 0.14 [0.24] | 0.04 [0.11] | 0.02 [0.06] | 0.02 [0.03] |
| 90 (all) | time-shuffled control | 0.29 | 0.02 | 0.02 | 0.02 | 0.02 | 0.01 |
| 90 (all) | details 1 to k, cumulative | 0.29 | 0.31 | 0.30 | 0.28 | 0.18 | 0.12 |

Seed std is at most 0.01. Detail minus control per seed (60 units): 0.10 to
0.11 at L2, 0.10 at L3, 0.01 to 0.02 at L4, 0.00 to 0.02 at L5 (above the
control in four seeds of five) and 0.00 to 0.01 at L6.

**The same three-scale multiplexing, at half the height.** Each of the 125
and 50 ms details identifies the image on its own at about half the
rate-only level (0.54 and 0.51 of L1, against 0.51 and 0.41 in VISp), the
25 ms detail is small but above the control in every seed, the 10 ms detail
is marginal and the 5 ms detail is within the control. The cumulative
detail readout gains 0.04 from L1 to L2 in both areas. So VISal
differs from VISp in how much image information it carries, not in which
temporal scales carry it.

**What this does and does not say about the hierarchy.** VISal is one
step above VISp and this is one session; a shift the size NeuroPixelHD
reports (toward 125 ms and beyond in associative areas) would be visible
as L2 overtaking L3, and it is not seen. VISpm and VISrl from the same
session (68 and 66 units) and a second session with VISam and VISl
would extend the test further up.

## VISpm and VISrl from the same session: four areas, one scale (2 Nov 2026)

The remaining higher visual areas of session 732592105 with enough quality
units, VISpm (69 units, 7.6 Hz mean in the window, 12 below 1 Hz) and VISrl
(66 units, 6.8 Hz, 14 below 1 Hz), through the same pipeline as VISal: 60
units per seed, 5 seeds, time-blocked holdout. Figures:
`e3_allen_732592105_VISpm_n60.png`, `e3_allen_732592105_VISrl_n60.png`. Raw
numbers: the `e3_`, `external_` and `residual_allen_732592105_<area>.json`
files.

### Continuous pyramid, nested-C cumulative decoder, 60 units, time-blocked

| area | L1 | L2 | L3 | L4 | L5 | L6 | L3 minus L1, per seed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | 0.40 | 0.45 | 0.47 | 0.45 | 0.41 | 0.37 | 0.06 to 0.07 |
| VISpm | 0.38 | 0.43 | 0.45 | 0.44 | 0.40 | 0.36 | 0.05 to 0.08 |
| VISal | 0.22 | 0.27 | 0.30 | 0.30 | 0.27 | 0.23 | 0.08 to 0.09 |
| VISrl | 0.18 | 0.22 | 0.24 | 0.24 | 0.21 | 0.18 | 0.04 to 0.07 |

Seed std is 0.015 or less. In every area and every seed L3 (50 ms) is above L2 (by 0.01 to 0.03 in
VISpm and VISrl, 0.02 to 0.04 in VISal) and L4 is within 0.02 of L3 (above
it by under 0.01 in two VISrl seeds); the fall from L3 to L6 is 0.04 to
0.10.
VISpm with 60 units is within 0.02 of VISp at every level; VISal and VISrl
carry about half as much, VISrl the least.

### Discrete readouts, 60 units, nested-C cumulative decoder

| area | readout | L1 | L2 | L3 | L4 | L5 | L6 | codes ahead of quantized pyramid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISpm | tokenizer codes | 0.05 | 0.10 | 0.14 | 0.18 | 0.20 | 0.21 | 19 of 30 seed-level pairs |
| VISpm | quantized pyramid | 0.05 | 0.09 | 0.13 | 0.17 | 0.20 | 0.22 | |
| VISrl | tokenizer codes | 0.03 | 0.05 | 0.07 | 0.09 | 0.10 | 0.10 | 20 of 30 seed-level pairs |
| VISrl | quantized pyramid | 0.03 | 0.05 | 0.06 | 0.08 | 0.09 | 0.10 | |

Codebooks are fully used in both areas (perplexity 27 of 32 at L1, 101 to
119 of 128 at L4 to L6 in VISpm, 105 to 115 in VISrl). In VISpm the codes lead the quantized
pyramid by 0.01 at L2 to L4 (ahead in 4 seeds of 5 at each) and trail by
0.01 at L6; over all pairs it is a tie. In VISrl the codes lead by 0.01 at L3 to L5 and tie at L6. Across the
four areas the learned codes' edge over residual k-means at matched bits is
0.03 in VISp, 0.01 to 0.02 at the coarse levels elsewhere and nil or
negative at 5 to 10 ms, so gate 2 stays unmet everywhere.

### E3b, continuous pyramid, clean minus perturbed, mean over seeds

| area | test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISpm | jitter 25 ms | 0.00 | 0.01 | 0.01 | 0.02 | 0.02 | 0.03 |
| VISpm | PSTH surrogate | 0.05 | 0.04 | 0.01 | 0.00 | -0.02 | -0.01 |
| VISrl | jitter 25 ms | 0.00 | 0.01 | 0.01 | 0.02 | 0.02 | 0.02 |
| VISrl | PSTH surrogate | 0.01 | 0.02 | 0.01 | 0.01 | 0.00 | 0.00 |

Jitter of 5 and 10 ms changes nothing in either area (per-seed differences
within 0.01 of either sign, except 0.01 at L6 for 10 ms in VISpm). Jitter
of 25 ms costs VISpm 0.01 at L3 (every seed, 0.005 to 0.014) and 0.02 to
0.03 at L4 to L6 (every seed, up to 0.05), the same size as VISp and VISal.
VISrl loses 0.01 at L2 to L3 and 0.02 at L4 to L6 (every seed at L5 and
L6). The PSTH-matched surrogate lowers VISpm by 0.02 to 0.07
at L1 and 0.03 to 0.04 at L2 in every seed, the largest coarse-level
correlation effect of the four areas, and raises L5 by 0.00 to 0.03; for
the codes it raises every level by 0.01 to 0.02. In VISrl the surrogate lowers L1 to L4 by 0.01 to 0.02 (every seed at L1,
L2 and L4) and leaves L5 to L6 unchanged; the codes move by under 0.01.

### Random folds and all units, continuous pyramid, nested-C decoder

| area | units | split | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISpm | 60 | time-blocked | 0.39 | 0.44 | 0.46 | 0.45 | 0.41 | 0.37 |
| VISpm | 60 | random 10-fold | 0.43 | 0.48 | 0.52 | 0.50 | 0.46 | 0.41 |
| VISpm | 69 (all) | time-blocked | 0.40 | 0.45 | 0.48 | 0.46 | 0.42 | 0.39 |
| VISpm | 69 (all) | random 10-fold | 0.44 | 0.50 | 0.53 | 0.52 | 0.47 | 0.43 |
| VISrl | 60 | time-blocked | 0.19 | 0.23 | 0.25 | 0.24 | 0.22 | 0.19 |
| VISrl | 60 | random 10-fold | 0.22 | 0.26 | 0.29 | 0.28 | 0.26 | 0.22 |
| VISrl | 66 (all) | time-blocked | 0.20 | 0.23 | 0.26 | 0.26 | 0.24 | 0.20 |
| VISrl | 66 (all) | random 10-fold | 0.24 | 0.29 | 0.31 | 0.30 | 0.27 | 0.24 |

Best level L3 in every row; plain logistic peaks at L2 (0.42 to 0.48 in
VISpm). Random folds add 0.03 to 0.06 in VISpm and all 69 units add 0.01
to 0.03 over 60. In VISrl plain logistic peaks at L2 (0.22 to 0.27), random folds add 0.03 to
0.05, and all 66 units add 0.01 to 0.02.

### Detail of level k alone, 60 units, 5 seeds, nested-C logistic

| area | readout | L1 (250) | L2 (125) | L3 (50) | L4 (25) | L5 (10) | L6 (5 ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | detail alone | 0.41 | 0.21 | 0.17 | 0.07 | 0.05 | 0.03 |
| VISpm | detail alone | 0.41 | 0.16 | 0.15 | 0.05 | 0.03 | 0.02 |
| VISal | detail alone | 0.22 | 0.12 | 0.11 | 0.04 | 0.02 | 0.02 |
| VISrl | detail alone | 0.18 | 0.08 | 0.08 | 0.03 | 0.02 | 0.02 |
| all four | time-shuffled control | = L1 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 |
| VISp | detail as a share of L1 | 1 | 0.51 | 0.42 | 0.17 | 0.11 | 0.07 |
| VISpm | detail as a share of L1 | 1 | 0.38 | 0.37 | 0.12 | 0.07 | 0.04 |
| VISal | detail as a share of L1 | 1 | 0.54 | 0.51 | 0.17 | 0.10 | 0.09 |
| VISrl | detail as a share of L1 | 1 | 0.45 | 0.47 | 0.18 | 0.11 | 0.09 |

All units (69 VISpm, 66 VISrl, one seed): VISpm 0.42, 0.17, 0.16, 0.05,
0.04, 0.02; VISrl 0.20, 0.09, 0.09, 0.03, 0.02, 0.01. Detail minus control
per seed: VISpm 0.14 to 0.15 at L2, 0.12 to 0.15 at L3, 0.03 to 0.04 at L4,
0.01 to 0.02 at L5, 0.00 at L6; VISrl 0.06 to 0.07 at L2, 0.06 to 0.08 at
L3, 0.01 to 0.03 at L4, 0.00 to 0.02 at L5 (above the control in four
seeds of five), 0.00 to 0.01 at L6.

**Four areas, one temporal code.** In every area the 125 ms detail and the
50 ms detail each identify the image on their own, far above the
shuffled control; the 25 ms detail is small but above the control in every
seed; the 10 ms detail is marginal; the 5 ms detail is within the control.
The continuous pyramid peaks at 50 ms, with 25 ms within 0.02 and 125 ms
within 0.04, in every area, unit count and split. What differs
between areas is the amount of information, which runs VISp about equal to
VISpm, then VISal, then VISrl, and the balance between rate and shape:
VISpm leans most on whole-window counts (its 125 and 50 ms details are 0.38
and 0.37 of its rate-only accuracy, against 0.42 to 0.54 elsewhere), which
is the direction NeuroPixelHD's shift toward coarser bins would predict,
but the optimum itself does not move. Within this session the
sensory-to-associative shift is at most a change in the rate-to-shape
balance, not in the scale of the shape.

**What this does not settle.** All four areas come from one animal and
one session, VISpm, VISal and VISrl have fewer and sparser units than
VISp, and the higher areas sampled here are all one step above VISp in the
anatomical hierarchy. A second session with VISam and VISl (798911424; the
794812542 named here on 2 Nov is a Functional Connectivity session with no
natural scenes) would add two more areas and a second animal.

## Rate-regressed details: temporal shape that is not a linear function of rate (11 Nov 2026)

The first caveat on the detail analysis was that a level's detail can be
decodable because its shape covaries with firing rate across images, not
because the shape carries anything of its own. `residual_levels.py` now has
three readouts that test this (`--readouts detail_unitrate,detail_poprate,shuffled_unitrate --tag rate`).
Before decoding, every detail feature from level 2 on is regressed on
whole-window rate, with the regression fit on the training trials only and
applied to both splits. `detail_unitrate` regresses each unit's detail on
that unit's own rate (its L1 coefficient and the square root of its
whole-window count, plus an intercept). `detail_poprate` regresses every
detail feature on the rates of all units, the population rate vector that
on its own identifies the image at 0.41: what survives is temporal shape
that no linear function of any unit's rate predicts, a conservative bound.
`shuffled_unitrate` is the time-shuffled control after the per-unit
regression. At L1 the readouts decode the rate itself and repeat the detail
row. Raw numbers: `residual_allen_732592105_<area>_rate.json`,
`residual_rate_rate.json` and `residual_timing_p25_rate.json`.

Synthetic checks (60 units, 16 stimuli, chance 0.06): the planted rate code,
which decoded at 1.00 from the L1 detail and at 0.05 to 0.08 from the finer
details before regression, stays at 0.04 to 0.08 after it; the planted 25 ms
timing code decodes at 1.00 from the L4 and L5 details and 0.91 to 0.95 from
L6 after either regression, the same as before it. So the regression removes
nothing from a code that is purely temporal and leaves nothing of one that
is purely rate.

### Allen 732592105, 60 units, 5 seeds, nested-C logistic

| area | readout | L1 (250) | L2 (125) | L3 (50) | L4 (25) | L5 (10) | L6 (5 ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | detail alone | 0.41 | 0.21 | 0.17 | 0.07 | 0.05 | 0.03 |
| VISp | own-rate regressed | 0.41 | 0.14 | 0.11 | 0.05 | 0.04 | 0.03 |
| VISp | population-rate regressed | 0.41 | 0.11 | 0.09 | 0.04 | 0.03 | 0.03 |
| VISp | shuffled, own-rate regressed | 0.41 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 |
| VISpm | detail alone | 0.41 | 0.16 | 0.15 | 0.05 | 0.03 | 0.02 |
| VISpm | own-rate regressed | 0.41 | 0.11 | 0.09 | 0.04 | 0.02 | 0.02 |
| VISpm | population-rate regressed | 0.41 | 0.09 | 0.07 | 0.03 | 0.02 | 0.02 |
| VISpm | shuffled, own-rate regressed | 0.41 | 0.02 | 0.02 | 0.01 | 0.01 | 0.02 |
| VISal | detail alone | 0.22 | 0.12 | 0.11 | 0.04 | 0.02 | 0.02 |
| VISal | own-rate regressed | 0.22 | 0.10 | 0.09 | 0.03 | 0.02 | 0.02 |
| VISal | population-rate regressed | 0.22 | 0.08 | 0.07 | 0.03 | 0.02 | 0.02 |
| VISal | shuffled, own-rate regressed | 0.22 | 0.02 | 0.01 | 0.02 | 0.01 | 0.01 |
| VISrl | detail alone | 0.18 | 0.08 | 0.08 | 0.03 | 0.02 | 0.02 |
| VISrl | own-rate regressed | 0.18 | 0.07 | 0.07 | 0.03 | 0.02 | 0.02 |
| VISrl | population-rate regressed | 0.18 | 0.06 | 0.06 | 0.02 | 0.02 | 0.02 |
| VISrl | shuffled, own-rate regressed | 0.18 | 0.02 | 0.01 | 0.01 | 0.01 | 0.01 |

Chance is 0.008. Seed std is at most 0.02 at L1 and 0.012 elsewhere. All
units, population-rate regressed (one seed): VISp 113 units 0.55, 0.14,
0.11, 0.05, 0.04, 0.03 (detail alone 0.55, 0.30, 0.24, 0.11, 0.06, 0.03);
VISal 90 units 0.29, 0.10, 0.08, 0.02, 0.02, 0.02; VISpm 69 units 0.42,
0.09, 0.08, 0.04, 0.02, 0.02; VISrl 66 units 0.20, 0.06, 0.06, 0.02, 0.01,
0.02.

Population-rate regressed minus the control, per seed: VISp 0.07 to 0.11 at
L2, 0.06 to 0.08 at L3, 0.02 to 0.03 at L4, 0.01 to 0.02 at L5, -0.01 to
0.01 at L6; VISpm 0.07 to 0.08, 0.05 to 0.06, 0.01 to 0.02, 0.01 to 0.02,
within 0.003 of zero; VISal 0.05 to 0.07, 0.05 to 0.06, 0.00 to 0.02, 0.00
to 0.01, 0.00 to 0.01; VISrl 0.04 to 0.05, 0.04 to 0.06, 0.00 to 0.01, 0.00
to 0.01, 0.00 to 0.01.

**About half of the 125 and 50 ms detail information is a linear function of
rate; the other half is not.** Regressing on the population rate vector
leaves the L2 detail at 0.51 to 0.57 of its unregressed accuracy in VISp and
VISpm and 0.64 to 0.75 in VISal and VISrl, and the L3 detail at 0.47 to 0.57
and 0.57 to 0.73. What remains is still 7 to 13 times chance in VISp and
VISpm (0.07 to 0.11) and 7 to 10 times chance in VISal and VISrl (0.06 to
0.08), above the shuffled control in every seed of every area. So the
125 ms and 50 ms shapes carry image information that the whole-window
counts, of the unit itself or of any unit in the population, do not predict.
The 25 ms detail survives in VISp (0.02 to 0.03 above the control in every
seed) and VISpm (0.01 to 0.02), and only marginally in VISal and VISrl. The
10 ms detail is 0.01 to 0.02 above the control in every VISp seed and is
marginal elsewhere. The 5 ms detail is within the control everywhere, as
before.

**Own-rate regression removes less than population-rate regression.** The
own-rate readout is above the population-rate readout by 0.025 to 0.042 at
L2 and 0.014 to 0.026 at L3 in every VISp seed, with the same sign in VISpm
and VISal and a smaller gap (0.003 to 0.013) in VISrl. Part of a unit's
temporal shape is therefore predictable from other units' rates but not its
own, which is what image-driven covariation between a unit's shape and the
population's rate pattern looks like. The population readout is the one to
quote as unique shape information.

What this does not rule out: the regression is linear, so a shape that
depends nonlinearly on rate (a threshold, a saturating latency shift) would
pass through it. The rate here is the window count; a shape that covaries
with a unit's rate in a different window is not controlled.

## A second animal: VISp, VISl, VISal and VISam of session 798911424 (11 Nov 2026)

Brain Observatory 1.1 session 798911424, a different mouse, with 96 VISp,
78 VISl, 92 VISal and 140 VISam units passing the quality filters (5.4 to
6.6 Hz mean in the window; 12, 13, 22 and 35 units below 1 Hz). Same 118
images and 50 repeats, same pipeline as before: E3 and E3b (60 units per
seed, 5 seeds, time-blocked holdout), the random-fold and all-unit
comparison, and the per-scale detail analysis plain and rate-regressed. VISl
is new (the first session had 40 units there), VISam is new and is the
highest area in the anatomical hierarchy sampled so far, and VISal is a
replication across animals. Figures: `e3_allen_798911424_<area>_n60.png`.
Raw numbers: the `e3_`, `external_` and `residual_allen_798911424_<area>`
files. Chance is 0.008.

### Continuous pyramid, nested-C cumulative decoder, 60 units, time-blocked

| area | L1 | L2 | L3 | L4 | L5 | L6 | L3 minus L1, per seed | L3 minus L2, per seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | 0.38 | 0.45 | 0.46 | 0.44 | 0.41 | 0.35 | 0.07 to 0.08 | -0.01 to 0.03 |
| VISl | 0.39 | 0.48 | 0.50 | 0.48 | 0.45 | 0.40 | 0.09 to 0.13 | 0.01 to 0.04 |
| VISal | 0.35 | 0.44 | 0.46 | 0.45 | 0.41 | 0.36 | 0.08 to 0.15 | 0.02 to 0.04 |
| VISam | 0.14 | 0.19 | 0.20 | 0.19 | 0.17 | 0.13 | 0.05 to 0.07 | 0.00 to 0.03 |

Seed std is at most 0.03 (VISp and VISal), 0.014 in VISam. L4 is below L3
by 0.00 to 0.03 in every area and seed, and the fall from L3 to L6 is 0.06
to 0.12. Chosen C falls with level as before (0.03 to 0.1 at L1, 0.001 at
L5 to L6).

### Random folds and all units, continuous pyramid, nested-C decoder

| area | units | split | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | 60 | time-blocked | 0.36 | 0.42 | 0.45 | 0.43 | 0.39 | 0.33 |
| VISp | 60 | random 10-fold | 0.41 | 0.49 | 0.51 | 0.49 | 0.46 | 0.41 |
| VISp | 96 (all) | time-blocked | 0.51 | 0.58 | 0.60 | 0.56 | 0.53 | 0.46 |
| VISp | 96 (all) | random 10-fold | 0.57 | 0.64 | 0.65 | 0.62 | 0.59 | 0.53 |
| VISl | 60 | time-blocked | 0.40 | 0.49 | 0.51 | 0.51 | 0.47 | 0.42 |
| VISl | 60 | random 10-fold | 0.43 | 0.52 | 0.55 | 0.54 | 0.51 | 0.46 |
| VISl | 78 (all) | time-blocked | 0.46 | 0.53 | 0.56 | 0.55 | 0.51 | 0.47 |
| VISl | 78 (all) | random 10-fold | 0.48 | 0.57 | 0.60 | 0.59 | 0.56 | 0.50 |
| VISal | 60 | time-blocked | 0.32 | 0.41 | 0.43 | 0.43 | 0.38 | 0.34 |
| VISal | 60 | random 10-fold | 0.36 | 0.45 | 0.48 | 0.46 | 0.43 | 0.38 |
| VISal | 92 (all) | time-blocked | 0.48 | 0.57 | 0.58 | 0.57 | 0.53 | 0.45 |
| VISal | 92 (all) | random 10-fold | 0.50 | 0.59 | 0.62 | 0.60 | 0.56 | 0.51 |
| VISam | 60 | time-blocked | 0.14 | 0.19 | 0.19 | 0.18 | 0.16 | 0.13 |
| VISam | 60 | random 10-fold | 0.16 | 0.22 | 0.23 | 0.21 | 0.20 | 0.16 |
| VISam | 140 (all) | time-blocked | 0.25 | 0.32 | 0.34 | 0.32 | 0.28 | 0.24 |
| VISam | 140 (all) | random 10-fold | 0.29 | 0.38 | 0.41 | 0.39 | 0.34 | 0.29 |

Best level L3 in every row (L2 ties it in VISam at 60 units, blocked). Under
the published protocol (all units, random folds) this animal's VISp reaches
0.65, again above the 0.31 to 0.55 range of the seven sessions in
arXiv 2510.09451, and its VISl and VISal reach 0.60 and 0.62.

**The scale replicates in a second animal.** In all four areas the pyramid
peaks at 50 ms, with 125 ms within 0.01 to 0.03 and 25 ms within 0.02, in
every unit count and split, as in the four areas of the first animal. The
50 ms level is above the 125 ms level in every VISl and VISal seed and in
four VISam seeds of five; in this animal's VISp the two are tied (L3 minus
L2 of -0.01 to 0.03 across seeds), where the first animal's VISp had L3
ahead by 0.01 to 0.03. Eight area samples in two mice now put the optimum
at 50 ms with 125 ms close behind, and none puts it at 25 ms or finer.

**The amount is not consistent across animals; the scale is.** In the first
mouse VISal carried about half of VISp's information at 60 units. Here VISal
matches VISp (0.46 against 0.46 at L3) and VISl is above both (0.50). VISam
is far below (0.20 at 60 units, 0.34 with all 140), with a quarter of its
units under 1 Hz. Which higher area is rich and which is sparse therefore
depends on the penetration (depth, receptive-field coverage of the
monitor, unit yield), and between-area differences in amount within one
session should not be read as properties of the areas. The temporal
profile, by contrast, has been the same in all eight samples.

### Discrete readouts, 60 units, nested-C cumulative decoder

| area | readout | L1 | L2 | L3 | L4 | L5 | L6 | codes ahead of quantized pyramid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | tokenizer codes | 0.07 | 0.13 | 0.17 | 0.21 | 0.23 | 0.24 | 28 of 30 seed-level pairs |
| VISp | quantized pyramid | 0.05 | 0.10 | 0.13 | 0.17 | 0.21 | 0.23 | |
| VISl | tokenizer codes | 0.06 | 0.13 | 0.19 | 0.22 | 0.25 | 0.25 | 24 of 30 |
| VISl | quantized pyramid | 0.05 | 0.11 | 0.16 | 0.19 | 0.24 | 0.27 | |
| VISal | tokenizer codes | 0.05 | 0.11 | 0.15 | 0.18 | 0.21 | 0.21 | 13 of 30 |
| VISal | quantized pyramid | 0.04 | 0.11 | 0.15 | 0.19 | 0.22 | 0.25 | |
| VISam | tokenizer codes | 0.02 | 0.05 | 0.06 | 0.07 | 0.08 | 0.07 | 8 of 30 |
| VISam | quantized pyramid | 0.02 | 0.04 | 0.07 | 0.08 | 0.09 | 0.10 | |

The reconstruction readout tracks the codes to within 0.03 everywhere. In
VISp the codes lead residual k-means by 0.02 to 0.04 at L1 to L5 (every
seed) and 0.01 at L6, the same edge as the first animal's VISp. In VISl they
lead by 0.01 to 0.03 at L1 to L5 and trail by 0.02 at L6 in every seed. In
VISal they lead by 0.01 at L1 and trail by 0.00 to 0.04 from L2 on, and in
VISam they trail from L3 on, by 0.03 at L6. Both discrete readouts again
keep under half of what the pyramid decodes (0.24 against 0.46 in VISp).

**Gate 2 across two animals.** The learned codes' edge over k-means at
matched bits is 0.03 in both VISp samples and 0.01 to 0.02 at the coarse
levels of VISpm, VISrl and VISl; it is nil in both VISal samples and
negative at 5 to 10 ms in VISal and VISam, where k-means wins by 0.02 to
0.04. The pattern is that learned codes help where the population is rich
and the level coarse, and residual k-means catches up or wins as the bins
get fine and the counts sparse. Gate 2 remains unmet in all eight samples.

### E3b, continuous pyramid, clean minus perturbed, mean over seeds

| area | test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | jitter 25 ms | 0.00 | 0.00 | 0.02 | 0.02 | 0.02 | 0.02 |
| VISp | PSTH surrogate | 0.03 | 0.00 | -0.01 | -0.01 | -0.03 | -0.02 |
| VISl | jitter 25 ms | 0.00 | 0.01 | 0.01 | 0.02 | 0.03 | 0.04 |
| VISl | PSTH surrogate | 0.03 | 0.03 | 0.01 | 0.00 | -0.01 | 0.00 |
| VISal | jitter 25 ms | 0.00 | 0.01 | 0.02 | 0.03 | 0.04 | 0.04 |
| VISal | PSTH surrogate | 0.02 | 0.01 | -0.01 | -0.01 | -0.02 | -0.02 |
| VISam | jitter 25 ms | 0.00 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |
| VISam | PSTH surrogate | 0.02 | 0.02 | 0.03 | 0.01 | 0.00 | 0.01 |

Jitter of 5 ms changes nothing anywhere (per-seed differences of either
sign within 0.02). Jitter of 10 ms costs 0.01 at L5 to L6 in VISp and VISl
(every seed at L6) and nothing elsewhere. Jitter of 25 ms costs 0.01 to
0.02 at L3 and 0.02 to 0.04 at L4 to L6 in VISp, VISl and VISal, every seed
from L4 on, a little more at the fine levels than the first animal's 0.02 to
0.03; in VISam it costs 0.01 throughout. So, as before, there is a small
amount of decodable timing between 10 and 25 ms, and the best level loses
0.01 to 0.02 of it.

The PSTH-matched surrogate lowers L1 by 0.02 to 0.03 in every area and
every seed, as in the first animal: noise correlations help whole-window
counts. Its effect at fine levels differs by area as it did before: it
raises VISp by 0.02 to 0.03 at L5 to L6 (every seed, as in the first
animal's VISp), VISal by 0.01 to 0.02 at L4 to L6, leaves VISl unchanged
from L4 on, and lowers VISam by 0.02 to 0.03 at L1 to L3 with no gain at
any level. For the codes the surrogate raises accuracy by 0.01 to 0.03 at
L3 to L6 in VISp, VISl and VISal, as before.

### Detail of level k alone, 60 units, 5 seeds, nested-C logistic

| area | readout | L1 (250) | L2 (125) | L3 (50) | L4 (25) | L5 (10) | L6 (5 ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | detail alone | 0.38 | 0.21 | 0.15 | 0.06 | 0.05 | 0.03 |
| VISp | population-rate regressed | 0.38 | 0.13 | 0.08 | 0.04 | 0.03 | 0.02 |
| VISl | detail alone | 0.37 | 0.20 | 0.18 | 0.06 | 0.03 | 0.03 |
| VISl | population-rate regressed | 0.37 | 0.12 | 0.10 | 0.03 | 0.03 | 0.02 |
| VISal | detail alone | 0.36 | 0.20 | 0.17 | 0.06 | 0.03 | 0.02 |
| VISal | population-rate regressed | 0.36 | 0.13 | 0.10 | 0.04 | 0.02 | 0.02 |
| VISam | detail alone | 0.14 | 0.10 | 0.07 | 0.02 | 0.02 | 0.02 |
| VISam | population-rate regressed | 0.14 | 0.08 | 0.05 | 0.02 | 0.02 | 0.02 |
| all four | time-shuffled controls | = L1 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 |
| VISp | detail as a share of L1 | 1 | 0.55 | 0.40 | 0.16 | 0.12 | 0.07 |
| VISl | detail as a share of L1 | 1 | 0.53 | 0.48 | 0.15 | 0.09 | 0.07 |
| VISal | detail as a share of L1 | 1 | 0.55 | 0.47 | 0.15 | 0.08 | 0.06 |
| VISam | detail as a share of L1 | 1 | 0.72 | 0.45 | 0.14 | 0.14 | 0.11 |

Seed std is at most 0.03 at L1 and 0.02 elsewhere. All units, detail alone
(one seed): VISp 96 units 0.49, 0.30, 0.21, 0.08, 0.05, 0.03; VISl 78 units
0.44, 0.24, 0.21, 0.06, 0.04, 0.02; VISal 92 units 0.48, 0.26, 0.23, 0.06,
0.03, 0.02; VISam 140 units 0.26, 0.19, 0.09, 0.03, 0.02, 0.02. Detail minus
control per seed: VISp 0.17 to 0.21 at L2, 0.12 to 0.14 at L3, 0.03 to 0.06
at L4, 0.02 to 0.03 at L5, 0.00 to 0.02 at L6; VISl 0.17 to 0.19, 0.15 to
0.17, 0.03 to 0.05, 0.01 to 0.03, 0.00 to 0.01; VISal 0.15 to 0.21, 0.14 to
0.18, 0.02 to 0.04, 0.01 to 0.02, 0.00 to 0.01; VISam 0.08 to 0.11, 0.04 to
0.06, 0.01, 0.00 to 0.01, 0.00. Population-rate regressed minus control:
VISp 0.09 to 0.13 at L2 and 0.05 to 0.07 at L3; VISl 0.10 to 0.12 and 0.08
to 0.09; VISal 0.10 to 0.13 and 0.07 to 0.09; VISam 0.05 to 0.08 and 0.03
to 0.04; 0.01 to 0.03 at L4 in VISp, VISl and VISal and 0.00 to 0.01
elsewhere and at finer levels.

**The three-scale multiplexing replicates, and half of it again survives
rate regression.** In every area of the second animal the 125 ms and 50 ms
details each identify the image alone, far above the shuffled control in
every seed; the 25 ms detail is small but above the control in every seed
of VISp, VISl and VISal; the 10 ms detail is marginal (above the control in
every VISp seed, by 0.02 to 0.03); the 5 ms detail is within the control.
Regressing on the population rate vector leaves the L2 detail at 0.60 to
0.64 and the L3 detail at 0.53 to 0.56 of its accuracy in VISp, VISl and
VISal, the same fractions as the first animal (0.51 to 0.75), and 0.75 and
0.72 in VISam.

**VISam leans on the 125 ms shape.** Its 125 ms detail is 0.72 of its
rate-only accuracy, against 0.53 to 0.55 in the other three areas of this
animal and 0.38 to 0.54 in the first animal, and its 50 ms detail is 0.62
of its 125 ms detail, against 0.73 to 0.91 here and 0.81 to 1.0 in the first
animal. Its rate-regressed details also keep a larger share (0.72 to 0.75
against 0.53 to 0.64), so the 125 ms shape in VISam is less a correlate of
rate than elsewhere. In the pyramid the optimum is still at 50 ms, with
125 ms tied at 60 units, so the hierarchy effect NeuroPixelHD reports shows
up here, in the one area two steps above VISp, as a tilt in the balance of
the details toward the coarser shape, not as a move of the best bin width.
Together with VISpm's tilt toward rate in the first animal, the higher areas
sampled lean coarser in what carries the information while the 50 to
125 ms scale itself stays put.

**What this does not settle.** Two animals and eight area samples, with
VISam seen once and VISpm and VISrl once each. VISam's low accuracy mixes
area with a sparse penetration (35 of 140 units under 1 Hz). The
sensory-to-associative comparison would need VISam in a second animal and
areas beyond the visual cortex (LP and LGd are available in several
sessions) to say whether the tilt grows with hierarchical distance.

## Caveats

- Synthetic codes are easy (the continuous pyramid is at 1.00), so they test
  localization better than retention.
- 60 epochs on CPU, 2 synthetic seeds and 5 real-data unit subsamples. Not tuned.
- Two Allen sessions, one per animal, eight area samples. The published
  comparison is against seven other sessions' distribution, not the same
  sessions.
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
  time, not mixtures. The rate regression is linear and uses the window
  count only.
- The 125 and 50 ms details are, in large part, old quantities in new
  coordinates. The level-2 detail of a unit is its second-half minus
  first-half count, so it measures how transient or sustained the response
  is; the level-3 detail (the 50 ms profile with the whole-window and
  half-window means removed) is dominated by where in the window the response
  rises, that is, by onset latency. Image information in response latency and
  in the transient-to-sustained ratio is well established (first-spike
  latency in retina, Gollisch and Meister 2008; temporal waveform coding in
  IT and V1, Optican and Richmond 1987, Reich, Mechler and Victor 2001).
  What this analysis adds is the population scale, the matched-capacity
  decoder, the time-shuffled control and the rate regression, not the
  existence of a latency or transience code. A readout built from an
  explicit per-unit latency estimate would say how much of the level-2 and
  level-3 detail is latency alone; it has not been run.
- The comparison across areas is within two sessions (one per animal);
  the amount of information per area varies with the penetration (VISal is
  half of VISp in one animal and equal to it in the other), so between-area
  differences in amount mix area and sampling. VISam, VISpm and VISrl were
  each seen in one animal.

## Suggested next steps

1. Gate 2 is not met and the matched-bits baseline shows why: the bottleneck
   shape, not the learning, limits both, with the learned codes about 0.03
   ahead. If the tokenizer is to be kept, the change is architectural:
   per-unit or per-group codebooks (a code per unit per bin, or per small
   group) so the bit budget scales with the population, or codebooks in the
   thousands with product quantization. Otherwise reframe around the
   analysis, with the quantized pyramid as a drop-in tokenizer.
2. Done on 11 Nov 2026 (session 798911424, a second animal): the 50 ms
   optimum, the three-scale multiplexing and the rate-regression result
   replicate in VISp, VISl, VISal and VISam. VISam tilts toward the 125 ms
   shape without moving the optimum. The next step up the hierarchy is
   VISam in a second animal and the thalamic areas (LP, LGd) that several
   Brain Observatory 1.1 sessions carry, to see whether the tilt grows with
   hierarchical distance, and whether LGd, below VISp, tilts the other way.
3. Done on 11 Nov 2026 (rate-regressed details): about half of the 125 and
   50 ms detail information survives regression on the population rate
   vector. A nonlinear version (regress on rate with a flexible model, or
   decode detail within rate-matched trial strata) would close the
   remaining gap.
