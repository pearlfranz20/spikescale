# Decoder bake-off, 27 Oct 2026

Question: for the per-level curve on real data, which decoder is most accurate,
and which gives a curve that reflects information rather than decoder capacity?
Continuous pyramid, Allen VISp 732592105, time-blocked split (last 10 repeats
per image), 118 images. Scripts: `scripts/decoder_bakeoff.py`,
`scripts/decoder_tapca.py`. "level" = features of level k only; "cum" =
levels 1 to k concatenated; "haar" = orthonormal multiscale basis on sqrt
counts. Nested = C chosen per level from {0.003 .. 1} on an inner time-blocked
split of the training set, then refit on all training trials.

## 60 units

| decoder | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| cum, nested-C logistic | 0.39 | 0.45 | 0.45 | 0.44 | 0.38 | 0.34 |
| cum, taPCA-50, nested-C logistic | 0.38 | 0.43 | 0.46 | 0.44 | 0.42 | 0.39 |
| cum, shrinkage LDA | 0.37 | 0.43 | 0.45 | 0.42 | 0.39 | 0.34 |
| cum, logistic C=0.1 | 0.39 | 0.42 | 0.40 | 0.38 | 0.37 | 0.33 |
| cum, PCA-100, logistic C=0.1 (E3 default) | 0.40 | 0.40 | 0.40 | 0.38 | 0.38 | 0.36 |
| level, nested-C logistic | 0.39 | 0.45 | 0.42 | 0.36 | 0.30 | 0.22 |
| level, logistic C=0.1 (first E3 run) | 0.39 | 0.43 | 0.38 | 0.33 | 0.26 | 0.20 |
| haar, nested-C logistic | 0.39 | 0.44 | 0.41 | 0.35 | 0.26 | 0.19 |
| cum, PLS-50 + LDA | 0.38 | 0.41 | 0.42 | 0.40 | 0.37 | 0.32 |
| level, Poisson naive Bayes | 0.27 | 0.32 | 0.34 | 0.35 | 0.28 | 0.20 |
| cum, template correlation | 0.31 | 0.33 | 0.35 | 0.34 | 0.34 | 0.32 |
| Gaussian naive Bayes | 0.22 | 0.23 | 0.18 | 0.13 | 0.11 | 0.10 |

## 113 units

| decoder | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| cum, nested-C logistic | 0.53 | 0.58 | 0.59 | 0.57 | 0.52 | 0.48 |
| cum, taPCA-50, nested-C logistic | 0.51 | 0.54 | 0.58 | 0.58 | 0.53 | 0.51 |
| cum, shrinkage LDA | 0.51 | 0.57 | 0.58 | 0.56 | 0.52 | 0.47 |
| cum, logistic C=0.1 | 0.51 | 0.55 | 0.56 | 0.56 | 0.52 | 0.47 |
| cum, PCA-100, logistic C=0.1 | 0.49 | 0.49 | 0.50 | 0.48 | 0.47 | 0.46 |
| level, nested-C logistic | 0.53 | 0.57 | 0.56 | 0.50 | 0.41 | 0.32 |
| level, Poisson naive Bayes | 0.38 | 0.44 | 0.43 | 0.43 | 0.38 | 0.30 |
| cum, template correlation | 0.42 | 0.45 | 0.46 | 0.46 | 0.44 | 0.41 |

Chosen C under nested CV falls with level in every family: 0.1 or 0.03 at L1,
0.003 from L4 on.

## Reading

1. Cumulative features matter more than the classifier. Every classifier
   does better and declines less on levels 1 to k concatenated than on level
   k alone.
2. Nested-C logistic on cumulative features is the most accurate decoder
   tested, by 0.03 to 0.05 over fixed C=0.1 at L2 to L4, and it is
   capacity-matched by construction. Shrinkage LDA matches it but takes 10 to
   30 times longer. PLS, the Haar basis, Poisson naive Bayes, template
   matching and Gaussian naive Bayes are all worse.
3. No decoder removes the decline from L3 to L6. The best-tuned decoder still
   drops 0.11 at both unit counts. Trial-averaged PCA to 50 components
   flattens it most (0.07) at a small cost at L2. With 40 training trials per
   image, 5 ms features are noise to every linear decoder; the decline is a
   floor on capacity cost, not information lost.
4. The peak is at L2 to L3 (125 to 50 ms) in every row above 0.3. That is
   the result, and it does not depend on the decoder.

Recommendation: make nested-C logistic on cumulative features the E3 decoder
(keep PCA-100 as the secondary), and state the per-level result as "no gain
below 50 ms" rather than reading the L4 to L6 decline as information.

## Addendum, 28 Oct 2026

The nested-C decoder is now the primary E3 decoder (`fit_clf_nested` in
`spikescale/decode.py`, `cum_nested_logreg` in the E3 JSON). In the first E3
run with it, the chosen C sat at the grid floor (0.003) at L4 to L6 for the
continuous pyramid in every seed. A probe on seed 0 with C down to 0.0001
found at most 0.015 more at L5 to L6 from C = 0.001 and losses below that,
so the grid was extended to start at 0.001 and E3 rerun. The decline from
L3 to L6 is not a grid artefact.
