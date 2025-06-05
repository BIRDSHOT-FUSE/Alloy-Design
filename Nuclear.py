import pandas as pd
import numpy as np

# === Input CSV path ===
input_file = "compositionforactivation.csv"  # ← Update this if needed

# === Master element list (must match order in data arrays) ===
master_elements = ["Ti", "V", "Ta", "Nb", "Mo", "Zr", "Cr", "Hf", "Fe", "Re", "W"]

# === Nuclear Property Data ===
activation_data = np.array([
    [1.000e+00, 1.000e+00, 1.000e+00],  # W
    [1.848e-02, 4.900e-02, 7.224e-02],  # Ti
    [4.948e-01, 5.673e-03, 6.319e-01],  # V
    [1.182e+01, 2.736e+01, 9.615e-01],  # Ta
    [2.121e-01, 3.796e-01, 2.541e+04],  # Nb
    [5.196e-02, 1.693e-02, 3.590e+04],  # Mo
    [4.165e-01, 2.798e-02, 8.576e+01],  # Zr
    [7.462e-02, 6.169e-02, 2.518e-01],  # Cr
    [2.787e+01, 1.216e-01, 7.969e+02],  # Hf
    [2.849e+00, 5.200e-01, 2.283e+02],  # Re
    [2.251e-02, 1.562e+00, 1.528e+00],  # Fe
])

gamma_data = np.array([
    [1.16e+03, 5.43e-07],  # Ti
    [1.75e+02, 6.22e-12],  # V
    [9.89e+04, 5.09e-07],  # Ta
    [2.14e+03, 1.20e+00],  # Nb
    [2.07e+02, 2.45e-02],  # Mo
    [1.33e+03, 2.68e-06],  # Zr
    [6.37e+01, 1.11e-14],  # Cr
    [6.91e+02, 3.07e-02],  # Hf
    [1.81e+02, 4.71e-07],  # Fe
    [1.50e+03, 1.78e-05],  # Re
    [6.67e+02, 4.69e-07],  # W
])

heat_data = np.array([
    [1.045e+01, 1.177e-08],  # Ti
    [9.654e+01, 4.412e-09],  # V
    [1.462e+03, 2.048e-08],  # Ta
    [2.100e+01, 7.884e-03],  # Nb
    [3.651e+01, 8.563e-04],  # Mo
    [3.997e+02, 1.420e-05],  # Zr
    [1.316e+02, 2.027e-09],  # Cr
    [5.286e+03, 7.388e-04],  # Hf
    [1.692e-01, 8.827e-11],  # Fe
    [1.010e+03, 6.244e-05],  # Re
    [3.423e+02, 2.041e-07],  # W
])

# === Normalization thresholds
activation_limit = np.array([2.0, 2.0, 2.0])
gamma_limit = np.array([10000, 0.00001])
heat_limit = np.array([3.423e+02, 0.001])

# === Load composition file
df = pd.read_csv(input_file)

# === Option: Define alloy space manually or auto-detect
# user_defined_elements = ["Ti", "Fe", "W"]  # ← Uncomment to manually select
user_defined_elements = None  # ← Set to None for automatic detection

# === Determine elements to use
if user_defined_elements:
    available_elements = [e for e in user_defined_elements if e in df.columns]
    print("Using user-defined alloy space:", available_elements)
else:
    available_elements = [e for e in master_elements if e in df.columns]
    print("Auto-detected alloy space:", available_elements)

if not available_elements:
    raise ValueError("No recognized element columns found in the input file.")

# === Extract composition for computation, keep original df intact
composition_df = df[available_elements]
compositions = composition_df.to_numpy()
indices = [master_elements.index(e) for e in available_elements]

# === Select rows of each property matrix
activation_used = activation_data[indices]
gamma_used = gamma_data[indices]
heat_used = heat_data[indices]

# === Compute property values
activation = compositions @ activation_used / 100
gamma = compositions @ gamma_used / 100
heat = compositions @ heat_used / 100

# === Normalize
activation_norm = activation / activation_limit
gamma_norm = gamma / gamma_limit
heat_norm = heat / heat_limit

# === Append results to original DataFrame
df["SpecificActivity"] = activation[:, 0]
df["DoseRate"] = activation[:, 1]
df["DecayHeat"] = activation[:, 2]
df["Gamma1"] = gamma[:, 0]
df["Gamma2"] = gamma[:, 1]
df["Heat1"] = heat[:, 0]
df["Heat2"] = heat[:, 1]
df["Normalize_Activation"] = activation_norm.mean(axis=1)
df["Normalize_Gamma"] = gamma_norm.mean(axis=1)
df["Normalize_Heat"] = heat_norm.mean(axis=1)
df["CombinedScore"] = df[["Normalize_Activation", "Normalize_Gamma", "Normalize_Heat"]].mean(axis=1)

# === Save final results
output_file = "nuclear_activation_results.csv"
df.to_csv(output_file, index=False)
print(f"Results saved to {output_file}")
