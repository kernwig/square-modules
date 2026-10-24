"""Source interface.

A ``Source`` produces canonical :class:`~sdimport.model.ModuleRecord` objects
from some origin (ceder.net today; JSON / plain text in the future). Keeping
this interface small lets the CLI and writer stay source-agnostic.
"""
from __future__ import annotations

from typing import Iterator, Protocol

from ..model import ModuleRecord


class SourceResult:
    """Mutable counters a source reports back to the orchestrator."""

    def __init__(self) -> None:
        self.fetched = 0
        self.excluded = 0
        self.errors = 0


class Source(Protocol):
    """Yields ModuleRecords. Implementations may update ``result`` counters."""

    name: str

    def records(self, result: "SourceResult") -> Iterator[ModuleRecord]:
        ...
