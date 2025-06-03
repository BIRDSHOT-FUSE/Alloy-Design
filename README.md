# Alloy Composition Generator (Nimplex)

This script uses the Nimplex library to generate alloy compositions within a simplex defined by 11 elements. It builds a composition graph with node coordinates and neighbor connections.

## Features

- Generates binary to quinary alloy compositions
- Assigns node IDs and neighbor relationships
- Outputs a CSV file with full composition data
- Includes optional 3D plotting (commented out)

## Elements

Ti, V, Ta, Nb, Mo, Zr, Cr, Hf, Fe, Re, W

## Requirements

- Python 3
- `nimplex`, `pandas`, `numpy`, `networkx`
- *(Optional)* `plotly`, `matplotlib`, `imageio`, `Pillow`

## Usage

```bash
python Generate_Composition_Nimplex.py```

#TC-Python Property Module
