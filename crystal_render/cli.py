"""Command-line interface for offline crystal rendering."""

from __future__ import annotations

import argparse
from pathlib import Path

from crystal_render.bonding import BondingOptions
from crystal_render.cell import CellSettings
from crystal_render.labels import LabelOptions
from crystal_render.orientation import Orientation
from crystal_render.render import RenderOptions, render_structure
from crystal_render.style import ColorScheme, RadiusScheme, RenderStyle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline crystal rendering (PyVista)")
    parser.add_argument("--cif", "--structure", dest="structure", required=True, help="Structure file path")
    parser.add_argument("--out", dest="output", required=True, help="Output PNG file path")

    parser.add_argument("--cell", default="input", choices=["input", "conventional", "primitive"])
    parser.add_argument("--repeat", nargs=3, type=int, default=(1, 1, 1))
    parser.add_argument("--show-boundary", action="store_true")
    parser.add_argument("--show-bonded-outside", action="store_true")
    parser.add_argument("--show-unit-cell", action="store_true")

    parser.add_argument("--bonding", default="CrystalNN", choices=["CrystalNN", "cutoff"])
    parser.add_argument("--cutoff", type=float, default=3.0)

    parser.add_argument("--colors", default="VESTA", choices=["VESTA", "Jmol"])
    parser.add_argument("--radii", default="covalent", choices=["uniform", "covalent", "ionic"])
    parser.add_argument("--uniform-radius", type=float, default=0.5)
    parser.add_argument("--bond-radius", type=float, default=0.1)

    parser.add_argument("--show-labels", action="store_true")
    parser.add_argument("--label-elements", nargs="*", default=None)
    parser.add_argument("--label-size", type=int, default=12)

    parser.add_argument("--miller", nargs=3, type=int, default=None)
    parser.add_argument("--in-plane", nargs=3, type=int, default=None)

    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("--dpi", type=int, default=200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cell_settings = CellSettings(
        mode=args.cell,
        repeat=tuple(args.repeat),
        show_boundary_images=args.show_boundary,
        show_bonded_outside=args.show_bonded_outside,
    )
    bonding = BondingOptions(method=args.bonding, cutoff=args.cutoff)
    colors = ColorScheme(name=args.colors)
    radii = RadiusScheme(name=args.radii, uniform_value=args.uniform_radius)
    style = RenderStyle(colors=colors, radii=radii, bond_radius=args.bond_radius)
    orientation = Orientation(
        miller=tuple(args.miller) if args.miller is not None else None,
        in_plane=tuple(args.in_plane) if args.in_plane is not None else None,
    )
    labels = LabelOptions(
        show=args.show_labels,
        elements=tuple(args.label_elements) if args.label_elements else None,
        font_size=args.label_size,
    )
    render_options = RenderOptions(
        width=args.width,
        height=args.height,
        dpi=args.dpi,
        show_unit_cell=args.show_unit_cell,
    )

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    render_structure(
        structure_path=args.structure,
        output_path=str(output),
        cell_settings=cell_settings,
        bonding_options=bonding,
        style=style,
        orientation=orientation,
        labels=labels,
        render_options=render_options,
    )


if __name__ == "__main__":
    main()
