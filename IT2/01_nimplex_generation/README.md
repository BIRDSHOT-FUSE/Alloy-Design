# IT2 Nimplex Generation

This folder contains the Nimplex step used to build the `IT2` composition space for the 11-element system:

`Ti V Ta Nb Mo Zr Cr Hf Fe Re W`

## What Is Nimplex

Nimplex is a library for working in compositional simplex spaces. It supports sampling, uniform grids, and graph-based traversal through composition space.

In this workflow, the main reason for using Nimplex was the graph-based representation of the composition space, including node and neighbor relationships.

## Overview

The composition space was generated with Nimplex. After generation, the Nimplex-specific parameters such as node and neighbor information were extracted from the full dataset.

For the later alloy-screening steps, only the composition data was needed. The CSV file generated from the Nimplex calculation without the Nimplex parameters was the file used to run the FLARE calculation.

The extracted Nimplex parameters were not required for FLARE or the later property-screening workflow.

## Why Nimplex Was Used Here

Nimplex was used because it provides a structured graph representation of a high-dimensional composition space.

This was useful for:

- generating the 11-element composition space in a systematic way,
- preserving node and neighbor relationships for graph-based analysis or plotting,
- separating the composition-only data needed for downstream property screening.

## Why The Nimplex Parameters Were Separated

The node and neighbor information is useful for describing the Nimplex representation, but it is not needed for later property calculations.

Separating those parameters makes the composition data easier to handle and reduces the size of the CSV used in the FLARE step.

## Files In This Folder

- `generate_nimplex.py`: generates the Nimplex composition space.
- `extract_compositions.py`: extracts the composition-only data from the generated Nimplex output.
- `add_nimplex_features.py`: adds back the Nimplex parameters when they are needed again for graph-based analysis or plotting.
- generated Nimplex data files may be created locally during the workflow, but large generated outputs are not kept in this repository.

## Workflow

1. Generate the composition space with `generate_nimplex.py`.
2. Extract the composition-only data with `extract_compositions.py`.
3. Use the generated composition-only CSV, without the Nimplex parameters, to run the FLARE calculation in `02_flare_screening/`.
4. If graph-based plotting or Nimplex-based analysis is needed later, restore the Nimplex parameters with `add_nimplex_features.py`.

## Notes

- No external input file was used for this step.
- The reduced composition-only file is the file used to run the FLARE calculation.
- The reduced composition-only file is not kept in this repository because of repository file-size limits.
- If graph-based analysis or plotting is needed later, the Nimplex parameters can be added back with `add_nimplex_features.py`.
- A plot can be included if available, but it is not required to understand this step.

## Learn More

- Nimplex repository: `https://github.com/amkrajewski/nimplex`
