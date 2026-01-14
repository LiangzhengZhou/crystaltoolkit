import numpy as np
from pymatgen.core import Lattice, Structure

from crystal_render.orientation import Orientation, rotation_from_orientation, miller_normal


def test_miller_normal_cubic():
    structure = Structure(Lattice.cubic(3.0), ["Na"], [[0, 0, 0]])
    normal = miller_normal(structure, (1, 0, 0))
    np.testing.assert_allclose(normal, np.array([1.0, 0.0, 0.0]))


def test_rotation_aligns_normal_to_z():
    structure = Structure(Lattice.cubic(3.0), ["Na"], [[0, 0, 0]])
    orientation = Orientation(miller=(1, 0, 0), in_plane=(0, 1, 0))
    rotation = rotation_from_orientation(structure, orientation)
    normal = miller_normal(structure, orientation.miller)
    rotated = normal @ rotation.T
    np.testing.assert_allclose(rotated, np.array([0.0, 0.0, 1.0]), atol=1e-6)
