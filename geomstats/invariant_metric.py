"""
Base class for special Riemannian metrics that
can be built on Lie groups:
- left-invariant metrics
- right-invariant metrics.

Note: Assume that the points are parameterized by
their Riemannian logarithm for the canonical left-invariant metric.
"""

import logging
import scipy.linalg

from geomstats.riemannian_metric import RiemannianMetric
import geomstats.backend as gs


class InvariantMetric(RiemannianMetric):
    """
    Base class for left- or right- invariant metrics
    that can be defined on Lie groups.
    """

    def __init__(self, group,
                 inner_product_mat_at_identity=None,
                 left_or_right='left'):
        if inner_product_mat_at_identity.ndim == 3:
            n_mats, _, _ = inner_product_mat_at_identity.shape
            assert n_mats == 1
            inner_product_mat_at_identity = gs.squeeze(
                               inner_product_mat_at_identity, axis=0)

        matrix_shape = inner_product_mat_at_identity.shape
        assert matrix_shape == (group.dimension,) * 2
        assert left_or_right in ('left', 'right')

        eigenvalues = gs.linalg.eigvalsh(inner_product_mat_at_identity)
        n_pos_eigval = gs.sum(eigenvalues > 0)
        n_neg_eigval = gs.sum(eigenvalues < 0)
        n_null_eigval = gs.sum(eigenvalues == 0)
        assert (n_pos_eigval + n_neg_eigval
                + n_null_eigval) == group.dimension

        self.group = group
        if inner_product_mat_at_identity is None:
            inner_product_mat_at_identity = gs.eye(self.group.dimension)

        self.inner_product_mat_at_identity = inner_product_mat_at_identity
        self.left_or_right = left_or_right
        self.signature = (n_pos_eigval, n_null_eigval, n_neg_eigval)

    def inner_product_at_identity(self, tangent_vec_a, tangent_vec_b):
        """
        Inner product between two tangent vectors at the identity of the
        Lie group.
        Note: tangent vectors are given in vector representation.
        """
        assert self.group.point_representation in ('vector', 'matrix')

        if self.group.point_representation == 'vector':
            tangent_vec_a = gs.to_ndarray(tangent_vec_a, to_ndim=2)
            tangent_vec_b = gs.to_ndarray(tangent_vec_b, to_ndim=2)

            aux_vec_a = gs.matmul(tangent_vec_a,
                                  self.inner_product_mat_at_identity)
            inner_prod = gs.einsum('ij,ij->i', aux_vec_a, tangent_vec_b)
            inner_prod = gs.to_ndarray(inner_prod,
                                                  to_ndim=2, axis=1)

        elif self.group.point_representation == 'matrix':
            logging.warning(
                'Only the canonical inner product -Frobenius inner product-'
                ' is implemented for Lie groups whose elements are represented'
                ' by matrices.')
            tangent_vec_a = gs.to_ndarray(tangent_vec_a, to_ndim=3)
            tangent_vec_b = gs.to_ndarray(tangent_vec_b, to_ndim=3)
            aux_prod = gs.matmul(gs.transpose(tangent_vec_a, axes=(0, 2, 1)),
                                 tangent_vec_b)
            inner_prod = gs.trace(aux_prod)

        return inner_prod

    def inner_product(self, tangent_vec_a, tangent_vec_b, base_point=None):
        if base_point is None:
            return self.inner_product_at_identity(tangent_vec_a,
                                                  tangent_vec_b)
        if self.group.point_representation == 'vector':
                return super(InvariantMetric, self).inner_product(
                                     tangent_vec_a,
                                     tangent_vec_b,
                                     base_point)

        if self.left_or_right == 'right':
            raise NotImplementedError(
                'inner_product not implemented for right invariant metrics.')
        jacobian = self.group.jacobian_translation(base_point)
        inv_jacobian = gs.linalg.inv(jacobian)
        tangent_vec_a_at_id = gs.matmul(inv_jacobian, tangent_vec_a)
        tangent_vec_b_at_id = gs.matmul(inv_jacobian, tangent_vec_b)
        inner_prod = self.inner_product_at_identity(tangent_vec_a_at_id,
                                                    tangent_vec_b_at_id)
        return inner_prod

    def inner_product_matrix(self, base_point=None):
        """
        Compute the matrix of the Riemmanian metric at point base_point,
        by translating inner_product from the identity to base_point.
        """
        if self.group.point_representation == 'matrix':
            raise NotImplementedError(
                'inner_product_matrix not implemented for Lie groups'
                ' whose elements are represented as matrices.')

        if base_point is None:
            base_point = self.group.identity
        base_point = self.group.regularize(base_point)

        jacobian = self.group.jacobian_translation(
                              point=base_point,
                              left_or_right=self.left_or_right)
        assert jacobian.ndim == 3
        inv_jacobian = gs.linalg.inv(jacobian)
        inv_jacobian_transposed = gs.transpose(inv_jacobian, axes=(0, 2, 1))

        inner_product_mat_at_id = self.inner_product_mat_at_identity
        inner_product_mat_at_id = gs.to_ndarray(
                             inner_product_mat_at_id, to_ndim=2)

        metric_mat = gs.matmul(inv_jacobian_transposed,
                               inner_product_mat_at_id)
        metric_mat = gs.matmul(metric_mat, inv_jacobian)
        return metric_mat

    def left_exp_from_identity(self, tangent_vec):
        """
        Compute the *left* Riemannian exponential from the identity of the
        Lie group of tangent vector tangent_vec.

        The left Riemannian exponential has a special role since the
        left Riemannian exponential of the canonical metric parameterizes
        the points.

        Note: In the case where the method is called by a right-invariant
        metric, it used the left-invariant metric associated to the same
        inner-product at the identity.
        """
        tangent_vec = gs.to_ndarray(tangent_vec, to_ndim=2)

        tangent_vec = self.group.regularize_tangent_vec_at_identity(
                                        tangent_vec=tangent_vec,
                                        metric=self)
        sqrt_inner_product_mat = scipy.linalg.sqrtm(
                                            self.inner_product_mat_at_identity)
        mat = sqrt_inner_product_mat.transpose()
        exp = gs.matmul(tangent_vec, mat)

        exp = self.group.regularize(exp)
        return exp

    def exp_from_identity(self, tangent_vec):
        """
        Compute the Riemannian exponential from the identity of the
        Lie group of tangent vector tangent_vec.
        """
        tangent_vec = gs.to_ndarray(tangent_vec, to_ndim=2)

        if self.left_or_right == 'left':
            exp = self.left_exp_from_identity(tangent_vec)

        else:
            opp_left_exp = self.left_exp_from_identity(-tangent_vec)
            exp = self.group.inverse(opp_left_exp)

        exp = self.group.regularize(exp)
        return exp

    def exp_basis(self, tangent_vec, base_point=None):
        """
        Compute the Riemannian exponential at point base_point
        of tangent vector tangent_vec.
        """
        if base_point is None:
            base_point = self.group.identity
        base_point = self.group.regularize(base_point)
        if base_point is self.group.identity:
            return self.exp_from_identity(tangent_vec)

        tangent_vec = gs.to_ndarray(tangent_vec, to_ndim=2)

        n_tangent_vecs, _ = tangent_vec.shape
        n_base_points, _ = base_point.shape

        assert n_tangent_vecs == 1 and n_base_points == 1

        jacobian = self.group.jacobian_translation(
                                 point=base_point,
                                 left_or_right=self.left_or_right)
        assert jacobian.ndim == 3
        inv_jacobian = gs.linalg.inv(jacobian)
        inv_jacobian_transposed = gs.transpose(inv_jacobian, axes=(0, 2, 1))

        tangent_vec_at_id = gs.matmul(tangent_vec, inv_jacobian_transposed)
        tangent_vec_at_id = gs.squeeze(tangent_vec_at_id, axis=0)
        exp_from_id = self.exp_from_identity(tangent_vec_at_id)

        if self.left_or_right == 'left':
            exp = self.group.compose(base_point, exp_from_id)

        else:
            exp = self.group.compose(exp_from_id, base_point)

        exp = self.group.regularize(exp)

        return exp

    def left_log_from_identity(self, point):
        """
        Compute the *left* Riemannian logarithm from the identity of the
        Lie group of tangent vector tangent_vec.

        The left Riemannian logarithm has a special role since the
        left Riemannian logarithm of the canonical metric parameterizes
        the points.
        """
        point = self.group.regularize(point)
        inner_prod_mat = self.inner_product_mat_at_identity
        sqrt_inv_inner_prod_mat = scipy.linalg.sqrtm(gs.linalg.inv(
                                                     inner_prod_mat))
        assert sqrt_inv_inner_prod_mat.shape == (self.group.dimension,) * 2

        log = gs.matmul(point, sqrt_inv_inner_prod_mat.transpose())
        log = self.group.regularize_tangent_vec_at_identity(
                                             tangent_vec=log,
                                             metric=self)
        assert log.ndim == 2
        return log

    def log_from_identity(self, point):
        """
        Compute the Riemannian logarithm of point at point base_point
        of point for the invariant metric from the identity.
        """
        point = self.group.regularize(point)
        if self.left_or_right == 'left':
            log = self.left_log_from_identity(point)

        else:
            inv_point = self.group.inverse(point)
            left_log = self.left_log_from_identity(inv_point)
            log = - left_log

        assert log.ndim == 2
        return log

    def log_basis(self, point, base_point=None):
        """
        Compute the Riemannian logarithm of point at point base_point
        of point for the invariant metric.
        """
        if base_point is None:
            base_point = self.group.identity
        base_point = self.group.regularize(base_point)
        if base_point is self.group.identity:
            return self.log_from_identity(point)

        point = self.group.regularize(point)

        n_points, _ = point.shape
        n_base_points, _ = base_point.shape
        assert n_points == 1 and n_base_points == 1

        if self.left_or_right == 'left':
            point_near_id = self.group.compose(
                                   self.group.inverse(base_point),
                                   point)

        else:
            point_near_id = self.group.compose(
                                   point,
                                   self.group.inverse(base_point))

        log_from_id = self.log_from_identity(point_near_id)

        jacobian = self.group.jacobian_translation(
                                       base_point,
                                       left_or_right=self.left_or_right)

        log = gs.matmul(log_from_id, gs.transpose(jacobian, axes=(0, 2, 1)))
        log = gs.squeeze(log, axis=0)
        assert log.ndim == 2
        return log
