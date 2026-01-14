import numpy as np
from pymatgen.core import Lattice, Structure

from crystal_render.bonding import bonds_cutoff


def test_bonds_cutoff_simple_cubic():
    structure = Structure(Lattice.cubic(2.5), ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    bonds = bonds_cutoff(structure, cutoff=3.0)

    assert len(bonds) > 0
    assert all(not np.allclose(bond.start, bond.end) for bond in bonds)


def test_bonds_cutoff_no_self_loops():
    structure = Structure(Lattice.cubic(2.8), ["Si", "Si"], [[0, 0, 0], [0.25, 0.25, 0.25]])
    bonds = bonds_cutoff(structure, cutoff=3.0)

    assert len(bonds) > 0
    for bond in bonds:
        assert not np.allclose(bond.start, bond.end)
