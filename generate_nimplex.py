import argparse
import nimplex
import pandas as pd


def generate_nimplex_space(
    elements: list,
    dimension: int,
    num_division: int,
    limit: list,
    no_csv=False,
    plot=False,
) -> pd.DataFrame:
    """
    Generate nimplex component space and neighbor list.

    Parameters:
        elements (list): List of element symbols.
        dimension (int): Dimension of the simplex.
        num_division (int): Number of divisions for the simplex.
        limit (list): Limits for each component as min max pairs. The list should contain 2 values (min and max) for each dimension,
                      e.g., for a 3-dimensional simplex, the limit should be [[min1, max1], [min2, max2], [min3, max3]].
        no_csv (bool): Whether to write the output to a CSV file. If True, the output will not be saved to a CSV file.
        plot (bool): Whether to plot the nimplex space.

    Returns:
        pd.DataFrame: DataFrame containing the component space and neighbor list.
    """
    if len(elements) != dimension:
        raise ValueError(f"Number of elements ({len(elements)}) must match the dimension ({dimension}).")

    if len(limit) != dimension or any(len(l) != 2 for l in limit):
        raise ValueError(f"Limit must have 2 values (min and max) for each component, got {len(limit)} limits.")

    if not all(isinstance(el, str) for el in elements):
        raise ValueError("All elements must be strings representing element symbols.")

    if num_division <= 0:
        raise ValueError("Number of divisions must be a positive integer.")

    if any(l[0] > l[1] for l in limit):
        raise ValueError("Each limit's minimum must be less than or equal to its maximum.")

    component_space, neighbor_list = nimplex.simplex_graph_limited_fractional_py(
        dim=dimension, ndiv=num_division, limit=limit
    )

    dataframe = pd.DataFrame(component_space, columns=elements)
    neighbors_df = pd.DataFrame(neighbor_list)
    neighbors_df.columns = [f"Neighbor_{i}" for i in range(neighbors_df.shape[1])]
    dataframe = pd.concat([neighbors_df, dataframe], axis=1)
    dataframe.reset_index(names="Node ID", inplace=True)

    if not no_csv:
        dataframe.to_csv(f"{''.join(elements)}_nimplex_space.csv", index=False)

    if plot:
        if dimension > 4:
            raise ValueError("Plotting is only supported for 1, 2, 3, and 4-component simplexes.")

        from utils import plotting
        import plotly.express as px

        pure_component_indices = nimplex.pure_component_indexes_py(dim, num_division)
        cartesian_grid = pd.DataFrame(plotting.simplex2cartesian_py(component_space), columns=['x', 'y', 'z'])

        labels = ['']*len(cartesian_grid)
        for comp, idx in zip(elements, pure_component_indices):
            labels[idx] = "<b>"+comp+"</b>"

        formulas = [
            f"({i:>3}) " + "".join(f"{el}{100*v:.1f} " for el, v in zip(elements, comp) if v > 0)
            for i, comp in enumerate(component_space)
        ]

        fig = px.scatter_3d(
                cartesian_grid,
                x="x",
                y="y",
                z="z",
                text=labels,
                hover_name=formulas,
                template="simple_white",
                width=800,
                height=700,
                hover_data={"x": False, "y": False, "z": False},
        )

        fig.write_html(f"{''.join(elements)}_plot.html")

    return dataframe


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate nimplex component space and neighbor list."
    )
    parser.add_argument(
        "elements",
        nargs="+",
        help="List of element symbols",
    )
    parser.add_argument(
        "--ndiv",
        type=int,
        default=10,
        help="Number of divisions for the simplex (default: %(default)s)",
    )
    parser.add_argument(
        "--limit",
        type=float,
        nargs="+",
        help="Limits for each component as min max pairs in the order [min1 max1 min2 max2 ...], e.g. --limit 0 1 0 1 0 1 0 1 for 4 dimensions",
    )
    parser.add_argument(
        "--no_csv",
        action="store_true",
        help="Whether to write the output to a CSV file (default: %(default)s)",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Whether to plot the nimplex space (supported for dimensions up to 4)."
    )
    args = parser.parse_args()

    element_list = args.elements
    dim = len(element_list)

    if args.limit is not None:
        if len(args.limit) != 2 * dim:
            raise ValueError("Limit must have 2 values per component (min and max).")
        lim = [args.limit[i * 2:(i + 1) * 2] for i in range(dim)]
    else:
        lim = [[0, 1] for _ in range(dim)]

    generate_nimplex_space(element_list, dim, args.ndiv, lim, args.no_csv, args.plot)
