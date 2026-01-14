"""Unit cell transformations and expansion."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core import Structure


@dataclass(frozen=True)
class CellSettings:
    mode: str = "input"
    repeat: tuple[int, int, int] = (1, 1, 1)
    show_boundary_images: bool = False
    show_bonded_outside: bool = False
    boundary_tolerance: float = 1e-3


def transform_unit_cell(structure: Structure, mode: str) -> Structure:
    """Return a structure transformed to the requested unit cell mode."""

    mode = mode.lower()
    if mode == "input":
        return structure.copy()
    analyzer = SpacegroupAnalyzer(structure)
    if mode == "conventional":
        return analyzer.get_conventional_standard_structure()
    if mode == "primitive":
        return analyzer.get_primitive_standard_structure()
    raise ValueError(f"Unsupported unit cell mode: {mode}")


def apply_repeat(structure: Structure, repeat: tuple[int, int, int]) -> Structure:
    """Create a repeated supercell."""

    if repeat == (1, 1, 1):
        return structure.copy()
    return structure * repeat


def boundary_images(structure: Structure, tolerance: float) -> Structure:
    """Duplicate atoms near the unit cell boundary for visual continuity."""

    lattice = structure.lattice
    species = []
    coords = []
    for site in structure:
        species.append(site.species)
        coords.append(site.coords)
        frac = site.frac_coords
        shifts = []
        for axis, value in enumerate(frac):
            if value < tolerance:
                shifts.append((axis, -1))
            if value > 1 - tolerance:
                shifts.append((axis, 1))
        if shifts:
            for axis, shift in shifts:
                vec = np.zeros(3)
                vec[axis] = shift
                coords.append(site.coords + lattice.get_cartesian_coords(vec))
                species.append(site.species)
    return Structure(lattice, species, coords, coords_are_cartesian=True, to_unit_cell=False)


def bonded_outside_images(structure: Structure) -> Structure:
    """Show periodic images bonded to atoms within the unit cell."""

    lattice = structure.lattice
    species = [site.species for site in structure]
    coords = [site.coords for site in structure]
    nn = CrystalNN()
    for index in range(len(structure)):
        for neighbor in nn.get_nn_info(structure, index):
            image = np.array(neighbor["image"], dtype=float)
            if np.allclose(image, 0):
                continue
            coords.append(neighbor["site"].coords)
            species.append(neighbor["site"].species)
    return Structure(lattice, species, coords, coords_are_cartesian=True, to_unit_cell=False)


def prepare_structure(structure: Structure, settings: CellSettings) -> Structure:
    """Apply unit cell transformations and expansion settings."""

    updated = transform_unit_cell(structure, settings.mode)
    updated = apply_repeat(updated, settings.repeat)
    if settings.show_bonded_outside and settings.repeat == (1, 1, 1):
        updated = bonded_outside_images(updated)
    if settings.show_boundary_images:
        updated = boundary_images(updated, settings.boundary_tolerance)
    return updated


def ensure_unique_sites(structure: Structure, tolerance: float = 1e-3) -> Structure:
    """Remove duplicate sites introduced by image generation."""

    matcher = StructureMatcher(ltol=tolerance, stol=tolerance, angle_tol=5)
    unique = Structure.from_sites([structure[0]])
    for site in structure[1:]:
        test = Structure(structure.lattice, [site.species], [site.coords], coords_are_cartesian=True)
        if not matcher.fit(unique, test):
            unique.append(site.species, site.coords, coords_are_cartesian=True)
    return unique
