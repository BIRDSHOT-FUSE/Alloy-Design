# -*- coding: utf-8 -*-

"""
import nimplex
# from utils import plotting
import pandas as pd
import numpy as np
import networkx as nx
# import plotly.express as px
# import plotly.graph_objects as go
# import plotly.io as pio
# from plotly.offline import plot
# import matplotlib.pyplot as plt
# import imageio
# from PIL import Image
# import io

# pio.templates.default = "simple_white"

# Function to check if all 'Node ID' values are unique
def check_unique_ids(dataframe):
    if dataframe['Node ID'].is_unique:
        print("All 'Node ID' values are unique.")
    else:
        print("Duplicate 'Node ID' values found.")
# Find and print simplex corners
def find_simplex_corners(df, cols):
    # Filter the rows where any of the values in the specified range of columns is 1
    corner_rows = df[(df.loc[:, cols] == 1).any(axis=1)]
    simplex_corners = corner_rows[elementalSpaceComponents+node_columns]
    # Print out the filtered rows
    print('Corners of the simplex are:\n', simplex_corners)

# Plot compositions from simplex
# def plot_simplex(df):
#     for element in elementalSpaceComponents:
#         # Hover approximate formula for each point
#         formulas = []
#         for i, comp in enumerate(comp_data):
#             formulas.append(f"({i:>3}) "+"".join([f"{el}{100*v:.1f} " if v>0 else "" for el, v in zip(elementalSpaceComponents, comp)]))
# 
#         # Generate the projected grid
#         gridAtt_projected_df = pd.DataFrame(plotting.simplex2cartesian_py(node_data), columns=['x','y','z'])
# 
#         # Attach pure component (alloy) labels to corners
#         pureComponentIndices = nimplex.pure_component_indexes_py(4, 20)
#         labels = ['']*len(gridAtt_projected_df)
#         for comp, idx in zip(attainableSpaceComponents, pureComponentIndices):
#             labels[idx] = "<b>"+comp+"</b>"
# 
#         # Add text labels at the corners of the simplex
#         fig = px.scatter_3d(gridAtt_projected_df, x='x', y='y', z='z', color=df[element], text=labels, hover_name=formulas,
#                     template='plotly_white', width=800, height=700, 
#                     labels={'color':element, 'x':'', 'y':'', 'z':''})
#         fig.write_html('Scatter_{}.html'.format(element))
#         # fig.show()
# 
# def plot_animation(df):
#     for element in elementalSpaceComponents:
#         # Hover approximate formula for each point
#         formulas = []
#         for i, comp in enumerate(comp_data):
#             formulas.append(f"({i:>3}) "+"".join([f"{el}{100*v:.1f} " if v>0 else "" for el, v in zip(elementalSpaceComponents, comp)]))
# 
#         # Generate the projected grid
#         gridAtt_projected_df = pd.DataFrame(plotting.simplex2cartesian_py(node_data), columns=['x','y','z'])
# 
#         # Attach pure component (alloy) labels to corners
#         pureComponentIndices = nimplex.pure_component_indexes_py(4, 20)
#         labels = ['']*len(gridAtt_projected_df)
#         for comp, idx in zip(attainableSpaceComponents, pureComponentIndices):
#             labels[idx] = "<b>"+comp+"</b>"
#         
#         x = gridAtt_projected_df['x']
#         y = gridAtt_projected_df['y']
#         z = gridAtt_projected_df['z']
# 
#         fig = go.Figure(
#         data=[go.Scatter3d(x=x, y=y, z=z, mode='markers+text', text=labels,
#             marker=dict(
#                 size=8,
#                 color=df[element],
#                 colorbar=dict(title=element)
#                 ))
#                 ],
#         layout=go.Layout(
#             scene=dict(
#                 xaxis=dict(range=[-1, 1]),
#                 yaxis=dict(range=[-1, 1]),
#                 zaxis=dict(range=[-1, 1])
#             ),
#             font=dict(
#                 size=18
#             )
#             # updatemenus=[
#             #     dict(
#             #         type="buttons",
#             #         buttons=[dict(label="Play", method="animate", args=[None])],
#             #     )
#             # ]
#         ),
#         frames=[
#             go.Frame(
#                 layout=go.Layout(
#                     scene=dict(
#                         camera=dict(eye=dict(x=np.cos(i), y=np.sin(i), z=1))
#                     )
#                 )
#             )
#             for i in np.linspace(0, 2*np.pi, 36)
#         ]
#     )
#         plot(fig, filename='rotating_scatter_{}.html'.format(element), auto_open=False)
#         images = []
#         for i in range(0, 360, 10):
#             fig.layout.scene.camera.eye = dict(x=np.cos(np.radians(i)), y=np.sin(np.radians(i)), z=1)
#             image = Image.open(io.BytesIO(fig.to_image(format="png", width=1080, height=1080)))
#             image = np.asarray(image)
#             # image = image.astype(np.uint8)
#             # print(image)
#             for j in range(0,5):
#                 images.append(image)
#                 # images.append(fig.to_image(format="png"))
# 
#         imageio.mimsave('rotating_scatter_{}.gif'.format(element), images, duration=0.05)

elementalSpaceComponents = ["Ti", "V", "Ta", "Nb", "Mo", "Zr", "Cr", "Hf", "Fe", "Re", "W"] # The elements that are contained in the simplex
attainableSpaceComponents = ["Ti", "V", "Ta", "Nb", "Mo", "Zr", "Cr", "Hf", "Fe", "Re", "W"] # The vertices of the simplex
# Elemental compositions of each vertex in mole percent
attainableSpaceComponentPositions = [[100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 100, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 100, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0], [0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 100]]

node_data, comp_data, neighbors_data = nimplex.embeddedpair_simplex_graph_fractional_py(attainableSpaceComponentPositions, 50)

#Create Dataframe starting with the elemental compositions
df = pd.DataFrame(data=comp_data, columns=elementalSpaceComponents)
# Display the first few rows of the DataFrame
print(df.head())

#Convert the numpy array for node (simplex) coordinates to a DataFrame for better readability
nodes_df = pd.DataFrame(node_data)
# Add node column names
node_columns = []
for i in range(len(nodes_df.columns)):
    node_columns.append('NodeCoord_{}'.format(i))
nodes_df.columns = node_columns

# Show first 10 rows of nodes data
print("First 10 rows of the nodes array:")
print(nodes_df.head(10))

# Print the number of nodes
num_rows = len(node_data)
print(f'Number of nodes: {num_rows}')

# Convert the numpy array of neighbors for each node to a DataFrame for better readability
neighbors_df = pd.DataFrame(neighbors_data)
# Add node column names
neighbor_columns = []
for i in range(len(neighbors_df.columns)):
    neighbor_columns.append('Neighbor_{}'.format(i))
neighbors_df.columns = neighbor_columns

# Check the first 10 rows of the original data
print("First 10 rows of the neighbors array:")
print(neighbors_df.head(10))

# Create NetworkX Graph of Alloy Nodes & JOINS_TO Edges
# Initialize an empty graph
G = nx.Graph()

# Add edges to the graph efficiently
edges = [
    (node, neighbor)
    for node, neighbors in enumerate(neighbors_data)
    for neighbor in neighbors if neighbor != -1
]
G.add_edges_from(edges)

# Print out the edges to verify working correctly
# print("Edges in the graph:", list(G.edges))

# Create a new column 'Node ID' in the dataframe and assign node IDs based on node_data
df['Node ID'] = [None] * len(df)
for node_id in range(len(nodes_df)):
    df.at[node_id, 'Node ID'] = node_id

# Add node coordinate and neighbor columns to df
df = pd.concat((neighbors_df,df), axis=1)
df = pd.concat((nodes_df,df), axis=1)

# Move node_id column first
df = df[[list(df.columns)[-1]]+list(df.columns)[:-1]]

# Display the dataframe to verify the 'Node ID' assignment
print(df.head())

# Check if all IDs are unique
check_unique_ids(df)

# Find and print the corners of the simplex to check that they match
find_simplex_corners(df, node_columns)

# Plot composition on simplex
# plot_simplex(df)
# plot_animation(df)

df.to_csv('CHD1_IT0_1_Nuclear.csv')
