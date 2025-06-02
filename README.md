<div align="center">

# Alloy Composition Generator (Nimplex)

[![Python](https://img.shields.io/badge/python-3.11+-brightgreen.svg)](https://www.python.org/)

This script uses the Nimplex library to generate alloy compositions within a simplex for any number of elements. It builds a composition graph with node coordinates and neighbor connections, and optionally visualizes the composition space (up to 4 elements).

<p>
  <a href="https://github.com/BIRDSHOT-FUSE/Alloy-Design/issues/new?labels=bug">Report a Bug</a> |
  <a href="https://github.com/BIRDSHOT-FUSE/Alloy-Design/issues/new?labels=enhancement">Request a Feature</a>
</p>

</div>

---

## Features

- Generates n-dimensional simplex-based alloy composition grids
- Supports custom composition limits for each element
- Exports a CSV with node IDs, compositions, and neighbor indices
- Supports 2D and 3D plotting of composition space for 3 and 4 element systems

## Requirements

- Python 3.11+
- `nimplex`, `pandas`, `numpy`,
- *(Optional)* `plotly`

- For installation instructions, see the [nimplex installation guide](https://github.com/BIRDSHOT-FUSE/nimplex#installation).

## Usage

Run the script from the command line:

```bash
python generate_nimplex.py Co Cr Fe Ni --ndiv 10 --limit 0 1 0 1 0 1 0 1 --plot
```

### Arguments

- `elements`: Positional argument. List of element symbols (space-separated). Example: `Co Cr Fe Ni`
- `--ndiv`: Number of divisions for the simplex (default: 10)
- `--limit`: Min and max for each element, in order. For 4 elements: `--limit 0 1 0 1 0 1 0 1`
- `--no_csv`: If set, skips writing output to CSV
- `--plot`: Generates a 2D or 3D plot of the composition space (only for 3 and 4 elements) For higher dimensions, the script will raise an error.

### Example

Generate a 4-element (Co, Cr, Fe, Ni) composition space with 10 divisions and equal composition limits (0 to 1):

```bash
python generate_nimplex.py Co Cr Fe Ni --ndiv 10 --limit 0 1 0 1 0 1 0 1 --plot
```

This will create:
- A CSV file: `CoCrFeNi_ndiv_10_nimplex_space.csv`
- An HTML file with a 3D plot: `CoCrFeNi_ndiv_10_plot.html`

## Output

The output CSV contains:
- `Node ID`: Unique identifier for each composition
- `Neighbor_*`: Indices of neighboring nodes in the composition graph
- One column per element: Fractional composition of each element
