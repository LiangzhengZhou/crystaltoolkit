# Offline crystal rendering (PyVista)

This document describes the offline, headless crystal rendering pipeline implemented in `crystal_render/`.
It mirrors the default Crystal Toolkit look-and-feel as closely as possible while avoiding Dash/WebGL.

## Design overview

**Modules and responsibilities**

- `crystal_render/io.py`
  - Reads CIF/POSCAR/VASP files via `pymatgen.Structure.from_file`.
- `crystal_render/cell.py`
  - Unit-cell transformations (input/conventional/primitive), repeats, and optional boundary/bonded images.
- `crystal_render/bonding.py`
  - CrystalNN- and cutoff-based bond generation.
- `crystal_render/style.py`
  - Color schemes (VESTA/Jmol from `pymatgen.vis.structure_vtk.EL_COLORS`) and radii presets.
- `crystal_render/orientation.py`
  - Miller-index view handling and rotation matrix generation.
- `crystal_render/labels.py`
  - Label filtering/formatting (element list, size, shadow).
- `crystal_render/render.py`
  - PyVista offscreen renderer with spheres, cylinders, optional unit cell edges and labels.
- `crystal_render/cli.py`
  - CLI entry point. Assembles options and calls `render_structure`.

**Data flow**

```
structure file -> io.load_structure
             -> cell.transform_unit_cell -> cell.apply_repeat
             -> (optional boundary/bonded images)
             -> orientation.rotation_from_orientation
             -> rotate coordinates and bonds
             -> render (spheres/cylinders/labels) -> PNG
```

## Miller → camera orientation math

Given a structure with lattice vectors **a1**, **a2**, **a3**:

1. Build reciprocal lattice vectors **b1**, **b2**, **b3**.
2. For Miller indices [h k l], compute normal:

   **n** ∝ h **b1** + k **b2** + l **b3**.

3. Normalize **n**.
4. If an in-plane direction [u v w] is specified, compute **p** ∝ u **a1** + v **a2** + w **a3**, then remove its projection on **n** and normalize.
5. Build orthonormal axes:

   **x** = **p** × **n**

   **y** = **n** × **x**

   **z** = **n**

6. The rotation matrix stacks (x, y, z) rows to align **n** with +Z.

See `crystal_render/orientation.py` for the implementation.

## Rendering implementation notes

- **Atoms**: rendered as high-resolution spheres with Phong shading (specular + ambient + diffuse).
- **Bonds**: cylinders oriented along the bond vector (capsule-like appearance).
- **Lighting**: white background, diffuse/ambient mix and specular highlights to mimic Crystal Toolkit defaults.
- **Unit cell**: optional box edges.
- **Labels**: billboard labels using `pyvista.Plotter.add_point_labels` (always facing camera).
- **Offscreen**: PyVista plotter uses `off_screen=True` to run headless.

## CLI examples

Render with defaults:

```bash
python -m crystal_render.cli --cif path/to/structure.cif --out output.png
```

Match Crystal Toolkit defaults with explicit settings:

```bash
python -m crystal_render.cli --cif X.cif --miller 1 1 1 \
  --cell input --bonding CrystalNN --colors VESTA --radii covalent \
  --repeat 2 2 2 --show-labels --label-elements V P --out X_111.png
```

## Default preset

Defaults are defined in:

- `RenderOptions`: 1600×1200 PNG, white background.
- `RenderStyle`: VESTA colors, covalent radii, bond radius 0.1.
- `BondingOptions`: CrystalNN bonding.
- `CellSettings`: input cell, repeat 1×1×1.

These defaults aim to resemble Crystal Toolkit’s visualization style but can be overridden in the CLI.

## Tests

- `tests/test_crystal_render_orientation.py` validates the Miller normal and rotation alignment.
