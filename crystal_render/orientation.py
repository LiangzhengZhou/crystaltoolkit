"""Crystal orientation utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pymatgen.core import Structure


@dataclass(frozen=True)
class Orientation:
    miller: tuple[int, int, int] | None = None
    in_plane: tuple[int, int, int] | None = None


def miller_normal(structure: Structure, miller: tuple[int, int, int]) -> np.ndarray:
    """Return the Cartesian normal for a given Miller index."""

    reciprocal = structure.lattice.reciprocal_lattice
    b1, b2, b3 = reciprocal.matrix
    h, k, l = miller
    normal = h * b1 + k * b2 + l * b3
    norm = np.linalg.norm(normal)
    if norm == 0:
        raise ValueError("Miller index results in zero normal.")
    return normal / norm


def in_plane_direction(structure: Structure, direction: tuple[int, int, int]) -> np.ndarray:
    """Return Cartesian direction for an in-plane vector."""

    a1, a2, a3 = structure.lattice.matrix
    u, v, w = direction
    vec = u * a1 + v * a2 + w * a3
    norm = np.linalg.norm(vec)
    if norm == 0:
        raise ValueError("In-plane direction results in zero vector.")
    return vec / norm


def rotation_from_orientation(structure: Structure, orientation: Orientation) -> np.ndarray:
    """Compute a rotation matrix that aligns the Miller normal to +Z."""

    if orientation.miller is None:
        return np.eye(3)
    normal = miller_normal(structure, orientation.miller)
    if orientation.in_plane is not None:
        plane_vec = in_plane_direction(structure, orientation.in_plane)
        plane_vec = plane_vec - np.dot(plane_vec, normal) * normal
        if np.linalg.norm(plane_vec) < 1e-6:
            plane_vec = np.array([0.0, 1.0, 0.0])
    else:
        plane_vec = np.array([0.0, 1.0, 0.0])
    plane_vec = plane_vec / np.linalg.norm(plane_vec)
    x_axis = np.cross(plane_vec, normal)
    x_axis = x_axis / np.linalg.norm(x_axis)
    y_axis = np.cross(normal, x_axis)
    rotation = np.vstack([x_axis, y_axis, normal])
    return rotation


def apply_rotation(coords: np.ndarray, rotation: np.ndarray) -> np.ndarray:
    """Apply a rotation matrix to coordinate array."""

    return coords @ rotation.T
