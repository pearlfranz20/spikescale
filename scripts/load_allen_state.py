"""Per-trial behavioural state for an extracted Allen session: running speed and pupil area.

Runs in the AllenSDK venv, like load_allen.py. For every data/allen_<session>_<area>.npz
of a session the trials are the same (the natural-scenes presentations, sorted by
image then onset), so one state file per session serves every area:

    data/allen_<session>_state.npz with
        running     (trials,) mean running speed (cm/s) over 0 to 250 ms from onset
        pupil       (trials,) mean pupil area (ellipse, pixels^2) over the same window,
                    NaN throughout when the session has no eye tracking
        start_time  (trials,) onset in seconds, to check alignment with the area files

    .venv-allen/Scripts/python.exe scripts/load_allen_state.py --session <id>
"""
from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np

WINDOW_S = 0.25


def window_means(times, values, starts):
    """Mean of values whose sample times fall in [start, start + WINDOW_S), per start; NaN when empty."""
    order = np.argsort(times)
    times, values = times[order], values[order]
    lo = np.searchsorted(times, starts)
    hi = np.searchsorted(times, starts + WINDOW_S)
    cs = np.concatenate([[0.0], np.nancumsum(values)])
    cnt = np.concatenate([[0], np.cumsum(~np.isnan(values))])
    n = cnt[hi] - cnt[lo]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, (cs[hi] - cs[lo]) / n, np.nan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--cache", default="allen_cache")
    ap.add_argument("--data", default="data")
    args = ap.parse_args()
    from load_allen import get_cache

    files = sorted(glob.glob(f"{args.data}/allen_{args.session}_*.npz"))
    files = [f for f in files if not f.endswith("_state.npz")]
    if not files:
        raise SystemExit(f"no extracted areas for session {args.session}")
    starts = np.load(files[0])["start_time"]
    for f in files[1:]:
        assert np.allclose(np.load(f)["start_time"], starts), f
    session = get_cache(Path(args.cache)).get_session_data(args.session)

    rs = session.running_speed
    t = ((rs["start_time"] + rs["end_time"]) / 2).to_numpy()
    running = window_means(t, rs["velocity"].to_numpy(), starts)

    pupil = np.full(len(starts), np.nan)
    try:
        pd_ = session.get_pupil_data()
        area = np.pi * (pd_["pupil_width"].to_numpy() / 2) * (pd_["pupil_height"].to_numpy() / 2)
        pupil = window_means(pd_.index.to_numpy().astype(float), area, starts)
    except Exception as e:  # sessions without eye tracking raise here
        print(f"no pupil data: {type(e).__name__}: {e}")

    out = Path(args.data) / f"allen_{args.session}_state.npz"
    np.savez_compressed(out, running=running, pupil=pupil, start_time=starts)
    ok_r, ok_p = np.isfinite(running).mean(), np.isfinite(pupil).mean()
    print(f"Saved {out}: {len(starts)} trials; running defined on {ok_r:.3f}, "
          f"median {np.nanmedian(running):.1f} cm/s, {np.nanmean(running > 5):.2f} of trials above 5 cm/s; "
          f"pupil defined on {ok_p:.3f}")


if __name__ == "__main__":
    main()
