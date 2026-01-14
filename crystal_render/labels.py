"""Atom labeling utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabelOptions:
    show: bool = False
    elements: tuple[str, ...] | None = None
    font_size: int = 12
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    text_color: str = "black"
    shadow: bool = True

    def should_label(self, element: str) -> bool:
        if not self.show:
            return False
        if self.elements is None:
            return True
        return element in self.elements
