from unittest import TestCase
import unittest

import numpy as np

from m01_dnn.utils.garden import cross


class GardenTest(TestCase):
    def test_cross(self):
        actual = cross([1, 2], [3, 4])
        expected = np.array([[3, 1], [4, 1], [3, 2], [4, 2]])
        self.assertTrue((expected == actual).all())


if __name__ == '__main__':
    unittest.main()