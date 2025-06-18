import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap

# === Configuration ===
input_file = "compositionforactivation.csv"  # Input composition file
output_file = "filtered_nuclear_alloys.csv"  # Filtered results only

# === Master element list (must match order in data arrays) ===
master_elements = ["Ti", "V", "Ta", "Nb", "Mo", "Zr", "Cr", "Hf", "Fe", "Re", "W"]

# === Nuclear Property Data ===
# Activation data (T0, 1year, 100years)
activation_data = np.array([
    [7.621e+11, 1.145e+10, 4.598e+03],  # Ti
    [2.038e+13, 1.324e+09, 4.020e+04],  # V
    [4.867e+14, 6.389e+12, 6.116e+04],  # Ta
    [8.733e+12, 8.864e+10, 1.616e+09],  # Nb
    [2.140e+12, 3.954e+09, 2.283e+09],  # Mo
    [1.715e+13, 6.534e+09, 5.456e+06],  # Zr
    [3.073e+12, 1.440e+10, 1.602e+04],  # Cr
    [1.148e+15, 2.837e+10, 5.070e+07],  # Hf
    [9.274e+11, 3.647e+11, 9.718e+04],  # Fe
    [1.174e+14, 1.214e+11, 1.453e+07],  # Re
    [4.119e+13, 2.335e+11, 6.361e+04],  # W
])

# Gamma doses (3.7 days, 100 years)
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

# Heat output (T0, 100 years)
heat_data = np.array([
    [1.112e-01, 1.250e-10],  # Ti
    [8.045e+00, 3.678e-11],  # V
    [1.589e+01, 2.226e-10],  # Ta
    [2.276e-01, 8.548e-05],  # Nb
    [5.326e-06, 7.990e-06],  # Mo
    [5.601e+00, 1.989e-07],  # Zr
    [9.516e-01, 1.466e-11],  # Cr
    [7.085e+01, 9.909e-06],  # Hf
    [1.692e-01, 8.821e-11],  # Fe
    [8.941e+00, 5.531e-07],  # Re
    [3.275e+00, 1.949e-09],  # W
])

# === Limits ===
activation_limit = np.array([8.238e+13, 4.670e+11, 1.272e+05])  # Bq/mol
gamma_limit = np.array([10000, 0.00001])  # Sv/h
heat_limit = np.array([3.423e+02, 0.001])  # W/mol

# === Step 1: Load and Process Compositions ===
df = pd.read_csv(input_file)

# Auto-detect available elements
available_elements = [e for e in master_elements if e in df.columns]
print(f"Detected elements: {available_elements}")

if not available_elements:
    raise ValueError("No recognized element columns found in the input file.")

# Extract compositions
composition_df = df[available_elements].copy()

# Convert to numpy and get indices
compositions = composition_df.to_numpy()
indices = [master_elements.index(e) for e in available_elements]

# Select corresponding property data
activation_used = activation_data[indices]
gamma_used = gamma_data[indices]
heat_used = heat_data[indices]

# === Step 2: Calculate Properties ===
print("Calculating nuclear properties...")
activation = compositions @ activation_used
gamma = compositions @ gamma_used
heat = compositions @ heat_used

# === Step 3: Apply Filtering ===
print("Applying safety filters...")
mask = (
        (activation[:, 0] < activation_limit[0]) &
        (activation[:, 1] < activation_limit[1]) &
        (activation[:, 2] < activation_limit[2]) &
        (gamma[:, 0] < gamma_limit[0]) &
        (gamma[:, 1] < gamma_limit[1]) &
        (heat[:, 0] < heat_limit[0]) &
        (heat[:, 1] < heat_limit[1])
)

# Filter the dataframe
filtered_df = df[mask].copy()
print(f"Filtered {len(filtered_df)} alloys out of {len(df)} total ({len(filtered_df) / len(df) * 100:.1f}%)")

if len(filtered_df) == 0:
    print("No alloys passed the filters!")
    print("Consider relaxing your constraints or checking your input compositions.")
else:
    # === Step 4: Calculate Scores for Filtered Alloys Only ===
    # Get filtered properties
    activation_filtered = activation[mask]
    gamma_filtered = gamma[mask]
    heat_filtered = heat[mask]

    # Normalize
    activation_norm = activation_filtered / activation_limit
    gamma_norm = gamma_filtered / gamma_limit
    heat_norm = heat_filtered / heat_limit

    # Add calculated property values
    filtered_df["Act_T0_Bq/mol"] = activation_filtered[:, 0]
    filtered_df["Act_1yr_Bq/mol"] = activation_filtered[:, 1]
    filtered_df["Act_100yr_Bq/mol"] = activation_filtered[:, 2]
    filtered_df["Gamma_3.7d_Sv/h"] = gamma_filtered[:, 0]
    filtered_df["Gamma_100yr_Sv/h"] = gamma_filtered[:, 1]
    filtered_df["Heat_T0_W/mol"] = heat_filtered[:, 0]
    filtered_df["Heat_100yr_W/mol"] = heat_filtered[:, 1]

    # Add normalized scores
    filtered_df["Normalize_Activation"] = activation_norm.mean(axis=1)
    filtered_df["Normalize_Gamma"] = gamma_norm.mean(axis=1)
    filtered_df["Normalize_Heat"] = heat_norm.mean(axis=1)
    filtered_df["CombinedScore"] = filtered_df[["Normalize_Activation", "Normalize_Gamma", "Normalize_Heat"]].mean(
        axis=1)

    # Sort by CombinedScore (lower is better)
    filtered_df.sort_values("CombinedScore", ascending=True, inplace=True)

    # Prepare columns to save
    calculated_columns = [
        "Act_T0_Bq/mol", "Act_1yr_Bq/mol", "Act_100yr_Bq/mol",
        "Gamma_3.7d_Sv/h", "Gamma_100yr_Sv/h",
        "Heat_T0_W/mol", "Heat_100yr_W/mol",
        "Normalize_Activation", "Normalize_Gamma", "Normalize_Heat", "CombinedScore"
    ]

    # Get all original columns from input file
    original_columns = df.columns.tolist()

    # Combine: original + calculated (avoiding duplicates)
    columns_to_save = original_columns + [col for col in calculated_columns if col not in original_columns]

    # Save filtered results
    filtered_df[columns_to_save].to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")

    # === Step 5: Visualization ===

    # Use available elements for visualization
    composition_cols = available_elements

    # Compositions are already in mole fractions
    comp_for_plot = filtered_df[composition_cols].copy()

    # Normalize so they sum to 1.0 (in case of numerical errors)
    normalized = comp_for_plot.div(comp_for_plot.sum(axis=1), axis=0).dropna()

    # Set up vertices for plot
    num_elements = len(composition_cols)
    angles = np.linspace(0, 2 * np.pi, num_elements, endpoint=False)
    vertices = np.stack([np.cos(angles), np.sin(angles)], axis=1)


    def project(row):
        return np.dot(row.values, vertices)


    coords = normalized.apply(project, axis=1, result_type='expand').values


    # Plot function
    def plot_property(property_name, vmin, vmax, title=None):
        values = filtered_df.loc[normalized.index, property_name].values
        cmap = LinearSegmentedColormap.from_list("custom", ["blue", "yellow", "red"])
        norm = Normalize(vmin=vmin, vmax=vmax)

        fig, ax = plt.subplots(figsize=(10, 10))
        scatter = ax.scatter(coords[:, 0], coords[:, 1], c=values, cmap=cmap, norm=norm,
                             edgecolors='none', s=50, alpha=0.7)

        # Draw polygon
        polygon = np.append(vertices, [vertices[0]], axis=0)
        ax.plot(polygon[:, 0], polygon[:, 1], 'k-', lw=1.5)

        # Add element labels
        for i, el in enumerate(composition_cols):
            x, y = vertices[i]
            ax.text(x * 1.15, y * 1.15, el, ha='center', va='center',
                    fontsize=12, weight='bold')

        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(property_name, fontsize=12)

        # Formatting
        ax.set_aspect('equal')
        ax.axis('off')
        plot_title = title if title else f"{property_name} Distribution"
        ax.set_title(plot_title, fontsize=16, pad=20)

        # Save
        filename = f"{property_name.replace(' ', '_').replace('/', '_')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {filename}")


    # Define properties to plot with appropriate value ranges
    plot_properties = {
        # Raw activation values
        "Act_T0_Bq/mol": (0, activation_limit[0], "Activation at T0 (Bq/mol)"),
        "Act_1yr_Bq/mol": (0, activation_limit[1], "Activation at 1 Year (Bq/mol)"),
        "Act_100yr_Bq/mol": (0, activation_limit[2], "Activation at 100 Years (Bq/mol)"),

        # Raw gamma values
        "Gamma_3.7d_Sv/h": (0, gamma_limit[0], "Gamma at 3.7 Days (Sv/h)"),
        "Gamma_100yr_Sv/h": (0, gamma_limit[1], "Gamma at 100 Years (Sv/h)"),

        # Raw heat values
        "Heat_T0_W/mol": (0, heat_limit[0], "Heat at T0 (W/mol)"),
        "Heat_100yr_W/mol": (0, heat_limit[1], "Heat at 100 Years (W/mol)"),

        # Normalized scores (0-1 scale)
        "Normalize_Activation": (0, 1, "Normalized Activation Score"),
        "Normalize_Gamma": (0, 1, "Normalized Gamma Score"),
        "Normalize_Heat": (0, 1, "Normalized Heat Score"),
        "CombinedScore": (0, 0.5, "Combined Score (Lower is Better)")
    }

    # Generate plots
    for prop, (vmin, vmax, title) in plot_properties.items():
        if prop in filtered_df.columns:
            plot_property(prop, vmin=vmin, vmax=vmax, title=title)
        else:
            print(f"Warning: Column '{prop}' not found in filtered data")

    # Print best alloy composition
    print("\nBest alloy composition:")
    best_alloy = filtered_df.iloc[0]
    for elem in composition_cols:
        if best_alloy[elem] > 0.001:  # Only show elements with >0.1%
            print(f"  {elem}: {best_alloy[elem] * 100:.1f}%")

    print(f"\nAll visualizations complete!")