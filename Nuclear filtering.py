import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap

# === Load input file ===
df = pd.read_csv("nuclear_activation_results.csv")

# === Define thresholds ===
activation_limit = np.array([2.0, 2.0, 2.0])
gamma_limit = np.array([10000, 0.00001])
heat_limit = np.array([3.423e+02, 0.001])

# === Apply filtering ===
mask = (
    (df["SpecificActivity"] < activation_limit[0]) &
    (df["DoseRate"] < activation_limit[1]) &
    (df["DecayHeat"] < activation_limit[2]) &
    (df["Gamma1"] < gamma_limit[0]) &
    (df["Gamma2"] < gamma_limit[1]) &
    (df["Heat1"] < heat_limit[0]) &
    (df["Heat2"] < heat_limit[1])
)
filtered_df = df[mask].copy()

# === Sort by CombinedScore (descending) ===
filtered_df.sort_values("CombinedScore", ascending=False, inplace=True)
filtered_df.to_csv("filtered_nuclear_alloys.csv", index=False)
print("Filtered CSV saved as 'filtered_nuclear_alloys.csv'")

# === Set alloy space and vertices ===
composition_cols = ['Ti', 'Ta', 'V', 'Mo', 'Fe', 'Re', 'Nb', 'Zr', 'Cr', 'Hf', 'W']
normalized = filtered_df[composition_cols].div(filtered_df[composition_cols].sum(axis=1), axis=0).dropna()
num_elements = len(composition_cols)
angles = np.linspace(0, 2 * np.pi, num_elements, endpoint=False)
vertices = np.stack([np.cos(angles), np.sin(angles)], axis=1)

def project(row):
    return np.dot(row.values, vertices)

coords = normalized.apply(project, axis=1, result_type='expand').values

# === Plot function ===
def plot_property(property_name, vmin, vmax):
    values = filtered_df.loc[normalized.index, property_name].values
    cmap = LinearSegmentedColormap.from_list("custom", ["blue", "yellow", "red"])
    norm = Normalize(vmin=vmin, vmax=vmax)

    fig, ax = plt.subplots(figsize=(10, 10))
    scatter = ax.scatter(coords[:, 0], coords[:, 1], c=values, cmap=cmap, norm=norm,
                         edgecolors='none', s=50)

    polygon = np.append(vertices, [vertices[0]], axis=0)
    ax.plot(polygon[:, 0], polygon[:, 1], 'k-', lw=1.5)

    for i, el in enumerate(composition_cols):
        x, y = vertices[i]
        ax.text(x * 1.1, y * 1.1, el, ha='center', va='center', fontsize=11, weight='bold')

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label(property_name, fontsize=12)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"{property_name}", fontsize=14)
    filename = f"{property_name}_affine_filtered_projection.png"
    plt.savefig(filename, dpi=600, bbox_inches='tight')
    plt.show()
    plt.close()
    print(f"Saved: {filename}")

# === Generate all four plots ===
plot_property("CombinedScore", vmin=0, vmax=filtered_df["CombinedScore"].max())
#plot_property("CombinedScore", vmin=0, vmax=1)
plot_property("Normalize_Activation", vmin=0, vmax=1)
plot_property("Normalize_Gamma", vmin=0, vmax=1)
plot_property("Normalize_Heat", vmin=0, vmax=1)
