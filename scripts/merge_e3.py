"""Merge E3 result files from runs split over seeds into one file.

    python scripts/merge_e3.py results/e3_x_n60_s0.json results/e3_x_n60_s1.json -o results/e3_x_n60.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_e3 import mean_runs  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    parts = [json.loads(Path(f).read_text()) for f in args.files]
    runs = [r for p in parts for r in p["runs"]]
    seeds = [s for p in parts for s in p["seeds"]]
    merged = {**parts[0], "repeats": len(runs), "seeds": seeds, "mean": mean_runs(runs), "runs": runs}
    Path(args.out).write_text(json.dumps(merged, indent=1))
    print(f"wrote {args.out}: {len(runs)} runs, seeds {seeds}")


if __name__ == "__main__":
    main()
