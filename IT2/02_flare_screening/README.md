# IT2 FLARE Screening

This folder contains the FLARE screening step for `IT2`.

## Overview

The composition-only CSV generated from the Nimplex calculation, without the Nimplex parameters, was used to calculate FLARE properties.

After the FLARE calculations, filtering was applied to produce the survivor archive used for the next stage of screening.

This step is focused on property-based screening rather than on the Nimplex graph representation.

## What Was Done

1. Use the composition-only data from `01_nimplex_generation/`.
2. Run the FLARE calculations for the generated compositions.
3. Stitch or combine the FLARE outputs when needed.
4. Apply the FLARE filtering workflow.
5. Keep the survivor outputs for downstream screening.

## Files In This Folder

- `run_FLARE_5at_1sec.py`: FLARE run script for the `1 sec` condition.
- `run_FLARE_5at_1month.py`: FLARE run script for the `1 month` condition.
- `run_FLARE_5at_100yr.py`: FLARE run script for the `100 year` condition.
- `run_FLARE_5at.slurm`: Slurm submission script used for the FLARE runs.
- `stitch_flare.py`: combines or stitches FLARE outputs for later analysis.
- `flare_5at_filter.ipynb`: notebook used for FLARE filtering and analysis.
- `outputs/`: retained FLARE figures kept in the repository.

## Outputs

- `outputs/Flare_survivor.png`: figure summarizing the FLARE survivor results.
- `outputs/Responses_filter-All_IT2_EUROFER_10.png`: FLARE filtering figure for the EUROFER comparison.
- `outputs/Responses_filter-All_IT2_W_10.png`: FLARE filtering figure for the W comparison.

## Output Of This Step

The selected `10x` survivor level used for `03_high_throughput_screening/` is stored as `03_high_throughput_screening/inputs/FLARE-survivors-5at-10x.csv`.

The full FLARE survivor archive from `1x` to `31x` is not kept in this repository because of repository file-size limits.

## Notes

- The FLARE workflow includes multiple run conditions and a stitching step before final filtering.
- This folder keeps the scripts and notebook at the top level, while the generated results are grouped under `outputs/`.
- This step was run in the `nimplex` environment, with FLARE installed in that environment.
