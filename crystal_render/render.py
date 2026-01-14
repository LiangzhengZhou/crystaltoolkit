"""Offline rendering pipeline using PyVista."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import importlib.util
import numpy as np

from crystal_render.bonding import Bond, BondingOptions, generate_bonds
from crystal_render.cell import CellSettings, prepare_structure
from crystal_render.labels import LabelOptions
from crystal_render.orientation import Orientation, apply_rotation, rotation_from_orientation
from crystal_render.style import DEFAULT_STYLE, RenderStyle
from crystal_render.io import load_structure


@dataclass(frozen=True)
class RenderOptions:
    width: int = 1600
    height: int = 1200
    dpi: int = 200
    show_atoms: bool = True
    show_bonds: bool = True
    show_unit_cell: bool = False
    show_polyhedra: bool = False
    background: str = "white"


def _require_pyvista() -> None:
    if importlib.util.find_spec("pyvista") is None:
        raise ImportError("pyvista is required for offline rendering (pip install pyvista vtk).")


def build_unit_cell_edges(lattice_matrix: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return the line segments for the unit cell box."""

    a, b, c = lattice_matrix
    origin = np.zeros(3)
    corners = [
        origin,
        a,
        b,
        c,
        a + b,
        a + c,
        b + c,
        a + b + c,
    ]
    edges = [
        (corners[0], corners[1]),
        (corners[0], corners[2]),
        (corners[0], corners[3]),
        (corners[1], corners[4]),
        (corners[1], corners[5]),
        (corners[2], corners[4]),
        (corners[2], corners[6]),
        (corners[3], corners[5]),
        (corners[3], corners[6]),
        (corners[4], corners[7]),
        (corners[5], corners[7]),
        (corners[6], corners[7]),
    ]
    return edges


def _apply_rotation_to_bonds(bonds: Iterable[Bond], rotation: np.ndarray) -> list[Bond]:
    rotated: list[Bond] = []
    for bond in bonds:
        rotated.append(
            Bond(
                start=apply_rotation(bond.start, rotation),
                end=apply_rotation(bond.end, rotation),
                elements=bond.elements,
            )
        )
    return rotated


def render_structure(
    structure_path: str,
    output_path: str,
    cell_settings: CellSettings,
    bonding_options: BondingOptions,
    style: RenderStyle = DEFAULT_STYLE,
    orientation: Orientation | None = None,
    labels: LabelOptions | None = None,
    render_options: RenderOptions | None = None,
) -> None:
    """Render a structure to a PNG image using PyVista."""

    _require_pyvista()
    import pyvista as pv

    structure = load_structure(structure_path)
    structure = prepare_structure(structure, cell_settings)

    if orientation is None:
        orientation = Orientation()
    rotation = rotation_from_orientation(structure, orientation)

    coords = np.array([site.coords for site in structure])
    coords = apply_rotation(coords, rotation)

    bonds = generate_bonds(structure, bonding_options)
    bonds = _apply_rotation_to_bonds(bonds, rotation)

    if labels is None:
        labels = LabelOptions()
    if render_options is None:
        render_options = RenderOptions()

    plotter = pv.Plotter(off_screen=True, window_size=(render_options.width, render_options.height))
    plotter.set_background(render_options.background)

    if render_options.show_atoms:
        for index, site in enumerate(structure):
            radius = style.radii.get_radius(site.specie.symbol)
            sphere = pv.Sphere(radius=radius, center=coords[index], theta_resolution=32, phi_resolution=32)
            plotter.add_mesh(
                sphere,
                color=style.colors.get_color(site.specie.symbol),
                smooth_shading=True,
                specular=0.6,
                specular_power=30,
                ambient=0.3,
                diffuse=0.6,
            )

    if render_options.show_bonds:
        for bond in bonds:
            start = np.array(bond.start)
            end = np.array(bond.end)
            direction = end - start
            length = np.linalg.norm(direction)
            if length == 0:
                continue
            cylinder = pv.Cylinder(center=(start + end) / 2, direction=direction, radius=style.bond_radius, height=length)
            plotter.add_mesh(
                cylinder,
                color=style.bond_rgb(bond.elements),
                smooth_shading=True,
                specular=0.3,
                specular_power=10,
                ambient=0.2,
                diffuse=0.7,
            )

    if render_options.show_unit_cell:
        edges = build_unit_cell_edges(apply_rotation(structure.lattice.matrix, rotation))
        for start, end in edges:
            line = pv.Line(start, end)
            plotter.add_mesh(line, color=(0.3, 0.3, 0.3), line_width=2)

    if render_options.show_polyhedra:
        plotter.add_text("Polyhedra rendering not implemented", font_size=10, color="gray")

    if labels.show:
        points = []
        texts = []
        for index, site in enumerate(structure):
            element = site.specie.symbol
            if not labels.should_label(element):
                continue
            points.append(coords[index] + np.array(labels.offset))
            texts.append(element)
        if points:
            plotter.add_point_labels(
                np.array(points),
                texts,
                font_size=labels.font_size,
                text_color=labels.text_color,
                shadow=labels.shadow,
                always_visible=True,
            )

    plotter.show_axes(False)
    plotter.camera_position = "xy"
    plotter.show(screenshot=output_path, auto_close=True)
