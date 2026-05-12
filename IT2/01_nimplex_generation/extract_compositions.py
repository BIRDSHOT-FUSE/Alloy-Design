"""
Strip a nimplex output CSV down to just the element-composition columns.

Auto-detects element columns (1-2 character capitalized names like Ti, V, Cr, Hf)
holding numeric atomic fractions in [0, 1], and drops everything else
(Node ID, NodeCoord_*, Neighbor_*).

Examples:
    # Auto-named output: AlTiV_nimplex_space.csv -> AlTiV_compositions.csv
    python exitnimplexinfo.py AlTiV_nimplex_space.csv

    # Explicit output name
    python exitnimplexinfo.py mygrid.csv --output for_flare.csv
"""
import argparse
import re
from pathlib import Path
import pandas as pd


ELEMENT_PATTERN = re.compile(r"^[A-Z][a-z]?$")


def infer_element_columns(df: pd.DataFrame) -> list:
    """Return columns whose names look like element symbols and hold fractions in [0, 1]."""
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
    return [
        col
        for col in numeric_cols
        if ELEMENT_PATTERN.match(str(col)) and df[col].max() <= 1.0
    ]


def derive_output_name(input_csv: str) -> str:
    """Build a sensible output name when --output isn't given."""
    stem = Path(input_csv).stem
    if stem.endswith("_nimplex_space"):
        stem = stem.replace("_nimplex_space", "")
    return f"{stem}_compositions.csv"


def strip_to_compositions(input_csv: str, output_csv: str = None) -> str:
    if not Path(input_csv).is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    # First pass: read just the header + first 5 rows to detect element columns.
    # This avoids loading the full CSV into memory (critical for big files).
    sample = pd.read_csv(input_csv, nrows=5)
    element_cols = infer_element_columns(sample)
    if not element_cols:
        raise ValueError(
            f"No element columns detected in {input_csv}. "
            f"Expected 1-2 character capitalized names like 'Ti', 'V', 'Cr' "
            f"with values in [0, 1]. Columns seen: {list(sample.columns)}"
        )

    if output_csv is None:
        output_csv = derive_output_name(input_csv)

    # Second pass: read ONLY the element columns. Memory-efficient for huge files.
    clean_df = pd.read_csv(input_csv, usecols=element_cols)

    clean_df.to_csv(output_csv, index=False)

    print(f"Input file:  {input_csv}")
    print(f"  - Total columns in input: {len(sample.columns)}")
    print(f"  - Rows kept:              {len(clean_df)}")
    print(f"Output file: {output_csv}")
    print(f"  - Element columns kept ({len(element_cols)}): {element_cols}")
    print()
    print("First 5 rows of clean data:")
    print(clean_df.head())

    return output_csv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Strip a nimplex CSV down to just element-composition columns."
    )
    parser.add_argument(
        "input_csv",
        help="Path to the nimplex output CSV.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV filename. If omitted, auto-derived from input name "
        "(e.g. 'foo_nimplex_space.csv' -> 'foo_compositions.csv').",
    )
    args = parser.parse_args()
    strip_to_compositions(args.input_csv, args.output)
