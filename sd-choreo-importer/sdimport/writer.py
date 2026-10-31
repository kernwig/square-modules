"""Serialize :class:`ModuleRecord` objects to Obsidian markdown files.

Responsibilities:
  * Build YAML frontmatter matching the existing reference files (numeric
    ``beats``, omitted-when-empty optionals, booleans only when ``true``).
  * Resolve the target path ``<vault>/<Level>/<Folder>/<name>.md``.
  * Generate filenames: ``<prefix><abbrev>-<id>.md`` with the <=20 char cap
    applied to the abbreviation only.
  * Deduplicate by scanning existing ``source:`` values in the vault and
    skipping records whose source already exists.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional

from .model import ModuleRecord

# Map the frontmatter ``level`` value to its display folder name.
LEVEL_FOLDERS = {
    "ms": "Mainstream",
    "plus": "Plus",
    "a1": "A1",
    "a2": "A2",
    "c1": "C1",
    "c2": "C2",
    "c3a": "C3A",
    "c3b": "C3B",
    "c4": "C4",
}

# Short tokens for common calls, used when abbreviating a sequence into a name.
_CALL_ABBREVS = [
    ("right and left thru", "RLT"),
    ("right & left thru", "RLT"),
    ("right and left grand", "RLG"),
    ("square thru", "SqThru"),
    ("star thru", "ST"),
    ("pass thru", "PT"),
    ("trade by", "TB"),
    ("swing thru", "SwThru"),
    ("touch 1/4", "Tch14"),
    ("wheel & deal", "WaD"),
    ("wheel and deal", "WaD"),
    ("ladies chain", "LC"),
    ("flutter wheel", "FW"),
    ("pass the ocean", "PO"),
    ("bend the line", "BtL"),
    ("separate", "Sep"),
    ("promenade", "Prom"),
    ("dosado", "DSD"),
    ("circulate", "Circ"),
    ("allemande left", "AL"),
]

_SOURCE_RE = re.compile(r"^source:\s*(\S+)\s*$", re.MULTILINE)


def _yaml_scalar(value: str) -> str:
    """Quote a YAML scalar only when needed (match the reference file style)."""
    # Reference files leave simple strings unquoted. Quote if it could be
    # misparsed (leading/trailing space, special chars, or looks numeric).
    if value == "" or value != value.strip():
        return f'"{value}"'
    if re.search(r'[:#\[\]{}",]', value):
        return f'"{value}"'
    return value


def render_frontmatter(record: ModuleRecord) -> str:
    """Render the YAML frontmatter block (including the delimiters)."""
    lines: list[str] = ["---"]
    lines.append(f"start: {_yaml_scalar(record.start)}")
    if record.end:
        lines.append(f"end: {_yaml_scalar(record.end)}")
    if record.difficulty:
        lines.append(f"difficulty: {_yaml_scalar(record.difficulty)}")
    if record.trick:
        lines.append("trick: true")
    if record.unvalidated:
        lines.append("unvalidated: true")
    if record.beats is not None:
        lines.append(f"beats: {int(record.beats)}")
    lines.append(f"level: {_yaml_scalar(record.level)}")
    if record.singer:
        lines.append(f"singer: {_yaml_scalar(record.singer)}")
    if record.author:
        lines.append(f"author: {_yaml_scalar(record.author)}")
    if record.source:
        lines.append(f"source: {_yaml_scalar(record.source)}")
    lines.append("---")
    return "\n".join(lines)


def render_markdown(record: ModuleRecord) -> str:
    """Render the full markdown file content for a record."""
    fm = render_frontmatter(record)
    body = record.body()
    if body:
        return f"{fm}\n{body}\n"
    return f"{fm}\n"


def abbreviate_calls(calls: Iterable[str], limit: int = 20) -> str:
    """Derive a short (<= ``limit`` char) abbreviation from the call lines."""
    tokens: list[str] = []
    for raw in calls:
        line = raw.strip().lower()
        # Strip leading parenthetical notes like "(Lesson 1)," and trailing punctuation.
        line = re.sub(r"\([^)]*\)", " ", line)
        line = line.strip(" ,.")
        if not line:
            continue
        abbr = None
        for needle, short in _CALL_ABBREVS:
            if needle in line:
                abbr = short
                break
        if abbr is None:
            # Fall back to initials of the first few words.
            words = re.findall(r"[a-z0-9]+", line)
            if not words:
                continue
            abbr = "".join(w[0].upper() for w in words[:3])
        tokens.append(abbr)

    name = ""
    for tok in tokens:
        candidate = tok if not name else f"{name}-{tok}"
        if len(candidate) > limit:
            break
        name = candidate
    if not name and tokens:
        # Guarantee something; truncate the first token to the limit.
        name = tokens[0][:limit]
    return name or "module"


def build_filename(record: ModuleRecord, record_id: str) -> str:
    """Build ``<prefix><abbrev>-<id>.md`` (prefix/suffix excluded from cap)."""
    abbrev = abbreviate_calls(record.calls, limit=20)
    return f"{record.filename_prefix}{abbrev}-{record_id}.md"


def _record_id_from_source(source: Optional[str]) -> str:
    """Extract the trailing id from a ``prefix-<id>`` source string."""
    if not source:
        return "0"
    return source.rsplit("-", 1)[-1]


def scan_existing_sources(vault_root: Path) -> set[str]:
    """Return the set of ``source:`` values already present under ``vault_root``."""
    found: set[str] = set()
    if not vault_root.exists():
        return found
    for md in vault_root.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # Only inspect a leading frontmatter block.
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        head = text[: end if end != -1 else len(text)]
        for m in _SOURCE_RE.finditer(head):
            found.add(m.group(1).strip().strip('"'))
    return found


class VaultWriter:
    """Writes records into ``<vault_root>`` with source-based deduplication."""

    def __init__(self, vault_root: Path, existing_sources: Optional[set[str]] = None):
        self.vault_root = Path(vault_root)
        self.existing_sources = (
            existing_sources
            if existing_sources is not None
            else scan_existing_sources(self.vault_root)
        )

    def target_path(self, record: ModuleRecord, record_id: str) -> Path:
        level_folder = LEVEL_FOLDERS.get(record.level, record.level)
        filename = build_filename(record, record_id)
        return self.vault_root / level_folder / record.folder / filename

    def write(self, record: ModuleRecord, *, dry_run: bool = False) -> Optional[Path]:
        """Write a record. Returns the path written, or ``None`` if skipped.

        Skips (returns ``None``) when the record's ``source`` already exists in
        the vault.
        """
        if record.source and record.source in self.existing_sources:
            return None

        record_id = _record_id_from_source(record.source)
        path = self.target_path(record, record_id)
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_markdown(record), encoding="utf-8")
        if record.source:
            self.existing_sources.add(record.source)
        return path
