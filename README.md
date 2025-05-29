<div align="center">

# Alloy Composition Generator (Nimplex)

[![Python](https://img.shields.io/badge/python-3.11+-brightgreen.svg)](https://www.python.org/)

This script uses the Nimplex library to generate alloy compositions within a simplex defined by 11 elements. It builds a composition graph with node coordinates and neighbor connections.

<p>
  <a href="https://github.com/BIRDSHOT-FUSE/Alloy-Design/issues/new?labels=bug">Report a Bug</a> |
  <a href="https://github.com/BIRDSHOT-FUSE/Alloy-Design/issues/new?labels=enhancement">Request a Feature</a>
</p>

</div>

---

## Features

- Generates simplex-based alloy composition grids for any number of elements
- Supports custom composition limits for each element
- Outputs a CSV with node IDs, compositions, and neighbor indices
- Includes optional 3D plotting

## Requirements

- Python 3.11+
- `nimplex`, `pandas`, `numpy`,
- *(Optional)* `plotly`, `matplotlib`, `imageio`, `Pillow`

- For installation instructions, see the [nimplex installation guide](https://github.com/BIRDSHOT-FUSE/nimplex#installation).

## Usage

Run the script from the command line:

```bash
python generate_nimplex.py --elements Co Cr Fe Ni --ndiv 10
```

### Arguments

- `--elements`: List of element symbols (space-separated). Example: `Co Cr Fe Ni`
- `--ndiv`: Number of divisions for the simplex (default: 10)
- `--limit`: Min and max for each element, in order. For 4 elements: `--limit 0 1 0 1 0 1 0 1`
- `--write_to_csv`: If set, writes the output to a CSV file (default: True)

### Example

Generate a 4-element (Co, Cr, Fe, Ni) composition space with 10 divisions and default limits (0 to 1 for each):

```bash
python generate_nimplex.py --elements Co Cr Fe Ni --ndiv 10 --limit 0 1 0 1 0 1 0 1 --write_to_csv
```

This will create a file named `CoCrFeNi_nimplex_space.csv` in the current directory.

## Output

The output CSV contains:
- `Node ID`: Unique identifier for each composition
- `Neighbor_*`: Indices of neighboring nodes in the composition graph
- One column per element: Fractional composition of each element
