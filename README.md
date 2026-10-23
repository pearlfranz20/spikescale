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
- [ ] E3 and E3b on Allen Visual Coding Neuropixels (needs a local run, below)
- [ ] E4 fixed-resolution ladder comparison

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
  run_e3.py      E3 and E3b on an extracted session
notes/
  diagnostics.md how the tokenizer design was debugged, and where it departs from the plan
```

## Quick start (synthetic, CPU, about 30 minutes)

```bash
pip install -r requirements.txt
PYTHONPATH=. python scripts/run_e2.py --seeds 2 --epochs 60 --out results
python scripts/plot_e2.py results/e2.json results/e2.png
```

## Real data (run locally)

Allen data needs a download of about 2 to 3 GB per session. AllenSDK works
best in a Python 3.10 or 3.11 venv.

```bash
python3.11 -m venv .venv-allen && source .venv-allen/bin/activate
pip install allensdk -r requirements.txt
python scripts/load_allen.py --list                       # BO 1.1 sessions, units per area
python scripts/load_allen.py --session <id> --area VISp   # writes data/allen_<id>_VISp.npz
PYTHONPATH=. python scripts/run_e3.py --data data/allen_<id>_VISp.npz --n-units 60 --repeats 5
```

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
- **Codes are the primary readout.** The reconstruction is computed from the
  codes, so decoding from it only adds decoder capacity. It is reported as a
  secondary check.
- **The decisive baseline is the quantized pyramid:** residual k-means on
  pooled log-counts, at the same level lengths and codebook sizes. If it
  matches the tokenizer, learned codes add nothing.

See `notes/diagnostics.md` for how these were arrived at.
