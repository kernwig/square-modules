"""Parse a ceder.net choreo detail page (viewsingle.php) into a ModuleRecord.

The detail page is the source of truth for start/end/folder (via SeqType),
author, difficulty, the unvalidated flag, the call sequence, and the comment.
"""
from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup

from .mapping import map_seqtype
from .model import ModuleRecord

_BEATS_RE = re.compile(r"\b(\d{1,3})\s*(?:beat|step)", re.IGNORECASE)
_DIFFICULTIES = {"easy", "medium", "hard"}


class ExcludedRecord(Exception):
    """Raised when a record's SeqType is excluded (e.g. Six Couples Hex)."""


class UnmappedSeqType(Exception):
    """Raised when a record's SeqType is not in the mapping table."""

    def __init__(self, label: str):
        super().__init__(f"Unmapped SeqType: {label!r}")
        self.label = label


def _text(node) -> str:
    return node.get_text(" ", strip=True) if node else ""


def extract_seqtype(soup: BeautifulSoup) -> str:
    """Return the raw SeqType label, e.g. ``Static Set ➔ Resolve``."""
    header = soup.select_one("#pageheader")
    if header:
        return header.get_text(strip=True)
    glow = soup.select_one("span.glow")
    return glow.get_text(strip=True) if glow else ""


def extract_author(soup: BeautifulSoup) -> Optional[str]:
    link = soup.select_one('a[href*="callerdb/viewsingle.php"]')
    if not link:
        return None
    span = link.select_one("span.text16")
    name = _text(span) if span else _text(link)
    return name or None


def extract_difficulty(soup: BeautifulSoup) -> Optional[str]:
    for span in soup.select("span.red"):
        val = span.get_text(strip=True).lower()
        if val in _DIFFICULTIES:
            return val
    return None


def is_unvalidated(soup: BeautifulSoup) -> bool:
    for span in soup.select("span.red"):
        if "not validated" in span.get_text(strip=True).lower():
            return True
    return False


def extract_calls(soup: BeautifulSoup) -> list[str]:
    """Return the call lines from the choreo div (split on <br>, trimmed)."""
    div = soup.select_one("div.size3A")
    if not div:
        return []
    # Replace <br> with newlines, then split.
    for br in div.find_all("br"):
        br.replace_with("\n")
    raw = div.get_text()
    lines = [ln.strip() for ln in raw.split("\n")]
    return [ln for ln in lines if ln]


def extract_comment(soup: BeautifulSoup) -> Optional[str]:
    """Return the comment div that follows the choreo div's trailing <hr>."""
    div = soup.select_one("div.size3A")
    if not div:
        return None
    # Walk forward siblings: first <hr>, then the comment <div>.
    seen_hr = False
    node = div
    while True:
        node = node.find_next_sibling()
        if node is None:
            return None
        name = getattr(node, "name", None)
        if name == "hr":
            seen_hr = True
            continue
        if seen_hr and name == "div":
            text = node.get_text(" ", strip=True)
            return text or None
        if name == "form":
            # Reached the "Add Comments" form without a comment div.
            return None
    return None


def extract_beats(comment: Optional[str]) -> Optional[int]:
    """Auto-extract a beat/step count from a comment, if present."""
    if not comment:
        return None
    m = _BEATS_RE.search(comment)
    return int(m.group(1)) if m else None


def parse_detail(
    html: str,
    record_id: str,
    level_value: str,
    choreo_html: Optional[str] = None,
) -> ModuleRecord:
    """Parse a detail-page HTML string into a :class:`ModuleRecord`.

    ``html`` is the main ``viewsingle.php`` page (source of truth for SeqType,
    author, difficulty, and the unvalidated flag). On the live site the call
    body + comment are loaded separately via ``ajax_viewsingle_choreo.php``; pass
    that fragment as ``choreo_html`` to read calls/comment from it. When
    ``choreo_html`` is omitted the body is read from ``html`` (used by fixtures
    that embed the body inline).

    Raises :class:`ExcludedRecord` for excluded SeqTypes and
    :class:`UnmappedSeqType` for unrecognized ones.
    """
    soup = BeautifulSoup(html, "html.parser")

    seqtype = extract_seqtype(soup)
    mapping = map_seqtype(seqtype)
    if mapping is None:
        raise UnmappedSeqType(seqtype)
    if mapping.excluded:
        raise ExcludedRecord(seqtype)

    body_soup = BeautifulSoup(choreo_html, "html.parser") if choreo_html else soup

    comment = extract_comment(body_soup)
    beats = extract_beats(comment)

    return ModuleRecord(
        start=mapping.start,
        end=mapping.end,
        level=level_value,
        calls=extract_calls(body_soup),
        difficulty=extract_difficulty(soup),
        author=extract_author(soup),
        source=f"ceder-{record_id}",
        beats=beats,
        unvalidated=is_unvalidated(soup),
        comment=comment,
        folder=mapping.folder,
        filename_prefix=mapping.prefix,
    )
