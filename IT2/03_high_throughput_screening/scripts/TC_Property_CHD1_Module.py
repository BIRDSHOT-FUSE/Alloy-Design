#!/usr/bin/env python
"""
TC Python property — IT2.

Changes from previous version:
  1. ProcessPoolExecutor worker count set via TC_MAX_WORKERS env var (default 2,
     to respect TC license seat limits). Set with: export TC_MAX_WORKERS=4
  2. multiprocessing 'spawn' start method to avoid fork+JVM deadlocks.
  3. PCTE save line moved INSIDE the temperature loop (was a bug — only saved
     at the last temperature).
  4. Calculation timeouts added (calculate(timeout_in_minutes=2)).
  5. result.invalidate() added after each calculation to free JVM memory.
  6. Resume check filename now matches the actual save filename (was checking
     'PROP-Results-Set-*' but saving 'PROP_OUT_*.csv').
  7. Status string consistent: function returns 'Calculation Completed', main
     checks for 'Calculation Completed'.
  8. Gathering-systems print throttled (was printing every row, log got huge).
  9. Reduced default batch size from 5000 to 500 (faster failure recovery,
     smaller pickle payloads).
"""
import numpy as np
import pandas as pd
from tc_python import *
from itertools import compress
from tc_python import server
import time
import concurrent.futures
import multiprocessing as mp
import os.path as path
import os
import sys
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
INPUT_CSV = 'FLARE-survivors-5at-10x_stoic.csv'
ELEMENTS = sorted(['Ti', 'V', 'Ta', 'Nb', 'Mo', 'Zr', 'Cr', 'Hf', 'Fe', 'Re', 'W'])
BATCH_SIZE = 500          # was 5000 — smaller batches recover faster on failure
CALC_TIMEOUT_MIN = 2      # per-calculation timeout (minutes)
DEFAULT_WORKERS = 2       # safe default if TC_MAX_WORKERS not set


def Property(param):
    indices = param["INDICES"]
    comp_df = param["COMP"].copy()    # don't mutate caller
    elements = param["ACT_EL"]
    active_el = elements

    output_path = Path('CalcFiles') / f'PROP_OUT_{indices[0]}.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with TCPython(logging_policy=LoggingPolicy.NONE) as session:
        session.disable_caching()
        eq_calculation = (
            session
                .select_database_and_elements('TCHEA6', active_el)
                .get_system()
                .with_property_model_calculation("Liquidus and Solidus Temperature")
                .set_argument('upperTemperatureLimit', 4000)
                .set_composition_unit(CompositionUnit.MOLE_FRACTION)
                .set_temperature(400))
        prop_calc = (
            session
                .select_database_and_elements('TCHEA6', active_el)
                .get_system()
                .with_property_model_calculation('Equilibrium with Freeze-in Temperature')
                .set_temperature(25 + 273.15)
                .set_composition_unit(CompositionUnit.MOLE_FRACTION))

        indices = sorted(indices)
        print(f'Starting alloys with indices {indices[0]}-{indices[-1]}', flush=True)
        total_alloys = param.get("TOTAL", len(comp_df))

        for i in indices:
            completed_ok = False
            comp = np.array(comp_df.loc[i][active_el])
            try:
                if len(active_el) != 1:
                    for j in range(len(active_el) - 1):
                        eq_calculation.set_composition(active_el[j], comp[j])
                        prop_calc.set_composition(active_el[j], comp[j])
                else:
                    eq_calculation.set_dependent_element(active_el[0])
                    prop_calc.set_dependent_element(active_el[0])

                # ---- Liquidus / Solidus ----
                result = eq_calculation.calculate(timeout_in_minutes=CALC_TIMEOUT_MIN)
                try:
                    comp_df.at[i, 'PROP LT (K)'] = result.get_value_of('Liquidus temperature')
                    comp_df.at[i, 'PROP ST (K)'] = result.get_value_of('Solidus temperature')
                finally:
                    try:
                        result.invalidate()
                    except Exception:
                        pass

                # ---- Solidus properties ----
                prop_calc = (prop_calc
                             .set_argument('Freeze-in-temperature', comp_df.at[i, 'PROP ST (K)'])
                             .set_argument('Minimization strategy', 'Global minimization only')
                             .set_temperature(comp_df.at[i, 'PROP ST (K)']))
                prop_result = prop_calc.calculate(timeout_in_minutes=CALC_TIMEOUT_MIN)
                try:
                    comp_df.at[i, 'PROP ST Density (g/cm3)'] = prop_result.get_value_of('Density (g/cm3)')
                    comp_df.at[i, 'PROP ST C (J/(mol K))']    = prop_result.get_value_of('Heat capacity (J/(mol K))')
                    comp_df.at[i, 'PROP ST THCD (W/(mK))']    = prop_result.get_value_of('Thermal conductivity (W/(mK))')
                    comp_df.at[i, 'PROP ST THRS (mK/W)']      = prop_result.get_value_of('Thermal resistivity (mK/W)')
                    comp_df.at[i, 'PROP ST TDIV (m2/s)']      = prop_result.get_value_of('Thermal diffusivity (m2/s)')
                    comp_df.at[i, 'PROP ST ELRS (Ohm m)']     = prop_result.get_value_of('Electric resistivity (ohm m)')
                    comp_df.at[i, 'PROP ST ELCD (S/m)']       = prop_result.get_value_of('Electric conductivity (S/m)')
                finally:
                    try:
                        prop_result.invalidate()
                    except Exception:
                        pass

                # ---- Liquidus properties ----
                prop_calc = (prop_calc
                             .set_argument('Freeze-in-temperature', comp_df.at[i, 'PROP LT (K)'])
                             .set_argument('Minimization strategy', 'Global minimization only')
                             .set_temperature(comp_df.at[i, 'PROP LT (K)']))
                prop_result = prop_calc.calculate(timeout_in_minutes=CALC_TIMEOUT_MIN)
                try:
                    comp_df.at[i, 'PROP LT Density (g/cm3)'] = prop_result.get_value_of('Density (g/cm3)')
                    comp_df.at[i, 'PROP LT C (J/(mol K))']    = prop_result.get_value_of('Heat capacity (J/(mol K))')
                    comp_df.at[i, 'PROP LT THCD (W/(mK))']    = prop_result.get_value_of('Thermal conductivity (W/(mK))')
                    comp_df.at[i, 'PROP LT THRS (mK/W)']      = prop_result.get_value_of('Thermal resistivity (mK/W)')
                    comp_df.at[i, 'PROP LT TDIV (m2/s)']      = prop_result.get_value_of('Thermal diffusivity (m2/s)')
                    comp_df.at[i, 'PROP LT ELRS (Ohm m)']     = prop_result.get_value_of('Electric resistivity (ohm m)')
                    comp_df.at[i, 'PROP LT ELCD (S/m)']       = prop_result.get_value_of('Electric conductivity (S/m)')
                finally:
                    try:
                        prop_result.invalidate()
                    except Exception:
                        pass

                # ---- Per-temperature properties ----
                temperatures = [25, 600, 650, 700, 800, 900]
                for temp in temperatures:
                    target_temp_K = temp + 273.15
                    prop_calc_temp = (prop_calc
                                      .set_argument('Freeze-in-temperature', target_temp_K)
                                      .set_argument('Minimization strategy', 'Global minimization only')
                                      .set_argument('Reference temperature for technical CTE', 25 + 273.15)
                                      .set_temperature(target_temp_K))
                    prop_result = prop_calc_temp.calculate(timeout_in_minutes=CALC_TIMEOUT_MIN)
                    try:
                        comp_df.at[i, f'PROP {temp}C Density (g/cm3)'] = prop_result.get_value_of('Density (g/cm3)')
                        comp_df.at[i, f'PROP {temp}C C (J/(mol K))']    = prop_result.get_value_of('Heat capacity (J/(mol K))')
                        comp_df.at[i, f'PROP {temp}C THCD (W/(mK))']    = prop_result.get_value_of('Thermal conductivity (W/(mK))')
                        comp_df.at[i, f'PROP {temp}C THRS (mK/W)']      = prop_result.get_value_of('Thermal resistivity (mK/W)')
                        comp_df.at[i, f'PROP {temp}C TDIV (m2/s)']      = prop_result.get_value_of('Thermal diffusivity (m2/s)')
                        comp_df.at[i, f'PROP {temp}C ELRS (Ohm m)']     = prop_result.get_value_of('Electric resistivity (ohm m)')
                        comp_df.at[i, f'PROP {temp}C ELCD (S/m)']       = prop_result.get_value_of('Electric conductivity (S/m)')
                        # 2023.1 quantity names — no '(Eq. Freeze-in Temp.)' suffix
                        comp_df.at[i, f'PROP {temp}C TCTE (1/K)']       = prop_result.get_value_of('Thermal expansion (1/K)')
                        # PCTE — now correctly inside the temperature loop (was a bug before)
                        comp_df.at[i, f'PROP {temp}C PCTE (1/K)']       = prop_result.get_value_of('Technical thermal expansion (1/K)')
                    finally:
                        try:
                            prop_result.invalidate()
                        except Exception:
                            pass

                completed_ok = True
            except Exception as e2:
                tb = traceback.extract_tb(e2.__traceback__)
                line = tb[0][1] if tb else '?'
                print(f'Exception on line {line}: {e2}', flush=True)
            finally:
                comp_df.to_csv(output_path, index=False)

            if completed_ok:
                percent_done = ((i + 1) / total_alloys) * 100.0
                comp_label = comp_df.at[i, 'composition'] if 'composition' in comp_df.columns else i
                print(f"Completed alloy {comp_label} (index {i}) — approx. {percent_done:.2f}% done", flush=True)

        print(f'Saving alloys with indices {indices[0]}-{indices[-1]}', flush=True)
    return 'Calculation Completed'


if __name__ == '__main__':
    # Critical: avoid fork+JVM deadlocks on Linux. Always 'spawn' for TC Python.
    try:
        mp.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

    ##########################################################################
    # Initialize variables and load the data
    print(f'Loading {INPUT_CSV} ...', flush=True)
    results_df = pd.read_csv(INPUT_CSV)
    elements = ELEMENTS
    print(f'Loaded {len(results_df)} compositions across {len(elements)} elements', flush=True)

    ##########################################################################
    # Reorganize dataframe to have ordered sequence of element groups
    # (to minimize Thermo-Calc initializations and improve efficiency)
    tic = time.time()
    Els = list()
    prev_active_el = []
    n_rows = results_df.shape[0]
    print_every = max(1, n_rows // 100)   # print roughly 100 progress lines, not 60K

    for row in range(n_rows):
        comp = results_df.iloc[row][elements]
        active_el = list(compress(elements, list(comp > 0)))
        if active_el not in Els:
            Els.append(active_el)
        prev_active_el = active_el
        if row % print_every == 0 or row == n_rows - 1:
            toc = time.time()
            pct = (row + 1) / n_rows * 100
            print(f"{pct:.1f} % Done Gathering Systems in {toc - tic:.2f} secs", flush=True)

    results_df = results_df.reset_index(drop=True)

    if not path.exists("CalcFiles"):
        os.mkdir("CalcFiles")

    indices = results_df.index
    prev_active_el = []
    parameters = []
    count = 0
    total_count = len(results_df)
    new_calc_dict = {"INDICES": [], "COMP": [], "ACT_EL": [], "TOTAL": total_count}

    for i in indices:
        comp = results_df.loc[i][elements]
        active_el = list(compress(elements, list(comp > 0)))
        if (active_el != prev_active_el) or (count == BATCH_SIZE):
            try:
                new_calc_dict["COMP"] = results_df.loc[new_calc_dict["INDICES"]]
                new_calc_dict["ACT_EL"] = prev_active_el
                new_calc_dict["TOTAL"] = total_count
                # Resume check — filename now matches the actual save name
                expected_out = f"CalcFiles/PROP_OUT_{new_calc_dict['INDICES'][0]}.csv"
                if not os.path.exists(expected_out):
                    parameters.append(new_calc_dict)
                else:
                    print(f"****** Calculation already done: {expected_out}", flush=True)
                new_calc_dict = {"INDICES": [], "COMP": [], "ACT_EL": [], "TOTAL": total_count}
            except Exception as e:
                new_calc_dict = {"INDICES": [], "COMP": [], "ACT_EL": [], "TOTAL": total_count}
            count = 0
        new_calc_dict["INDICES"].append(i)
        prev_active_el = active_el
        count += 1

    # Final batch
    new_calc_dict["COMP"] = results_df.loc[new_calc_dict["INDICES"]]
    new_calc_dict["ACT_EL"] = prev_active_el
    new_calc_dict["TOTAL"] = total_count
    expected_out = f"CalcFiles/PROP_OUT_{new_calc_dict['INDICES'][0]}.csv"
    if not os.path.exists(expected_out):
        parameters.append(new_calc_dict)
        print(f"** Calculation added: Start Index {new_calc_dict['INDICES'][0]}", flush=True)
    else:
        print(f"** Already done: {expected_out}", flush=True)

    print(f"***** {len(parameters)} calculation sets generated *****\n", flush=True)
    completed_calculations = []
    del results_df

    # Worker count — env var TC_MAX_WORKERS, else DEFAULT_WORKERS
    max_env = int(os.getenv("TC_MAX_WORKERS", "0"))
    max_workers = max_env if max_env > 0 else DEFAULT_WORKERS
    max_workers = min(max_workers, len(parameters))
    print(f'Running with {max_workers} parallel workers '
          f'(set TC_MAX_WORKERS env var to change)', flush=True)

    # Parallel dispatch
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        for params, results in zip(parameters, executor.map(Property, parameters)):
            if results == 'Calculation Completed':
                completed_calculations.append('Completed')

    print(f'Done. {len(completed_calculations)} / {len(parameters)} batches completed.', flush=True)
