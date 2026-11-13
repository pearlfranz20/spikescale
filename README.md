# spikescale

Where in time does a population's stimulus information sit? This repository
decodes image identity from Allen Neuropixels responses one temporal scale at
a time, from whole-window counts down to 5 ms bins, and asks which scales
carry information that the coarser ones do not. The answer so far, in eighteen
area samples from six mice analysed in full (VISp, VISl, VISal, VISrl, VISpm,
VISam, LGd, LP): one profile across cortex from VISp to VISam, a 50 to 125 ms code
with the 125 ms and 50 ms shapes each decodable on their own, about half
of that shape information not a linear function of firing rate, a small
component at 25 ms and nothing at 5 ms. The thalamus reads finer. Twenty
more samples from seven mice, added to test this, bring the count to 38
samples (13 thalamic) in twelve mice, eleven of them with both tissues.
The thalamus also fires faster (about 10 against 7 Hz), and thinning its
spikes at random to the same animal's cortical rate separates two effects.
That the thalamus keeps more of its 50 ms accuracy at 10 ms (0.95 against
0.88) is about half firing rate: at matched rate the difference halves
and is no longer significant (p = 0.057). What survives rate matching is
in the fine temporal shape. Within animals and after correction over four
tests, the thalamus carries a larger share of image information in 25 ms
structure that no coarser scale contains (p < 0.001, 9 of 11 mice),
reads the natural movie better at 10 ms relative to its best (9 of 10
mice) and gains more from timing over 2 s of grating (Holm 0.013 for
both).

Two more stimuli bound the claim. On the natural movie, which has no
stimulus onsets, cortex is still read best at 50 ms in 250 ms segments
(15 of 17 samples), and over 1 s segments the thalamus is read best at
about 30 ms against about 130 ms in cortex. On drifting gratings, which
carry their own fast drive, cortex is read as well at 10 to 25 ms as at
50, so the fall of cortical accuracy below 50 ms belongs to natural
images; over 2 s of grating the thalamus gains more from timing over the
count (0.20 against 0.11; unchanged at matched rate)
(`results/RESULTS.md`; figures in `results/summary.png` for the six mice
analysed in full and `results/summary_stimuli.png` for all).

The analysis started as a test of a multiscale residual VQ tokenizer for
spikes, which is kept as one of four readouts. Its gate was a clear win over
residual k-means at matched bits, and it did not pass: learned codes lead
k-means by about 0.03 in VISp and less elsewhere, and both discrete readouts
keep under half of what the continuous pyramid decodes, because one code of
32 to 128 entries per time bin is too narrow a bottleneck for a 60-unit
population. The pyramid of pooled counts is the primary readout for the
per-scale question; the tokenizer results are reported in full.

Level k of the tokenizer pools the population response to L_k bins and adds a
discrete code at that resolution. Levels run from one code for the whole
250 ms window to one code per 5 ms bin:

| level | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| codes per window | 1 | 2 | 5 | 10 | 25 | 50 |
| bin width (ms) | 250 | 125 | 50 | 25 | 10 | 5 |
| codebook size | 32 | 64 | 64 | 128 | 128 | 128 |

Decoding the stimulus from levels 1 to k, level by level, shows where the
information appears. The idea follows Next-Concept Modeling
([arXiv 2610.14162](https://arxiv.org/abs/2610.14162)), applied to spikes.

## Status

- [x] Synthetic spike generator with planted codes at known timescales (validated)
- [x] Tokenizer, pyramid baselines, per-level decoding
- [x] E2 on synthetic data (gate 1), see `results/`
- [x] E3 and E3b on one Allen Visual Coding Neuropixels session (VISp), see `results/`
- [x] Quantized pyramid and PCA decoder in E3; comparison with published VISp decoding
- [x] Decoder bake-off; nested-C cumulative logistic as the E3 decoder
- [x] E3 figure; published comparison rerun with the nested-C decoder
- [x] Unique information per scale: each level's orthogonal detail decoded alone, with a time-shuffled control
- [x] Same pipeline on VISal, VISpm and VISrl from the same session: four areas, one 50 to 125 ms scale
- [x] Rate-regressed per-scale details: temporal shape not linearly predictable from firing rate
- [x] Second session 798911424 (VISp, VISl, VISal, VISam; a second animal): same 50 ms optimum, same three-scale multiplexing; VISam tilts toward 125 ms
- [x] Third session 754829445 (VISp, LGd, LP; a third animal): VISp unchanged; LGd tilts finer (25 to 50 ms tie, 10 ms jitter costs accuracy); LP tilts like LGd
- [x] Fourth session 763673393 (VISp, VISam, LGd; a fourth animal): LGd's finer scale replicates (25 ms optimum every seed); VISam's 125 ms tilt does not, this VISam matches VISp
- [x] Fifth session 757216464 (LP, VISp; a fifth animal): LP's flat 50 to 10 ms profile and 25 ms share replicate with 116 units; thalamus against cortex, not hierarchical rank
- [x] Explicit latency readout on all sixteen samples: first-spike latency and centre of mass do not substitute for the pooled counts and leave the 125 and 50 ms details above the control in every seed
- [x] Behavioural state: running and pupil explain none of the detail information; the pyramid's profile is the same within running and stationary trials, locomotion scales it up
- [x] Nonlinear rate regression (kernel ridge on random Fourier features of the population rate vector): removes a few hundredths more than the linear fit; the details stay above the control in every seed
- [x] Drifting gratings (750749662, then 763673393 and 757216464): no window is read better coarser, but the cortical 50 ms peak at grating onset is not robust (flat from 50 to 10 ms in two animals); in 2 s windows the thalamus gains 0.12 to 0.25 from timing, cortex mostly little
- [x] Thalamic state split (same session): within running trials LGd keeps its flat 50 to 10 ms profile while VISp peaks at 50 ms; stationary LGd too weak to resolve
- [x] Full pipeline on the same session's VISp, LGd and LP: VISp inside every cortical range, a weak LGd still thalamic, LP not driven by the scenes
- [x] Natural movie (same session): the 50 ms optimum holds without stimulus onsets; in 1 s segments LGd and LP are best at 50 ms bins, cortex at 125 to 500 ms
- [x] Natural movie in a second animal (763673393): the 250 ms profile and LGd's finer details replicate; 1 s segments at ceiling
- [x] Natural movie in a third animal (757216464): LP reads the movie finer than VISp (25 ms against 50 ms in 250 ms segments, 25 against 250 ms in 1 s segments)
- [x] Thalamus against cortex tested with animals as the unit: complete separation on the scenes (pooled p = 0.0001; 0.028 within animals, the design's floor); movie and gratings same direction, not significant alone
- [x] Seven more sessions with both tissues (scenes, movie and gratings on the same units; twelve mice, eleven with both): all four primary claims survive Holm correction within animals; LGd separates from cortex in every sample, LP on average
- [x] Rate-matched control (thalamic spikes thinned to the same animal's cortical rate): half of the scenes 10/50 flatness is rate and loses significance; the 25 ms detail share, the movie's finer reading and the gratings timing gain survive
- [x] Nonlinear decoders (kernel SVM, convolutional networks) against the linear one: none reads more at any bin width in VISp or LGd; with ~32 training trials per image the linear decoder is the best tested
- ~~E4 fixed-resolution ladder comparison~~ dropped on 1 Nov 2026: what the
  ladder should compare was never written down, and the decoder bake-off and
  E3b already answer the per-level question on real data

## Layout

```
spikescale/
  synth.py       planted-code spike generator (rate, timing at 5 to 125 ms, mixed, 2 ms control)
  tokenizer.py   multiscale residual VQ tokenizer
  decode.py      time-blocked split, one fixed decoder, pyramid baselines
  jitter.py      E3b controls: spike jitter and PSTH-matched surrogates
scripts/
  run_e2.py      E2 synthetic level attribution (gate 1)
  plot_e2.py     E2 figure
  load_allen.py  extract natural-scenes trials from one Allen session
  load_allen_state.py  per-trial running speed and pupil area for an extracted session
  load_allen_gratings.py  drifting-gratings trials (2 s, 40 conditions) for one area
  load_allen_movie.py  natural_movie_one repeats (30 s at 1 ms) for one or more areas
  gratings_pyramid.py  the pyramid on gratings in 250, 1000 and 2000 ms windows, beside the scenes pyramid of the same units;
                       --movie cuts the natural movie into 250 and 1000 ms segments
  run_e3.py      E3 and E3b on an extracted session (codes, recon, both pyramids, four decoders)
  merge_e3.py    merge E3 runs split over seeds
  plot_e3.py     E3 and E3b figure
  compare_external.py  pyramid decoding under random 10-fold CV and all units, to set beside published numbers
  plot_summary.py      cross-sample figure over all area samples (results/summary.png)
  plot_stimuli.py      movie and gratings across animals, and the tissue test (results/summary_stimuli.png)
  stats_tissue.py      thalamus against cortex per claim: exact permutations within animals and pooled, hierarchical bootstrap (--thinned: rate-matched thalamus)
  rates_tissue.py      firing rate per sample and stimulus, and the thalamic thinning targets
  nonlinear_svm.py     Gaussian-kernel SVM on the pyramid features, against the linear decoder
  nonlinear_timing.py  temporal convolutional network on 5 ms bins (overfits at this trial count)
  residual_levels.py   decode from each level's orthogonal detail alone (is the information at a scale unique to it?),
                       with rate-regressed readouts (--readouts detail_unitrate,detail_poprate,shuffled_unitrate --tag rate)
  latency_readout.py   are the 125 and 50 ms details just first-spike latency and centre of mass, per unit or for the population? (no);
                       also running and pupil as covariates and the pyramid within running or stationary trials (--tag state),
                       and the details regressed nonlinearly on the population rate (--tag nonlin)
notes/
  diagnostics.md how the tokenizer design was debugged, and where it departs from the plan
  decoder_bakeoff.md  twelve decoders on the continuous pyramid; why nested-C cumulative logistic is the E3 decoder
```

## Quick start (synthetic, CPU, about 30 minutes)

```bash
pip install -r requirements.txt
PYTHONPATH=. python scripts/run_e2.py --seeds 2 --epochs 60 --out results
python scripts/plot_e2.py results/e2.json results/e2.png
```

## Real data (run locally)

Allen data needs a download of about 2 to 3 GB per session. AllenSDK pins
numpy below 1.24 and pandas 1.5.3, which conflicts with `requirements.txt`, so
it gets its own Python 3.10 or 3.11 venv used only for extraction. The npz it
writes is then analysed with the main environment.

```bash
python3.11 -m venv .venv-allen && source .venv-allen/bin/activate
pip install --prefer-binary allensdk "marshmallow<4" "hdmf<4"   # newer versions break allensdk 2.16
python scripts/load_allen.py --list                       # BO 1.1 sessions, units per area
python scripts/load_allen.py --session <id> --area VISp   # writes data/allen_<id>_VISp.npz
deactivate
PYTHONPATH=. python scripts/run_e3.py --data data/allen_<id>_VISp.npz --n-units 60 --repeats 5
PYTHONPATH=. python scripts/compare_external.py --data data/allen_<id>_VISp.npz
PYTHONPATH=. python scripts/residual_levels.py --data data/allen_<id>_VISp.npz --n-units 60 --repeats 5 --all-units
```

E3 repeats can run in parallel: `--repeats 1 --seed k --tag sk` per process,
then `scripts/merge_e3.py` to combine the files. `scripts/plot_e3.py` draws the
figure from the merged JSON.

On Windows the venv's interpreter is `.venv-allen\Scripts\python.exe`.

Use `--synthetic timing_p10` in place of `--data` to test the E3 pipeline
without downloading anything.

## Design choices

- **Window 0 to 250 ms.** Natural scenes play back to back with no gray gap, so
  a longer window would include the next image.
- **Linear encoder, nonlinear decoder, both pointwise in time.** Pooling then
  commutes with encoding, and nearest-neighbour upsampling means level k can
  only change rates at its own resolution.
- **Each level is scored on counts pooled to its own length.** At 5 ms bins,
  Poisson noise otherwise drowns the training signal.
- **Cumulative features, C chosen per level.** The level-k readout is the
  concatenation of level-1 to level-k features, so the coarse counts stay
  explicit and a level cannot score below the levels above it for reasons of
  decoder geometry. The L2 logistic's C is chosen per level on an inner
  time-blocked split of the training set, so capacity is matched across
  levels by construction. A fixed-C PCA-100 decoder on the same features is
  the secondary; plain per-level logistic is kept for continuity. See
  `notes/decoder_bakeoff.md` for the comparison of twelve decoders.
- **Codes are the primary readout.** The reconstruction is computed from the
  codes, so decoding from it only adds decoder capacity. It is reported as a
  secondary check.
- **The decisive baseline is the quantized pyramid:** residual k-means on
  pooled log-counts, at the same level lengths and codebook sizes. If it
  matches the tokenizer, learned codes add nothing.

See `notes/diagnostics.md` for how these were arrived at.
