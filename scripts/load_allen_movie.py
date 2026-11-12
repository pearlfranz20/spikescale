"""Extract natural_movie_one responses from one Allen Visual Coding Neuropixels session.

Runs in the AllenSDK venv, like load_allen.py, with the same unit filters, so
the units match the natural-scenes file of the same area (asserted when it
exists). natural_movie_one is a 30 s clip (900 frames at 30 Hz) shown 20
times in two blocks of 10. Unlike the scenes and gratings it has no stimulus
onsets after the first frame: the picture changes continuously. Each repeat
is stored whole at 1 ms resolution; scripts/gratings_pyramid.py --movie cuts
it into segments.

    .venv-allen/Scripts/python.exe scripts/load_allen_movie.py --session <id> --area VISp

Output: data/allen_<session>_<area>_movie.npz with
    spikes_ms     (repeats, units, 30000) int16, 1 ms bins from the onset of frame 0
    repeat_start  (repeats,) onset of frame 0 in seconds, chronological
    frame_ms      (900,) onset of every frame relative to frame 0, ms (median over repeats)
    unit_ids, firing_rate (units,)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

MOVIE = "natural_movie_one"
LEN_MS = 30000


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

    stim = session.get_stimulus_table([MOVIE]).sort_values("start_time")
    frame = stim["frame"].astype(float).astype(int).to_numpy()
    t = stim["start_time"].to_numpy()
    n_frames = frame.max() + 1
    starts = t[frame == 0]
    rel = np.array([t[(frame >= 0) & (t >= s0)][:n_frames] - s0 for s0 in starts])  # (repeats, frames)
    assert rel.shape == (len(starts), n_frames)
    frame_ms = np.median(rel, axis=0) * 1000
    jitter = np.abs(rel * 1000 - frame_ms).max()

    spikes_ms = np.zeros((len(starts), len(unit_ids), LEN_MS), dtype=np.int16)
    for j, u in enumerate(unit_ids):
        st = session.spike_times[u]
        for i, s0 in enumerate(starts):
            lo, hi = np.searchsorted(st, [s0, s0 + LEN_MS / 1000])
            ms = np.floor((st[lo:hi] - s0) * 1000).astype(int)
            np.add.at(spikes_ms[i, j], ms[ms < LEN_MS], 1)

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"allen_{session_id}_{area}_movie.npz"
    np.savez_compressed(path, spikes_ms=spikes_ms, repeat_start=starts, frame_ms=frame_ms,
                        unit_ids=unit_ids, firing_rate=units["firing_rate"].to_numpy())
    print(f"Saved {path}: {len(starts)} repeats, {len(unit_ids)} units, {n_frames} frames, "
          f"frame times consistent across repeats within {jitter:.1f} ms, "
          f"mean rate {spikes_ms.sum(-1).mean() / LEN_MS * 1000:.1f} Hz")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="allen_cache")
    ap.add_argument("--out", default="data")
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--areas", default="VISp")
    args = ap.parse_args()
    from load_allen import get_cache
    cache = get_cache(Path(args.cache))
    for area in args.areas.split(","):
        extract(cache, args.session, area, Path(args.out))


if __name__ == "__main__":
    main()
