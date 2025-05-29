import argparse
import nimplex
import pandas as pd


def generate_nimplex_space(
    elements: list, dimension: int, num_division: int, limit: list, write_to_csv=True
):
    """
    Generate nimplex component space and neighbor list.

    Parameters:
        elements (list): List of element symbols.
        dimension (int): Dimension of the simplex.
        num_division (int): Number of divisions for the simplex.
        limit (list): Limits for each component as min max pairs. The list should contain 2 values (min and max) for each dimension,
                      e.g., for a 3-dimensional simplex, limit should be [[min1, max1], [min2, max2], [min3, max3]].
        write_to_csv (bool): Whether to write the output to a CSV file. Default is True.

    Returns:
        pd.DataFrame: DataFrame containing the component space and neighbor list.
    """
    component_space, neighbor_list = nimplex.simplex_graph_limited_fractional_py(
        dim=dimension, ndiv=num_division, limit=limit
    )

    dataframe = pd.DataFrame(component_space, columns=elements)
    neighbors_df = pd.DataFrame(neighbor_list)
    neighbors_df.columns = [f"Neighbor_{i}" for i in range(neighbors_df.shape[1])]
    dataframe = pd.concat([neighbors_df, dataframe], axis=1)
    dataframe.reset_index(names="Node ID", inplace=True)
    if write_to_csv:
        dataframe.to_csv(f"{''.join(elements)}_nimplex_space.csv", index=False)

    return dataframe


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate nimplex component space and neighbor list."
    )
    parser.add_argument(
        "--elements",
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
        "--write_to_csv",
        action="store_true",
        default=True,
        help="Whether to write the output to a CSV file (default: %(default)s)",
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

    df = generate_nimplex_space(element_list, dim, args.ndiv, lim, args.write_to_csv)
