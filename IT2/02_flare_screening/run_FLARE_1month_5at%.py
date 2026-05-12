"""
FLARE responses at 1-month decay time — CHUNKED version for SLURM array jobs.

Each SLURM array task processes only its own slice of the composition CSV
(via df.iloc[CHUNK_IDX::N_CHUNKS]) and saves a per-chunk .pkl into
flareFile/1month/. After all chunks complete, run stitch_flare.py to merge
them into the final response file.

The script reads SLURM_ARRAY_TASK_ID and SLURM_ARRAY_TASK_COUNT from the
environment. If those aren't set (e.g. local testing), it processes the
full CSV as a single "chunk 0".

Edit DF_PATH, OUT_FILENAME, FILTER_CRITERIA, and CHUNK_DIR for your run.
"""
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed
from pymatgen.core import Composition
from tqdm_joblib import tqdm_joblib

from flare import Alloy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ---------------------------------------------------------------------------
# CONFIG — edit these for your run
# ---------------------------------------------------------------------------
N_JOBS       = int(os.environ.get("SLURM_NTASKS", 1))
DF_PATH      = Path("TiVTaNbMoZrCrHfFeReW_ndiv_20_compositions.csv")
OUT_FILENAME = "flare_responses_5at_2y_irr-1month_dec-over_spect"
CHUNK_DIR    = Path("FlareFiles/1month")

# ~1-month decay (1.0e-1 years ≈ 36.5 days), 8e13 flux, 2 year irradiation
FILTER_CRITERIA = {
    "Flux":     "8.000E+13",
    "Irr_time": "2.000E+00",
    "Dec_time": "1.000E-01",
}

# SLURM array bookkeeping (defaults make local single-process runs work too)
CHUNK_IDX = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))
N_CHUNKS  = int(os.environ.get("SLURM_ARRAY_TASK_COUNT", 1))
# ---------------------------------------------------------------------------


CHUNK_DIR.mkdir(parents=True, exist_ok=True)
out_path = CHUNK_DIR / f"{OUT_FILENAME}_chunk{CHUNK_IDX:03d}.pkl"

# Skip if this chunk has already been computed (resumability)
if out_path.exists():
    logging.info(f"Chunk {CHUNK_IDX} already exists at {out_path} — skipping.")
    sys.exit(0)

logging.info(f"Loading composition dictionary from {DF_PATH}")
df_full = pd.read_csv(DF_PATH)
logging.info(f"Loaded {len(df_full)} total compositions.")

df = df_full.iloc[CHUNK_IDX::N_CHUNKS].reset_index(drop=True)
logging.info(
    f"Chunk {CHUNK_IDX} of {N_CHUNKS}: processing {len(df)} compositions "
    f"(rows {CHUNK_IDX}::{N_CHUNKS} of input)."
)


def process_composition(composition):
    """Return FLARE responses (filtered + averaged) for one composition dict."""
    comp_str = Composition.from_dict(composition).to_pretty_string()
    logging.debug(f"Processing composition: {comp_str}")

    alloy = Alloy(composition)
    res_simple = alloy.responses_simple.copy()
    res_all = alloy.responses.copy()

    mask_simple = (res_simple[list(FILTER_CRITERIA)] == pd.Series(FILTER_CRITERIA)).all(axis=1)
    mask_all    = (res_all   [list(FILTER_CRITERIA)] == pd.Series(FILTER_CRITERIA)).all(axis=1)

    filtered = pd.merge(res_simple[mask_simple], res_all[mask_all])

    result = filtered.mean(numeric_only=True).to_frame().T
    result.reset_index(inplace=True, drop=True)
    result["composition"] = comp_str
    return result


with tqdm_joblib(unit="composition", total=len(df)) as pbar:
    dfs = Parallel(n_jobs=N_JOBS, batch_size=1)(
        delayed(process_composition)(composition.to_dict()) for _, composition in df.iterrows()
    )

logging.info("Parallel processing complete.")

logging.info("Merging this chunk's DataFrames...")
chunk_df = pd.concat(dfs, ignore_index=True)
chunk_df.set_index("composition", inplace=True)

logging.info(f"Saving chunk {CHUNK_IDX} to {out_path}")
chunk_df.to_pickle(out_path)
logging.info(f"Chunk {CHUNK_IDX} save complete.")
