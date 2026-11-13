# The temporal scale of image information in mouse visual cortex and thalamus

*Summary of the spikescale analyses, 13 Nov 2026. The full record, with
every table, control and revision in the order it was run, is
`results/RESULTS.md`; where the two differ, this summary reflects the
later analyses.*

## Abstract

We decoded natural-image identity from Allen Brain Observatory Neuropixels
recordings one temporal scale at a time. Each population response was
reduced to a pyramid of spike counts pooled at 250, 125, 50, 25, 10 and
5 ms, decoded with a capacity-matched linear classifier, and split into
orthogonal per-scale components so that each scale's unique contribution
could be measured.

Across 25 cortical samples (six visual areas, twelve mice), image identity
is read best with 50 ms bins in 24. Structure at 125 and 50 ms adds 0.03 to
0.11 accuracy over the whole-window count, and nothing is added below
25 ms. The 125 and 50 ms components are each decodable on their own, and
about half of their information survives regression on the population
firing rate, linear or nonlinear. First-spike latency and response centre
of mass account for part of the rest but not all of it. The profile is the
same in running and stationary trials and on a natural movie without
stimulus onsets.

Thalamic samples (LGd and LP, 13 samples) keep more of their accuracy in
fine bins, but they also fire faster. When thalamic spikes are randomly
thinned to the same animal's cortical rate, half of that difference
disappears and is no longer significant (p = 0.057). Within animals, after
correction over four tests, the thalamus still carries more image
information in 25 ms structure that no coarser scale contains (0.22
against 0.16 of the count, p < 0.001, 9 of 11 mice). It also reads a
natural movie better at 10 ms relative to its best bin width (Holm
p = 0.013) and gains more from timing over 2 s of drifting grating (Holm
p = 0.013).

A kernel SVM and convolutional networks read less than the linear decoder
at every bin width. A spike-level transformer trained across all 39
populations at once (184,000 trials) reads no more from spike times at
1 ms than from the same spikes rounded to 25 ms (-0.004, 13 of 39
recordings higher), although 25 to 250 ms timing is worth 0.08 to it. On
this data, no decoder tried finds image information below 25 ms. A learned multiscale spike tokenizer, the project's starting
point, kept under half of the decodable information and beat plain
k-means quantization by only about 0.03.

## 1. Question

A population response to a briefly shown image can carry information in
how many spikes each neuron fires, and in when within the response it
fires them. Which temporal scales carry information that coarser scales
do not? Is that a property of the stimulus, the brain area or the
animal's state? And how much of an apparent timing code is firing rate,
or response latency, in disguise? The analysis began as a test of a
multiscale tokenizer for spikes (Section 7) and became a decoding study
of these questions.

## 2. Data and methods

**Recordings.** Allen Brain Observatory Visual Coding Neuropixels (Brain
Observatory 1.1), 12 sessions, one per mouse. Units pass the Allen quality
filters.

| set | samples | mice | what was run |
| --- | --- | --- | --- |
| full pipeline | 19 (VISp ×6, VISl, VISal ×2, VISrl, VISpm, VISam ×2, LGd ×3, LP ×3), of which 18 are driven by the scenes | 6 | everything below; latency, state and nonlinear-regression analyses on the 16 samples of the first 5 mice |
| tissue test | 38 scenes samples (25 cortical, 13 thalamic) | 12 (11 with both tissues) | pyramid and per-scale details on scenes; movie and gratings on 29 samples in 10 mice |

**Stimuli.**
- Natural scenes: 118 images, 50 repeats, 250 ms each, back to back. The
  window is 0 to 250 ms from onset.
- natural_movie_one: 30 s, 20 repeats, cut into 120 segments of 250 ms or
  30 segments of 1 s.
- Drifting gratings: 40 conditions, 15 repeats, 2 s.

**Readout.** 60 units are subsampled per seed, with 5 seeds, and the
same subsets are used for every analysis of a sample. The held-out set is
time-blocked: the last 20% of every stimulus's repeats, so slow drift
cannot inflate accuracy. Random folds inflate it by 0.00 to 0.25 depending
on session.

The *pyramid* at level k is the concatenated log1p spike counts pooled to
each bin width down to level k's (250, 125, 50, 25, 10, 5 ms in the scenes
window). It is decoded by an L2 logistic regression whose penalty is
chosen per level on an inner time-blocked split, which matches decoder
capacity across levels. This decoder won a comparison of twelve
(`notes/decoder_bakeoff.md`).

The *detail* at level k is the part of a unit's 5 ms response at level k
that is orthogonal to all coarser levels. It is decoded alone, against a
control in which each unit's 5 ms bins are shuffled within the trial. The
control keeps the counts and destroys the timing.

**Controls.**
- Spike jitter of 5, 10 and 25 ms.
- Regression of the details on the population rate vector, linear and
  kernel (random Fourier features).
- Regression on per-unit first-spike latency and centre of mass, and on
  population response timing.
- Running and pupil covariates, and decoding within running or stationary
  trials.
- For the tissue comparison: permutation of thalamus/cortex labels within
  animals, a hierarchical bootstrap, Holm correction over four primary
  metrics fixed in advance, and random spike thinning of each thalamic
  sample to the mean firing rate of the same animal's cortex.

**Sanity check against published decoding.** Under the published protocol
(all units, random 10-fold), VISp of the first session decodes the 118
images at 0.63. The closest published single-area figure is 0.31 to 0.55
over seven sessions ([arXiv 2510.09451](https://arxiv.org/html/2510.09451v1)),
so the extraction and decoder are not the weak link.

## 3. Results

### 3.1 Cortex reads natural images at 50 to 125 ms

In the first session's VISp, the pyramid decodes 0.40 from the
whole-window count, rises to 0.47 at 50 ms bins and falls to 0.37 at 5 ms.
Jitter of 5 ms changes nothing, and 25 ms jitter costs the best level
0.01. Across all 25 cortical samples, from VISp to VISam, the best bin
width is 50 ms in 24; the exception is a VISam at 25 ms. The gain from
count to 50 ms is 0.03 to 0.11. No cortical sample gains from bins finer
than 25 ms. The fall below 50 ms is the capacity cost of finer features
for a linear decoder with about 40 training trials per image, so it marks
where information stops being added, not information being lost.

Within cortex the scale does not change along the hierarchy. VISp, VISl,
VISal, VISrl, VISpm and VISam share one profile wherever they are
informative. An earlier VISam that tilted toward 125 ms did not replicate
in a second animal.

### 3.2 Three scales carry unique information

Decoded alone, each orthogonal detail of VISp (60 units) identifies the
image at 0.41 (count), 0.21 (125 ms), 0.17 (50 ms), 0.07 (25 ms),
0.05 (10 ms) and 0.03 (5 ms). The time-shuffled control is 0.02 at every
level from 125 ms down. So the 125 ms shape (one number per unit, the
second half of the window against the first) and the 50 ms shape each
carry a large share that is not in any coarser description. 25 ms carries
a small share, 10 ms a trace, and 5 ms is within the control.

### 3.3 The shape information is not rate, not latency and not state

- **Rate.** After the 125 and 50 ms details are regressed on every unit's
  whole-window count, about half of their accuracy remains. That is 0.43
  to 0.75 (125 ms) and 0.40 to 0.83 (50 ms) of the unregressed accuracy
  across 16 samples, above the control in every seed of every sample. A
  kernel regression on the rate vector removes only a few hundredths more.
- **Latency.** Per-unit first-spike latency and centre of mass decode the
  image on their own (0.06 to 0.38), but add nothing to the count. They
  account for about a third to a half of the rate-independent 125 ms
  detail and about a fifth of the 50 ms detail. The remainder, 0.03 to
  0.09 absolute, is above the control in every seed of every sample.
  Population-level response timing decodes the image at 0.011 to 0.019
  (chance 0.008) and removes nothing. What remains is how each unit's
  response is distributed within the window relative to the others: one
  peak or two, decay, rebound.
- **Behavioural state.** Running and pupil decode the image at chance and
  leave the details unchanged. Trials with the mouse running decode 1.1
  to 3.0 times better at the 50 ms level than stationary trials with the
  same trial count, but the best bin width is 50 ms in both states in
  every cortical sample tested (125 ms ties it in one stationary VISp).

### 3.4 The scale belongs to the response, not the presentation

Natural scenes play back to back, so every window ends where the next
image begins. Two other stimuli separate the profile from that boundary:

- **Natural movie, no onsets.** In 250 ms segments, cortex is read best
  at 50 ms in 15 of 17 samples (Figure 2A).
- **Drifting gratings, a stimulus with its own fast drive.** In the first
  250 ms of a grating, cortex is read as well at 10 to 25 ms as at 50 ms
  in two of the three animals examined, and no window is read better with
  coarser bins. Over 2 s, cortex gains 0.01 to 0.22 from timing over the
  count, and the thalamus gains more (Section 3.5, Figure 2C).

So the 50 ms optimum is not set by the next image, and the fall of
cortical accuracy below 50 ms is specific to natural images, flashed or
continuous.

### 3.5 Thalamus against cortex: rate explains half of it

The thalamic samples look finer than cortex on every measure. On the
scenes their pyramid is flatter from 50 to 10 ms (10 ms over 50 ms
accuracy 0.95 against 0.88) and 11 of 13 are read best at 25 ms or
finer. But thalamic units fire faster: about 10 against 7 Hz in the
decoding windows. Spike thinning tests what that does. Each thalamic
sample's spikes are deleted at random, keeping their times, until it
fires at the mean rate of the same animal's cortex. The tissue test is
then rerun with the same cortex and samples.

| claim (primary metrics fixed in advance) | thalamus / cortex, original | difference at matched rate [95% CI] | p within animals, Holm-corrected, matched rate | mice in the thalamic direction |
| --- | --- | --- | --- | --- |
| scenes: 10 ms accuracy / 50 ms accuracy | 0.951 / 0.883 | +0.034 [-0.009, +0.070] | 0.057 | 8 of 11 |
| scenes: 25 ms detail alone / count | 0.238 / 0.157 | +0.064 [+0.024, +0.112] | 0.0003 | 9 of 11 |
| movie, 250 ms segments: 10 ms level / best level | 0.945 / 0.857 | +0.062 [+0.019, +0.105] | 0.013 | 9 of 10 |
| gratings, 2 s: best level minus count | 0.196 / 0.105 | +0.097 [+0.007, +0.196] | 0.013 | 8 of 10 |

The within-animal p values come from permuting the tissue labels within
each mouse, so differences between animals cannot produce them.

**Firing rate accounts for:**
- About half of the flatness, which drops from +0.067 to +0.034 and loses
  significance.
- Most of the shift in optimum: at matched rate, 6 of 13 thalamic samples
  peak at 25 ms and the rest at 50 ms, with the two levels within about
  0.01 in most.
- All of the 5 ms difference (+0.089 to +0.027, p = 0.26).

**What survives rate matching is in the temporal structure itself:**
- A larger share of image information in the 25 ms component orthogonal
  to every coarser scale (Figure 2D).
- Better reading of the movie at fine bins.
- A larger gain from timing over a long grating, which thinning does not
  reduce at all.
- A finer best bin width in 1 s movie segments: about 45 against 135 ms
  (geometric means), p = 0.001, 9 of 10 mice, a secondary metric.

LGd shows this more cleanly than LP. Two LP samples that the scenes
barely drive are as steep below 50 ms as cortex, though their 25 ms share
is the largest of all 38 samples.

### 3.6 A better decoder does not find more

| sample | decoder (3 seeds) | 50 ms | 5 ms |
| --- | --- | --- | --- |
| VISp | linear (nested-C logistic) | 0.460 | 0.357 |
| VISp | Gaussian-kernel SVM | 0.432 | 0.328 |
| LGd | linear | 0.687 | 0.646 |
| LGd | Gaussian-kernel SVM | 0.680 | 0.617 |

The SVM's kernel width and penalty were chosen on the same inner split as
the logistic's penalty. It is below the linear decoder in 11 of 12 seed
and width pairs, with the same profile across bin widths. Temporal
convolutional networks, with and without a linear path, did worse
(0.37 to 0.40 at 50 ms in VISp): with about 32 training trials per image
they overfit within a few epochs.

**More training data.** All 39 populations (25 cortical, 14 thalamic,
3504 units) saw the same 118 images, so one decoder can be trained on all
of them: 184,080 training trials instead of about 4,700. A Perceiver over
individual spikes (after POYO, Azabou et al. 2023; a learned embedding per
unit, a time encoding per spike, one shared classifier, 1.5 M parameters)
was trained with every spike time rounded to the centre of a W ms bin, so
that it could use timing down to W ms and no finer. Same test trials as
everywhere, mean over the 39 recordings:

| spike times given at | 1 ms | 10 ms | 25 ms | 50 ms | 250 ms |
| --- | --- | --- | --- | --- | --- |
| transformer (seeds 0, 1) | 0.381, 0.379 | 0.381 | 0.386, 0.382 | 0.380 | 0.302 |

Paired across recordings, 1 ms is no better than 25 ms (-0.004, 13 of 39
higher, p = 0.03 in the wrong direction), 25 ms is slightly better than
50 ms (+0.006, 27 of 39, p = 0.006, carried by cortex: the small 25 ms
component of Section 3.2), and timing above 25 ms is worth +0.08 in every
recording. The transformer is 0.035 below a linear decoder on all units of
each recording (0.419 at its best level), and by about as much on
whole-window counts alone (0.302 against 0.335). Its deficit is in reading
which units fire, not in timing, and its comparison across resolutions is
internal: the same model and training at every W.

## 4. Figures

- Figure 1, `results/summary.png`: the 18 fully analysed samples. It shows the
  pyramid relative to its 50 ms level, each detail as a share of the
  count, the details before and after rate and timing regression, the
  10 ms jitter cost, and learned codes against k-means. It predates the
  rate-matching control: the thalamic flatness it shows is half rate
  (Section 3.5).
- Figure 2, `results/summary_stimuli.png`: (A, B) the natural movie in 250 ms and
  1 s segments and (C) drifting gratings over 2 s, for the 29 movie and
  gratings samples, thalamus unthinned. (D) The 25 ms detail share per
  sample and animal, with the thalamus at its animal's cortical firing
  rate (hollow markers: before thinning).

## 5. Discussion

**Relation to earlier work.** That image information in mouse visual
cortex sits at 50 to 125 ms agrees with NeuroPixelHD
([Frontiers in Cellular Neuroscience, 2024](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10899419/)).
That study decoded the same 118 images and found 125 ms bins best
across the brain. It also reported the optimum shifting along the
sensory-to-associative hierarchy; within visual cortex we do not see that
shift, though the samples per higher area are few. The overlap of the
125 and 50 ms details with response transience and latency places them in
a long line of work on temporal waveform and latency codes (Optican and
Richmond 1987; Reich, Mechler and Victor 2001; Gollisch and Meister 2008).
What this analysis adds is the per-scale decomposition at the population
level, the matched-capacity decoder, and the rate, latency and state
controls that leave a component no summary of rate or response timing
explains.

That the thalamus is more temporally precise than cortex is well
established for single LGN neurons (e.g. Reinagel and Reid 2000; Butts
et al. 2007). The population-level version here is a caution as much as a
replication. The most visible thalamic difference, keeping accuracy in
fine bins, is half firing rate. Any decoding comparison across areas with
different rates needs a rate-matched control before reading timing into
it.

**What the results do and do not say.** The per-scale claims are about
what a capacity-matched linear readout of 60 units can recover with about
40 training trials per image. Within that, every decoder tried agrees:
little below 25 ms in cortex, a real but small 25 ms component, and a
thalamus whose extra 25 ms structure survives rate matching. Whether
spikes carry more below 25 ms than such decoders can reach was then put to
a decoder trained across all 39 populations at once, on individual spike
times, after the POYO family. With forty times the training data it also
finds nothing below 25 ms. That decoder is below the linear one in
absolute accuracy, so it is not the strongest possible test; a model
pretrained on far more sessions, or on other stimuli and spontaneous
activity, could still differ. But every readout tried, linear, kernel,
convolutional and transformer, now agrees.

## 6. Limitations

- **Sessions.** One session per mouse. Six of the twelve mice were added
  for the tissue test and run with scenes, movie and gratings readouts
  only, without the latency, state and regression analyses.
- **Areas.** Most higher cortical areas are represented by one to three
  samples. LP is weakly driven by natural scenes in several animals.
- **Gratings sample size.** Gratings and movie results rest on 120 to
  600 held-out trials per seed. Differences under about 0.04 on gratings
  are noise.
- **Spike thinning.** It matches the population mean rate only, not how
  rate is spread across units. Random deletion adds count noise that a
  naturally slower population need not have, so the rate-matched
  thalamic numbers are, if anything, a lower bound.
- **Cross-session transformer.** One architecture and one setting of its
  training, chosen on validation accuracy at 25 ms and kept for all
  resolutions; two seeds at 1 and 25 ms, one at 10, 50 and 250 ms. It
  stays 0.035 below the linear decoder, so its null below 25 ms is weaker
  evidence than a null from a decoder at least as strong as the linear one.
- **Tissue test.** The scenes within-animal p values are estimated from
  200,000 random relabellings. The movie and gratings ones are exact.

## 7. The tokenizer: a negative result

The project began as a test of a multiscale residual vector-quantized
tokenizer for spikes, with one discrete code per time bin at six
resolutions, following the idea of next-concept modeling. On synthetic
data with planted codes, information first appeared at the planted scale
in every condition, and the retention criterion passed in 6 of 7.

Its second gate was a clear win over residual k-means at matched bits,
and it failed it. On real data the learned codes lead k-means by about
0.03, and both discrete readouts keep under half of what the continuous
pyramid decodes (0.23 against 0.47 in VISp). One code of 32 to 128
entries per time bin cannot represent a 60-unit population. Codebooks
are fully used, so the bottleneck is the shape of the code, not the
training. A tokenizer worth keeping would need per-unit or per-group
codes, as current spike foundation models use per-spike or per-unit
tokens.

## 8. Reproducing

Extraction runs in a separate AllenSDK environment (see `README.md`).
The main scripts:

| script | role |
| --- | --- |
| `run_e3.py` | pyramid, tokenizer and E3b controls per sample |
| `residual_levels.py` | per-scale details and rate regression |
| `latency_readout.py` | latency, state and nonlinear regression |
| `gratings_pyramid.py` | gratings, movie and scenes readouts on the same units, with `--thin-to` for rate matching |
| `rates_tissue.py` | per-sample rates and thinning targets |
| `stats_tissue.py` | the tissue test (`--thinned` for rate-matched) |
| `nonlinear_svm.py`, `nonlinear_timing.py` | the nonlinear decoders |
| `pack_spikes.py`, `spike_transformer.py` | the cross-session spike transformer (GPU), `--res` for the time resolution |
| `linear_allunits.py` | its linear baseline on all units |
| `plot_summary.py`, `plot_stimuli.py` | figures |

Every number above is in a JSON under `results/`, named for its session
and area.
