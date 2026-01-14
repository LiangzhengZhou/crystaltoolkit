"""Color and radius presets."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pymatgen.analysis.molecule_structure_comparator import CovalentRadius
from pymatgen.core import Element
from pymatgen.vis import structure_vtk


@dataclass(frozen=True)
class ColorScheme:
    name: str = "VESTA"

    def get_color(self, element: str) -> tuple[float, float, float]:
        colors = structure_vtk.EL_COLORS[self.name]
        rgb = colors.get(element)
        if rgb is None:
            return (0.5, 0.5, 0.5)
        return tuple(channel / 255 for channel in rgb)


@dataclass(frozen=True)
class RadiusScheme:
    name: str = "covalent"
    uniform_value: float = 0.5

    def get_radius(self, element: str) -> float:
        if self.name == "uniform":
            return self.uniform_value
        if self.name == "covalent":
            return CovalentRadius.radius.get(element, self.uniform_value)
        if self.name == "ionic":
            elem = Element(element)
            radius = elem.average_ionic_radius
            if radius is None:
                return self.uniform_value
            return radius
        raise ValueError(f"Unsupported radius scheme: {self.name}")


@dataclass(frozen=True)
class RenderStyle:
    colors: ColorScheme = ColorScheme()
    radii: RadiusScheme = RadiusScheme()
    bond_radius: float = 0.1
    bond_color: tuple[float, float, float] | None = None

    def bond_rgb(self, elements: tuple[str, str]) -> tuple[float, float, float]:
        if self.bond_color is not None:
            return self.bond_color
        first = np.array(self.colors.get_color(elements[0]))
        second = np.array(self.colors.get_color(elements[1]))
        return tuple(((first + second) / 2).tolist())


DEFAULT_STYLE = RenderStyle()
