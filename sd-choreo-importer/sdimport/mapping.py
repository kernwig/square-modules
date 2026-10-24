"""SeqType -> (start, end, folder, filename prefix) mapping and level codes.

Mirrors the table documented in Square-Modules/SCHEMA.md and the plan.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ceder uses U+2794 (HEAVY WIDE-HEADED RIGHTWARDS ARROW) between formations.
ARROW = "\u2794"


@dataclass(frozen=True)
class SeqMapping:
    start: str
    end: Optional[str]
    folder: str
    prefix: str = ""
    excluded: bool = False


# Sentinel for excluded types (Six Couples Hex).
EXCLUDED = SeqMapping(start="", end=None, folder="", excluded=True)

# Keyed by a normalized SeqType label (see normalize_seqtype).
SEQTYPE_MAP: dict[str, SeqMapping] = {
    "static set -> resolve": SeqMapping("home", "home", "Home"),
    "static set -> zero line": SeqMapping("home", "lines", "Home"),
    "static set -> zero box": SeqMapping("home", "8chain", "Home"),
    "zero line -> resolve": SeqMapping("line-partner", "home", "Resolves", "PL-Resolve-"),
    "zero line -> zero line": SeqMapping("lines", "lines", "Lines"),
    "zero line -> zero box": SeqMapping("lines", "8chain", "Lines"),
    "zero box -> resolve": SeqMapping("box-corner", "home", "Resolves", "CB-Resolve-"),
    "zero box -> zero line": SeqMapping("8chain", "lines", "8-Chain"),
    "zero box -> zero box": SeqMapping("8chain", "8chain", "8-Chain"),
    "zero (eight chain thru)": SeqMapping("8chain", "8chain", "Zeros"),
    "zero (facing lines)": SeqMapping("lines", "lines", "Zeros"),
    "zero (parallel waves)": SeqMapping("waves", "waves", "Zeros"),
    "zero (facing couples)": SeqMapping("box", "box", "Zeros"),
    "singing call (corner progression)": SeqMapping("home", "home", "Singer-figure"),
    "singing call (r-h lady progression)": SeqMapping("home", "home", "Singer-figure"),
    "singing break": SeqMapping("home", "home", "Singer-break"),
    "stir the bucket": SeqMapping("home", "home", "Patter-stir"),
    "two couples (facing couples)": SeqMapping("home", "home", "Two-Couples"),
    "six couples (rectangle)": SeqMapping("home", "home", "Rectangle"),
    "six couples (hex)": EXCLUDED,
}

# Level name/alias -> (FindLevel POST code, frontmatter level value).
LEVELS: dict[str, tuple[int, str]] = {
    "mainstream": (20, "ms"),
    "ms": (20, "ms"),
    "plus": (30, "plus"),
    "a1": (40, "a1"),
    "a2": (50, "a2"),
    "c1": (60, "c1"),
    "c2": (70, "c2"),
    "c3a": (80, "c3a"),
    "c3b": (90, "c3b"),
    "c4": (100, "c4"),
}


def normalize_seqtype(label: str) -> str:
    """Normalize a SeqType label for lookup.

    Collapses whitespace, lowercases, and converts the ceder arrow (and common
    ASCII fallbacks) to ``->``. Strips any trailing ``- Complete Dance Routine``
    style suffix that may ride along in a header.
    """
    text = label.strip()
    # Normalize arrow variants to ' -> '.
    for arrow in (ARROW, "\u2192", "\u279c", "->", "\u2b95"):
        text = text.replace(arrow, " -> ")
    text = text.lower()
    text = " ".join(text.split())
    # Tidy spacing around the arrow.
    text = text.replace(" ->", " ->").replace("->  ", "-> ")
    text = " ".join(text.split())
    return text


def map_seqtype(label: str) -> Optional[SeqMapping]:
    """Return the mapping for a SeqType label, or ``None`` if unrecognized."""
    return SEQTYPE_MAP.get(normalize_seqtype(label))
