"""Extract drifting-gratings trials from one Allen Visual Coding Neuropixels session.

Runs in the AllenSDK venv, like load_allen.py, and uses the same unit filters,
so for an area already extracted with load_allen.py the units are the same, in
the same order (asserted when the natural-scenes file exists). The drifting
gratings are the one Brain Observatory 1.1 stimulus with many conditions and a
gray gap: 2 s of grating, 1 s of mean gray, 8 directions x 5 temporal
frequencies, 15 repeats each. They give a window that is not bounded by the
next stimulus, which the 250 ms natural-scenes window is.

    .venv-allen/Scripts/python.exe scripts/load_allen_gratings.py --session <id> --area VISp

Output: data/allen_<session>_<area>_dg.npz with
    spikes_ms   (trials, units, 2000) int16, 1 ms bins, 0 to 2000 ms from grating onset
    labels      (trials,) condition index 0..39 (direction-major, then temporal frequency)
    ori, tf     (trials,) direction in degrees and temporal frequency in Hz
    start_time  (trials,) onset in seconds
    unit_ids, firing_rate (units,)
Trials are sorted by condition, then onset, so blocked_split holds out the last
repeats of every condition. Blank sweeps are dropped.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

WINDOW_MS = 2000


def extract(cache, session_id: int, area: str, out_dir: Path):
    session = cache.get_session_data(
        session_id,
        isi_violations_maximum=0.5,
        amplitude_cutoff_maximum=0.1,
        presence_ratio_minimum=0.9,
    )
    units = session.units
    units = units[units["ecephys_structure_acronym"] == area]
    if len(units) == 0:
        raise SystemExit(f"No units in {area} for session {session_id}")
    unit_ids = units.index.to_numpy()
    scenes = out_dir / f"allen_{session_id}_{area}.npz"
    if scenes.exists():
        assert np.array_equal(np.load(scenes)["unit_ids"], unit_ids), "unit set differs from the natural-scenes file"

    stim = session.get_stimulus_table(["drifting_gratings"])
    ok = (stim["orientation"].astype(str) != "null") & (stim["temporal_frequency"].astype(str) != "null")
    stim = stim[ok].copy()
    stim["ori"] = stim["orientation"].astype(float)
    stim["tf"] = stim["temporal_frequency"].astype(float)
    oris, tfs = np.sort(stim["ori"].unique()), np.sort(stim["tf"].unique())
    stim["cond"] = (np.searchsorted(oris, stim["ori"].to_numpy()) * len(tfs)
                    + np.searchsorted(tfs, stim["tf"].to_numpy()))
    stim = stim.sort_values(["cond", "start_time"])
    pres_ids = stim.index.to_numpy()

    spk = session.presentationwise_spike_times(
        stimulus_presentation_ids=stim.sort_values("start_time").index.to_numpy(),
        unit_ids=unit_ids,
    )
    pres_pos = {p: i for i, p in enumerate(pres_ids)}
    unit_pos = {u: i for i, u in enumerate(unit_ids)}
    spikes_ms = np.zeros((len(pres_ids), len(unit_ids), WINDOW_MS), dtype=np.int16)
    t_ms = np.floor(spk["time_since_stimulus_presentation_onset"].to_numpy() * 1000).astype(int)
    keep = (t_ms >= 0) & (t_ms < WINDOW_MS)
    rows = np.array([pres_pos[p] for p in spk["stimulus_presentation_id"].to_numpy()[keep]])
    cols = np.array([unit_pos[u] for u in spk["unit_id"].to_numpy()[keep]])
    np.add.at(spikes_ms, (rows, cols, t_ms[keep]), 1)

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"allen_{session_id}_{area}_dg.npz"
    np.savez_compressed(
        path,
        spikes_ms=spikes_ms,
        labels=stim["cond"].to_numpy(),
        ori=stim["ori"].to_numpy(),
        tf=stim["tf"].to_numpy(),
        start_time=stim["start_time"].to_numpy(),
        unit_ids=unit_ids,
        firing_rate=units["firing_rate"].to_numpy(),
    )
    reps = np.bincount(stim["cond"].to_numpy())
    dur = (stim["stop_time"] - stim["start_time"]).to_numpy()
    print(f"Saved {path}: {len(pres_ids)} trials, {len(unit_ids)} units, {len(oris)} directions x {len(tfs)} "
          f"temporal frequencies {tfs.tolist()}, {reps.min()} to {reps.max()} repeats per condition, "
          f"duration {dur.min():.2f} to {dur.max():.2f} s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="allen_cache")
    ap.add_argument("--out", default="data")
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--area", default="VISp")
    args = ap.parse_args()
    from load_allen import get_cache
    extract(get_cache(Path(args.cache)), args.session, args.area, Path(args.out))


if __name__ == "__main__":
    main()
