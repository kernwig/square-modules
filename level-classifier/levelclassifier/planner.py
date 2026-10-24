"""Scan a vault, classify modules, and build/apply a change plan.

Two modes:
  * fill-missing  : only modules lacking a ``level`` are planned; set to the
    detected level and move to the detected level's folder.
  * flag-mismatch : modules whose set ``level`` differs from the detected level
    are reported for confirmation (never auto-applied unless --apply + approved).

The plan is written as a TSV report the user can review/edit; applying reads an
approved report and performs the frontmatter rewrite + folder move.

Folder move preserves the path *between* the level folder and the filename,
including the empty case (a file directly under the level folder stays directly
under the new level folder).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .classifier import Classification, classify_lines
from .mdfile import LEVEL_FOLDERS, read_module, rewrite_level

# Reverse: folder name -> level value (for locating the level segment in a path).
_FOLDER_TO_LEVEL = {v: k for k, v in LEVEL_FOLDERS.items()}


@dataclass
class PlanRow:
    path: Path
    current_level: Optional[str]
    detected_level: str
    confidence: str
    deciding_call: str
    unknown_tokens: list[str]
    mode: str                 # "fill" | "mismatch"
    new_path: Path

    def as_tsv(self, vault_root: Path) -> list[str]:
        return [
            str(self.path.relative_to(vault_root)),
            self.current_level or "(none)",
            self.detected_level,
            self.confidence,
            self.deciding_call,
            " ".join(self.unknown_tokens),
            self.mode,
            str(self.new_path.relative_to(vault_root)),
        ]


TSV_HEADER = [
    "file",
    "current_level",
    "detected_level",
    "confidence",
    "deciding_call",
    "unknown_tokens",
    "mode",
    "new_path",
]


def iter_module_files(vault_root: Path) -> Iterable[Path]:
    """Yield module markdown files, skipping templates and dotfiles."""
    for md in sorted(vault_root.rglob("*.md")):
        if md.name.startswith("_"):
            continue  # _Template.md etc.
        if any(part.startswith(".") for part in md.relative_to(vault_root).parts):
            continue
        yield md


def _relocate(path: Path, vault_root: Path, new_level: str) -> Path:
    """Compute the destination path for ``new_level``, preserving the sub-path.

    The vault layout is ``<vault>/<LevelFolder>/<maybe/sub/dirs>/<file>.md``.
    We swap only the ``<LevelFolder>`` segment. If the file is not currently
    under a recognized level folder, it is moved under the new level folder at
    the same relative position below the vault root.
    """
    rel = path.relative_to(vault_root)
    parts = list(rel.parts)
    new_folder = LEVEL_FOLDERS.get(new_level, new_level)

    if parts and parts[0] in _FOLDER_TO_LEVEL:
        # Replace the leading level-folder segment; keep the rest (which may be
        # just the filename, i.e. a file directly under the level folder).
        parts[0] = new_folder
    else:
        # No level folder in the path: nest under the new level folder.
        parts = [new_folder] + parts
    return vault_root.joinpath(*parts)


def build_plan(vault_root: Path, *, mode: str) -> list[PlanRow]:
    """Build the change plan.

    ``mode`` is ``"fill"`` (only modules with no level) or ``"mismatch"``
    (modules whose level disagrees with detection). ``"all"`` combines both.
    """
    rows: list[PlanRow] = []
    for md in iter_module_files(vault_root):
        mod = read_module(md)
        cls: Classification = classify_lines(mod.call_lines)

        is_missing = mod.level is None
        is_mismatch = mod.level is not None and mod.level != cls.detected_level

        row_mode: Optional[str] = None
        if is_missing and mode in ("fill", "all"):
            row_mode = "fill"
        elif is_mismatch and mode in ("mismatch", "all"):
            row_mode = "mismatch"
        if row_mode is None:
            continue

        new_path = _relocate(md, vault_root, cls.detected_level)
        rows.append(
            PlanRow(
                path=md,
                current_level=mod.level,
                detected_level=cls.detected_level,
                confidence=cls.confidence,
                deciding_call=cls.deciding_call,
                unknown_tokens=cls.unknown_tokens,
                mode=row_mode,
                new_path=new_path,
            )
        )
    return rows


def write_report(rows: list[PlanRow], vault_root: Path, report_path: Path) -> None:
    with report_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(TSV_HEADER)
        for r in rows:
            w.writerow(r.as_tsv(vault_root))


@dataclass
class ApplyResult:
    changed: int = 0
    moved: int = 0
    skipped: int = 0
    errors: list[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def apply_report(report_path: Path, vault_root: Path, *, dry_run: bool = False) -> ApplyResult:
    """Apply an (approved) report: rewrite level frontmatter and move files.

    Only rows whose ``new_path`` differs or whose level changes are acted on.
    Rows can be removed from the report by the user to skip them.
    """
    res = ApplyResult()
    with report_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            src = vault_root / row["file"]
            dst = vault_root / row["new_path"]
            new_level = row["detected_level"].strip()
            if not src.exists():
                res.errors.append(f"missing source: {row['file']}")
                continue
            try:
                text = src.read_text(encoding="utf-8")
                new_text = rewrite_level(text, new_level)
                if not dry_run:
                    if dst != src:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                    src.write_text(new_text, encoding="utf-8")
                    if dst != src:
                        src.rename(dst)
                res.changed += 1
                if dst != src:
                    res.moved += 1
            except Exception as exc:  # noqa: BLE001 - report and continue
                res.errors.append(f"{row['file']}: {exc}")
    return res
