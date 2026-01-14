"""Bond generation utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.core import Structure


@dataclass(frozen=True)
class Bond:
    start: np.ndarray
    end: np.ndarray
    elements: tuple[str, str]


@dataclass(frozen=True)
class BondingOptions:
    method: str = "CrystalNN"
    cutoff: float = 3.0
    tolerance: float = 0.1
    hide_bonds_to_hidden: bool = True


def bonds_crystalnn(structure: Structure) -> list[Bond]:
    """Generate bonds using CrystalNN."""

    nn = CrystalNN()
    bonds: list[Bond] = []
    for index, site in enumerate(structure):
        for neighbor in nn.get_nn_info(structure, index):
            if neighbor["site_index"] < index:
                continue
            bonds.append(
                Bond(
                    start=site.coords,
                    end=neighbor["site"].coords,
                    elements=(
                        site.specie.symbol,
                        neighbor["site"].specie.symbol,
                    ),
                )
            )
    return bonds


def bonds_cutoff(structure: Structure, cutoff: float) -> list[Bond]:
    """Generate bonds using a simple distance cutoff."""

    bonds: list[Bond] = []
    for index, site in enumerate(structure):
        neighbors = structure.get_sites_in_sphere(site.coords, cutoff, include_index=True)
        for entry in neighbors:
            neighbor = entry[0]
            dist = entry[1]
            neighbor_index = entry[-1]
            if neighbor_index == index or neighbor_index < index:
                continue
            bonds.append(
                Bond(
                    start=site.coords,
                    end=neighbor.coords,
                    elements=(site.specie.symbol, neighbor.specie.symbol),
                )
            )
    return bonds


def generate_bonds(structure: Structure, options: BondingOptions) -> list[Bond]:
    """Generate bonds based on the requested algorithm."""

    method = options.method.lower()
    if method == "crystalnn":
        return bonds_crystalnn(structure)
    if method == "cutoff":
        return bonds_cutoff(structure, options.cutoff)
    raise ValueError(f"Unsupported bonding method: {options.method}")
