"""
Stitch per-chunk FLARE outputs into final per-decay response files.

After all SLURM array tasks complete (run_FLARE_*_chunked.py), each chunk
has saved a .pkl into FlareFiles/{1sec,1month,100yr}/. This script reads
each subfolder, concatenates the chunks, and writes one stitched .pkl per
decay time in the FLARE working directory.

CSV is also written by default but can be skipped at very large scale by
setting WRITE_CSV = False below — at ndiv=20 the CSV can be 5-50 GB.

Run AFTER the SLURM array completes:

    python stitch_flare.py

Optionally validate that no chunks are missing:

    python stitch_flare.py --expected 100
"""
import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ---------------------------------------------------------------------------
# CONFIG — must match the chunked run scripts
# ---------------------------------------------------------------------------
# (subfolder under FlareFiles, final output basename)
DECAY_RUNS = [
    ("1sec",   "flare_responses_5at_2y_irr-1sec_dec-over_spect"),
    ("1month", "flare_responses_5at_2y_irr-1month_dec-over_spect"),
    ("100yr",  "flare_responses_5at_2y_irr-100yr_dec-over_spect"),
]

FLAREFILE_ROOT = Path("FlareFiles")
WRITE_CSV      = False   # set False to skip CSV (binary pkl is much smaller)
SORT_INDEX     = True   # sort rows by composition string (deterministic order)
# ---------------------------------------------------------------------------


def stitch_one(subdir: str, basename: str, expected: int | None) -> Path:
    chunk_dir = FLAREFILE_ROOT / subdir
    files = sorted(chunk_dir.glob(f"{basename}_chunk*.pkl"))
    n = len(files)

    if n == 0:
        logging.error(f"[{subdir}] No chunk files found in {chunk_dir} — skipping.")
        return None

    if expected is not None and n != expected:
        # Identify missing chunk indices
        found_idxs = sorted(
            int(f.stem.rsplit("_chunk", 1)[-1]) for f in files
        )
        missing = sorted(set(range(expected)) - set(found_idxs))
        logging.warning(
            f"[{subdir}] Found {n} chunks but expected {expected}. "
            f"Missing chunk IDs: {missing}"
        )
        logging.warning(
            "Stitching anyway with what's available. Re-submit missing chunks "
            f"via: sbatch --array={','.join(str(i) for i in missing)} run_FLARE_chunked.slurm"
        )

    logging.info(f"[{subdir}] Reading {n} chunk files from {chunk_dir} ...")
    dfs = [pd.read_pickle(f) for f in files]

    logging.info(f"[{subdir}] Concatenating {n} DataFrames ...")
    merged = pd.concat(dfs)

    if SORT_INDEX:
        # 'composition' is set as the index by the chunk scripts.
        if merged.index.name == "composition":
            merged.sort_index(inplace=True)
        else:
            logging.warning(
                f"[{subdir}] Expected index name 'composition' but found "
                f"'{merged.index.name}'. Skipping sort."
            )

    out_pkl = Path(f"{basename}.pkl")
    logging.info(f"[{subdir}] Saving stitched .pkl to {out_pkl} "
                 f"({len(merged):,} rows)")
    merged.to_pickle(out_pkl)

    if WRITE_CSV:
        out_csv = Path(f"{basename}.csv")
        logging.info(f"[{subdir}] Saving stitched .csv to {out_csv} "
                     f"(this can be slow for large ndiv runs) ...")
        merged.to_csv(out_csv)

    logging.info(f"[{subdir}] Done.")
    return out_pkl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expected", type=int, default=None,
        help=("Expected number of chunks per decay (e.g. 100). If set, "
              "warn (and list missing IDs) when fewer chunks are found.")
    )
    parser.add_argument(
        "--decay", choices=[d for d, _ in DECAY_RUNS], default=None,
        help="Stitch only one decay subfolder (default: all three)."
    )
    args = parser.parse_args()

    runs = DECAY_RUNS if args.decay is None else [
        r for r in DECAY_RUNS if r[0] == args.decay
    ]

    if not FLAREFILE_ROOT.exists():
        logging.error(f"{FLAREFILE_ROOT} not found — nothing to stitch.")
        sys.exit(1)

    for subdir, basename in runs:
        stitch_one(subdir, basename, args.expected)

    logging.info("All requested decay times stitched.")


if __name__ == "__main__":
    main()
