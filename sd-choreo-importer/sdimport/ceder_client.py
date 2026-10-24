"""Low-level ceder.net HTTP access + results-page parsing.

Network I/O is isolated in :class:`CederClient` so parsing/pagination can be
tested against saved fixtures with a stub fetcher.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable, Iterator, Optional

import requests
from bs4 import BeautifulSoup

from .mapping import LEVELS

BASE_URL = "https://www.ceder.net/choreodb/"
DETAIL_URL = "https://www.ceder.net/choreodb/viewsingle.php"
CHOREO_AJAX_URL = "https://www.ceder.net/choreodb/ajax_viewsingle_choreo.php"
USER_AGENT = "sd-choreo-importer/1.0 (personal Obsidian vault import)"

_RECORDID_RE = re.compile(r"RecordId=(\d+)")
_PAGE_COUNT_RE = re.compile(r"\bof\s+(\d+)\b")

# A fetcher takes (method, url, data) and returns the response text.
Fetcher = Callable[[str, str, Optional[dict]], str]


def level_to_code(level: str) -> int:
    """Map a level name/alias to the ceder FindLevel POST code."""
    try:
        return LEVELS[level.strip().lower()][0]
    except KeyError as exc:
        raise ValueError(f"Unknown level: {level!r}") from exc


def extract_record_ids(html: str) -> list[str]:
    """Return the ordered, de-duplicated RecordIds from result links."""
    soup = BeautifulSoup(html, "html.parser")
    ids: list[str] = []
    seen: set[str] = set()
    for a in soup.select('a.pre[href*="viewsingle.php?RecordId="]'):
        m = _RECORDID_RE.search(a.get("href", ""))
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            ids.append(m.group(1))
    return ids


def extract_page_count(html: str) -> int:
    """Return the total page count from the ``of N`` indicator (default 1)."""
    soup = BeautifulSoup(html, "html.parser")
    # The page selector is followed by a '<span>of N</span>'.
    for span in soup.find_all("span", class_="footnote"):
        text = span.get_text(" ", strip=True)
        m = _PAGE_COUNT_RE.search(text)
        if m and "of" in text:
            return int(m.group(1))
    # Fallback: scan the whole document text.
    m = _PAGE_COUNT_RE.search(soup.get_text(" ", strip=True))
    return int(m.group(1)) if m else 1


@dataclass
class CederClient:
    """Fetches search result pages and detail pages from ceder.net."""

    delay: float = 1.0
    fetcher: Optional[Fetcher] = None
    sleep: Callable[[float], None] = time.sleep

    def _fetch(self, method: str, url: str, data: Optional[dict] = None) -> str:
        if self.fetcher is not None:
            return self.fetcher(method, url, data)
        headers = {"User-Agent": USER_AGENT}
        if method == "POST":
            resp = requests.post(url, data=data, headers=headers, timeout=30)
        else:
            resp = requests.get(url, params=data, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text

    def search_page(self, level_code: int, page: int) -> str:
        data = {
            "FindLevel": str(level_code),
            "FindSeqType": "-1",
            "FindHandle": "-1",
            "Special": "-1",
            "FindDifficulty": "-1",
            "Page": str(page),
            "Style": "condensed",
        }
        return self._fetch("POST", BASE_URL, data)

    def iter_record_ids(self, level: str) -> Iterator[str]:
        """Yield every RecordId across all result pages for ``level``.

        Pauses ``delay`` seconds between page requests (not before the first).
        """
        code = level_to_code(level)
        first = self.search_page(code, 1)
        total_pages = extract_page_count(first)
        yield from extract_record_ids(first)
        for page in range(2, total_pages + 1):
            self.sleep(self.delay)
            html = self.search_page(code, page)
            yield from extract_record_ids(html)

    def detail_page(self, record_id: str) -> str:
        return self._fetch("GET", DETAIL_URL, {"RecordId": str(record_id)})

    def choreo_fragment(self, record_id: str) -> str:
        """Fetch the AJAX choreo fragment (call body + comment) for a record."""
        return self._fetch("GET", CHOREO_AJAX_URL, {"RecordId": str(record_id)})
