# IT2 Workflow

This directory documents the full `IT2` candidate-selection workflow from composition generation through final filtering.

## Pipeline Summary

1. Generate the composition space with Nimplex, extract the Nimplex parameters, and prepare the composition-only file.
2. Run the FLARE workflow on the composition-only file, including calculations, filtering, survivor sets, and plots.
3. Run high-throughput screening on the selected survivor level.
4. Apply final filtering to the combined property results.
5. Collect the final candidates, figures, and summary tables.

## Directory Guide

- `00_overview/`: high-level workflow notes, assumptions, and environment details.
- `01_nimplex_generation/`: composition generation inputs, scripts, and outputs.
- `02_flare_screening/`: FLARE calculations, filtering, survivor outputs, and plots.
- `03_high_throughput_screening/`: STOIC and CALPHAD screening for the selected survivor set.
- `04_final_filtering/`: final filtering of the high-throughput results.
- `05_final_candidates/`: final deliverables for `IT2`.

## Current Notes

- `IT2_FLARE_survivors.zip` is stored under `02_flare_screening/outputs/`.
- Step 2 is intended to hold both survivor files and plots produced from the FLARE workflow.

## Recommended Use

Each step folder should contain:

- a short `README.md` describing the step,
- the relevant input files,
- scripts or notebooks used for the step,
- output tables or summary results that feed the next stage.

Keep large raw calculation outputs out of Git when possible. Prefer committing scripts, settings, reduced CSV outputs, and final summary tables.
