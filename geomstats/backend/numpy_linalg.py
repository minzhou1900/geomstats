"""Numpy based linear algebra backend."""

import numpy as np


def norm(*args, **kwargs):
    return np.linalg.norm(*args, **kwargs)


def inv(*args, **kwargs):
    return np.linalg.inv(*args, **kwargs)


def matrix_rank(*args, **kwargs):
    return np.linalg.matrix_rank(*args, **kwargs)


def eigvalsh(*args, **kwargs):
    return np.linalg.eigvalsh(*args, **kwargs)
