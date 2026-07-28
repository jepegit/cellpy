"""Lazy cell store.

Replaces ``batch_core.Data`` + ``experiment.cell_data_frames`` + the ``x_``
prefixed accessor dict. A standard ``Mapping`` with lazy loading; tab completion
comes from ``_ipython_key_completions_`` (the supported mechanism for
``store["<TAB>"]``) instead of prefix-mangled attribute names -- which also
removes the ``str.lstrip`` label-mangling bug (batch_core.py:180, where a cell
named ``xenon_cell`` round-tripped to ``enon_cell``).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Iterator


class CellStore(Mapping):
    """A lazy ``Mapping[str, CellpyCell]``.

    Construct with per-label zero-argument loaders (called on first access) or
    with already-loaded cells (:meth:`from_cells`). Loaded cells are cached.
    """

    def __init__(
        self,
        loaders: Mapping[str, Callable[[], Any]] | None = None,
        cells: Mapping[str, Any] | None = None,
    ) -> None:
        self._loaders: dict[str, Callable[[], Any]] = dict(loaders or {})
        self._cache: dict[str, Any] = dict(cells or {})
        # preserve insertion order, loaders first then any cache-only labels
        self._labels: list[str] = list(self._loaders)
        for label in self._cache:
            if label not in self._loaders:
                self._labels.append(label)

    @classmethod
    def from_cells(cls, cells: Mapping[str, Any]) -> "CellStore":
        """Build a store over already-loaded cells (e.g. from a BatchResult)."""
        return cls(cells=cells)

    def __getitem__(self, label: str) -> Any:
        if label in self._cache:
            return self._cache[label]
        if label in self._loaders:
            cell = self._loaders[label]()
            self._cache[label] = cell
            return cell
        raise KeyError(label)

    def __iter__(self) -> Iterator[str]:
        return iter(self._labels)

    def __len__(self) -> int:
        return len(self._labels)

    def first(self) -> Any:
        """Load and return the first cell."""
        if not self._labels:
            raise KeyError("no cells in store")
        return self[self._labels[0]]

    def sample(self) -> Any:
        """Alias for :meth:`first` (a representative cell)."""
        return self.first()

    def is_loaded(self, label: str) -> bool:
        return label in self._cache

    def unload(self, label: str) -> None:
        """Drop a loaded cell from the cache (explicit memory management)."""
        self._cache.pop(label, None)

    def _ipython_key_completions_(self) -> list[str]:
        """Tab completion for ``store["<TAB>"]`` -- no prefix mangling."""
        return list(self._labels)
