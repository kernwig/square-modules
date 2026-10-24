"""Read/parse/rewrite an Obsidian choreography-module markdown file.

Self-contained (no dependency on the importer). A module file is:

    ---
    start: ...
    level: ms
    ...
    ---
    <body lines>

    ---

    <optional comment>

The classifier only needs the ``level`` value and the body's *call lines*
(everything before the comment separator). Rewriting changes only the ``level``
frontmatter line, leaving the rest of the file byte-for-byte intact.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Folder name for each level value (mirrors the vault layout).
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

_LEVEL_RE = re.compile(r"^level:\s*(.+?)\s*$", re.MULTILINE)


@dataclass
class ModuleFile:
    path: Path
    level: Optional[str]          # current frontmatter level (None if absent)
    call_lines: list[str]         # body lines before the comment separator
    _frontmatter_raw: str         # the frontmatter block including delimiters
    _rest_raw: str                # everything after the closing delimiter

    @property
    def body_text(self) -> str:
        return "\n".join(self.call_lines)


def _split_frontmatter(text: str) -> tuple[Optional[str], str]:
    """Split leading YAML frontmatter from the remainder.

    Returns ``(frontmatter_including_delimiters, rest)``. If there is no
    frontmatter block, returns ``(None, text)``.
    """
    if not text.startswith("---"):
        return None, text
    # Find the closing '---' on its own line after the opening one.
    m = re.search(r"\n---[ \t]*\r?\n", text)
    if not m:
        return None, text
    end = m.end()
    return text[:end], text[end:]


def _call_lines(body: str) -> list[str]:
    """Return body call lines, excluding anything after a '---' comment rule."""
    lines = body.splitlines()
    out: list[str] = []
    for ln in lines:
        if ln.strip() == "---":
            break  # comment separator; calls are above it
        out.append(ln)
    # Trim surrounding blank lines but keep internal structure.
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return [ln for ln in out if ln.strip()]


def read_module(path: Path) -> ModuleFile:
    text = path.read_text(encoding="utf-8")
    fm, rest = _split_frontmatter(text)
    level = None
    if fm:
        m = _LEVEL_RE.search(fm)
        if m:
            level = m.group(1).strip().strip('"').strip("'").lower()
    return ModuleFile(
        path=path,
        level=level,
        call_lines=_call_lines(rest),
        _frontmatter_raw=fm or "",
        _rest_raw=rest,
    )


def rewrite_level(text: str, new_level: str) -> str:
    """Return ``text`` with the frontmatter ``level:`` set to ``new_level``.

    If a ``level:`` line exists it is replaced in place; otherwise one is
    inserted just before the closing frontmatter delimiter. Only the frontmatter
    is touched.
    """
    fm, rest = _split_frontmatter(text)
    if fm is None:
        raise ValueError("file has no frontmatter block")

    if _LEVEL_RE.search(fm):
        new_fm = _LEVEL_RE.sub(f"level: {new_level}", fm, count=1)
    else:
        # Insert before the closing delimiter line.
        lines = fm.splitlines(keepends=True)
        # lines[-1] (or [-2]) is the closing '---'; find last '---'.
        insert_at = len(lines) - 1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "---":
                insert_at = i
                break
        lines.insert(insert_at, f"level: {new_level}\n")
        new_fm = "".join(lines)
    return new_fm + rest
