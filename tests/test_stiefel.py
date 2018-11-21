"""
Unit tests for Stiefel manifolds.
"""

import unittest
import warnings

import geomstats.backend as gs

from geomstats.stiefel import Stiefel


class TestStiefelMethods(unittest.TestCase):
    _multiprocess_can_split_ = True

    def setUp(self):
        warnings.simplefilter('ignore', category=ImportWarning)

        gs.random.seed(1234)

        self.p = 3
        self.n = 4
        self.space = Stiefel(self.n, self.p)
        self.n_samples = 10
        self.dimension = int(
            self.p * self.n - (self.p * (self.p + 1) / 2))

    def test_belongs(self):
        point = self.space.random_uniform()
        belongs = self.space.belongs(point)

        gs.testing.assert_allclose(belongs.shape, (1, 1))

    def test_random_and_belongs(self):
        point = self.space.random_uniform()
        result = self.space.belongs(point)
        expected = gs.array([[True]])

        gs.testing.assert_allclose(result, expected)

    def test_random_uniform(self):
        point = self.space.random_uniform()

        gs.testing.assert_allclose(point.shape, (1, self.n, self.p))

    def test_inner_product(self):
        point_a = gs.array([
            [1., 0., 0.],
            [0., 1., 0.],
            [0., 0., 1.],
            [0., 0., 0.]])

        point_b = gs.array([
            [1., 0., 0.],
            [0., 1., 0.],
            [0., 0., 1.],
            [1., 0., 0.]])

        result = self.metric.inner_product(point_a, point_b)



if __name__ == '__main__':
        unittest.main()
