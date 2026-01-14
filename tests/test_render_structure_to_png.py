import pytest
from pymatgen.core import Lattice, Structure

from crystal_render.bonding import BondingOptions
from crystal_render.cell import CellSettings
from crystal_render.render import render_structure


pytest.importorskip("pyvista")


def test_render_structure_to_png(tmp_path):
    structure = Structure(Lattice.cubic(3.5), ["Si"], [[0, 0, 0]])
    cif_path = tmp_path / "structure.cif"
    structure.to(filename=str(cif_path))

    output_path = tmp_path / "render.png"
    render_structure(
        str(cif_path),
        str(output_path),
        CellSettings(),
        BondingOptions(method="cutoff", cutoff=3.0),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0
