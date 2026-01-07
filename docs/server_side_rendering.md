# Server-Side PNG Rendering

This document explains how to generate structure images without a browser by using
the server-side rendering utilities added to Crystal Toolkit.

## Overview

Two workflows are supported:

1. **Component export**: `StructureMoleculeComponent` can generate PNGs using a
   server-side renderer by setting `export_mode="server"`.
2. **Direct rendering**: `render_structure_png` can be called in Python to render
   a `Structure`, `StructureGraph`, `Molecule`, or `MoleculeGraph` to PNG bytes.

Both paths support an optional `view_direction` vector to align the structure with
the +Z axis before rendering.

## Component export (Dash)

```python
from crystal_toolkit.components.structure import StructureMoleculeComponent

component = StructureMoleculeComponent(
    struct_or_mol=structure,
    export_mode="server",
    view_direction=(0, 0, 1),
)
```

When the image download button is triggered, the PNG is generated on the server
and returned as a downloadable file.

## Direct rendering (Python)

```python
from crystal_toolkit.renderers.scene_renderer import render_structure_png

result = render_structure_png(
    structure,
    view_direction=(1, 0, 0),
    image_size=(1024, 1024),
    background="white",
    include_legend=True,
)

with open("structure.png", "wb") as handle:
    handle.write(result.image_bytes)
```

## Notes

- The lightweight renderer currently supports spheres and cylinders and will
  ignore other primitive types.
- The legend overlay uses the same `Legend` color scheme defaults as the
  interactive viewer.
