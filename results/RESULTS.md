# Results so far, 11 Nov 2026

`summary.png` (from `scripts/plot_summary.py`) draws the sixteen area samples
together: the pyramid relative to its 50 ms level, each level's detail as a
share of the count, the 125 and 50 ms details before and after rate and
timing regression, the 10 ms jitter cost, and learned codes against k-means.

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

## Below and beside the cortex: VISp, LGd and LP of session 754829445 (11 Nov 2026)

Brain Observatory 1.1 session 754829445, a third mouse, with 95 VISp, 90 LGd
and 170 LP units passing the quality filters (6.9, 10.9 and 7.9 Hz mean in
the window; 15, 1 and 9 units below 1 Hz). LGd is the dorsal lateral
geniculate, the thalamic relay one step below VISp; LP is the lateral
posterior nucleus, the higher-order visual thalamus that sits beside the
cortical hierarchy and exchanges projections with its upper areas. Same
pipeline as the other two animals: E3 and E3b (60 units per seed, 5 seeds,
time-blocked holdout), the random-fold and all-unit comparison, and the
per-scale detail analysis plain and rate-regressed. Figures:
`e3_allen_754829445_<area>_n60.png`. Raw numbers: the `e3_`, `external_` and
`residual_allen_754829445_<area>` files. Chance is 0.008.

### Continuous pyramid, nested-C cumulative decoder, 60 units, time-blocked

| area | L1 | L2 | L3 | L4 | L5 | L6 | L3 minus L1, per seed | L3 minus L2, per seed | L3 minus L6, per seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | 0.38 | 0.44 | 0.46 | 0.45 | 0.42 | 0.38 | 0.07 to 0.10 | 0.01 to 0.03 | 0.08 to 0.10 |
| LGd | 0.35 | 0.41 | 0.45 | 0.45 | 0.43 | 0.41 | 0.08 to 0.10 | 0.03 to 0.05 | 0.01 to 0.05 |
| LP | 0.10 | 0.14 | 0.16 | 0.16 | 0.16 | 0.13 | 0.05 to 0.07 | 0.01 to 0.03 | 0.02 to 0.03 |

Seed std is at most 0.02 in VISp and LP and 0.03 to 0.04 in LGd. The best
level is L3 in every VISp seed; in LGd it is L4 in three seeds and L3 in two
(L4 minus L3 of 0.00 to 0.01); in LP it is L3, L4 or L5 (within 0.01 of
each other). Chosen C falls with level as before.

### Random folds and all units, continuous pyramid, nested-C decoder

| area | units | split | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | 60 | time-blocked | 0.36 | 0.44 | 0.46 | 0.45 | 0.41 | 0.37 |
| VISp | 60 | random 10-fold | 0.52 | 0.59 | 0.62 | 0.62 | 0.58 | 0.52 |
| VISp | 95 (all) | time-blocked | 0.50 | 0.56 | 0.56 | 0.55 | 0.52 | 0.48 |
| VISp | 95 (all) | random 10-fold | 0.67 | 0.72 | 0.73 | 0.72 | 0.69 | 0.64 |
| LGd | 60 | time-blocked | 0.31 | 0.38 | 0.41 | 0.42 | 0.40 | 0.37 |
| LGd | 60 | random 10-fold | 0.55 | 0.61 | 0.66 | 0.66 | 0.64 | 0.61 |
| LGd | 90 (all) | time-blocked | 0.49 | 0.54 | 0.56 | 0.55 | 0.55 | 0.53 |
| LGd | 90 (all) | random 10-fold | 0.73 | 0.77 | 0.80 | 0.80 | 0.79 | 0.77 |
| LP | 60 | time-blocked | 0.12 | 0.16 | 0.19 | 0.19 | 0.18 | 0.16 |
| LP | 60 | random 10-fold | 0.17 | 0.24 | 0.29 | 0.29 | 0.28 | 0.22 |
| LP | 170 (all) | time-blocked | 0.22 | 0.30 | 0.35 | 0.35 | 0.31 | 0.29 |
| LP | 170 (all) | random 10-fold | 0.34 | 0.44 | 0.50 | 0.50 | 0.47 | 0.40 |

Under the published protocol (all units, random folds) this animal's VISp
reaches 0.73, the highest of the three VISp samples and again above the
0.31 to 0.55 range of arXiv 2510.09451. LGd reaches 0.80 with 90 units, more
than any cortical sample: the relay identifies the image better per unit
than the cortex above it, at double the firing rate.

**Random folds inflate more in this session.** Random 10-fold is above the
time-blocked split by 0.16 in VISp and 0.25 in LGd at 60 units, against 0.03
to 0.06 in every area of the first two animals. Slow drift over the session
(the stimulus order is fixed, so neighbouring trials in time share state)
is evidently stronger in this recording, and the random-fold numbers lean
on it. The time-blocked split is the one the conclusions rest on; the
published comparison is reported for the protocol, not the estimate.

**VISp, third animal: the same profile.** The pyramid peaks at 50 ms with
125 ms within 0.01 to 0.03 in every seed and 25 ms within 0.02, and the
fall to 5 ms is 0.08 to 0.10. Three VISp samples from three mice now agree
on every number in this table to within 0.02.

**LGd tilts finer, as the hierarchy predicts.** The optimum is shared
between 50 and 25 ms (L4 wins three seeds, L3 two), 10 ms is within 0.02
and 5 ms within 0.04 of the best level, against 0.08 to 0.10 in the VISp
above it. The 5 ms level still decodes 0.41, above the whole-window count
(0.35) by 0.06. So the relay's code sits at 25 to 50 ms, one level finer
than the cortex, and it keeps more of its information down to 5 ms bins.

### Discrete readouts, 60 units, nested-C cumulative decoder

| area | readout | L1 | L2 | L3 | L4 | L5 | L6 | codes ahead of quantized pyramid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | tokenizer codes | 0.05 | 0.10 | 0.14 | 0.17 | 0.20 | 0.22 | 23 of 30 seed-level pairs |
| VISp | quantized pyramid | 0.04 | 0.09 | 0.13 | 0.16 | 0.19 | 0.21 | |
| LGd | tokenizer codes | 0.03 | 0.07 | 0.11 | 0.15 | 0.18 | 0.21 | 10 of 30 |
| LGd | quantized pyramid | 0.04 | 0.08 | 0.11 | 0.15 | 0.20 | 0.25 | |
| LP | tokenizer codes | 0.01 | 0.02 | 0.04 | 0.05 | 0.06 | 0.07 | 5 of 30 |
| LP | quantized pyramid | 0.02 | 0.02 | 0.04 | 0.05 | 0.07 | 0.08 | |

The reconstruction readout is within 0.04 of the codes everywhere. In VISp
the codes lead residual k-means by 0.01 to 0.03 on average (per seed -0.02
to 0.04), the third VISp sample with the same small edge. In LGd k-means
wins from L5 on, by 0.02 to 0.06 at L6 in every seed, and in LP k-means is
level or ahead at every level. Both discrete readouts again keep under half
of what the pyramid decodes (0.22 against 0.46 in VISp, 0.25 against 0.45
in LGd). Gate 2 is unmet in all eleven samples, and the pattern from the
first two animals holds: learned codes help only in rich cortex at coarse
levels, and the finer and sparser the bins, the more k-means wins.

### E3b, continuous pyramid, clean minus perturbed, mean over seeds

| area | test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | jitter 10 ms | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.01 |
| VISp | jitter 25 ms | 0.00 | 0.01 | 0.01 | 0.02 | 0.03 | 0.03 |
| VISp | PSTH surrogate | 0.03 | 0.04 | 0.01 | -0.01 | -0.02 | -0.01 |
| LGd | jitter 10 ms | 0.00 | 0.00 | 0.00 | 0.01 | 0.02 | 0.02 |
| LGd | jitter 25 ms | 0.00 | 0.00 | 0.01 | 0.02 | 0.03 | 0.04 |
| LGd | PSTH surrogate | 0.05 | 0.05 | 0.02 | 0.01 | 0.00 | 0.00 |
| LP | jitter 10 ms | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.01 |
| LP | jitter 25 ms | 0.00 | 0.00 | 0.01 | 0.01 | 0.02 | 0.02 |
| LP | PSTH surrogate | 0.01 | 0.02 | 0.01 | 0.01 | 0.01 | 0.01 |

Jitter of 5 ms changes nothing in any area (per-seed differences within
0.02 of either sign). Jitter of 10 ms costs 0.01 to 0.02 at L5 to L6 in
every LGd seed, 0.01 at L6 in VISp, and nothing in LP. Jitter of 25 ms
costs LGd 0.02 to 0.05 at L4 to L6 in every seed and VISp 0.01 to 0.04 from
L3 on, the same as the earlier VISp samples. So LGd is the first area where
10 ms jitter has a reliable cost, consistent with its flatter pyramid.

The PSTH-matched surrogate lowers whole-window counts by 0.03 in VISp and
0.05 in LGd (0.02 to 0.08 per seed), and 125 ms counts by about the same;
noise correlations help the coarse readouts more in the relay than in any
cortical sample (0.02 to 0.03 before). It raises VISp's fine levels by 0.01
to 0.02 as in the other two animals' VISp, and does nothing to LGd or LP
from L4 on. For the codes the surrogate raises VISp by 0.01 to 0.02 at L2
to L6 and leaves LGd and LP unchanged.

### Detail of level k alone, 60 units, 5 seeds, nested-C logistic

| area | readout | L1 (250) | L2 (125) | L3 (50) | L4 (25) | L5 (10) | L6 (5 ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | detail alone | 0.38 | 0.18 | 0.19 | 0.05 | 0.04 | 0.02 |
| VISp | population-rate regressed | 0.38 | 0.11 | 0.09 | 0.04 | 0.03 | 0.02 |
| LGd | detail alone | 0.34 | 0.12 | 0.16 | 0.08 | 0.03 | 0.02 |
| LGd | population-rate regressed | 0.34 | 0.06 | 0.07 | 0.04 | 0.02 | 0.02 |
| LP | detail alone | 0.09 | 0.06 | 0.07 | 0.03 | 0.01 | 0.01 |
| LP | population-rate regressed | 0.09 | 0.05 | 0.05 | 0.02 | 0.01 | 0.01 |
| all three | time-shuffled controls | = L1 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 | 0.01 | 0.01 |
| VISp | detail as a share of L1 | 1 | 0.49 | 0.51 | 0.14 | 0.09 | 0.06 |
| LGd | detail as a share of L1 | 1 | 0.37 | 0.46 | 0.22 | 0.10 | 0.06 |
| LP | detail as a share of L1 | 1 | 0.59 | 0.74 | 0.27 | 0.15 | 0.12 |

Seed std is at most 0.03 at L1 and 0.02 elsewhere. All units, detail alone
(one seed): VISp 95 units 0.49, 0.28, 0.26, 0.07, 0.04, 0.02; LGd 90 units
0.46, 0.18, 0.21, 0.11, 0.06, 0.02; LP 170 units 0.22, 0.14, 0.13, 0.04,
0.02, 0.01. Detail minus control per seed: VISp 0.16 to 0.19 at L2, 0.14 to
0.19 at L3, 0.03 to 0.05 at L4, 0.01 to 0.03 at L5, 0.00 to 0.01 at L6; LGd
0.10 to 0.13, 0.12 to 0.17, 0.04 to 0.07, 0.01 to 0.04, 0.00 to 0.02; LP
0.04 to 0.06, 0.05 to 0.09, 0.01 to 0.02, 0.00 to 0.01, -0.01 to 0.00.
Population-rate regressed minus control: VISp 0.08 to 0.10 at L2, 0.06 to
0.08 at L3, 0.01 to 0.04 at L4; LGd 0.04 to 0.07, 0.05 to 0.08, 0.02 to
0.03; LP 0.03 to 0.04, 0.03 to 0.04, 0.00 to 0.01. The per-unit rate
regression keeps more than the population one, as before (VISp 0.14 and
0.12 at L2 and L3, LGd 0.08 and 0.10, LP 0.05 and 0.05).

**VISp, third animal: the same multiplexing.** The 125 and 50 ms details
each decode at about half the rate-only accuracy (0.49 and 0.51 of L1; the
first two animals' VISp gave 0.51 and 0.42, and 0.55 and 0.40), the 25 ms
detail is small and above
the control in every seed, the 10 ms detail marginal, the 5 ms detail
within the control. Regressing on the population rate vector leaves 0.58
and 0.49 of the L2 and L3 details, inside the 0.51 to 0.75 of the other
samples.

**The balance of the shapes runs with the hierarchy** (revised in the next
section: the VISam end of this gradient did not replicate). Take the ratio of
the 50 ms detail to the 125 ms detail as the index of how fine the shape
information is. It is 1.26 in LGd, 0.73 to 1.05 in the eight cortical
samples of VISp, VISl, VISal, VISrl and VISpm (1.04 in this animal's VISp),
and 0.62 in VISam. The 25 ms detail's share of the rate-only accuracy tells
the same story at the next level: 0.22 in LGd against 0.12 to 0.18 in every
cortical sample. LGd's 125 ms share (0.37) is as low as any cortical
sample's (0.38 to 0.55), where VISam's is 0.72.
So the direction predicted from the first two animals holds: the relay
below VISp tilts toward the finer shapes exactly as VISam above it tilts
toward the coarser one, while the best single bin width moves only one
level, from 50 ms in cortex to a 25 to 50 ms tie in LGd. The gradient is a
redistribution of information between the 125, 50 and 25 ms shapes along
the pathway, with the scale band itself fixed at 25 to 125 ms from thalamus
to the highest cortical area sampled.

**LP looks thalamic, not high.** LP carries little image information at 60
units (0.16; 0.35 with all 170, 0.50 under random folds), consistent with
its weak and broad visual selectivity. What it carries is distributed like
LGd's rather than VISam's: the pyramid is flat from 50 to 10 ms, the 50 ms
detail is 1.26 times the 125 ms detail, and the 25 ms detail is 0.27 of
the rate-only accuracy, the highest share of any area. Its position in the
hierarchy (it projects to and from the higher visual areas) would have
predicted a VISam-like tilt toward 125 ms; it shows the opposite. The
numbers behind these shares are small (0.03 to 0.07 against a control of
0.01, each above the control in every seed at L2 and L3 and in four of
five at L4), so the direction is reliable and the magnitudes are not, and
60 of 170 units is a thin sample of a nucleus with heterogeneous
subdivisions. A reading that fits is that the temporal structure of the
code reflects the input (retinal and collicular for LGd and much of LP;
cortical for VISam) rather than hierarchical rank.

**What this does not settle.** One sample each of LGd and LP, in one animal,
and VISam still seen once. The LGd and VISam tilts are each a single
penetration, and the hierarchy reading needs both in a second animal
before it is more than a consistent pattern across eleven samples. The
random-fold inflation in this session (0.16 to 0.25 against 0.03 to 0.06
before) says that slow state is strong here; the time-blocked split
guards the main numbers against it, but a state covariate (running,
pupil) in the regression would be the direct check.

## LGd and VISam in one animal: session 763673393 (11 Nov 2026)

Brain Observatory 1.1 session 763673393, a fourth mouse, chosen because it
carries both ends of the gradient suggested by the third animal: 74 VISp,
77 VISam and 78 LGd units pass the quality filters (8.5, 7.6 and 11.1 Hz
mean in the window; 4, 8 and 4 units below 1 Hz). Same pipeline. Figures:
`e3_allen_763673393_<area>_n60.png`. Raw numbers: the `e3_`, `external_`
and `residual_allen_763673393_<area>` files. Chance is 0.008.

### Continuous pyramid, nested-C cumulative decoder, 60 units, time-blocked

| area | L1 | L2 | L3 | L4 | L5 | L6 | L3 minus L1, per seed | L3 minus L2, per seed | L3 minus L6, per seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | 0.54 | 0.60 | 0.62 | 0.60 | 0.56 | 0.50 | 0.08 to 0.09 | 0.02 to 0.03 | 0.11 to 0.13 |
| VISam | 0.33 | 0.41 | 0.44 | 0.43 | 0.41 | 0.35 | 0.09 to 0.13 | 0.02 to 0.04 | 0.09 to 0.11 |
| LGd | 0.57 | 0.65 | 0.69 | 0.70 | 0.69 | 0.66 | 0.09 to 0.14 | 0.03 to 0.05 | 0.01 to 0.05 |

Seed std is at most 0.03. The best level is L3 in every VISp and VISam
seed and L4 in every LGd seed (L4 minus L3 of 0.00 to 0.01). This is the
richest session so far: its VISp decodes 0.62 at 60 units where the other
three VISp samples gave 0.46 to 0.47, and its VISam decodes 0.44 where the
first VISam gave 0.20.

### Random folds and all units, continuous pyramid, nested-C decoder

| area | units | split | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | 60 | time-blocked | 0.54 | 0.59 | 0.63 | 0.61 | 0.57 | 0.52 |
| VISp | 60 | random 10-fold | 0.54 | 0.59 | 0.61 | 0.60 | 0.57 | 0.53 |
| VISp | 74 (all) | time-blocked | 0.57 | 0.64 | 0.65 | 0.65 | 0.60 | 0.55 |
| VISp | 74 (all) | random 10-fold | 0.58 | 0.63 | 0.65 | 0.64 | 0.60 | 0.57 |
| VISam | 60 | time-blocked | 0.31 | 0.38 | 0.40 | 0.39 | 0.36 | 0.31 |
| VISam | 60 | random 10-fold | 0.34 | 0.42 | 0.44 | 0.43 | 0.40 | 0.34 |
| VISam | 77 (all) | time-blocked | 0.39 | 0.47 | 0.52 | 0.50 | 0.47 | 0.41 |
| VISam | 77 (all) | random 10-fold | 0.43 | 0.52 | 0.54 | 0.53 | 0.49 | 0.44 |
| LGd | 60 | time-blocked | 0.55 | 0.63 | 0.68 | 0.68 | 0.67 | 0.63 |
| LGd | 60 | random 10-fold | 0.55 | 0.61 | 0.66 | 0.67 | 0.65 | 0.62 |
| LGd | 78 (all) | time-blocked | 0.66 | 0.73 | 0.76 | 0.77 | 0.75 | 0.74 |
| LGd | 78 (all) | random 10-fold | 0.66 | 0.71 | 0.75 | 0.76 | 0.74 | 0.72 |

Random folds add nothing here (within 0.02 of the time-blocked split, of
either sign), against 0.16 to 0.25 in the third animal and 0.03 to 0.06 in
the first two. Slow drift is a property of the recording, not of the
protocol, and the random-fold estimate is unreliable by an amount that
cannot be known without the blocked split beside it. Under the published
protocol this VISp reaches 0.65 and LGd 0.76 with 78 units.

**VISp, fourth animal: the same profile at a higher level.** 50 ms optimum
in every seed, 125 ms within 0.03, 25 ms within 0.02, a fall of 0.11 to
0.13 to 5 ms, and the 125 and 50 ms details at 0.49 and 0.37 of rate-only
accuracy (four VISp samples: 0.49 to 0.55 and 0.37 to 0.51). The richer
population changes the amount and nothing about where it sits in time.

**LGd's finer scale replicates.** The optimum is at 25 ms in every seed
(the first LGd split 50 and 25 ms), 10 ms is within 0.01 and 5 ms within
0.05 of it, and the 5 ms level decodes 0.66, above the whole-window count
by 0.09. Two LGd samples from two animals now agree: the relay's code is a
level finer than the cortex above it, and holds its information down to
5 ms bins where cortex loses 0.06 to 0.13.

**VISam's tilt toward 125 ms does not replicate.** This VISam has the
cortical profile exactly: 50 ms optimum in every seed, 125 ms within 0.04,
details at 0.53 and 0.46 of rate-only accuracy with the 50 ms detail at
0.86 of the 125 ms detail, against 0.72, 0.45 and 0.62 in the first VISam.
It is indistinguishable from VISp, VISl and VISal. The first VISam sample
was the sparsest in the study (0.20 at 60 units, a quarter of its units
under 1 Hz), and its tilt looks in retrospect like a property of that
penetration, not of the area. The gradient proposed after the third animal
therefore reduces to a single step: the thalamic relay is finer than
cortex, and cortex is one scale from VISp to VISam.

### Discrete readouts, 60 units, nested-C cumulative decoder

| area | readout | L1 | L2 | L3 | L4 | L5 | L6 | codes ahead of quantized pyramid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | tokenizer codes | 0.06 | 0.15 | 0.20 | 0.26 | 0.29 | 0.29 | 28 of 30 seed-level pairs |
| VISp | quantized pyramid | 0.04 | 0.11 | 0.15 | 0.20 | 0.24 | 0.28 | |
| VISam | tokenizer codes | 0.04 | 0.09 | 0.13 | 0.16 | 0.18 | 0.19 | 27 of 30 |
| VISam | quantized pyramid | 0.03 | 0.06 | 0.09 | 0.12 | 0.16 | 0.18 | |
| LGd | tokenizer codes | 0.07 | 0.15 | 0.23 | 0.30 | 0.36 | 0.39 | 2 of 30 |
| LGd | quantized pyramid | 0.08 | 0.18 | 0.26 | 0.32 | 0.40 | 0.48 | |

The reconstruction readout is within 0.05 of the codes everywhere. In this
session's cortex the learned codes have their largest edge yet over
residual k-means: 0.02 to 0.07 at L2 to L4 in every VISp seed and 0.01 to
0.06 in VISam, falling to nil at L6. In LGd k-means wins at every level
and every seed, by 0.06 to 0.10 at L6. Both discrete readouts still keep
under half of the pyramid (0.29 against 0.62 in VISp, 0.48 against 0.70 in
LGd). Gate 2 is unmet in all fourteen samples, and the split is now sharp:
learned codes help in cortex, by 0.02 in sparse samples and 0.05 in rich
ones, and residual k-means wins in the thalamus, where the fine-bin counts
are high enough that a one-code-per-bin bottleneck on log-counts is the
better summary.

### E3b, continuous pyramid, clean minus perturbed, mean over seeds

| area | test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | jitter 10 ms | 0.00 | 0.00 | 0.00 | 0.01 | 0.01 | 0.01 |
| VISp | jitter 25 ms | 0.00 | 0.01 | 0.02 | 0.03 | 0.04 | 0.03 |
| VISp | PSTH surrogate | 0.04 | 0.03 | 0.01 | -0.02 | -0.01 | -0.04 |
| VISam | jitter 10 ms | 0.00 | 0.00 | 0.00 | 0.01 | 0.01 | 0.01 |
| VISam | jitter 25 ms | 0.00 | 0.01 | 0.02 | 0.03 | 0.04 | 0.03 |
| VISam | PSTH surrogate | 0.03 | 0.05 | 0.03 | 0.01 | -0.01 | 0.00 |
| LGd | jitter 10 ms | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.02 |
| LGd | jitter 25 ms | 0.00 | 0.00 | 0.01 | 0.02 | 0.04 | 0.05 |
| LGd | PSTH surrogate | 0.03 | 0.01 | -0.02 | -0.04 | -0.02 | -0.03 |

Jitter of 5 ms changes nothing in any area. Jitter of 10 ms costs 0.01 to
0.03 at L5 to L6 in every LGd seed, as in the first LGd, and at most 0.01
in cortex. Jitter of 25 ms costs LGd 0.03 to 0.07 at L5 to L6 and the two
cortical areas 0.02 to 0.06 from L3 on. The PSTH-matched surrogate lowers
whole-window counts by 0.03 to 0.04 everywhere and raises LGd's fine
levels by 0.02 to 0.04 in every seed from L3 on, which the first LGd did
not show; noise correlations in this relay sample hurt the fine-bin
readout. For the codes the surrogate raises LGd by 0.02 to 0.05 at L2 to
L6 and cortex by 0.01 to 0.03.

### Detail of level k alone, 60 units, 5 seeds, nested-C logistic

| area | readout | L1 (250) | L2 (125) | L3 (50) | L4 (25) | L5 (10) | L6 (5 ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | detail alone | 0.57 | 0.28 | 0.21 | 0.08 | 0.04 | 0.02 |
| VISp | population-rate regressed | 0.57 | 0.13 | 0.12 | 0.05 | 0.03 | 0.02 |
| VISam | detail alone | 0.34 | 0.18 | 0.16 | 0.04 | 0.03 | 0.02 |
| VISam | population-rate regressed | 0.34 | 0.11 | 0.09 | 0.02 | 0.02 | 0.02 |
| LGd | detail alone | 0.58 | 0.23 | 0.30 | 0.11 | 0.07 | 0.03 |
| LGd | population-rate regressed | 0.58 | 0.10 | 0.12 | 0.05 | 0.04 | 0.03 |
| all three | time-shuffled controls | = L1 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 |
| VISp | detail as a share of L1 | 1 | 0.49 | 0.37 | 0.15 | 0.07 | 0.04 |
| VISam | detail as a share of L1 | 1 | 0.53 | 0.46 | 0.11 | 0.08 | 0.05 |
| LGd | detail as a share of L1 | 1 | 0.40 | 0.53 | 0.19 | 0.12 | 0.05 |

Seed std is at most 0.03 at L1 and 0.02 elsewhere. All units, detail alone
(one seed): VISp 74 units 0.62, 0.31, 0.24, 0.09, 0.04, 0.02; VISam 77
units 0.42, 0.21, 0.18, 0.04, 0.03, 0.02; LGd 78 units 0.68, 0.30, 0.37,
0.14, 0.08, 0.03. Detail minus control per seed: VISp 0.24 to 0.27 at L2,
0.18 to 0.22 at L3, 0.04 to 0.07 at L4, 0.01 to 0.03 at L5, 0.00 to 0.01
at L6; VISam 0.16 to 0.18, 0.14 to 0.15, 0.02 to 0.03, 0.00 to 0.02, 0.00
to 0.01; LGd 0.20 to 0.24, 0.27 to 0.32, 0.08 to 0.11, 0.05 to 0.06, 0.01
to 0.02. Population-rate regressed minus control: VISp 0.09 to 0.12 at L2,
0.10 to 0.11 at L3, 0.02 to 0.03 at L4; VISam 0.09 to 0.11, 0.06 to 0.08,
0.01 to 0.02; LGd 0.08 to 0.10, 0.10 to 0.12, 0.03 to 0.05, 0.02 to 0.03
at L5. The per-unit regression keeps more, as before (VISp 0.17 and 0.15,
VISam 0.13 and 0.11, LGd 0.17 and 0.18 at L2 and L3).

**Rate regression, fourth animal.** The population-rate regression leaves
0.46 to 0.61 of the 125 ms detail and 0.40 to 0.57 of the 50 ms detail in
the three areas, inside the range of the other eleven samples, each 10 to
14 times chance.

**LGd is the one area with a decodable 10 ms shape.** Its 10 ms detail
decodes 0.07, 0.05 to 0.06 above the control in every seed and 0.02 to
0.03 above it after rate regression; in the first LGd it was 0.01 to 0.04
above. Its 5 ms detail is 0.01 to 0.02 above the control, the only area
where that difference has one sign in every seed. In every cortical
sample across four animals the 10 ms detail is within 0.03 of the control
and the 5 ms detail within 0.01. So the relay carries a little image
information at 10 ms and a trace at 5 ms that the cortex above it does
not, consistent with its 25 ms optimum, its 10 ms jitter cost and its
higher firing rates.

**Where this leaves the hierarchy question.** Fourteen samples, four
animals. Cortex from VISp to VISam, nine samples, has one temporal
profile in eight of them: a 50 ms optimum, 125 ms within 0.04, the 125 and
50 ms details at 0.37 to 0.55 of rate-only accuracy, a small 25 ms detail,
nothing at 5 ms. The one that departed from it, the first VISam, was the
sparsest, and the second VISam does not. The thalamic relay, two samples,
is finer by one level and keeps information to 5 ms. LP, one sample,
leans the same way as LGd. The temporal structure of the code follows
whether the population is thalamic or cortical, not its rank in the
cortical hierarchy, as far as these samples can tell; an increase in
timescale within cortex, which the timescale-hierarchy literature reports
for autocorrelation and latency, does not show up as a change in which bin
widths carry image identity.

## LP in a second animal: session 757216464 (11 Nov 2026)

Brain Observatory 1.1 session 757216464, a fifth mouse, chosen for its LP
yield: 116 LP and 88 VISp units pass the quality filters (10.7 and 8.1 Hz
mean in the window; 3 and 11 units below 1 Hz). The first LP sample (170
units in the third animal) was sparse in information (0.16 at 60 units)
and its shares were read off small numbers; this one is rich. Same
pipeline. Figures: `e3_allen_757216464_<area>_n60.png`. Raw numbers: the
`e3_`, `external_` and `residual_allen_757216464_<area>` files. Chance is
0.008.

### Continuous pyramid, nested-C cumulative decoder, 60 units, time-blocked

| area | L1 | L2 | L3 | L4 | L5 | L6 | L3 minus L1, per seed | L3 minus L2, per seed | L3 minus L6, per seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LP | 0.18 | 0.27 | 0.32 | 0.32 | 0.31 | 0.28 | 0.13 to 0.16 | 0.03 to 0.07 | 0.02 to 0.05 |
| VISp | 0.40 | 0.46 | 0.49 | 0.48 | 0.45 | 0.41 | 0.08 to 0.10 | 0.01 to 0.04 | 0.06 to 0.09 |

Seed std is at most 0.02. The best level is L3 or L4 in both areas (LP: L4
in three seeds; VISp: L4 in two), within 0.02 of each other.

### Random folds and all units, continuous pyramid, nested-C decoder

| area | units | split | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LP | 60 | time-blocked | 0.18 | 0.27 | 0.31 | 0.29 | 0.30 | 0.26 |
| LP | 60 | random 10-fold | 0.23 | 0.33 | 0.39 | 0.40 | 0.38 | 0.33 |
| LP | 116 (all) | time-blocked | 0.29 | 0.40 | 0.49 | 0.50 | 0.48 | 0.44 |
| LP | 116 (all) | random 10-fold | 0.39 | 0.52 | 0.60 | 0.61 | 0.60 | 0.55 |
| VISp | 60 | time-blocked | 0.40 | 0.45 | 0.49 | 0.48 | 0.44 | 0.40 |
| VISp | 60 | random 10-fold | 0.49 | 0.56 | 0.59 | 0.57 | 0.54 | 0.48 |
| VISp | 88 (all) | time-blocked | 0.47 | 0.55 | 0.56 | 0.53 | 0.51 | 0.49 |
| VISp | 88 (all) | random 10-fold | 0.59 | 0.65 | 0.67 | 0.66 | 0.62 | 0.58 |

Random folds add 0.08 to 0.10 at 60 units here, between the third animal's
0.16 to 0.25 and the fourth's 0.00. With all 116 units LP decodes 0.50 on
the blocked split, as much as the first animal's VISp.

**LP's profile replicates, and it is thalamic.** The relative gain from
whole-window count to 125 ms is the largest in the study (0.07 to 0.11 per
seed against 0.04 to 0.10 in cortex and the two LGd samples), the pyramid
is flat from 50 to 10 ms (L3 minus L6 of 0.02 to 0.05, as the first LP's
0.02 to 0.03 and both LGd samples' 0.01 to 0.05, against 0.06 to 0.13 in
every cortical sample), and the 25 ms detail is 0.24 of rate-only accuracy
(first LP 0.27, LGd 0.19 and 0.22, cortex 0.11 to 0.18 until this
session's VISp, see below). What does not carry over from LGd is the
balance between the two coarse shapes (the 50 ms detail equals the 125 ms
detail here, 1.00, against 1.26 to 1.30 in LGd and the first LP) and the
10 ms jitter cost (0.00 to 0.02 per seed at L5 to L6, at the edge of
resolution, where LGd gave 0.01 to 0.03 in every seed). So LP sits between
the relay and the cortex in how fine its shape information is, with the
thalamic flatness below 50 ms and the cortical balance above it.

**LP leans on shape more than any other area.** Its 125 and 50 ms details
are each 0.64 of its rate-only accuracy (the first LP gave 0.59 and 0.74;
cortex 0.37 to 0.55; LGd 0.37 to 0.53), and 0.69 to 0.71 of each survives
regression on the population rate vector (cortex 0.46 to 0.75). The
whole-window count is a smaller part of what LP says about the image than
anywhere else sampled, which fits a nucleus whose visual responses are
shaped by cortical feedback and collicular input arriving at different
latencies.

**VISp, fifth animal: the same profile, a little finer.** 50 ms optimum
(L4 within 0.02 in every seed), the 125 and 50 ms details at 0.48 and 0.49
of rate-only accuracy, half surviving rate regression. Its 25 ms detail
is 0.22 of rate-only accuracy, above the 0.11 to 0.18 of the other eight
cortical samples and level with LGd, and its 10 ms detail is 0.03 to 0.04
above the control in every seed; the pyramid's fall to 5 ms (0.06 to 0.09)
and the absent 10 ms jitter cost are still cortical. One VISp of five with
a slightly larger 25 ms share is within what the penetrations have varied
by elsewhere.

### Discrete readouts, 60 units, nested-C cumulative decoder

| area | readout | L1 | L2 | L3 | L4 | L5 | L6 | codes ahead of quantized pyramid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LP | tokenizer codes | 0.02 | 0.04 | 0.07 | 0.09 | 0.11 | 0.12 | 9 of 30 seed-level pairs |
| LP | quantized pyramid | 0.03 | 0.04 | 0.07 | 0.09 | 0.11 | 0.14 | |
| VISp | tokenizer codes | 0.06 | 0.13 | 0.18 | 0.22 | 0.25 | 0.26 | 27 of 30 |
| VISp | quantized pyramid | 0.05 | 0.09 | 0.13 | 0.17 | 0.21 | 0.24 | |

The reconstruction readout is within 0.05 of the codes. The pattern of the
previous fourteen samples holds: learned codes lead k-means in cortex (0.02
to 0.07 at L2 to L5 in every VISp seed) and k-means is level or ahead in
the thalamus (LP: level at L2 to L5, ahead by 0.01 to 0.04 at L6 in every
seed). Both discrete readouts keep under half of the pyramid (0.26 against
0.49 in VISp; 0.14 against 0.32 in LP). Gate 2 is unmet in all sixteen
samples.

### E3b, continuous pyramid, clean minus perturbed, mean over seeds

| area | test set | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LP | jitter 10 ms | 0.00 | 0.00 | 0.01 | 0.01 | 0.01 | 0.01 |
| LP | jitter 25 ms | 0.00 | 0.01 | 0.02 | 0.03 | 0.03 | 0.04 |
| LP | PSTH surrogate | 0.03 | 0.04 | 0.03 | 0.02 | 0.01 | 0.02 |
| VISp | jitter 10 ms | 0.00 | 0.00 | 0.00 | 0.01 | 0.01 | 0.01 |
| VISp | jitter 25 ms | 0.00 | 0.00 | 0.02 | 0.02 | 0.03 | 0.04 |
| VISp | PSTH surrogate | 0.03 | 0.02 | 0.02 | 0.00 | 0.00 | 0.00 |

Jitter of 5 ms changes nothing. Jitter of 10 ms costs 0.00 to 0.02 at L4
to L6 in both areas. Jitter of 25 ms costs 0.02 to 0.06 from L4 on in
every seed of both. The PSTH-matched surrogate lowers LP at every level
(0.01 to 0.06 per seed, every seed at L1 to L3 and L6), the first area
where noise correlations help the fine readouts as well as the coarse; in
VISp it lowers L1 to L3 by 0.02 to 0.03 and leaves L4 to L6 unchanged. The
codes are unaffected by the surrogate in LP and raised by 0.01 to 0.02 in
VISp as in the other animals.

### Detail of level k alone, 60 units, 5 seeds, nested-C logistic

| area | readout | L1 (250) | L2 (125) | L3 (50) | L4 (25) | L5 (10) | L6 (5 ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LP | detail alone | 0.18 | 0.12 | 0.12 | 0.04 | 0.02 | 0.01 |
| LP | population-rate regressed | 0.18 | 0.08 | 0.08 | 0.03 | 0.02 | 0.01 |
| VISp | detail alone | 0.41 | 0.20 | 0.20 | 0.09 | 0.05 | 0.03 |
| VISp | population-rate regressed | 0.41 | 0.10 | 0.11 | 0.06 | 0.04 | 0.03 |
| both | time-shuffled controls | = L1 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 | 0.01 to 0.02 |
| LP | detail as a share of L1 | 1 | 0.64 | 0.64 | 0.24 | 0.14 | 0.07 |
| VISp | detail as a share of L1 | 1 | 0.48 | 0.49 | 0.22 | 0.13 | 0.08 |

Seed std is at most 0.01. All units, detail alone (one seed): LP 116 units
0.30, 0.19, 0.19, 0.04, 0.03, 0.02; VISp 88 units 0.48, 0.25, 0.25, 0.12,
0.06, 0.03. Detail minus control per seed: LP 0.10 to 0.12 at L2, 0.09 to
0.13 at L3, 0.02 to 0.04 at L4, 0.01 to 0.03 at L5, 0.00 to 0.01 at L6;
VISp 0.17 to 0.19, 0.17 to 0.20, 0.06 to 0.08, 0.03 to 0.04, 0.01 to 0.02.
Population-rate regressed minus control: LP 0.06 to 0.09 at L2 and L3,
0.01 to 0.03 at L4; VISp 0.08 to 0.09, 0.08 to 0.10, 0.03 to 0.04, 0.02 to
0.03 at L5. The per-unit regression keeps more, as before (LP 0.10 and
0.09, VISp 0.14 and 0.14 at L2 and L3).

**Where this leaves the picture, sixteen samples in five animals.** Cortex
has one profile from VISp to VISam, with nine of ten samples inside the
same ranges and the sparse first VISam the exception. The thalamus differs
from the cortex in the same direction in all four samples (two LGd, two
LP): a flat pyramid from 50 to 10 ms, a 25 ms detail at 0.19 to 0.27 of
rate-only accuracy, and in LGd a decodable 10 ms detail and a 10 ms jitter
cost. LP's two samples agree with each other on the flatness, the 25 ms
share and the large share of shape relative to rate, and disagree with
LGd on the 50 to 125 ms balance. The division in the data is thalamus
against cortex, not position in the cortical hierarchy.

## VISp, LGd and LP of session 750749662: a sixth animal (12 Nov 2026)

The session downloaded for the gratings and the thalamic state split also
ran the full natural-scenes pipeline on its three areas: 60 VISp, 83 LGd
and 145 LP units pass the quality filters (7.7, 8.6 and 9.0 Hz mean in the
window). VISp has exactly 60 units, so its five seeds use the same units
and differ only in the tokenizer's initialization; they count as one
sample. Figures: `e3_allen_750749662_<area>_n60.png`. Raw numbers: the
`e3_`, `external_`, `residual_` and `latency_allen_750749662_<area>` files.
Chance is 0.008.

### Continuous pyramid, nested-C cumulative decoder, 60 units, time-blocked

| area | L1 | L2 | L3 | L4 | L5 | L6 | L3 minus L1, per seed | L3 minus L2, per seed | L3 minus L6, per seed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | 0.33 | 0.38 | 0.40 | 0.39 | 0.36 | 0.34 | 0.06 | 0.02 | 0.06 |
| LGd | 0.11 | 0.14 | 0.15 | 0.16 | 0.14 | 0.11 | 0.02 to 0.06 | 0.00 to 0.01 | 0.02 to 0.06 |
| LP | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | 0.02 | -0.00 to 0.01 | -0.00 to 0.01 | -0.01 to 0.01 |

All units, time-blocked (random 10-fold): VISp is the 60-unit row (random
folds 0.31, 0.35, 0.37, 0.36, 0.33, 0.30, the only sample where they fall
below the blocked split); LGd 83 units 0.13, 0.18, 0.21, 0.21, 0.18, 0.15
(0.14, 0.19, 0.22, 0.22, 0.20, 0.17); LP 145 units 0.03 at every level
(0.03 to 0.05).

### Detail of level k alone, 60 units, 5 seeds, nested-C logistic

| area | readout | L1 (250) | L2 (125) | L3 (50) | L4 (25) | L5 (10) | L6 (5 ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp | detail alone | 0.35 | 0.19 | 0.16 | 0.06 | 0.03 | 0.02 |
| VISp | population-rate regressed | 0.35 | 0.08 | 0.10 | 0.04 | 0.02 | 0.02 |
| LGd | detail alone | 0.12 | 0.05 | 0.06 | 0.02 | 0.01 | 0.01 |
| LGd | population-rate regressed | 0.12 | 0.03 | 0.03 | 0.02 | 0.01 | 0.01 |
| LP | detail alone | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |
| all | time-shuffled controls | = L1 | 0.01 | 0.01 | 0.01 | 0.01 to 0.02 | 0.01 to 0.02 |
| VISp | detail as a share of L1 | 1 | 0.54 | 0.46 | 0.17 | 0.09 | 0.06 |
| LGd | detail as a share of L1 | 1 | 0.39 | 0.50 | 0.21 | 0.11 | 0.08 |

Detail minus control per seed: VISp 0.17 to 0.18 at L2, 0.14 to 0.15 at
L3, 0.04 to 0.05 at L4, 0.01 to 0.02 at L5; LGd 0.03 to 0.05, 0.04 to
0.06, 0.01 to 0.02, and nothing resolvable below. Population-rate
regressed minus control: VISp 0.06 to 0.07 and 0.08 to 0.09 at L2 and L3,
0.02 to 0.03 at L4; LGd 0.02 to 0.03 and 0.01 to 0.03.

**LP is not driven by the natural scenes in this animal.** At 0.02 with 60
units and 0.03 with all 145, its pyramid and details sit at two to four
times chance with no level distinguishable from another, as in the
gratings and the state split. It has no profile to compare and is left
out of the counts below; the session is a sixth animal for VISp and LGd
only.

**VISp is cortical in every respect.** 50 ms optimum, the 25 ms level 0.01
below it, a fall of 0.06 to 5 ms, 125 and 50 ms details at 0.54 and 0.46
of rate-only accuracy, 0.42 and 0.60 of them surviving the population-rate
regression, and a 25 ms share of 0.17 (cortex 0.11 to 0.22). Jitter of
10 ms costs 0.01 to 0.03 at L6 only; the PSTH-matched surrogate raises L4
and L5 by 0.02 to 0.05 in every seed, the noise correlations costing the
fine readouts here where they were neutral in the other VISp samples.

**LGd is weak but thalamic where it can be read.** At 0.15 it decodes
half as well as the weakest earlier LGd, and its best level moves between
L3 and L5 across seeds. Within that resolution it keeps the thalamic
signature: the pyramid within 0.02 from 50 to 10 ms, a 25 ms share of
0.21 (earlier thalamic samples 0.19 to 0.27), the 50 ms detail larger than
the 125 ms one (1.29, as 1.26 to 1.30 in the earlier LGd), and learned
codes no better than k-means (ahead in 11 of 30 seed-level pairs). The
10 ms jitter cost that both earlier LGd showed (0.01 to 0.03) is not
resolvable at this accuracy (-0.01 to 0.01).

**The other readouts agree.** Discrete readouts: codes ahead of the
quantized pyramid in 25 of 30 VISp pairs, both under half the pyramid
(VISp 0.19 against 0.40), so Gate 2 is unmet in all eighteen informative
samples. Latency readout: first-spike latency and centre of mass decode
0.12 and 0.20 in VISp (0.03 and 0.05 in LGd), add nothing to the count,
and leave the 125 and 50 ms details at 0.24 and 0.40 (VISp) and 0.38 and
0.45 (LGd) of their accuracy alone, inside the earlier ranges, above the
control in every seed (VISp 0.03 to 0.04 and 0.05 to 0.06; LGd 0.01 to
0.02). Nonlinear rate regression: VISp keeps 0.86 and 0.72 of its
linearly regressed 125 and 50 ms details (the 50 ms figure just below the
earlier 0.74 to 0.95), 0.05 above the control in every seed; LGd keeps
all of it, and its nonlinear count decoder gains 0.003, not the 0.02 to
0.03 of the earlier LGd.

**Reading.** A sixth animal adds a VISp that falls inside every cortical
range and an LGd that, at a third of the earlier LGd accuracy, still
shows the flat 50 to 10 ms pyramid, the larger 25 ms share and the 50 over
125 ms balance. Eighteen informative samples in six animals: one cortical
profile, and the thalamus different from it in the same direction in all
five thalamic samples.

## An explicit latency readout: the details are not first-spike latency (11 Nov 2026)

The caveat below says the 125 ms detail is transience and the 50 ms detail
is largely onset latency, both long known to carry image information. This
section tests how much of the two details an explicit per-unit timing
summary accounts for, on all sixteen samples (60 units, 5 seeds, same
subsets and split as everything else). From the 1 ms spike array, three
per-unit, per-trial summaries: first-spike time (1.0 when silent), a silent
indicator, and the centre of mass of the unit's spike times (0.5 when
silent). About half of unit-trial pairs are silent in the window. Two
tests, both through the nested-C logistic (`scripts/latency_readout.py`,
raw numbers in `latency_allen_<session>_<area>.json`):

1. In the pyramid's own coordinates (cumulative log pooled counts): the
   gain from L1 to L3 (the number every section above reports), the gain
   from adding the timing summaries to L1, and the gain from L3 counts
   once the timing summaries are already in. If the details were latency,
   the second would match the first and the third would be near zero.
2. In the detail coordinates: each detail decoded alone, after regression
   on the population rate vector (the control of the rate-regression
   section), and after regression on rate and the timing summaries of
   every unit together.

| sample | centre of mass alone | pyramid L3 minus L1 | L1 + timing minus L1 | L3 + timing minus L1 + timing | 125 ms detail: alone / rate-regressed / rate-and-timing-regressed | 50 ms detail: same | timing-regressed minus control, per seed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp 105 | 0.25 | 0.07 | -0.03 | 0.07 | 0.21 / 0.11 / 0.07 | 0.17 / 0.09 / 0.07 | 0.04 to 0.06, 0.05 to 0.06 |
| VISp 424 | 0.28 | 0.08 | -0.02 | 0.08 | 0.21 / 0.12 / 0.06 | 0.15 / 0.08 / 0.06 | 0.04 to 0.05, 0.04 to 0.05 |
| VISp 445 | 0.24 | 0.09 | -0.03 | 0.10 | 0.18 / 0.11 / 0.05 | 0.19 / 0.09 / 0.07 | 0.03 to 0.05, 0.05 to 0.07 |
| VISp 393 | 0.38 | 0.08 | -0.02 | 0.09 | 0.28 / 0.13 / 0.08 | 0.21 / 0.12 / 0.09 | 0.05 to 0.07, 0.07 to 0.08 |
| VISp 464 | 0.28 | 0.09 | -0.01 | 0.08 | 0.20 / 0.10 / 0.07 | 0.20 / 0.11 / 0.09 | 0.05 to 0.06, 0.06 to 0.08 |
| VISal 105 | 0.17 | 0.08 | +0.01 | 0.07 | 0.12 / 0.08 / 0.05 | 0.11 / 0.06 / 0.05 | 0.02 to 0.03, 0.03 to 0.04 |
| VISal 424 | 0.25 | 0.11 | -0.00 | 0.09 | 0.20 / 0.13 / 0.06 | 0.17 / 0.10 / 0.08 | 0.02 to 0.05, 0.05 to 0.08 |
| VISl 424 | 0.31 | 0.11 | +0.01 | 0.09 | 0.20 / 0.12 / 0.06 | 0.18 / 0.10 / 0.07 | 0.05 to 0.06, 0.04 to 0.06 |
| VISrl 105 | 0.12 | 0.06 | -0.01 | 0.05 | 0.08 / 0.06 / 0.04 | 0.08 / 0.06 / 0.04 | 0.02 to 0.03, 0.02 to 0.04 |
| VISpm 105 | 0.20 | 0.07 | -0.04 | 0.08 | 0.16 / 0.09 / 0.06 | 0.15 / 0.07 / 0.05 | 0.04 to 0.05, 0.03 to 0.04 |
| VISam 424 | 0.11 | 0.06 | -0.00 | 0.05 | 0.10 / 0.08 / 0.03 | 0.06 / 0.05 / 0.04 | 0.02 to 0.03, 0.02 to 0.03 |
| VISam 393 | 0.20 | 0.11 | -0.03 | 0.11 | 0.18 / 0.11 / 0.06 | 0.16 / 0.09 / 0.07 | 0.05 to 0.06, 0.05 to 0.07 |
| LGd 445 | 0.16 | 0.10 | -0.04 | 0.12 | 0.12 / 0.06 / 0.04 | 0.16 / 0.07 / 0.07 | 0.02 to 0.04, 0.04 to 0.07 |
| LGd 393 | 0.31 | 0.12 | -0.05 | 0.15 | 0.23 / 0.10 / 0.05 | 0.30 / 0.12 / 0.09 | 0.03 to 0.05, 0.07 to 0.09 |
| LP 445 | 0.06 | 0.06 | -0.00 | 0.06 | 0.06 / 0.05 / 0.03 | 0.07 / 0.05 / 0.04 | 0.01 to 0.02, 0.02 to 0.03 |
| LP 464 | 0.10 | 0.14 | +0.01 | 0.11 | 0.12 / 0.08 / 0.05 | 0.12 / 0.08 / 0.06 | 0.03 to 0.04, 0.04 to 0.06 |

Sample names end in the last three digits of the session id. Chance is
0.008; the time-shuffled controls are 0.01 to 0.02.

**Timing summaries do not substitute for the pooled counts.** The centre
of mass alone identifies the image at 0.06 to 0.38 and first-spike
latency alone at 0.04 to 0.24, so the summaries carry image information.
Added to the whole-window count they change accuracy by -0.05 to 0.01,
nothing or a small loss from the extra dimensions, in every sample, while
the 125 and 50 ms counts added on top of count and timing still gain
0.05 to 0.15, the same as their gain without the timing summaries. What
the timing summaries know about the image, the count already knows; what
the pooled counts know, the summaries do not.

**Regressing the details on timing removes more than rate alone, and
leaves a shape component in every sample and seed.** After regression on
rate and the timing summaries of every unit, the 125 ms detail keeps
0.23 to 0.49 of its accuracy and the 50 ms detail 0.31 to 0.59, against
0.44 to 0.81 and 0.40 to 0.73 after rate alone. Relative to the
rate-regressed detail, the timing summaries account for a further
0.30 to 0.57 of the 125 ms detail and
0.13 to 0.31 of the 50 ms detail. What is left is
0.03 to 0.09 absolute, above the shuffled control by at least
0.01 (125 ms) and 0.02 (50 ms) in every seed of
every sample, 4 to 11 times chance in the cortical samples and the second
LGd. Both details together, timing-regressed, decode 0.04 to 0.12.

**Reading.** First-spike latency and the centre of mass are the natural
single-trial summaries of when a unit's response happens, and they do
capture part of what the details carry: about a third to a half of the
rate-independent 125 ms detail and about a fifth of the rate-independent
50 ms detail, more at 125 ms because transience moves the centre of mass
directly. The remainder is temporal structure within the window that
neither the count nor the timing of the response as a whole describes:
whether the response has one peak or two, how fast it decays, whether it
rebounds. The caveat stands in its weaker form: the details overlap with
latency and transience, and a reader who prefers to think of them as
latency codes is describing part of them. Two limits. Single-trial
latency estimates from units that fire one or two spikes in the window
are noisy, and linear regression on a noisy covariate removes less than
the covariate's true share, so the "further share" above is a lower
bound; the pyramid test is less exposed to this, since the decoder can
weight the summaries however it likes, and it shows the same thing. And
the summaries are per unit; a population-level latency is tested
separately below.

**Population-level timing adds nothing.** A second run (`--tag pop`,
`latency_allen_<session>_<area>_pop.json`) adds three per-trial summaries
of the population response as a whole: the time of its first spike, the
centre of mass of the summed spike count over the window, and the time
at which the cumulative population count reaches half. On their own they
identify the image at 0.011 to 0.019 against chance 0.008: the moment the
population as a whole responds says almost nothing about which image it
is. Added to count plus per-unit timing they change accuracy by -0.003 to
0.006, and the 125 and 50 ms pooled counts gain 0.04 to 0.14 on top of all
of it, as before. Regressing the details on rate, per-unit timing and
population timing together leaves them within 0.005 of the per-unit
timing regression in every sample (ratios 0.94 to 1.04), still above the
control by 0.01 to 0.06 (125 ms) and 0.02 to 0.07 (50 ms) in every seed.
Whatever the details carry, it is not when the population responds; it
is how the response of each unit is distributed within the window,
relative to the others.

## Behavioural state: running and pupil as covariates, and the pyramid within running and stationary trials (11 Nov 2026)

`scripts/load_allen_state.py` reads each session's running speed and, where
the session has eye tracking (four of five; not 732592105), pupil area, and
averages them over the 0 to 250 ms window of every trial
(`data/allen_<session>_state.npz`). The fraction of trials with the mouse
running above 5 cm/s is 0.50, 0.39, 0.20, 0.12 and 0.56 in sessions
732592105, 798911424, 754829445, 763673393 and 757216464. Two uses, through
`scripts/latency_readout.py --tag state` (`latency_allen_<session>_<area>_state.json`),
60 units, 5 seeds as everywhere:

1. State as a covariate: decoded alone, added to the whole-window count and
   to the L3 pyramid, and added to the population rate regression of the
   125 and 50 ms details (z-scored on the training trials).
2. The pyramid decoded within running trials only and within stationary
   trials only, the larger set subsampled to the smaller's size so the two
   decoders see the same number of trials. Done where the smaller state has
   at least 8 repeats of every image: the ten samples of sessions
   732592105, 798911424 and 757216464. Sessions 754829445 and 763673393,
   with the mouse running on 0.20 and 0.12 of trials, have too few running
   trials, which takes both LGd samples and one LP out of this test.

**State explains none of the stimulus information.** Running and pupil
alone decode the image at 0.003 to 0.007 (chance 0.008). Added to the
count they change accuracy by -0.003 to 0.005, added to the L3 pyramid
by -0.003 to 0.007, and added to the rate regression they move the
125 ms detail by -0.003 to 0.003 and the 50 ms detail by -0.002 to 0.001,
in every one of the sixteen samples. This is the expected outcome: state
is not image-specific, so it can neither carry image identity nor, as a
linear covariate, account for any of what the details carry. The drift
that inflates random folds in the third animal is therefore not something
a linear running or pupil term absorbs; the time-blocked split remains the
guard against it.

### Pyramid within one behavioural state, 60 units, 5 seeds, equal trial counts

| sample | running fraction | trials per state | running L1 to L6 | stationary L1 to L6 | L3 minus L1, running / stationary | L3 minus L6, running / stationary |
| --- | --- | --- | --- | --- | --- | --- |
| VISp 105 | 0.50 | 2950 | 0.45 0.50 0.52 0.50 0.46 0.41 | 0.31 0.33 0.34 0.30 0.28 0.23 | 0.07 / 0.03 | 0.12 / 0.11 |
| VISp 424 | 0.39 | 2301 | 0.53 0.61 0.63 0.59 0.54 0.47 | 0.28 0.32 0.32 0.30 0.26 0.22 | 0.10 / 0.03 | 0.16 / 0.10 |
| VISp 445 | 0.20 | too few running trials (1180, under 8 repeats of some image) | | | | |
| VISp 393 | 0.12 | too few running trials (708, under 8 repeats of some image) | | | | |
| VISp 464 | 0.56 | 2596 | 0.48 0.55 0.57 0.55 0.52 0.46 | 0.33 0.35 0.37 0.33 0.28 0.24 | 0.09 / 0.04 | 0.12 / 0.13 |
| VISal 105 | 0.50 | 2950 | 0.22 0.29 0.32 0.30 0.27 0.23 | 0.16 0.21 0.24 0.22 0.20 0.16 | 0.10 / 0.08 | 0.09 / 0.08 |
| VISal 424 | 0.39 | 2301 | 0.43 0.52 0.55 0.53 0.47 0.40 | 0.26 0.31 0.33 0.30 0.26 0.22 | 0.12 / 0.06 | 0.14 / 0.11 |
| VISl 424 | 0.39 | 2301 | 0.43 0.50 0.54 0.52 0.48 0.41 | 0.29 0.36 0.37 0.35 0.30 0.25 | 0.11 / 0.08 | 0.13 / 0.12 |
| VISrl 105 | 0.50 | 2950 | 0.17 0.20 0.22 0.21 0.18 0.14 | 0.17 0.20 0.20 0.18 0.16 0.14 | 0.06 / 0.03 | 0.08 / 0.06 |
| VISpm 105 | 0.50 | 2950 | 0.42 0.49 0.52 0.51 0.48 0.40 | 0.27 0.29 0.31 0.30 0.25 0.20 | 0.10 / 0.04 | 0.12 / 0.10 |
| VISam 424 | 0.39 | 2301 | 0.17 0.22 0.23 0.20 0.17 0.14 | 0.09 0.11 0.12 0.10 0.10 0.08 | 0.06 / 0.03 | 0.08 / 0.04 |
| VISam 393 | 0.12 | too few running trials (708, under 8 repeats of some image) | | | | |
| LGd 445 | 0.20 | too few running trials (1180, under 8 repeats of some image) | | | | |
| LGd 393 | 0.12 | too few running trials (708, under 8 repeats of some image) | | | | |
| LP 445 | 0.20 | too few running trials (1180, under 8 repeats of some image) | | | | |
| LP 464 | 0.56 | 2596 | 0.20 0.27 0.33 0.34 0.33 0.29 | 0.14 0.20 0.22 0.23 0.21 0.18 | 0.13 / 0.08 | 0.04 / 0.04 |

**Locomotion scales the information up; the temporal profile does not
move.** With equal numbers of trials, the running trials decode the image
better at every level in every sample, by a factor of 1.12 to 1.98 at
the 50 ms level (the known gain increase of mouse visual cortex under
locomotion, here as decodable image identity). The best level is 50 ms in
both states in every cortical sample (125 ms ties it in the stationary
trials of one VISp), with LP's optimum at 25 ms in both; the fall from 50 to 5 ms is 0.04 to 0.16 running against
0.04 to 0.13 stationary, and LP is flat below 50 ms in both states.
The gain from the count to the 50 ms level is larger when running in
absolute terms, 0.06 to 0.13 against 0.03 to 0.08, in
47 of 50 seed-sample pairs; relative to
the count it is not consistently larger, so locomotion raises the shape
information at least in proportion to the count and perhaps a little
more. The scale at which the code sits is a property of the tissue, not
of the behavioural state the animal is in.

Caveats: a 5 cm/s threshold and a single binary split; stationary trials
include the quiet-wakefulness and drowsy states the pupil distinguishes,
which are not separated here; each state's decoder trains on 1,800 to
2,400 trials against about 4,700 for the full-data numbers, so the
absolute accuracies in this table are not comparable with the rest of the
results, only the two states with each other.

## A nonlinear rate regression: the linear fit is not what left the details standing (11 Nov 2026)

The rate regression of the detail section is linear: each detail is
projected off the population rate vector (every unit's whole-window count,
as log1p and as sqrt) by least squares on the training trials. A detail
that depended on rate through a curve rather than a line would survive
that regression without being rate-independent. This section repeats the
regression with a flexible model. The rate vector is standardized on the
training trials and expanded with 3,000 random Fourier features (a
Gaussian kernel with its bandwidth at the median pairwise distance of the
training rows), the linear columns kept in front so the linear fit is
nested, and each detail is regressed on the expansion by ridge with the
penalty chosen on an inner time-blocked split. The same expansion is also
fed to the decoder in place of the count alone, as a check that it can
represent what a nonlinear readout of rate would see. All sixteen samples,
60 units, 5 seeds, same subsets and split as everywhere
(`scripts/latency_readout.py --tag nonlin`, raw numbers in
`latency_allen_<session>_<area>_nonlin.json`).

| sample | count: linear / nonlinear decoder | 125 ms detail: alone / linear rate-regressed / nonlinear rate-regressed / rate-and-timing-regressed | 50 ms detail: same | nonlinear-regressed minus control, worst seed (125, 50 ms) | both details, nonlinear-regressed |
| --- | --- | --- | --- | --- | --- |
| VISp 105 | 0.41 / 0.42 | 0.21 / 0.11 / 0.09 / 0.07 | 0.17 / 0.09 / 0.07 / 0.07 | 0.06, 0.05 | 0.11 |
| VISp 424 | 0.38 / 0.39 | 0.21 / 0.12 / 0.11 / 0.06 | 0.15 / 0.08 / 0.06 / 0.06 | 0.08, 0.04 | 0.11 |
| VISp 445 | 0.38 / 0.38 | 0.18 / 0.11 / 0.10 / 0.05 | 0.19 / 0.09 / 0.08 / 0.07 | 0.07, 0.05 | 0.13 |
| VISp 393 | 0.57 / 0.57 | 0.28 / 0.13 / 0.11 / 0.08 | 0.21 / 0.12 / 0.10 / 0.09 | 0.08, 0.07 | 0.14 |
| VISp 464 | 0.41 / 0.42 | 0.20 / 0.10 / 0.09 / 0.07 | 0.20 / 0.11 / 0.09 / 0.09 | 0.06, 0.06 | 0.13 |
| VISal 105 | 0.22 / 0.23 | 0.12 / 0.08 / 0.07 / 0.05 | 0.11 / 0.06 / 0.06 / 0.05 | 0.05, 0.04 | 0.10 |
| VISal 424 | 0.36 / 0.36 | 0.20 / 0.13 / 0.12 / 0.06 | 0.17 / 0.10 / 0.08 / 0.08 | 0.08, 0.05 | 0.13 |
| VISl 424 | 0.37 / 0.39 | 0.20 / 0.12 / 0.11 / 0.06 | 0.18 / 0.10 / 0.09 / 0.07 | 0.08, 0.06 | 0.13 |
| VISrl 105 | 0.18 / 0.18 | 0.08 / 0.06 / 0.05 / 0.04 | 0.08 / 0.06 / 0.06 / 0.04 | 0.04, 0.04 | 0.08 |
| VISpm 105 | 0.41 / 0.41 | 0.16 / 0.09 / 0.08 / 0.06 | 0.15 / 0.07 / 0.06 / 0.05 | 0.06, 0.03 | 0.10 |
| VISam 424 | 0.14 / 0.14 | 0.10 / 0.08 / 0.07 / 0.03 | 0.06 / 0.05 / 0.04 / 0.04 | 0.06, 0.03 | 0.07 |
| VISam 393 | 0.34 / 0.35 | 0.18 / 0.11 / 0.10 / 0.06 | 0.16 / 0.09 / 0.08 / 0.07 | 0.09, 0.06 | 0.14 |
| LGd 445 | 0.34 / 0.36 | 0.12 / 0.06 / 0.06 / 0.04 | 0.16 / 0.07 / 0.06 / 0.07 | 0.04, 0.04 | 0.09 |
| LGd 393 | 0.58 / 0.60 | 0.23 / 0.10 / 0.09 / 0.05 | 0.30 / 0.12 / 0.09 / 0.09 | 0.07, 0.07 | 0.14 |
| LP 445 | 0.09 / 0.10 | 0.06 / 0.05 / 0.05 / 0.03 | 0.07 / 0.05 / 0.04 / 0.04 | 0.03, 0.03 | 0.07 |
| LP 464 | 0.18 / 0.18 | 0.12 / 0.08 / 0.08 / 0.05 | 0.12 / 0.08 / 0.07 / 0.06 | 0.06, 0.05 | 0.12 |

Sample names end in the last three digits of the session id. Chance is
0.008; the time-shuffled controls are 0.01 to 0.02.

**A nonlinear readout of the count sees little the linear one misses.**
Decoding the image from the rate vector and its random features changes
accuracy by -0.002 to 0.020 against the linear count readout in the
twelve cortical samples and both LP, and gains 0.022 to 0.028 in the
two LGd samples. The expansion is expressive enough to overfit if there
were nothing to find, and in cortex it finds nothing, so the count's image
information there is linear in the log count as far as this decoder is
concerned; LGd's count carries a small nonlinear part, in keeping with its
larger and more rate-driven responses.

**The nonlinear regression removes a little more than the linear one and
leaves the details standing.** After the nonlinear fit the 125 ms detail
keeps 0.82 to 1.03 of its linearly-regressed accuracy and the 50 ms
detail 0.74 to 0.95, that is, -0.001 to 0.021 and 0.003 to 0.032
absolute removed on top of the linear fit (the largest extra removals are
in the second LGd, the smallest in the first LP, where the nonlinear fit
takes nothing more from the 125 ms detail). Relative to the detail alone
that is 0.39 to 0.83 (125 ms) and 0.30 to 0.70 (50 ms) surviving,
against 0.43 to 0.75 and 0.40 to 0.83 after the linear fit. The
timing-regressed figures in the same table, which remove a further share
through covariates the rate expansion does not contain, stay lower in
every sample. What survives the nonlinear regression is above the shuffled
control by at least 0.03 (125 ms) and 0.03
(50 ms) in every seed of every sample, and both details together,
nonlinearly rate-regressed, decode 0.07 to 0.14.

**Reading.** The caveat that the rate regression is linear is closed in
the direction the rest of the results need: a flexible function of the
population rate accounts for only a few hundredths more of the details
than a line does. The detail information is not a nonlinear echo of the
count. Rate-matched strata, the other version of this test, would decode
the details within trials of near-equal population count; with 118 images
and 60 units the strata would be thin, and the regression with a kernel
expansion asks the same question with all the trials. One limit: 3,000
random features approximate the Gaussian kernel, not represent it, and the
bandwidth is a single median heuristic; a different kernel would move the
numbers by a few thousandths, not reverse them, given how close the
nonlinear and linear figures already are.

## Drifting gratings: the 50 ms optimum is not set by the next image, and long windows favour the count (12 Nov 2026)

Natural scenes play back to back every 250 ms, so every window above ends
where the next image begins, and the 50 ms optimum could in principle be a
property of that boundary rather than of the tissue. The drifting gratings
of the same sessions are shown for 2 s each after 1 s of gray, 8 directions
x 5 temporal frequencies (1, 2, 4, 8, 15 Hz), 15 repeats per condition.
`scripts/load_allen_gratings.py` extracts them (same units as the
natural-scenes files) and `scripts/gratings_pyramid.py` decodes the pyramid
in windows of 250, 1000 and 2000 ms from grating onset, with bins from the
whole window down to 5 ms, for three label sets: the 40 conditions, the
direction alone (frequencies pooled; a static property, the analogue of
image identity) and the temporal frequency alone (directions pooled; a
property that lives in time, the positive control for fine bins). The same
script runs the 250 ms natural-scenes pyramid on the same unit subsets.
Session 750749662, a sixth animal, downloaded for this test and the
thalamic state split below; five areas, 60 units, 5 seeds.

### Whole-window count / best level, accuracy at best bin width (ms)

| area (units) | scenes, 250 ms window | gratings, condition, 250 ms | condition, 1000 ms | condition, 2000 ms | direction, 2000 ms | temporal frequency, 2000 ms | 50 ms detail minus control, condition, 2000 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VISp (60) | 0.33 / 0.40 at 50 | 0.20 / 0.33 at 50 | 0.44 / 0.53 at 25 | 0.57 / 0.58 at 50 | 0.91 / 0.91 at 2000 | 0.65 / 0.76 at 50 | +0.28 |
| VISpm (68) | 0.09 / 0.12 at 50 | 0.13 / 0.16 at 25 | 0.25 / 0.28 at 125 | 0.27 / 0.31 at 500 | 0.52 / 0.60 at 50 | 0.54 / 0.55 at 50 | +0.02 |
| VISam (68) | 0.12 / 0.17 at 50 | 0.12 / 0.17 at 50 | 0.23 / 0.32 at 50 | 0.31 / 0.32 at 125 | 0.78 / 0.79 at 250 | 0.52 / 0.58 at 25 | +0.06 |
| LGd (83) | 0.11 / 0.16 at 25 | 0.12 / 0.19 at 5 | 0.20 / 0.34 at 25 | 0.24 / 0.36 at 50 | 0.40 / 0.44 at 25 | 0.70 / 0.76 at 50 | +0.23 |
| LP (145) | 0.02 / 0.02 at 25 | 0.05 / 0.08 at 25 | 0.10 / 0.12 at 125 | 0.13 / 0.13 at 2000 | 0.31 / 0.34 at 1000 | 0.52 / 0.52 at 2000 | +0.02 |

Chance is 0.008 for scenes, 0.025 for condition, 0.125 for direction and
0.2 for temporal frequency. Each gratings accuracy rests on 120 held-out
trials (the last 3 repeats of each condition), so differences under about
0.04 are noise; VISp has exactly 60 units here, so its five seeds use the
same units and count as one sample.

**The onset profile does not depend on what follows it.** In the first
250 ms of a grating, which is followed by more of the same grating rather
than by a new stimulus, VISp and VISam peak at 50 ms and VISpm at 25 ms,
as their natural-scenes pyramids do on the same units, and LGd keeps
improving down to 5 to 25 ms, as LGd does on scenes. The 50 ms cortical
optimum is therefore not created by the next image arriving at 250 ms.
This animal also reproduces the thalamus-against-cortex division on
natural scenes: VISp, VISpm and VISam peak at 50 ms, LGd at 25 ms.

**With longer windows the count catches up in cortex, not in LGd.** For
condition identity in VISp, the gain from the whole-window count to the
best level is 0.13 in the 250 ms window, 0.09 in 1000 ms and 0.02 in
2000 ms: the timing information that matters for a static stimulus is
concentrated at the response onset, and two seconds of sustained count
recover what the onset dynamics carried. Direction, the static attribute,
is read entirely from the 2 s count in VISp (0.91, no level beats it) and
VISam. LGd keeps a gain of 0.13 to 0.14 at 1000 and 2000 ms, with its
50 ms detail 0.2 above the control: LGd follows the drifting grating cycle
by cycle (its well-known phase-locked, F1-dominated response), so for a
moving stimulus the thalamus carries stimulus-locked temporal structure
throughout, and cortex mostly at onset.

**The best bin width stays near 25 to 125 ms in absolute terms.** In 1000
and 2000 ms windows the optimum for condition and for temporal frequency
is 25 to 125 ms wherever it is clear (VISp, VISam, LGd), not a fixed
fraction of the window (the analogue of the 50 ms level would be 200 and
400 ms). Temporal frequency, the positive control, gains 0.06 to 0.11 over
the count in VISp, VISam and LGd at 25 to 50 ms bins, the scale of the
grating periods (67 to 1000 ms); nothing gains below 25 ms, consistent
with no stimulus-locked structure faster than the 15 Hz grating. VISpm is
flat within noise in the long windows, and LP in this animal is barely
driven by either stimulus (scenes at 0.02, twice chance), so neither says
much here.

**Reading.** The 50 ms scale of the natural-scenes results is a property
of the onset response, not of the 250 ms presentation boundary. The
gratings add one thing the scenes could not show: for a static attribute
the advantage of temporal structure over the count belongs to the first
few hundred milliseconds and fades as the count accumulates, while a
stimulus that moves drives locked temporal structure at its own periods,
read best at 25 to 50 ms bins and most strongly in LGd. Limits: one
session, 120 test trials per seed, and gratings are a different stimulus
class with their own temporal drive, so the long windows test the decoder
on stimulus-locked timing as much as on intrinsic timescales; the natural
movies, continuous and without repeats of short presentations, would be
the next stimulus to try.

## The state split in the thalamus: LGd keeps its profile when the mouse runs (12 Nov 2026)

The behavioural-state section could not split LGd into running and
stationary trials: in both sessions with LGd the mouse ran on too few
trials. Session 750749662 (the gratings session above) runs on 0.28 of
natural-scenes trials, with 4 of the 118 images shown fewer than 8 times
while running. `scripts/latency_readout.py --state-drop-short 5` drops
those four images from both states and runs the split on the remaining
114 (1,632 trials per state, the stationary set subsampled to the running
set's size), same pyramid, decoder and seeds as before
(`latency_allen_750749662_<area>_split.json`; the state covariates are in
the `_state` files, and as in every other sample they decode at chance
and leave the details unchanged).

| area | running, L1 to L6 (250 to 5 ms) | stationary, L1 to L6 | running / stationary at 50 ms | 5 ms level / 50 ms level, running / stationary |
| --- | --- | --- | --- | --- |
| VISp | 0.481 0.540 0.561 0.543 0.490 0.418 | 0.174 0.184 0.188 0.182 0.167 0.134 | 3.0 | 0.74 / 0.71 |
| LGd | 0.137 0.170 0.193 0.208 0.202 0.175 | 0.053 0.063 0.080 0.066 0.053 0.054 | 2.4 | 0.90 / 0.68 |
| LP | 0.022 0.022 0.023 0.028 0.023 0.024 | 0.015 0.013 0.015 0.015 0.016 0.016 | 1.5 | 1.03 / 1.04 |

Chance is 0.009 with 114 images; each accuracy rests on about 330
held-out trials.

**Locomotion scales this animal's responses far more than the others'.**
At the 50 ms level the running trials decode 3.0 times better in VISp and
2.4 times better in LGd, against 1.12 to 1.98 in the three earlier
animals; stationary VISp here decodes the image at only 0.19.

**In running trials LGd shows the thalamic profile and VISp the cortical
one.** VISp peaks at 50 ms in both states and falls to 0.74 (running) and
0.71 (stationary) of that by 5 ms. Running LGd peaks at 25 ms and is flat
from 50 to 10 ms (0.193, 0.208, 0.202), keeping 0.90 of its 50 ms
accuracy at 5 ms: the flat, finer-reaching profile of the four thalamic
samples, now in a fifth thalamic sample and within one behavioural state.
Stationary LGd is too weakly informative here (0.05 to 0.08) to resolve
its profile: it peaks at 50 ms, but the difference from 25 ms is about
one standard error. LP in this animal is barely driven by the natural
scenes (0.02 in both states) and says nothing.

**Reading.** The thalamus-against-cortex difference is not a product of
the mixture of behavioural states in the trials: within running trials,
in one animal, LGd reaches finer than VISp. Whether it holds as clearly
in stationary trials needs a session with a more informative stationary
LGd; this one cannot say.

## Caveats

- Synthetic codes are easy (the continuous pyramid is at 1.00), so they test
  localization better than retention.
- 60 epochs on CPU, 2 synthetic seeds and 5 real-data unit subsamples. Not tuned.
- Five Allen sessions, one per animal, sixteen area samples. The published
  comparison is against seven other sessions' distribution, not the same
  sessions, and random folds inflate the estimate by an amount that varies
  by session (0.00 to 0.25).
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
  time, not mixtures. The rate regression of the detail section is linear
  and uses the window count only; the nonlinear version (random-feature
  kernel ridge on the population rate vector, section above) removes a few
  hundredths more and leaves the details above the control in every seed.
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
  existence of a latency or transience code. The explicit latency readout
  (section above) finds that first-spike latency and centre of mass
  account for a third to a half of the rate-independent 125 ms detail and
  a fifth of the 50 ms detail, and that what remains is above the control
  in every seed of every sample.
- The comparison across areas is within five sessions (one per animal);
  the amount of information per area varies with the penetration (VISal is
  half of VISp in one animal and equal to it in the other; VISam is 0.20 in
  one and 0.44 in the other), so between-area differences in amount mix
  area and sampling, and so can the shape of a sparse sample (the first
  VISam's tilt). VISpm and VISrl were each seen in one animal; VISam, LGd
  and LP in two; VISp in five.

## Suggested next steps

1. Gate 2 is not met and the matched-bits baseline shows why: the bottleneck
   shape, not the learning, limits both, with the learned codes about 0.03
   ahead. If the tokenizer is to be kept, the change is architectural:
   per-unit or per-group codebooks (a code per unit per bin, or per small
   group) so the bit budget scales with the population, or codebooks in the
   thousands with product quantization. Otherwise reframe around the
   analysis, with the quantized pyramid as a drop-in tokenizer.
2. Done on 11 Nov 2026 (sessions 798911424, 754829445 and 763673393; four
   animals in all): the 50 ms optimum, the three-scale multiplexing and the
   rate-regression result hold in every cortical sample (VISp in four
   animals, VISam in two, VISl, VISal, VISrl, VISpm). LGd is one level finer
   in both animals (25 ms optimum, 10 ms jitter cost, a decodable 10 ms
   detail); the first VISam's tilt toward 125 ms did not replicate in the
   second. LP in a second animal (757216464, 116 units) replicates the
   flat 50 to 10 ms profile and the 25 ms share, so the thalamus differs
   from cortex in the same direction in all four thalamic samples. The
   explicit latency readout is done (11 Nov): the details are not reducible
   to first-spike latency or centre of mass, nor to the timing of the
   population response as a whole. Running and pupil as covariates (11
   Nov) explain none of it, and the pyramid's profile is the same within
   running and within stationary trials, with locomotion scaling the
   information up. A nonlinear rate regression (11 Nov, random Fourier
   features of the population rate vector) removes a few hundredths more
   than the linear one. Drifting gratings (12 Nov, session 750749662):
   the 50 ms onset optimum does not depend on the next stimulus, and in
   long windows the count catches up in cortex but not in LGd. Nothing
   from this list is open. The state split in the thalamus (12 Nov, same
   session): running LGd keeps the flat, finer-reaching thalamic profile;
   stationary LGd is too weak there to resolve. Candidate beyond it: the
   natural movies as a continuous stimulus.
3. Done on 11 Nov 2026 (rate-regressed details): about half of the 125 and
   50 ms detail information survives regression on the population rate
   vector. The nonlinear version (11 Nov, kernel ridge on random Fourier
   features of the rate vector) removes a few hundredths more; the
   remainder is not a nonlinear function of the count.
