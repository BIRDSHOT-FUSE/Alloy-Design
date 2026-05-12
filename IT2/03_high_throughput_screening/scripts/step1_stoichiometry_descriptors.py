"""Batch compute stoichiometric descriptors for alloy candidates.

The script loads a CSV of candidate compositions, groups rows by their active
(elemental) basis, and evaluates thermodynamic/elastic descriptors in
parallel.  The previous version of this file had a large amount of duplicated
code, relied on side-effects (e.g. implicit globals and repeated overwrites of
columns), and repeatedly rebuilt constant look-up tables inside the worker
function.  This refactor keeps the original behaviour while making the data
flow explicit, reducing repeated work, and improving readability.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import compress
from pathlib import Path
from typing import List, Sequence
import argparse
import os
import time
import warnings

import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

# ---------------------------------------------------------------------------
# Elemental data (kept at module scope so that worker processes can reuse it).
# ---------------------------------------------------------------------------
ELEMENT_PROPERTY_DATA = {
    'W':  {'Atomic Weight [g/mol]': 183.84,   'Density [g/cm^3]': 19.25, 'Pauling Electronegativity': 2.36, 'Allen Electronegativity': 1.47,  'Melting Temperature [K]': 3695,   'Valence Electrons': 6, 'Atomic Number': 74},
    'Mo': {'Atomic Weight [g/mol]': 95.95,    'Density [g/cm^3]': 10.28, 'Pauling Electronegativity': 2.16, 'Allen Electronegativity': 1.47,  'Melting Temperature [K]': 2896,   'Valence Electrons': 6, 'Atomic Number': 42},
    'Ta': {'Atomic Weight [g/mol]': 180.95,   'Density [g/cm^3]': 16.69, 'Pauling Electronegativity': 1.5,  'Allen Electronegativity': 1.34,  'Melting Temperature [K]': 3290,   'Valence Electrons': 5, 'Atomic Number': 73},
    'Nb': {'Atomic Weight [g/mol]': 92.906,   'Density [g/cm^3]': 8.57,  'Pauling Electronegativity': 1.6,  'Allen Electronegativity': 1.41,  'Melting Temperature [K]': 2750,   'Valence Electrons': 5, 'Atomic Number': 41},
    'V':  {'Atomic Weight [g/mol]': 50.942,   'Density [g/cm^3]': 6.11,  'Pauling Electronegativity': 1.63, 'Allen Electronegativity': 1.53,  'Melting Temperature [K]': 2183,   'Valence Electrons': 5, 'Atomic Number': 23},
    'Al': {'Atomic Weight [g/mol]': 26.982,   'Density [g/cm^3]': 2.7,   'Pauling Electronegativity': 1.61, 'Allen Electronegativity': 1.613, 'Melting Temperature [K]': 933,    'Valence Electrons': 3, 'Atomic Number': 13},
    'Ti': {'Atomic Weight [g/mol]': 47.867,   'Density [g/cm^3]': 4.506, 'Pauling Electronegativity': 1.54, 'Allen Electronegativity': 1.38,  'Melting Temperature [K]': 1941,   'Valence Electrons': 4, 'Atomic Number': 22},
    'Zr': {'Atomic Weight [g/mol]': 91.224,   'Density [g/cm^3]': 6.52,  'Pauling Electronegativity': 1.33, 'Allen Electronegativity': 1.32,  'Melting Temperature [K]': 2128,   'Valence Electrons': 4, 'Atomic Number': 40},
    'Hf': {'Atomic Weight [g/mol]': 178.49,   'Density [g/cm^3]': 13.31, 'Pauling Electronegativity': 1.3,  'Allen Electronegativity': 1.16,  'Melting Temperature [K]': 2506,   'Valence Electrons': 4, 'Atomic Number': 72},
    'Cr': {'Atomic Weight [g/mol]': 51.996,   'Density [g/cm^3]': 7.15,  'Pauling Electronegativity': 1.66, 'Allen Electronegativity': 1.65,  'Melting Temperature [K]': 2180,   'Valence Electrons': 6, 'Atomic Number': 24},
    'Re': {'Atomic Weight [g/mol]': 186.207,  'Density [g/cm^3]': 21.02, 'Pauling Electronegativity': 1.9,  'Allen Electronegativity': 1.6,   'Melting Temperature [K]': 3459,   'Valence Electrons': 7, 'Atomic Number': 75},
    'Ru': {'Atomic Weight [g/mol]': 101.07,   'Density [g/cm^3]': 12.37, 'Pauling Electronegativity': 2.2,  'Allen Electronegativity': 1.54,  'Melting Temperature [K]': 2607.15,'Valence Electrons': 8, 'Atomic Number': 44},
    'Fe': {'Atomic Weight [g/mol]': 55.845,   'Density [g/cm^3]': 7.874, 'Pauling Electronegativity': 1.83, 'Allen Electronegativity': 1.8,   'Melting Temperature [K]': 1811,   'Valence Electrons': 8, 'Atomic Number': 26},
    'Ni': {'Atomic Weight [g/mol]': 58.6934,  'Density [g/cm^3]': 8.908, 'Pauling Electronegativity': 1.91, 'Allen Electronegativity': 1.88,  'Melting Temperature [K]': 1728,   'Valence Electrons': 10,'Atomic Number': 28},
    'Co': {'Atomic Weight [g/mol]': 58.933194, 'Density [g/cm^3]': 8.9,  'Pauling Electronegativity': 1.88, 'Allen Electronegativity': 1.84,  'Melting Temperature [K]': 1768,   'Valence Electrons': 2, 'Atomic Number': 27},
    'Mn': {'Atomic Weight [g/mol]': 54.938044, 'Density [g/cm^3]': 7.47, 'Pauling Electronegativity': 1.55, 'Allen Electronegativity': 1.75,  'Melting Temperature [K]': 2334,   'Valence Electrons': 7, 'Atomic Number': 25},
    'Cu': {'Atomic Weight [g/mol]': 63.546,   'Density [g/cm^3]': 8.96,  'Pauling Electronegativity': 1.9,  'Allen Electronegativity': 1.85,  'Melting Temperature [K]': 1358,   'Valence Electrons': 11,'Atomic Number': 29},
}

ELASTIC_PROPERTY_DATA = {
    'W':  {'C11': 517.8, 'C12': 201.7, 'C44': 139.4, 'B': 306.4, 'G': 139.4, 'B*': 310,  'G*': 161,  'V*': 0.28,  'Rm': 140.8},
    'Mo': {'C11': 466.0, 'C12': 165.2, 'C44': 99.5,  'B': 265.8, 'G': 99.5,  'B*': 230,  'G*': 20,   'V*': 0.31,  'Rm': 140.0},
    'Ta': {'C11': 260.9, 'C12': 165.2, 'C44': 70.4,  'B': 197.1, 'G': 70.4,  'B*': 200,  'G*': 67,   'V*': 0.34,  'Rm': 146.7},
    'Nb': {'C11': 247.2, 'C12': 140.0, 'C44': 14.2,  'B': 175.7, 'G': 14.2,  'B*': 170,  'G*': 38,   'V*': 0.40,  'Rm': 146.8},
    'V':  {'C11': 272.0, 'C12': 144.8, 'C44': 17.6,  'B': 187.2, 'G': 17.6,  'B*': 160,  'G*': 47,   'V*': 0.37,  'Rm': 134.6},
    'Al': {'C11': 38.7,  'C12': 79.2,  'C44': 33.0,  'B': 65.7,  'G': 33.0,  'B*': 76,   'G*': 26,   'V*': 0.35,  'Rm': 143.2},
    'Ti': {'C11': 95.9,  'C12': 115.9, 'C44': 40.3,  'B': 109.2, 'G': 40.3,  'B*': 110,  'G*': 44,   'V*': 0.32,  'Rm': 146.2},
    'Zr': {'C11': 81.8,  'C12': 94.3,  'C44': 30.2,  'B': 90.1,  'G': 30.2,  'B*': 91.1, 'G*': 33,   'V*': 0.34,  'Rm': 160.2},
    'Hf': {'C11': 73.7,  'C12': 117.0, 'C44': 51.7,  'B': 102.8, 'G': 51.7,  'B*': 110,  'G*': 30,   'V*': 0.37,  'Rm': 158.0},
    'Cr': {'C11': 247.6, 'C12': 73.4,  'C44': 48.3,  'B': 131.5, 'G': 48.3,  'B*': 160,  'G*': 115,  'V*': 0.21,  'Rm': 136.0},
    'Re': {'C11': 325.0, 'C12': 380.2, 'C44': 158.6, 'B': 361.5, 'G': 158.6, 'B*': 324,  'G*': 185,  'V*': 0.30,  'Rm': 137.0},
    'Ru': {'C11': 46.6,  'C12': 401.1, 'C44': 173.4, 'B': 283.1, 'G': 173.4, 'B*': 220,  'G*': 173,  'V*': 0.30,  'Rm': 134.0},
    'Fe': {'C11': 279.2, 'C12': 148.8, 'C44': 93.0,  'B': 192.3, 'G': 93.0,  'B*': 170,  'G*': 82,   'V*': 0.291, 'Rm': 127.4},
    'Ni': {'C11': 148.6, 'C12': 214.3, 'C44': 151.7, 'B': 192.4, 'G': 151.7, 'B*': 181,  'G*': 79,   'V*': 0.31,  'Rm': 124.6},
    'Co': {'C11': 129.3, 'C12': 140.9, 'C44': 93.5,  'B': 136.9, 'G': 93.5,  'B*': 193,  'G*': 74,   'V*': 0.32,  'Rm': 125.2},
    'Mn': {'C11': 256.9, 'C12': 272.2, 'C44': 105.4, 'B': 267.1, 'G': 105.4, 'B*': 92.6, 'G*': 76.4, 'V*': 0.35,  'Rm': 135.0},
    'Cu': {'C11': 129.3, 'C12': 140.9, 'C44': 93.5,  'B': 136.9, 'G': 93.5,  'B*': 137.5,'G*': 46.5, 'V*': 0.34,  'Rm': 127.8}
}

OUTPUT_DIR = Path('CalcFiles')

# ---------------------------------------------------------------------------
# Strength model implementation (embedded for modularity)
# ---------------------------------------------------------------------------
STRENGTH_ELASTIC_CONSTANTS = {
    'Al': {'C11': 38.7, 'C12': 79.2, 'C44': 33.0},
    'C': {'C11': 184.6, 'C12': 175.4, 'C44': 144.5},
    'Co': {'C11': 129.3, 'C12': 140.9, 'C44': 93.5},
    'Cr': {'C11': 247.6, 'C12': 73.4, 'C44': 48.3},
    'Cu': {'C11': 129.3, 'C12': 140.9, 'C44': 93.5},
    'Fe': {'C11': 279.2, 'C12': 148.8, 'C44': 93.0},
    'Hf': {'C11': 73.7, 'C12': 117.0, 'C44': 51.7},
    'Li': {'C11': 14.6, 'C12': 13.8, 'C44': 11.5},
    'Mg': {'C11': 36.4, 'C12': 34.1, 'C44': 30.9},
    'Mn': {'C11': 256.9, 'C12': 272.2, 'C44': 105.4},
    'Mo': {'C11': 466.0, 'C12': 165.2, 'C44': 99.5},
    'Nb': {'C11': 247.2, 'C12': 140.0, 'C44': 14.2},
    'Ni': {'C11': 148.6, 'C12': 214.3, 'C44': 151.7},
    'Pd': {'C11': 152.6, 'C12': 177.2, 'C44': 93.3},
    'Re': {'C11': 325.0, 'C12': 380.2, 'C44': 158.6},
    'Ru': {'C11': 46.6, 'C12': 401.1, 'C44': 173.4},
    'Sc': {'C11': 53.2, 'C12': 54.9, 'C44': 32.5},
    'Si': {'C11': 5.6, 'C12': 131.1, 'C44': 12.7},
    'Sn': {'C11': 29.7, 'C12': 59.9, 'C44': 17.6},
    'Ta': {'C11': 260.9, 'C12': 165.2, 'C44': 70.4},
    'Ti': {'C11': 95.9, 'C12': 115.9, 'C44': 40.3},
    'V': {'C11': 272.0, 'C12': 144.8, 'C44': 17.6},
    'W': {'C11': 517.8, 'C12': 201.7, 'C44': 139.4},
    'Y': {'C11': 16.1, 'C12': 48.4, 'C44': 14.8},
    'Zn': {'C11': 47.2, 'C12': 76.1, 'C44': -1.0},
    'Zr': {'C11': 81.8, 'C12': 94.3, 'C44': 30.2},
}

STRENGTH_BCC_VOLUMES = {
    'Al': 17.08,
    'Co': 11.07,
    'Cr': 11.575,
    'Cu': 12.077,
    'Fe': 11.358,
    'Hf': 22.128,
    'Mn': 10.985,
    'Mo': 15.956,
    'Nb': 18.342,
    'Ni': 11.012,
    'Re': 15.135,
    'Ru': 14.348,
    'Ta': 18.313,
    'Ti': 17.123,
    'V': 13.453,
    'W': 16.229,
    'Zr': 22.885,
}


def _strength_model(elements: dict[str, dict[str, float]], alpha: float = 1 / 12, prop_dfs: list | None = None) -> dict[str, np.ndarray | float]:
    if prop_dfs:
        warnings.warn('Custom property data frames are ignored; using built-in tables.', RuntimeWarning)

    missing_elastic = [el for el in elements if el not in STRENGTH_ELASTIC_CONSTANTS]
    missing_volume = [el for el in elements if el not in STRENGTH_BCC_VOLUMES]
    if missing_elastic:
        raise KeyError(f'Missing elastic constants for elements: {", ".join(missing_elastic)}')
    if missing_volume:
        raise KeyError(f'Missing BCC volumes for elements: {", ".join(missing_volume)}')

    bar_C11 = bar_C12 = bar_C44 = bar_V = 0.0
    misfit_vol_factor = 0.0
    misfit: dict[str, float] = {}

    for element, props in elements.items():
        constants = STRENGTH_ELASTIC_CONSTANTS[element]
        fraction = float(props['fraction'])
        bar_C11 += constants['C11'] * fraction
        bar_C12 += constants['C12'] * fraction
        bar_C44 += constants['C44'] * fraction

        props['BCCVol'] = STRENGTH_BCC_VOLUMES[element]
        bar_V += props['BCCVol'] * fraction

    for element, props in elements.items():
        misfit[element] = props['BCCVol'] - bar_V
        misfit_vol_factor += float(props['fraction']) * (misfit[element] ** 2)

    mu_bar = np.sqrt(0.5 * bar_C44 * (bar_C11 - bar_C12))
    B_bar = (bar_C11 + 2 * bar_C12) / 3
    nu_bar = (3 * B_bar - 2 * mu_bar) / (2 * (3 * B_bar + mu_bar))
    unit_cell_a = (2 * bar_V) ** (1 / 3)
    b_bar = unit_cell_a * np.sqrt(3) / 2

    tau_y_zero = 0.040 * (alpha ** (-1 / 3)) * mu_bar * (((1 + nu_bar) / (1 - nu_bar)) ** (4 / 3)) * ((misfit_vol_factor / (b_bar ** 6)) ** (2 / 3))
    delta_E_b = 2.00 * (alpha ** (1 / 3)) * mu_bar * (b_bar ** 3) * (((1 + nu_bar) / (1 - nu_bar)) ** (2 / 3)) * ((misfit_vol_factor / (b_bar ** 6)) ** (1 / 3))

    return {
        'tau_y_0': tau_y_zero,
        'delta_Eb': delta_E_b / 160.2176621,
        'Average C': [bar_C11, bar_C12, bar_C44],
        'misfit': misfit,
        'a': unit_cell_a,
        'bar_V': bar_V,
        'b_bar': b_bar,
        'mu_bar': mu_bar,
        'nu_bar': nu_bar,
    }


def _strength_temp_model(results: dict[str, float], eps_dot: float, approx_model: bool = False, T: float | Sequence[float] = 1573) -> np.ndarray:
    eps_dot_0 = 1e4
    k = 8.617e-5
    T_arr = np.asarray(T, dtype=float)

    if approx_model:
        tau = results['tau_y_0'] * np.exp(-(1 / 0.55) * (((k * T_arr) / results['delta_Eb']) * np.log(eps_dot_0 / eps_dot)) ** 0.91)
    else:
        tau_low = results['tau_y_0'] * (1 - (((k * T_arr) / results['delta_Eb']) * np.log(eps_dot_0 / eps_dot)) ** (2 / 3))
        tau_high = results['tau_y_0'] * np.exp(-(1 / 0.55) * ((k * T_arr) / results['delta_Eb']) * np.log(eps_dot_0 / eps_dot))
        mask = (tau_low / results['tau_y_0']) > 0.5
        tau = np.where(mask, tau_low, tau_high)
    return tau


def strength_model_control(element_list: Sequence[str], comp_list: Sequence[float], T: float = 1573, prop_dfs: list | None = None) -> tuple[float, float, np.ndarray]:
    model_input = {element_list[i]: {'fraction': float(comp_list[i])} for i in range(len(element_list))}
    result = _strength_model(model_input, prop_dfs=prop_dfs)
    tau = _strength_temp_model(result, 0.001, True, T)
    return result['tau_y_0'], result['delta_Eb'], tau


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def write_to_tracker(calc_name: str, text: str) -> None:
    """Append the supplied text to the tracker file, retrying if locked."""
    tracker_path = Path(f"{calc_name}-tracker.txt")
    while True:
        try:
            with tracker_path.open('a', encoding='utf-8') as handle:
                handle.write(text)
            return
        except OSError:
            time.sleep(0.05)


def _element_vector(elements: Sequence[str], data: dict[str, dict[str, float]], key: str) -> np.ndarray:
    return np.array([data[el][key] for el in elements], dtype=float)


def _rom_metrics(fractions: np.ndarray, element_values: np.ndarray, averages: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the ROM delta (sqrt sum) and min/max span for a property."""
    values = element_values[None, :]
    with np.errstate(divide='ignore', invalid='ignore'):
        normalised = 1.0 - (values / averages[:, None])
    contributions = fractions * normalised**2
    delta = np.sqrt(contributions.sum(axis=1))
    spread = contributions.max(axis=1) - contributions.min(axis=1)
    return delta, spread


@dataclass(slots=True)
class CalculationBatch:
    indices: List[int]
    compositions: pd.DataFrame
    active_elements: List[str]

    def __post_init__(self) -> None:
        # Workers mutate the dataframe; ensure each batch operates on its own copy.
        self.compositions = self.compositions.copy()


# ---------------------------------------------------------------------------
# Worker routine
# ---------------------------------------------------------------------------

def compute_property_batch(batch: CalculationBatch) -> str:
    start = time.time()
    comp_df = batch.compositions
    elements = batch.active_elements

    if comp_df.empty or not elements:
        return "No compositions provided"

    fractions = comp_df[elements].to_numpy(dtype=float)

    density_vec = _element_vector(elements, ELEMENT_PROPERTY_DATA, 'Density [g/cm^3]')
    mw_vec = _element_vector(elements, ELEMENT_PROPERTY_DATA, 'Atomic Weight [g/mol]')
    tm_vec = _element_vector(elements, ELEMENT_PROPERTY_DATA, 'Melting Temperature [K]')
    ve_vec = _element_vector(elements, ELEMENT_PROPERTY_DATA, 'Valence Electrons')
    pen_vec = _element_vector(elements, ELEMENT_PROPERTY_DATA, 'Pauling Electronegativity')
    allen_vec = _element_vector(elements, ELEMENT_PROPERTY_DATA, 'Allen Electronegativity')
    atomic_number_vec = _element_vector(elements, ELEMENT_PROPERTY_DATA, 'Atomic Number')

    c11_vec = _element_vector(elements, ELASTIC_PROPERTY_DATA, 'C11')
    c12_vec = _element_vector(elements, ELASTIC_PROPERTY_DATA, 'C12')
    c44_vec = _element_vector(elements, ELASTIC_PROPERTY_DATA, 'C44')
    b_vec = _element_vector(elements, ELASTIC_PROPERTY_DATA, 'B')
    g_vec = _element_vector(elements, ELASTIC_PROPERTY_DATA, 'G')
    b_reuss_vec = _element_vector(elements, ELASTIC_PROPERTY_DATA, 'B*')
    g_reuss_vec = _element_vector(elements, ELASTIC_PROPERTY_DATA, 'G*')
    v_reuss_vec = _element_vector(elements, ELASTIC_PROPERTY_DATA, 'V*')
    radius_vec = _element_vector(elements, ELASTIC_PROPERTY_DATA, 'Rm')

    comp_df['Density Avg'] = fractions @ density_vec
    comp_df['MW Avg'] = fractions @ mw_vec
    tm_avg = fractions @ tm_vec
    comp_df['Tm Avg'] = tm_avg
    comp_df['VEC Avg'] = fractions @ ve_vec
    comp_df['Atomic Number Avg'] = fractions @ atomic_number_vec

    comp_df['C11'] = fractions @ c11_vec
    comp_df['C12'] = fractions @ c12_vec
    comp_df['C44'] = fractions @ c44_vec
    comp_df['Cauchy Pres Avg'] = comp_df['C12'] - comp_df['C44']

    comp_df['Bulk Modulus Avg'] = fractions @ b_vec
    comp_df['Shear Modulus Avg'] = fractions @ g_vec

    b_reuss_avg = fractions @ b_reuss_vec
    g_reuss_avg = fractions @ g_reuss_vec
    v_reuss_avg = fractions @ v_reuss_vec

    comp_df['B_avgr'] = b_reuss_avg
    comp_df['G_avgr'] = g_reuss_avg
    comp_df['V_avgr'] = v_reuss_avg
    comp_df['E_avgr PS'] = 3 * b_reuss_avg * (1 - 2 * v_reuss_avg)
    comp_df['G_avgr PS'] = 0.5 * comp_df['E_avgr PS'] / (1 + v_reuss_avg)
    with np.errstate(divide='ignore', invalid='ignore'):
        comp_df['Pugh_Ratio_PRIOR'] = b_reuss_avg / comp_df['G_avgr PS']

    comp_df['Pauling Electronegativity Avg'] = fractions @ pen_vec
    comp_df['R'] = fractions @ radius_vec

    with np.errstate(divide='ignore', invalid='ignore'):
        log_terms = np.where(fractions > 0, np.log(fractions), 0.0)
    comp_df['Sconf'] = -(fractions * log_terms).sum(axis=1)

    delta_tm, spread_tm = _rom_metrics(fractions, tm_vec, tm_avg)
    delta_g, spread_g = _rom_metrics(fractions, g_reuss_vec, g_reuss_avg)
    delta_b, spread_b = _rom_metrics(fractions, b_reuss_vec, b_reuss_avg)
    delta_v, spread_v = _rom_metrics(fractions, v_reuss_vec, v_reuss_avg)
    delta_r, spread_r = _rom_metrics(fractions, radius_vec, comp_df['R'].to_numpy())
    delta_en, spread_en = _rom_metrics(fractions, allen_vec, comp_df['Pauling Electronegativity Avg'].to_numpy())

    comp_df['delta_T_ROM'] = delta_tm
    comp_df['delta_G_ROM'] = delta_g
    comp_df['delta_B_ROM'] = delta_b
    comp_df['delta_V_ROM'] = delta_v
    comp_df['delta_R_ROM'] = delta_r
    comp_df['delta_EN_ROM'] = delta_en

    comp_df['T_Delt'] = spread_tm
    comp_df['G_Delt'] = spread_g
    comp_df['B_Delt'] = spread_b
    comp_df['V_Delt'] = spread_v
    comp_df['R_Delt'] = spread_r
    comp_df['EN_Delt'] = spread_en

    hv_scale = 3000 * (3 / 9.807)
    comp_df = comp_df.reset_index()

    for idx, row in comp_df.iterrows():
        fractions_row = row[elements].to_numpy(dtype=float)
        test_temp_c = float(row['test_temperature_C'])

        tau_y0, delta_eb, tau_low = strength_model_control(elements, fractions_row, T=25)
        comp_df.at[idx, 'YS 25-273C PRIOR'] = 3000 * tau_low
        comp_df.at[idx, 'HV 25-273C PRIOR'] = hv_scale * tau_low + 150

        tau_y0, delta_eb, tau_room = strength_model_control(elements, fractions_row, T=25 + 273)
        comp_df.at[idx, 'YS 25C PRIOR'] = 3000 * tau_room
        comp_df.at[idx, 'HV 25C PRIOR'] = hv_scale * tau_room + 150

        tau_y0_high, delta_eb_high, tau_high = strength_model_control(elements, fractions_row, T=test_temp_c + 273)
        comp_df.at[idx, 'Tau_y 0'] = tau_y0_high
        comp_df.at[idx, 'delta Eb'] = delta_eb_high
        comp_df.at[idx, 'Tau_y 25C'] = tau_high
        comp_df.at[idx, 'YS T C PRIOR'] = 3000 * tau_high
        comp_df.at[idx, 'HV T C PRIOR'] = hv_scale * tau_high + 150

        _, _, tau_delta = strength_model_control(elements, fractions_row, T=test_temp_c)
        comp_df.at[idx, 'Tau_y 25-273C'] = tau_delta
        comp_df.at[idx, 'YS T-273C PRIOR'] = 3000 * tau_delta
        comp_df.at[idx, 'HV T-273C PRIOR'] = hv_scale * tau_delta + 150
        
        #YS at 600°C
        tau_y0_600, delta_eb_600, tau_600 = strength_model_control(elements, fractions_row, T=600 + 273)
        comp_df.at[idx, 'YS 600C PRIOR'] = 3000 * tau_600
        comp_df.at[idx, 'HV 600C PRIOR'] = hv_scale * tau_600 + 150

        #YS at 650°C
        tau_y0_650, delta_eb_650, tau_650 = strength_model_control(elements, fractions_row, T=650 + 273)
        comp_df.at[idx, 'YS 650C PRIOR'] = 3000 * tau_650
        comp_df.at[idx, 'HV 650C PRIOR'] = hv_scale * tau_650 + 150

    output_path = OUTPUT_DIR / f'STOIC_OUT_{batch.indices[0]}.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    comp_df.to_csv(output_path, index=False)

    duration = time.time() - start
    print(f'Completed batch starting at {batch.indices[0]} in {duration:.2f} s')
    return 'Calculation Completed'


# ---------------------------------------------------------------------------
# Batch generation
# ---------------------------------------------------------------------------

def build_batches(
    results_df: pd.DataFrame,
    elements: Sequence[str],
    batch_size: int = 200,
    calc_prefix: str = 'PROP',
) -> list[CalculationBatch]:
    parameters: list[CalculationBatch] = []
    current_indices: list[int] = []
    current_active: list[str] | None = None

    calc_dir = OUTPUT_DIR

    for idx in results_df.index:
        row = results_df.loc[idx]
        active_elements = list(compress(elements, row[elements].to_numpy(dtype=float) > 0))

        if current_active is None:
            current_active = active_elements

        should_flush = (
            active_elements != current_active or
            len(current_indices) >= batch_size
        )

        if should_flush and current_indices:
            start_idx = current_indices[0]
            marker_path = calc_dir / f'{calc_prefix}-Results-Set-{start_idx}'
            if not marker_path.exists():
                batch_df = results_df.loc[current_indices]
                parameters.append(CalculationBatch(current_indices.copy(), batch_df, current_active))
                write_to_tracker(calc_prefix, f'Calculation added: start index {start_idx}\n')
            else:
                write_to_tracker(calc_prefix, f'Calculation skipped (already present): start index {start_idx}\n')

            current_indices = []
            current_active = active_elements

        current_indices.append(idx)

    if current_indices:
        start_idx = current_indices[0]
        marker_path = calc_dir / f'{calc_prefix}-Results-Set-{start_idx}'
        if not marker_path.exists():
            batch_df = results_df.loc[current_indices]
            parameters.append(CalculationBatch(current_indices, batch_df, current_active or []))
            write_to_tracker(calc_prefix, f'Calculation added: start index {start_idx}\n')
        else:
            write_to_tracker(calc_prefix, f'Calculation skipped (already present): start index {start_idx}\n')

    return parameters


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate stoichiometric descriptors in batches.')
    parser.add_argument('--input', default='FLARE-survivors-5at-10x.csv', help='Input CSV file with alloy compositions')
    parser.add_argument('--output-dir', default='CalcFiles', help='Directory to write batch outputs')
    parser.add_argument('--max-workers', type=int, default=25, help='Maximum parallel workers')
    parser.add_argument('--batch-size', type=int, default=200, help='Rows per calculation batch')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    global OUTPUT_DIR
    OUTPUT_DIR = Path(args.output_dir)

    results_df = pd.read_csv(args.input)
    print(f'Loaded dataset with {len(results_df)} alloys')

    if 'test_temperature_C' not in results_df.columns:
        results_df['test_temperature_C'] = 1300.0
    element_candidates = [col for col in results_df.columns if col in ELEMENT_PROPERTY_DATA]
    if not element_candidates:
        raise ValueError('No elemental fraction columns found in input file.')
    elements = sorted(element_candidates)
    print(f'Active elements detected ({len(elements)}): {elements}')

    def alloy_system(row: pd.Series) -> str:
        return '_'.join(sorted(el for el in elements if row[el] > 0))

    results_df['alloy_system'] = results_df.apply(alloy_system, axis=1)
    results_df = results_df.sort_values('alloy_system').reset_index(drop=True)

    write_to_tracker('PROP', '***** Start generating calculation sets *****\n')
    batches = build_batches(results_df, elements, batch_size=args.batch_size)
    write_to_tracker('PROP', f'Generated {len(batches)} calculation batches\n')
    print(f'Generated {len(batches)} calculation batches')

    max_workers = min(args.max_workers, os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for batch, outcome in zip(batches, executor.map(compute_property_batch, batches)):
            if outcome == 'Calculation Completed':
                continue
            print(f'Batch {batch.indices[0]} finished with status: {outcome}')


if __name__ == '__main__':
    main()
