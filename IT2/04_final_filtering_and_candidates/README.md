# IT2 Final Filtering And Candidates

This folder contains the final filtering step for `IT2` and the final candidate outputs produced from that step.

## Overview

This step takes the equilibrium-based result from the high-throughput screening workflow and applies the final filtering pipeline to identify the final candidate groups.

The input used in the notebook is the equilibrium-based table, typically saved as:

`FLARE-survivors-5at-10x_equil.csv`

That file is generated in the high-throughput workflow and then carried into this step.

## What Was Done

1. Start from the equilibrium-based result generated after the high-throughput screening workflow.
2. Load that input into `filter_5at_IT2.ipynb`.
3. Apply the weak-filtering stage to identify acceptable candidates.
4. Build the KNN graph and identify connected candidate subgraphs.
5. Save the master table and the subgraph tables.
6. Apply the second-stage filtering for Subgraph 1 to separate the final alloy categories.
7. Save the final tables and figures.

## Folder Layout

- `filter_5at_IT2.ipynb`: notebook used for the final filtering workflow.
- `outputs/`: final tables and figures produced by this step.

## Input To This Step

- Input file:
  equilibrium-based result table, typically `FLARE-survivors-5at-10x_equil.csv`

- Source of input:
  generated from the high-throughput screening workflow in `03_high_throughput_screening/`

- Role of input:
  this file is the starting table used by the notebook for the final filtering pipeline

## Filtering Pipeline

### Stage 1: Weak Filtering

The notebook first applies the weak-filtering criteria to the equilibrium-based input table.

This stage keeps candidates that satisfy the selected screening conditions and then builds a KNN graph to identify connected candidate subgraphs.

Outputs from this stage include:

- `outputs/IT2_master.csv`
- `outputs/IT2_Subgraph1.csv`
- `outputs/IT2_Subgraph2.csv`
- `outputs/IT2_Subgraph3.csv`
- `outputs/IT2_weakfilter_subgraphs.png`

### Stage 2: Final Candidate Categorization

The notebook then takes `Subgraph 1`, which is the main candidate cluster, and applies the second-stage filtering to classify the final alloy candidates.

Outputs from this stage include:

- `outputs/IT2_Subgraph1_AlloyAB.csv`
- `outputs/IT2_subgraph1_alloyAB.png`
- `outputs/IT2_subgraph1_continuous.png`

## Outputs

- `outputs/IT2_master.csv`: combined table used for final filtering.
- `outputs/IT2_Subgraph1.csv`: final candidate subgraph 1.
- `outputs/IT2_Subgraph1_AlloyAB.csv`: alloy summary table for subgraph 1.
- `outputs/IT2_subgraph1_alloyAB.png`: figure for subgraph 1 alloy relationships.
- `outputs/IT2_subgraph1_continuous.png`: continuous representation for subgraph 1.
- `outputs/IT2_Subgraph2.csv`: final candidate subgraph 2.
- `outputs/IT2_Subgraph3.csv`: final candidate subgraph 3.
- `outputs/IT2_weakfilter_subgraphs.png`: figure summarizing the weak-filter subgraphs.

## Output Of This Step

This step produces the final filtered tables, candidate group files, and summary figures for `IT2`.
