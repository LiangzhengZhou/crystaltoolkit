"""I/O helpers for reading crystal structures."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pymatgen.core import Structure


SUPPORTED_EXTENSIONS = {".cif", ".vasp", ".poscar", ".cif.gz"}


def load_structure(path: str | Path) -> Structure:
    """Load a crystal structure from a file."""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Structure file not found: {file_path}")
    return Structure.from_file(str(file_path))


def resolve_structure_path(path_parts: Iterable[str]) -> Path:
    """Resolve a path from CLI parts."""

    return Path(" ".join(path_parts)).expanduser().resolve()
