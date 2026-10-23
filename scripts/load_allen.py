"""Extract natural-scenes trials from one Allen Visual Coding Neuropixels session.

Run this on your own machine (it downloads NWB data, about 2 to 3 GB per
session). AllenSDK currently works best on Python 3.10 or 3.11:

    python3.11 -m venv .venv-allen && source .venv-allen/bin/activate
    pip install allensdk numpy
    python scripts/load_allen.py --list
    python scripts/load_allen.py --session <id> --area VISp

Output: data/allen_<session>_<area>.npz with
    spikes_ms   (trials, units, 250) int16, 1 ms bins, 0 to 250 ms from image onset
    counts      (trials, units, 50)  float32, 5 ms bins
    labels      (trials,) image index 0..117
    start_time  (trials,) onset in seconds, used for time-blocked splits
    unit_ids, firing_rate (units,)

Choices from the plan:
- Brain Observatory 1.1 sessions only (natural scenes are not shown in the
  Functional Connectivity sessions).
- Units pass isi_violations < 0.5, amplitude_cutoff < 0.1, presence_ratio > 0.9.
- Window is 0 to 250 ms because images play back to back with no gray gap.
- Blank presentations (frame == -1) are dropped.
- Trials are sorted by image, then onset time, so the last repeats of each
  image form the time-blocked test set in spikescale.decode.blocked_split.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

WINDOW_MS = 250
BIN_MS = 5


def get_cache(manifest_dir: Path):
    from allensdk.brain_observatory.ecephys.ecephys_project_cache import EcephysProjectCache
    manifest_dir.mkdir(parents=True, exist_ok=True)
    return EcephysProjectCache.from_warehouse(manifest=str(manifest_dir / "manifest.json"))


def list_sessions(cache):
    sessions = cache.get_session_table()
    bo = sessions[sessions["session_type"] == "brain_observatory_1.1"]
    units = cache.get_unit_table()
    units = units[
        (units["isi_violations"] < 0.5)
        & (units["amplitude_cutoff"] < 0.1)
        & (units["presence_ratio"] > 0.9)
    ]
    counts = (
        units[units["ecephys_session_id"].isin(bo.index)]
        .groupby(["ecephys_session_id", "ecephys_structure_acronym"]).size()
        .unstack(fill_value=0)
    )
    cols = [c for c in ["VISp", "VISl", "VISal", "VISrl", "VISpm", "VISam", "LGd", "LP"] if c in counts]
    table = counts[cols].sort_values("VISp", ascending=False)
    print("Brain Observatory 1.1 sessions, units passing quality filters (sorted by VISp):")
    print(table.head(15).to_string())


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

    stim = session.get_stimulus_table(["natural_scenes"])
    stim = stim[stim["frame"].astype(float) >= 0].copy()
    stim["frame"] = stim["frame"].astype(float).astype(int)
    stim = stim.sort_values(["frame", "start_time"])
    pres_ids = stim.index.to_numpy()

    spk = session.presentationwise_spike_times(
        stimulus_presentation_ids=pres_ids, unit_ids=unit_ids
    )
    pres_pos = {p: i for i, p in enumerate(pres_ids)}
    unit_pos = {u: i for i, u in enumerate(unit_ids)}
    spikes_ms = np.zeros((len(pres_ids), len(unit_ids), WINDOW_MS), dtype=np.int16)
    t_ms = np.floor(spk["time_since_stimulus_presentation_onset"].to_numpy() * 1000).astype(int)
    keep = (t_ms >= 0) & (t_ms < WINDOW_MS)
    rows = np.array([pres_pos[p] for p in spk["stimulus_presentation_id"].to_numpy()[keep]])
    cols = np.array([unit_pos[u] for u in spk["unit_id"].to_numpy()[keep]])
    np.add.at(spikes_ms, (rows, cols, t_ms[keep]), 1)

    counts = spikes_ms.reshape(len(pres_ids), len(unit_ids), WINDOW_MS // BIN_MS, BIN_MS).sum(-1)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"allen_{session_id}_{area}.npz"
    np.savez_compressed(
        path,
        spikes_ms=spikes_ms,
        counts=counts.astype(np.float32),
        labels=stim["frame"].to_numpy(),
        start_time=stim["start_time"].to_numpy(),
        unit_ids=unit_ids,
        firing_rate=units["firing_rate"].to_numpy(),
    )
    reps = np.bincount(stim["frame"].to_numpy())
    print(f"Saved {path}: {len(pres_ids)} trials, {len(unit_ids)} units, "
          f"{reps.min()} to {reps.max()} repeats per image")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="allen_cache")
    ap.add_argument("--out", default="data")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--session", type=int)
    ap.add_argument("--area", default="VISp")
    args = ap.parse_args()
    cache = get_cache(Path(args.cache))
    if args.list:
        list_sessions(cache)
    elif args.session:
        extract(cache, args.session, args.area, Path(args.out))
    else:
        ap.error("pass --list or --session")


if __name__ == "__main__":
    main()
