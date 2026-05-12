# IT2 High-Throughput Screening

This folder contains the high-throughput screening step for `IT2`.

## Overview

The selected FLARE survivor set was taken forward for additional high-throughput screening.

This step is a chained workflow:

1. start from the selected `10x` FLARE survivor set,
2. generate stoichiometry descriptors,
3. use the stoichiometry output as input to the property calculation,
4. use the property output as input to the equilibrium calculation,
5. carry the final equilibrium-based result forward to the final filtering step.

## What Was Done

1. Use the selected `10x` FLARE survivor set from `02_flare_screening/`.
2. Run `step1_stoichiometry_descriptors.py` to generate the stoichiometry descriptor output.
3. Use the stoichiometry output as input to `TC_Property_CHD1_Module.py`.
4. Use the property output as input to `TC_Equilibrium_Module_CHD.py`.
5. Use the equilibrium-based result in `04_final_filtering_and_candidates/`.

## Folder Layout

- `inputs/`: input survivor set carried forward from the FLARE screening step.
- `scripts/`: scripts used for stoichiometry and high-throughput calculations.

## Files In This Folder

- `inputs/FLARE-survivors-5at-10x.csv`: selected `10x` FLARE survivor set used in this step.
- `scripts/step1_stoichiometry_descriptors.py`: reads the selected `10x` FLARE survivor set and generates the stoichiometry-descriptor output.
- `scripts/TC_Property_CHD1_Module.py`: uses the stoichiometry output as input and runs the property calculation workflow.
- `scripts/TC_Equilibrium_Module_CHD.py`: uses the property output as input and runs the equilibrium calculation workflow.

## Input And Output Chain

- Input to this step:
  `inputs/FLARE-survivors-5at-10x.csv`

- Output from `step1_stoichiometry_descriptors.py`:
  stoichiometry-descriptor table, typically saved as
  `FLARE-survivors-5at-10x_stoic.csv`

- Input to `TC_Property_CHD1_Module.py`:
  stoichiometry-descriptor table, typically
  `FLARE-survivors-5at-10x_stoic.csv`

- Output from `TC_Property_CHD1_Module.py`:
  property-based result table, typically saved as
  `FLARE-survivors-5at-10x_prop.csv`

- Input to `TC_Equilibrium_Module_CHD.py`:
  property-based result table, typically
  `FLARE-survivors-5at-10x_prop.csv`

- Output from `TC_Equilibrium_Module_CHD.py`:
  equilibrium-based result table, typically saved as
  `FLARE-survivors-5at-10x_equil.csv`

- Input to the next step:
  the equilibrium-based result table, typically
  `FLARE-survivors-5at-10x_equil.csv`, is carried into
  `04_final_filtering_and_candidates/`

## Execution Environment

- compute system: Texas A&M HPRC Grace
- Thermo-Calc version: `2023.1`
- TC-Python database used for the property and equilibrium calculations: `TCHEA06`

## Output Of This Step

This step can generate multiple output tables, including:

- a stoichiometry-descriptor output,
- a property-calculation output,
- an equilibrium-calculation output.

These outputs are used in sequence, with each later calculation depending on the output of the previous one.

The final output carried to `04_final_filtering_and_candidates/` is the equilibrium-based result.

The full set of generated output files is not committed here because of repository file-size limits and because different runs may produce different working outputs.
