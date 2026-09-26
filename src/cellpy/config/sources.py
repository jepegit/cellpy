"""Config source layers and provenance tracking."""

from __future__ import annotations

from enum import Enum
from typing import Any


class SourceLayer(str, Enum):
    """Where a config value was resolved from (lowest → highest precedence)."""

    DEFAULT = "default"
    USER_FILE = "user_file"
    PROJECT_FILE = "project_file"
    ENV = "env"
    RUNTIME = "runtime"


class ProvenanceRegistry:
    """Records the winning source layer per dotted config path."""

    def __init__(self) -> None:
        self._layers: dict[str, SourceLayer] = {}

    def clear(self) -> None:
        self._layers.clear()

    def record(self, layer: SourceLayer, payload: dict[str, Any], prefix: str = "") -> None:
        """Record provenance for nested dict payloads."""

        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self.record(layer, value, path)
            else:
                self._layers[path] = layer

    def get(self, path: str) -> SourceLayer | None:
        return self._layers.get(path)

    def as_dict(self) -> dict[str, str]:
        return {path: layer.value for path, layer in sorted(self._layers.items())}
