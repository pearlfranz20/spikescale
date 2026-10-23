# Tokenizer diagnostics, 23 Oct 2026

How the first working tokenizer was reached, and why the design differs from the
reviewed plan in four places. Every number below comes from the synthetic rate
code (60 units, 16 stimuli, 100 trials each, chance 0.06) or the 25 ms timing
code, decoded on time-blocked held-out trials.

## Starting point

The tokenizer as planned: nonlinear pointwise encoder, d = 16, EMA codebooks of
32 to 128 entries, single-scale Poisson NLL on 5 ms bins.

| readout at level 1, rate code | accuracy |
| --- | --- |
| Binning pyramid, continuous counts | 1.00 |
| Tokenizer codes | 0.21 |

The tokenizer kept almost none of the easiest possible code.

## What was wrong, in the order found

1. **5 ms Poisson noise swamps the training signal.** Knowing the true
   stimulus only improves held-out NLL from 0.3444 to 0.3390, a 1.6% change.
   A single-scale reconstruction loss barely rewards learning the stimulus.
   *Fix:* score each level's reconstruction against counts pooled to that
   level's own length (multiscale loss).

2. **Level weighting bug.** The first multiscale loss divided each term by
   T / L_k, which shrank the level-1 term 50x. *Fix:* no rescaling.

3. **Dead-code restarts fired every step.** The restart threshold was
   hard-coded (the config field was never used). At level 1 a batch gives only
   about 2 vectors per code, so codes were reshuffled constantly. *Fix:*
   restart only codes unused over a 100-step window.

4. **Capacity was not the problem.** Codebooks 4x and 16x larger only reached
   0.28 and 0.36. A no-learning baseline, residual k-means on pooled
   log-counts with the same 5 bits at level 1, reached 1.00. Each level-1 code
   mixed about 5 stimuli, so the learned latent itself was the problem.

5. **The nonlinear pointwise encoder broke pooling.** Level 1 is the
   time-average of f(x_t). With a nonlinear f applied to sparse 5 ms spike
   vectors, that average is a poor summary of counts. Even the unquantized
   latent decoded at only 0.58. Warm-up and k-means init did not help on their
   own. *Fix:* a linear 1x1 encoder, so pooling commutes with encoding and level
   k sees a projection of counts pooled at its own timescale. The decoder stays
   nonlinear.

## Result after the fixes

| condition | levels 1 to 6, code readout |
| --- | --- |
| rate, d = 16 | 0.91 0.91 0.89 0.89 0.80 0.80 |
| rate, d = 32 | 0.91 0.91 0.91 0.88 0.83 0.86 |
| timing 25 ms, d = 16 | 0.03 0.06 0.06 0.88 0.89 0.89 |
| timing 25 ms, d = 32 | 0.06 0.04 0.05 0.90 0.96 0.98 |

The timing code now appears exactly at level 4 (25 ms bins) with nothing
before it. d = 32 is the new default.

## Changes to the reviewed design

| plan said | now | why |
| --- | --- | --- |
| 1D conv encoder (nonlinear) | linear 1x1 encoder | item 5 |
| Poisson NLL on 5 ms bins | NLL on counts pooled to each level | item 1 |
| d = 128 to start (draft), 16 in first code | d = 32 | best of 16 and 32 |
| EMA codebooks, FSQ fallback | EMA plus a third of training as unquantized warm-up, k-means init, windowed restarts, commitment 0.05 | items 3 and 4, standard VQ practice |

Also added: a **quantized pyramid** baseline (residual k-means on pooled
log-counts, same level lengths and codebook sizes). This is the true
matched-bits baseline that gate 2 calls for. The continuous pyramid has
unbounded bits and is a ceiling, not a matched comparison.

## Open concern

The quantized pyramid already reaches 1.00 on the rate code with no learning.
If it matches the tokenizer everywhere, gate 2 fails and the project becomes the
negative result the plan anticipated. The full E2 run compares both.
