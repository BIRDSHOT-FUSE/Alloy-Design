"""
Annotate an existing composition CSV with nimplex graph features, optionally plotting it.

Adds Node ID and Neighbor_* columns to each row of your input CSV without modifying
the compositions. Two graph modes available:

  embedded (default)
    Treats each row as a vertex of an embedded simplex with ndiv=1. Result: a
    fully-connected graph (every alloy connected to every other). Works for ANY
    composition list, even non-lattice ones.

  lattice (--lattice flag)
    Detects the lattice resolution (ndiv) from the data and computes simplex-graph
    neighbors using the standard lattice rule (one coord +1/ndiv, another -1/ndiv).
    Builds the induced subgraph for whatever rows are present, so it works correctly
    even if you've filtered out some compositions. Only valid when the input came
    from a regular simplex grid (e.g. output of generate_nimplex.py).

Examples:
    python add_nimplex_features.py my_alloys.csv
    python add_nimplex_features.py grid.csv --lattice
    python add_nimplex_features.py grid.csv --lattice --plot
    python add_nimplex_features.py my_alloys.csv --output annotated.csv
"""
import argparse
import re
from pathlib import Path
import numpy as np
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


def derive_output_name(input_csv: str, suffix: str = "_with_nimplex.csv") -> str:
    stem = Path(input_csv).stem
    return f"{stem}{suffix}"


# ---------------------------------------------------------------------------
# Lattice-graph helpers
# ---------------------------------------------------------------------------

def detect_ndiv(compositions: np.ndarray, atol: float = 1e-6) -> int:
    """
    Detect lattice resolution ndiv such that all compositions are integer multiples
    of 1/ndiv. Raises if the data isn't on a lattice.
    """
    nonzero = compositions[compositions > atol]
    if len(nonzero) == 0:
        raise ValueError("All composition values are ~zero; can't detect ndiv.")
    smallest = float(np.min(nonzero))
    ndiv = int(round(1.0 / smallest))
    rounded = np.round(compositions * ndiv) / ndiv
    if not np.allclose(compositions, rounded, atol=atol * 10):
        raise ValueError(
            f"Compositions are not on a regular lattice. Detected candidate ndiv={ndiv} "
            f"but values don't match this resolution within tolerance. "
            f"Lattice mode requires data from a regular simplex grid (e.g. generate_nimplex.py)."
        )
    return ndiv


def compute_lattice_neighbors(compositions: np.ndarray, ndiv: int):
    """
    For each row, find which OTHER rows are simplex-lattice neighbors.

    Two rows are lattice neighbors if their compositions differ by +1/ndiv in
    exactly one coordinate and -1/ndiv in another (all other coords equal).

    Returns:
        neighbor_lists : list of sorted lists of neighbor indices
        max_neighbors  : max number of neighbors any row has
    """
    n_rows, n_dim = compositions.shape

    # Convert to integer barycentric coords (each row sums to ndiv, all integers)
    int_coords = np.round(compositions * ndiv).astype(int)

    # Lookup: tuple of int coords -> row index
    coord_to_idx = {tuple(row): i for i, row in enumerate(int_coords)}

    neighbor_lists = []
    for idx in range(n_rows):
        c = int_coords[idx]
        neighbors = set()
        for i in range(n_dim):
            if c[i] == 0:  # can't decrease coord i
                continue
            for j in range(n_dim):
                if i == j:
                    continue
                # Candidate neighbor: decrease c[i] by 1, increase c[j] by 1
                candidate = c.copy()
                candidate[i] -= 1
                candidate[j] += 1
                key = tuple(candidate)
                hit = coord_to_idx.get(key)
                if hit is not None and hit != idx:
                    neighbors.add(hit)
        neighbor_lists.append(sorted(neighbors))

    max_neighbors = max((len(nl) for nl in neighbor_lists), default=0)
    return neighbor_lists, max_neighbors


def neighbor_lists_to_array(neighbor_lists: list, max_neighbors: int) -> np.ndarray:
    """Pad each list with -1 to a uniform width."""
    n_rows = len(neighbor_lists)
    arr = np.full((n_rows, max_neighbors), -1, dtype=int)
    for i, nl in enumerate(neighbor_lists):
        for j, val in enumerate(nl):
            arr[i, j] = val
    return arr


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_graph(df: pd.DataFrame, elements: list, output_html: str) -> None:
    """Affine projection onto a regular N-gon. Works for any number of elements."""
    import plotly.graph_objects as go

    n = len(elements)
    angles = np.array([-np.pi / 2 + 2 * np.pi * i / n for i in range(n)])
    vx = np.cos(angles)
    vy = np.sin(angles)

    compositions = df[elements].values
    pxs = compositions @ vx
    pys = compositions @ vy

    neighbor_cols = [c for c in df.columns if c.startswith("Neighbor_")]
    edge_x, edge_y = [], []
    for i in range(len(df)):
        row = df.iloc[i]
        for col in neighbor_cols:
            j = row[col]
            if pd.notna(j) and j != -1:
                j = int(j)
                if i < j:
                    edge_x.extend([pxs[i], pxs[j], None])
                    edge_y.extend([pys[i], pys[j], None])

    formulas = [
        " ".join(f"{el}{100 * v:.1f}" for el, v in zip(elements, comp) if v > 0.001)
        for comp in compositions
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="lightgray", width=0.5),
        hoverinfo="none", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=pxs, y=pys, mode="markers",
        marker=dict(color="steelblue", size=6, line=dict(color="white", width=0.5)),
        text=formulas, hoverinfo="text", name="Alloys",
    ))
    fig.add_trace(go.Scatter(
        x=vx, y=vy, mode="markers",
        marker=dict(color="black", size=10),
        hoverinfo="none", showlegend=False,
    ))
    label_r = 1.15
    fig.add_trace(go.Scatter(
        x=label_r * np.cos(angles),
        y=label_r * np.sin(angles),
        mode="text",
        text=[f"<b>{el}</b>" for el in elements],
        textfont=dict(size=14),
        hoverinfo="none", showlegend=False,
    ))
    fig.update_layout(
        template="simple_white", width=800, height=800,
        title=f"Alloy graph affine projection ({n} elements, {len(df)} alloys)",
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
    )
    fig.write_html(output_html)
    print(f"Plot saved to {output_html}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def add_nimplex_features(
    input_csv: str,
    output_csv: str = None,
    mode: str = "embedded",
    plot: bool = False,
) -> str:
    if not Path(input_csv).is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)

    elements = infer_element_columns(df)
    if not elements:
        raise ValueError(
            f"No element columns detected in {input_csv}. Expected 1-2 character "
            f"capitalized names like 'Ti', 'V', 'Cr' with fractions in [0, 1]."
        )
    if len(df) < 2:
        raise ValueError(
            f"Input must have at least 2 alloys to form a graph. Got {len(df)} row(s)."
        )

    compositions = df[elements].values
    if not np.allclose(compositions.sum(axis=1), 1.0, atol=1e-3):
        raise ValueError(
            "Compositions do not sum to 1.0 (within 1e-3). Normalize your input first."
        )

    annotation = pd.DataFrame({"Node ID": range(len(df))})

    if mode == "embedded":
        # Use nimplex's embedded simplex (fully-connected graph)
        import nimplex
        node_coords, comp_data, neighbor_data = nimplex.embeddedpair_simplex_graph_fractional_py(
            compositions.tolist(), 1
        )
        if len(comp_data) != len(df):
            raise RuntimeError(
                f"nimplex returned {len(comp_data)} nodes, expected {len(df)}."
            )
        if not np.allclose(np.array(comp_data), compositions, atol=1e-6):
            raise RuntimeError(
                "nimplex returned compositions in a different order than input."
            )
        node_coord_df = pd.DataFrame(
            node_coords,
            columns=[f"NodeCoord_{i}" for i in range(len(node_coords[0]))],
        )
        neighbor_df = pd.DataFrame(
            neighbor_data,
            columns=[f"Neighbor_{i}" for i in range(neighbor_data.shape[1])],
        )
        # Convert -1 padding to empty cells (cleaner CSV)
        neighbor_df = neighbor_df.astype("Int64").where(neighbor_df != -1)
        annotation = pd.concat([annotation, node_coord_df, neighbor_df], axis=1)
        graph_summary = (
            f"embedded mode: ndiv=1 (fully-connected); "
            f"max neighbors = {neighbor_data.shape[1]}"
        )

    elif mode == "lattice":
        # Detect ndiv, build induced subgraph
        ndiv = detect_ndiv(compositions)
        neighbor_lists, max_n = compute_lattice_neighbors(compositions, ndiv)
        if max_n == 0:
            neighbor_arr = np.full((len(df), 1), -1, dtype=int)
        else:
            neighbor_arr = neighbor_lists_to_array(neighbor_lists, max_n)
        cols = [f"Neighbor_{i}" for i in range(neighbor_arr.shape[1])]
        neighbor_df = pd.DataFrame(neighbor_arr, columns=cols)
        # Convert -1 padding to empty cells (cleaner CSV)
        neighbor_df = neighbor_df.astype("Int64").where(neighbor_df != -1)
        annotation = pd.concat([annotation, neighbor_df], axis=1)
        graph_summary = (
            f"lattice mode: detected ndiv={ndiv} ({100/ndiv:.4g} at% steps); "
            f"max neighbors = {max_n}"
        )

    else:
        raise ValueError(f"Unknown mode '{mode}'. Use 'embedded' or 'lattice'.")

    # Metadata (Node ID + neighbors) goes FIRST, matching generate_nimplex.py output
    result = pd.concat(
        [annotation.reset_index(drop=True), df.reset_index(drop=True)],
        axis=1,
    )

    if output_csv is None:
        output_csv = derive_output_name(input_csv)
    result.to_csv(output_csv, index=False)

    print(f"Input file:  {input_csv}")
    print(f"  - Rows:             {len(df)}")
    print(f"  - Element columns:  {elements}")
    print(f"  - Graph: {graph_summary}")
    print(f"Output file: {output_csv}")
    print(f"  - Total columns now: {len(result.columns)}")

    if plot:
        plot_html = derive_output_name(input_csv, suffix="_graph_plot.html")
        plot_graph(result, elements, plot_html)

    return output_csv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Annotate a composition CSV with nimplex graph features (Node ID, neighbors)."
    )
    parser.add_argument("input_csv", help="Input CSV with alloy compositions.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV filename. If omitted, auto-derived (e.g. 'foo.csv' -> 'foo_with_nimplex.csv').",
    )
    parser.add_argument(
        "--lattice",
        action="store_true",
        help="Use lattice-graph mode (auto-detects ndiv). Default is embedded (fully-connected).",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Also save an interactive HTML plot of the graph (affine projection).",
    )
    args = parser.parse_args()

    mode = "lattice" if args.lattice else "embedded"
    add_nimplex_features(args.input_csv, args.output, mode=mode, plot=args.plot)
