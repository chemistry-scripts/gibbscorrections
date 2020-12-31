import os
import numpy as np
from gibbscorrections import gibbscorrection


def test_get_coordinates():
    input_file = os.path.abspath("../data/gaussian_C6H6.log")
    benzene_coordinates = gibbscorrection.get_coordinates(input_file)
    test_coords = np.array(
        [
            [1.632960e-01, -1.390546e00, 0.000000e00],
            [-1.122669e00, -8.366810e-01, 9.000000e-06],
            [-1.285976e00, 5.538630e-01, -8.000000e-06],
            [-1.632720e-01, 1.390549e00, 1.000000e-06],
            [1.122655e00, 8.366990e-01, 8.000000e-06],
            [1.285967e00, -5.538840e-01, -8.000000e-06],
            [2.908730e-01, -2.477613e00, -6.000000e-06],
            [-2.000235e00, -1.490794e00, 8.000000e-06],
            [-2.291185e00, 9.869280e-01, -1.700000e-05],
            [-2.909190e-01, 2.477608e00, -1.000000e-06],
            [2.000262e00, 1.490757e00, 3.000000e-06],
            [2.291202e00, -9.868870e-01, -9.000000e-06],
        ]
    )
    assert np.array_equal(benzene_coordinates, test_coords)


def test_get_input_arguments():
    pass