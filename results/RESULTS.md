# Results so far, 23 Oct 2026

All on synthetic data: 60 units, 16 stimuli, 100 trials each, time-blocked
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

## Caveats

- Synthetic codes are easy (the continuous pyramid is at 1.00), so they test
  localization better than retention.
- 60 epochs on CPU, 2 seeds. Not tuned.
- No real data yet. Allen hosts are unreachable from the build environment.

## Suggested next steps

1. Run E3 on one Allen session locally (README, "Real data").
2. Before more tuning, decide whether gate 2 can still be met. Options:
   longer training, codebooks fit to the quantized-pyramid init, or reframing
   the project around the analysis (E2 and E3b) with the quantized pyramid as
   the tokenizer.
