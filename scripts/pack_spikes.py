"""Pack every natural-scenes population into one spike-token dataset for the cross-session decoder.

Every extracted population (data/allen_<session>_<area>.npz, 118 images x 50
repeats, 0 to 250 ms, all units) becomes a list of trials, each trial a list of
spikes (global unit index, time in ms). Units are numbered globally, so the
same neuron keeps one index and different recordings never share one. The
split is the one every other analysis uses: the last 20% of each image's
repeats are the test set (decoding.blocked_split); of the rest, the last 25%
of each image's repeats are the validation set used to choose the number of
training epochs.

    python scripts/pack_spikes.py
Output: data/packed_scenes.npz
  tok_unit, tok_time   int32 / int16, one entry per spike, trials concatenated
  trial_start          int64, start of each trial's spikes (length n_trials + 1)
  trial_rec, trial_label, trial_split (0 train, 1 val, 2 test)
  rec_names, rec_unit_start (length n_rec + 1), rec_tissue (0 cortex, 1 thalamus)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spikescale.decode import blocked_split  # noqa: E402

DATA = Path("data")
THAL = {"LGd", "LP"}


def main():
    files = sorted(f for f in DATA.glob("allen_*_*.npz")
                   if len(f.stem.split("_")) == 3 and f.stem.split("_")[2] != "state")
    units, times, starts, rec, lab, split = [], [], [0], [], [], []
    names, ustart, tissue = [], [0], []
    n_tok = 0
    for r, f in enumerate(files):
        d = np.load(f)
        sp, y = d["spikes_ms"], d["labels"]
        assert sp.shape[2] == 250 and len(np.unique(y)) == 118
        tr, te = blocked_split(len(y), y)
        tri = np.nonzero(tr)[0]
        itr, iva = blocked_split(len(tri), y[tri], test_frac=0.25)
        s = np.full(len(y), 2, np.int8)
        s[tri[itr]] = 0
        s[tri[iva]] = 1
        tr_i, un, tt = np.nonzero(sp)
        reps = sp[tr_i, un, tt].astype(np.int64)
        tr_i, un, tt = np.repeat(tr_i, reps), np.repeat(un, reps), np.repeat(tt, reps)  # nonzero sorts by trial
        counts = np.bincount(tr_i, minlength=len(y))
        units.append((un + ustart[-1]).astype(np.int32))
        times.append(tt.astype(np.int16))
        starts.extend((n_tok + np.cumsum(counts)).tolist())
        n_tok += len(un)
        rec.append(np.full(len(y), r, np.int16))
        lab.append(y.astype(np.int16))
        split.append(s)
        area = f.stem.split("_")[2]
        names.append(f.stem.replace("allen_", ""))
        tissue.append(int(area in THAL))
        ustart.append(ustart[-1] + sp.shape[1])
        print(f"{f.stem}: {sp.shape[1]} units, {len(un) / len(y):.0f} spikes per trial", flush=True)
    np.savez(DATA / "packed_scenes.npz", tok_unit=np.concatenate(units), tok_time=np.concatenate(times),
             trial_start=np.array(starts, np.int64), trial_rec=np.concatenate(rec), trial_label=np.concatenate(lab),
             trial_split=np.concatenate(split), rec_names=np.array(names), rec_unit_start=np.array(ustart),
             rec_tissue=np.array(tissue, np.int8))
    print(f"{len(files)} recordings, {ustart[-1]} units, {len(starts) - 1} trials, {n_tok} spikes")


if __name__ == "__main__":
    main()
