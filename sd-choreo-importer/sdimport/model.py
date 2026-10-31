"""Canonical data model shared by all import sources.

A :class:`ModuleRecord` is the source-agnostic representation of one
choreography module. Sources (ceder.net, future JSON/plaintext) produce
``ModuleRecord`` instances; :mod:`sdimport.writer` serializes them to Obsidian
markdown files.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# Valid formation slugs (documented in Square-Modules/SCHEMA.md).
FORMATION_SLUGS = {
    "home",
    "8chain",
    "lines",
    "waves",
    "box",
    "line-partner",
    "box-corner",
}

DIFFICULTIES = {"easy", "medium", "hard"}


@dataclass
class ModuleRecord:
    """One choreography module in canonical form.

    Attributes mirror the frontmatter schema plus the body text, the folder it
    files under, and the filename prefix (non-empty only for Resolve types).
    """

    # Required frontmatter
    start: str
    level: str
    # Body: list of call lines (already trailing-trimmed) -- the exact source text.
    calls: list[str] = field(default_factory=list)

    # Optional frontmatter (omitted when empty / falsey)
    end: Optional[str] = None
    difficulty: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None
    beats: Optional[int] = None
    trick: bool = False
    unvalidated: bool = False
    # Singing-call kind: "corner-progression" (figure) or "break". Omitted for
    # non-singing modules.
    singer: Optional[str] = None

    # Optional free-text comment appended to the body after a blank line.
    comment: Optional[str] = None

    # Filing metadata (not written to frontmatter).
    folder: str = ""
    filename_prefix: str = ""

    def body(self) -> str:
        """Return the markdown body: calls, then comment after a horizontal rule."""
        lines = [line.rstrip() for line in self.calls]
        text = "\n".join(lines)
        if self.comment:
            comment = self.comment.strip()
            if comment:
                # Separate the comment with a Markdown horizontal rule.
                text = f"{text}\n\n---\n\n{comment}" if text else comment
        return text
