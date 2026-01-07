from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont
from pymatgen.analysis.graphs import MoleculeGraph, StructureGraph
from pymatgen.core import Element, Molecule, Structure

from crystal_toolkit.core.legend import Legend
from crystal_toolkit.core.orientation import direction_to_rotation, rotate_scene_json


@dataclass
class RenderResult:
    image_bytes: bytes
    size: tuple[int, int]


def render_scene_png(
    scene_json: dict[str, Any],
    legend: Legend | None = None,
    image_size: tuple[int, int] = (800, 800),
    background: str = "white",
    include_legend: bool = True,
) -> RenderResult:
    """Render a Scene JSON to a PNG image.

    This is a simplified renderer intended for server-side export in headless
    environments. It supports spheres and cylinders and ignores other
    primitives.
    """
    background_color = ImageColor.getrgb(background)
    if len(background_color) == 3:
        background_color = (*background_color, 255)
    image = Image.new("RGBA", image_size, background_color)
    draw = ImageDraw.Draw(image)

    if not scene_json:
        return _encode_image(image)

    origin = np.array(scene_json.get("origin", [0, 0, 0]), dtype=float)
    contents = scene_json.get("contents", [])

    primitives = _flatten_primitives(contents)
    if primitives:
        positions = _collect_positions(primitives)
    else:
        positions = np.zeros((1, 3))

    center = positions.mean(axis=0) if positions.size else np.zeros(3)
    extent = np.ptp(positions, axis=0) if positions.size else np.ones(3)
    scale = 0.45 * min(image_size) / max(extent.max(), 1e-6)

    def project(point: np.ndarray) -> tuple[float, float]:
        xy = (point - center) * scale
        return (
            image_size[0] / 2 + xy[0] + origin[0],
            image_size[1] / 2 - xy[1] - origin[1],
        )

    for primitive in primitives:
        if primitive["type"] == "spheres":
            color = primitive.get("color", "#808080")
            radius = primitive.get("radius", 1.0) * scale
            for pos in primitive.get("positions", []):
                x, y = project(np.array(pos))
                draw.ellipse(
                    [x - radius, y - radius, x + radius, y + radius],
                    fill=color,
                    outline=None,
                )
        elif primitive["type"] == "cylinders":
            color = primitive.get("color", "#808080")
            width = max(1, int(primitive.get("radius", 0.2) * scale))
            for pair in primitive.get("positionPairs", []):
                start, end = pair
                x1, y1 = project(np.array(start))
                x2, y2 = project(np.array(end))
                draw.line([x1, y1, x2, y2], fill=color, width=width)

    if include_legend and legend is not None:
        _draw_legend(draw, legend, image_size)

    return _encode_image(image)


def _flatten_primitives(contents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primitives: list[dict[str, Any]] = []
    for item in contents:
        if not isinstance(item, dict):
            continue
        if item.get("type"):
            primitives.append(item)
        nested_contents = item.get("contents", [])
        if nested_contents:
            primitives.extend(_flatten_primitives(nested_contents))
    return primitives


def _collect_positions(primitives: list[dict[str, Any]]) -> np.ndarray:
    positions: list[np.ndarray] = []
    for primitive in primitives:
        if primitive["type"] == "spheres":
            for pos in primitive.get("positions", []):
                positions.append(np.array(pos))
        elif primitive["type"] == "cylinders":
            for pair in primitive.get("positionPairs", []):
                for pos in pair:
                    positions.append(np.array(pos))
    if not positions:
        return np.zeros((1, 3))
    return np.vstack(positions)


def _draw_legend(
    draw: ImageDraw.ImageDraw,
    legend: Legend,
    image_size: tuple[int, int],
) -> None:
    legend_data = legend.get_legend()
    composition = legend_data.get("composition", {})
    if not composition:
        return

    padding = 10
    box_size = 18
    text_offset = 6
    x = image_size[0] - 200
    y = padding

    for element in composition:
        color = legend.get_color(Element(str(element)))
        draw.rectangle(
            [x, y, x + box_size, y + box_size], fill=color, outline="black"
        )
        draw.text(
            (x + box_size + text_offset, y),
            str(element),
            fill="black",
            font=ImageFont.load_default(),
        )
        y += box_size + padding


def _encode_image(image: Image.Image) -> RenderResult:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return RenderResult(image_bytes=buffer.getvalue(), size=image.size)


def render_structure_png(
    struct_or_mol: Structure | StructureGraph | Molecule | MoleculeGraph,
    *,
    view_direction: np.ndarray | None = None,
    image_size: tuple[int, int] = (800, 800),
    background: str = "white",
    include_legend: bool = True,
) -> RenderResult:
    """Render a structure or molecule (or their graph variants) to PNG bytes."""
    if isinstance(struct_or_mol, StructureGraph):
        graph = struct_or_mol
        struct_or_mol = graph.structure
    elif isinstance(struct_or_mol, MoleculeGraph):
        graph = struct_or_mol
        struct_or_mol = graph.molecule
    else:
        graph = None

    legend = Legend(struct_or_mol)

    if graph is not None:
        scene = graph.get_scene(legend=legend)
    else:
        scene = struct_or_mol.get_scene(legend=legend)

    scene_json = scene.to_json()

    if view_direction is not None and hasattr(struct_or_mol, "lattice"):
        rotation = direction_to_rotation(
            np.array(view_direction, dtype=float),
            lattice=struct_or_mol.lattice.matrix,
        )
        scene_json = rotate_scene_json(scene_json, rotation)

    return render_scene_png(
        scene_json,
        legend=legend,
        image_size=image_size,
        background=background,
        include_legend=include_legend,
    )
