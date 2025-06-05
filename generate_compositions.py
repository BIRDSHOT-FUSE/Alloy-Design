import numpy as np
import pandas as pd
import time
from itertools import combinations, compress

# Start timer
tic = time.time()

##### USER INPUTS ###########################
elements = ['Ti', 'Ta', 'V', 'Mo', 'Fe', 'Re', 'Nb', 'Zr', 'Cr', 'Hf', 'W']
only_extra = False  # currently unused
savename = 'Quinary_Compositions'
n_comps = 20        # e.g. 100/20 = 5 at.% resolution
sys_d = 5           # fixed at 5 for quinary
#############################################

# Generate list of all 5-element combinations from the element list
sys_list = [list(sys) for sys in combinations(elements, sys_d)]

# Generate compositions for a 5-element system where the sum of parts = n_comps
comps = []
indices = np.ndindex(*[n_comps for _ in range(sys_d)])
j = 0
for index in indices:
    j += 1
    if sum(index) == n_comps:
        comps.append(np.array(index) / n_comps)
    if j % 100000 == 0:
        toc = time.time()
        print(f"{round(j / (n_comps**sys_d) * 100, 2)}% Checked | {len(comps)} Valid Comps | {round(toc - tic, 2)}s")

# Build full DataFrame of all sampled quinary compositions
results_df = pd.DataFrame(columns=elements)
for i, s_els in enumerate(sys_list):
    new_df = pd.DataFrame(comps, columns=s_els).fillna(0)
    results_df = pd.concat([results_df, new_df], ignore_index=True)
    toc = time.time()
    print(f"{round(i / len(sys_list) * 100, 2)}% Systems Added | {round(toc - tic, 2)}s")

# Remove duplicates and reset index
results_df = results_df.fillna(0).drop_duplicates().reset_index(drop=True)

# Optional filtering (uncomment to apply)
# results_df = results_df.loc[results_df['W'] <= 0.15]
# results_df = results_df.loc[results_df['Mo'] <= 0.15]
# results_df = results_df.loc[results_df['V'] <= 0.30]
# results_df = results_df.loc[results_df['Ta'] + results_df['Nb'] >= 0.5]
# results_df = results_df.loc[results_df['Ti'] >= 0.05]

# Save to CSV
results_df.to_csv("compositionforactivation.csv", index=False)
print(f"✅ Total valid compositions: {len(results_df)}")
print(f"📁 File saved as: {savename}.csv")
