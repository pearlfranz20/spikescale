"""Population firing rates per sample and stimulus, and the thinning targets for the thalamus.

The tissue test finds the thalamus flatter below 50 ms than cortex, and the
thalamus fires about twice as fast. More spikes leave fewer empty 10 ms bins,
so a rate difference alone could flatten the pyramid. This script measures
each sample's mean rate (spikes per unit per second, all units, in the window
the decoder reads) for every stimulus, and sets each thalamic sample's target
to the mean rate of the same animal's cortical samples on the same stimulus.
gratings_pyramid.py --thin-to then deletes thalamic spikes at random,
independently per spike, until the decoded 60-unit subset fires at that
target; spike times are untouched.

  scenes  250 ms from image onset, 5,900 trials
  movie   the whole 30 s of natural_movie_one, 20 repeats
  dg      the first 2,000 ms of every grating, 600 trials

    python scripts/rates_tissue.py
Output: results/rates_tissue.json  {sample: {stimulus: rate}}, {thalamic sample: {stimulus: target}}
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

DATA, RES = Path("data"), Path("results")
THAL = {"LGd", "LP"}
WINDOW = {"scenes": 250, "movie": None, "dg": 2000}


def rate(path, window):
    x = np.load(path)["spikes_ms"]
    if window is not None:
        x = x[..., :window]
    return float(x.sum(dtype=np.int64) / (x.shape[0] * x.shape[1] * x.shape[2]) * 1000)


def main():
    rates = {}
    for f in sorted(DATA.glob("allen_*_*.npz")):
        parts = f.stem.split("_")
        if len(parts) == 3:
            sid, area, stim = parts[1], parts[2], "scenes"
        elif len(parts) == 4 and parts[3] in ("movie", "dg"):
            sid, area, stim = parts[1], parts[2], parts[3]
        else:
            continue
        if area == "state":
            continue
        rates.setdefault(f"{sid}_{area}", {})[stim] = rate(f, WINDOW[stim])
    targets = {}
    for k, r in rates.items():
        sid, area = k.split("_")
        if area not in THAL:
            continue
        for stim in r:
            ctx = [v[stim] for kk, v in rates.items() if kk.split("_")[0] == sid and kk.split("_")[1] not in THAL and stim in v]
            if ctx:
                targets.setdefault(k, {})[stim] = float(np.mean(ctx))
    (RES / "rates_tissue.json").write_text(json.dumps({"rates": rates, "targets": targets}, indent=1))
    for k in sorted(rates):
        t = targets.get(k, {})
        print(f"{k:22s} " + "  ".join(f"{s} {rates[k][s]:5.1f}" + (f" -> {t[s]:4.1f}" if s in t else "") for s in ("scenes", "movie", "dg") if s in rates[k]))
    print("wrote results/rates_tissue.json")


if __name__ == "__main__":
    main()
