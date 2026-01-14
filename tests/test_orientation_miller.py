import numpy as np
from pymatgen.core import Lattice, Structure

from crystal_render.orientation import Orientation, miller_normal, rotation_from_orientation


def test_miller_normal_normalizes_vector():
    structure = Structure(Lattice.cubic(4.0), ["Na"], [[0, 0, 0]])
    normal = miller_normal(structure, (1, 1, 0))
    expected = np.array([1.0, 1.0, 0.0]) / np.sqrt(2.0)
    np.testing.assert_allclose(normal, expected)


def test_rotation_aligns_miller_to_z_axis():
    structure = Structure(Lattice.cubic(4.0), ["Na"], [[0, 0, 0]])
    orientation = Orientation(miller=(1, 1, 1), in_plane=(1, -1, 0))
    rotation = rotation_from_orientation(structure, orientation)
    normal = miller_normal(structure, orientation.miller)
    rotated = normal @ rotation.T
    np.testing.assert_allclose(rotated, np.array([0.0, 0.0, 1.0]), atol=1e-6)
