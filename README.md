# spikescale

A multiscale residual VQ tokenizer for spike data, and a test of how much
stimulus information sits at each temporal scale of a population response.

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
  run_e3.py      E3 and E3b on an extracted session (codes, recon, both pyramids, four decoders)
  merge_e3.py    merge E3 runs split over seeds
  plot_e3.py     E3 and E3b figure
  compare_external.py  pyramid decoding under random 10-fold CV and all units, to set beside published numbers
  residual_levels.py   decode from each level's orthogonal detail alone (is the information at a scale unique to it?)
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
