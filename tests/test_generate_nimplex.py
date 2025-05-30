import os
import unittest
import pandas as pd

from generate_nimplex import generate_nimplex_space


class TestGenerateNimplexSpace(unittest.TestCase):
    def test_generates_correct_dataframe_structure(self):
        elements = ["Co", "Cr", "Fe"]
        dimension = 3
        num_division = 5
        limit = [[0, 1], [0, 1], [0, 1]]
        result = generate_nimplex_space(elements, dimension, num_division, limit, no_csv=True)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("Node ID", result.columns)
        self.assertIn("Neighbor_0", result.columns)
        self.assertIn("Co", result.columns)
        self.assertIn("Cr", result.columns)
        self.assertIn("Fe", result.columns)

    def test_handles_invalid_limits(self):
        elements = ["Co", "Cr", "Fe"]
        dimension = 3
        num_division = 5
        limit = [[0, 1], [0, 1]]
        with self.assertRaises(ValueError):
            generate_nimplex_space(elements, dimension, num_division, limit, no_csv=True)

    def test_handles_plotting_with_high_dimensions(self):
        elements = ["Co", "Cr", "Fe", "Ni", "Mn"]
        dimension = 5
        num_division = 5
        limit = [[0, 1]] * dimension
        with self.assertRaises(ValueError):
            generate_nimplex_space(elements, dimension, num_division, limit, no_csv=True, plot=True)

    def test_generates_correct_csv_file(self):
        elements = ["Co", "Cr", "Fe"]
        dimension = 3
        num_division = 5
        limit = [[0, 1], [0, 1], [0, 1]]
        generate_nimplex_space(elements, dimension, num_division, limit, no_csv=False)
        expected_filename = "CoCrFe_nimplex_space.csv"
        self.assertTrue(os.path.exists(expected_filename))
        os.remove(expected_filename)

    def test_raises_error_for_mismatched_element_and_dimension(self):
        elements = ["Co", "Cr", "Fe"]
        dimension = 4
        num_division = 5
        limit = [[0, 1], [0, 1], [0, 1], [0, 1]]
        with self.assertRaises(ValueError):
            generate_nimplex_space(elements, dimension, num_division, limit, no_csv=True)

    def test_generates_dataframe_with_correct_node_ids(self):
        elements = ["Co", "Cr", "Fe"]
        dimension = 3
        num_division = 5
        limit = [[0, 1], [0, 1], [0, 1]]
        result = generate_nimplex_space(elements, dimension, num_division, limit, no_csv=True)
        self.assertTrue(all(result["Node ID"] == range(len(result))))

    def test_raises_error_for_negative_num_division(self):
        elements = ["Co", "Cr", "Fe"]
        dimension = 3
        num_division = -1
        limit = [[0, 1], [0, 1], [0, 1]]
        with self.assertRaises(ValueError):
            generate_nimplex_space(elements, dimension, num_division, limit, no_csv=True)

    def test_raises_error_for_limit_with_min_greater_than_max(self):
        elements = ["Co", "Cr", "Fe"]
        dimension = 3
        num_division = 5
        limit = [[1, 0], [0, 1], [0, 1]]
        with self.assertRaises(ValueError):
            generate_nimplex_space(elements, dimension, num_division, limit, no_csv=True)

    def test_generates_empty_dataframe_for_zero_divisions(self):
        elements = ["Co", "Cr", "Fe"]
        dimension = 3
        num_division = 0
        limit = [[0, 1], [0, 1], [0, 1]]
        with self.assertRaises(ValueError):
            generate_nimplex_space(elements, dimension, num_division, limit, no_csv=True)



if __name__ == '__main__':
    unittest.main()
