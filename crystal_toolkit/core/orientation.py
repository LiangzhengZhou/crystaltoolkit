from __future__ import annotations

import numpy as np


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Zero-length direction vector is not allowed.")
    return vector / norm


def direction_to_rotation(
    direction: np.ndarray,
    lattice: np.ndarray | None = None,
    target_axis: np.ndarray | None = None,
) -> np.ndarray:
    """Return a rotation matrix aligning direction to target_axis.

    Args:
        direction: Vector in fractional or Cartesian coordinates.
        lattice: Optional 3x3 lattice matrix to convert fractional to Cartesian.
        target_axis: Target axis in Cartesian coordinates (default is +Z).

    Returns:
        3x3 rotation matrix.
    """
    vector = np.array(direction, dtype=float)
    if lattice is not None:
        vector = np.dot(lattice, vector)
    vector = normalize_vector(vector)
    target = np.array(target_axis if target_axis is not None else [0, 0, 1.0])
    target = normalize_vector(target)

    axis = np.cross(vector, target)
    axis_norm = np.linalg.norm(axis)
    if axis_norm == 0:
        return np.eye(3)
    axis = axis / axis_norm
    angle = np.arccos(np.clip(np.dot(vector, target), -1.0, 1.0))

    cos_angle = np.cos(angle)
    sin_angle = np.sin(angle)
    ux, uy, uz = axis

    return np.array(
        [
            [
                cos_angle + ux * ux * (1 - cos_angle),
                ux * uy * (1 - cos_angle) - uz * sin_angle,
                ux * uz * (1 - cos_angle) + uy * sin_angle,
            ],
            [
                uy * ux * (1 - cos_angle) + uz * sin_angle,
                cos_angle + uy * uy * (1 - cos_angle),
                uy * uz * (1 - cos_angle) - ux * sin_angle,
            ],
            [
                uz * ux * (1 - cos_angle) - uy * sin_angle,
                uz * uy * (1 - cos_angle) + ux * sin_angle,
                cos_angle + uz * uz * (1 - cos_angle),
            ],
        ]
    )


def rotate_scene_json(scene_json: dict, rotation: np.ndarray) -> dict:
    """Rotate a Scene JSON dict using a rotation matrix."""
    rotation = np.array(rotation, dtype=float)

    def rotate_point(point: list[float]) -> list[float]:
        return (rotation @ np.array(point, dtype=float)).tolist()

    def rotate_points(points: list[list[float]]) -> list[list[float]]:
        return [rotate_point(point) for point in points]

    def rotate_contents(contents: list[dict]) -> list[dict]:
        rotated = []
        for item in contents:
            if not isinstance(item, dict):
                rotated.append(item)
                continue
            if "origin" in item and item["origin"] is not None:
                item["origin"] = rotate_point(item["origin"])
            if "lattice" in item and item["lattice"] is not None:
                item["lattice"] = rotate_points(item["lattice"])
            if item.get("type") == "spheres" and item.get("positions"):
                item["positions"] = rotate_points(item["positions"])
            if item.get("type") == "cylinders" and item.get("positionPairs"):
                item["positionPairs"] = [
                    rotate_points(pair) for pair in item["positionPairs"]
                ]
            if item.get("type") == "lines" and item.get("positions"):
                item["positions"] = rotate_points(item["positions"])
            if item.get("type") == "cubes" and item.get("positions"):
                item["positions"] = rotate_points(item["positions"])
            if item.get("type") == "ellipsoids":
                if item.get("positions"):
                    item["positions"] = rotate_points(item["positions"])
                if item.get("rotate_to"):
                    item["rotate_to"] = rotate_points(item["rotate_to"])
            if item.get("type") == "arrows" and item.get("positionPairs"):
                item["positionPairs"] = [
                    rotate_points(pair) for pair in item["positionPairs"]
                ]
            if item.get("type") in {"surface", "convex"} and item.get("positions"):
                item["positions"] = rotate_points(item["positions"])
            if item.get("type") == "bezier" and item.get("controlPoints"):
                item["controlPoints"] = [
                    rotate_points(points) for points in item["controlPoints"]
                ]
            if item.get("contents"):
                item["contents"] = rotate_contents(item["contents"])
            rotated.append(item)
        return rotated

    rotated_scene = dict(scene_json)
    if "origin" in rotated_scene and rotated_scene["origin"] is not None:
        rotated_scene["origin"] = rotate_point(rotated_scene["origin"])
    if "lattice" in rotated_scene and rotated_scene["lattice"] is not None:
        rotated_scene["lattice"] = rotate_points(rotated_scene["lattice"])
    if rotated_scene.get("contents"):
        rotated_scene["contents"] = rotate_contents(rotated_scene["contents"])
    return rotated_scene
