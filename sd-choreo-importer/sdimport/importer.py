"""Orchestrates a source -> writer run and tallies a summary."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .sources.base import Source, SourceResult
from .writer import VaultWriter


@dataclass
class ImportSummary:
    fetched: int = 0
    written: int = 0
    skipped_dup: int = 0
    excluded: int = 0
    errors: int = 0

    def as_text(self) -> str:
        return (
            f"fetched={self.fetched} written={self.written} "
            f"skipped_dup={self.skipped_dup} excluded={self.excluded} "
            f"errors={self.errors}"
        )


def run_import(
    source: Source,
    vault_root: Path,
    *,
    dry_run: bool = False,
    limit: Optional[int] = None,
) -> ImportSummary:
    """Pull records from ``source`` and write them under ``vault_root``.

    ``limit`` caps how many *fetched* records are processed (for safe testing).
    """
    writer = VaultWriter(Path(vault_root))
    result = SourceResult()
    summary = ImportSummary()

    for rec in source.records(result):
        if limit is not None and (summary.written + summary.skipped_dup) >= limit:
            break
        path = writer.write(rec, dry_run=dry_run)
        if path is None:
            summary.skipped_dup += 1
        else:
            summary.written += 1

    summary.fetched = result.fetched
    summary.excluded = result.excluded
    summary.errors = result.errors
    return summary
