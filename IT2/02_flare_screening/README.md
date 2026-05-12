# IT2 FLARE Screening

This folder contains the FLARE screening step for `IT2`.

## Overview

The composition-only data from the Nimplex step was used to calculate FLARE properties. After the FLARE calculations, filtering was applied to identify the survivor set used for the next stage of screening.

This step is focused on property-based screening rather than on the Nimplex graph representation.

## What Was Done

1. Use the composition-only data from `01_nimplex_generation/`.
2. Run the FLARE calculations for the generated compositions.
3. Stitch or combine the FLARE outputs when needed.
4. Apply the FLARE filtering workflow.
5. Keep the survivor set for the next screening stage.

## Files In This Folder

- `run_FLARE_1sec_5at%.py`: FLARE run script for the `1 sec` condition.
- `run_FLARE_1month_5at%.py`: FLARE run script for the `1 month` condition.
- `run_FLARE_100yr_5at%.py`: FLARE run script for the `100 year` condition.
- `run_FLARE_5at%.slurm`: Slurm submission script used for the FLARE runs.
- `stitch_flare.py`: combines or stitches FLARE outputs for later analysis.
- `5at%flare_filter.ipynb`: notebook used for FLARE filtering and analysis.
- `FLARE-survivor-summary-5at.csv`: summary table of survivor counts from `1x` to `31x`, including file sizes in bytes and MB.
- `FLARE-survivors-5at-10x.csv`: filtered FLARE survivor set.
- `Flare_survivor.png`: figure summarizing the FLARE survivor results.
- `Responses_filter-All_IT2_EUROFER_10.png`: FLARE filtering figure for the EUROFER comparison.
- `Responses_filter-All_IT2_W_10.png`: FLARE filtering figure for the W comparison.

## Output Of This Step

The main output of this step is the `10x` FLARE survivor set, which is then used in `03_high_throughput_screening/`.

The summary table records the survivor counts for `1x` through `31x` so readers can see how the survivor set changes across the screening levels.

## Notes

- The FLARE workflow includes multiple run conditions and a stitching step before final filtering.
- This folder keeps the filtered FLARE results and summary figures needed to explain the screening step.
- The important artifact for the next stage is the `10x` survivor set, not every intermediate calculation file.
- The survivor summary table is kept to show the progression from `1x` to `31x` without storing every survivor CSV in the repository.
