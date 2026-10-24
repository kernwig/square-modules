"""ceder.net import source.

Combines :class:`~sdimport.ceder_client.CederClient` (search + pagination +
detail fetch) with :func:`~sdimport.detail.parse_detail` to yield canonical
records for a given level.
"""
from __future__ import annotations

from typing import Iterator, Optional

from ..ceder_client import CederClient
from ..detail import ExcludedRecord, UnmappedSeqType, parse_detail
from ..mapping import LEVELS
from ..model import ModuleRecord
from .base import SourceResult


class CederSource:
    name = "ceder"

    def __init__(self, level: str = "mainstream", client: Optional[CederClient] = None):
        key = level.strip().lower()
        if key not in LEVELS:
            raise ValueError(f"Unknown level: {level!r}")
        self.level = key
        self.level_value = LEVELS[key][1]
        self.client = client or CederClient()

    def records(self, result: SourceResult) -> Iterator[ModuleRecord]:
        for record_id in self.client.iter_record_ids(self.level):
            try:
                html = self.client.detail_page(record_id)
                self.client.sleep(self.client.delay)
                choreo = self.client.choreo_fragment(record_id)
                rec = parse_detail(html, record_id, self.level_value, choreo_html=choreo)
            except ExcludedRecord:
                result.excluded += 1
                continue
            except UnmappedSeqType:
                result.errors += 1
                continue
            except Exception:  # network / parse hiccup on a single record
                result.errors += 1
                continue
            result.fetched += 1
            yield rec
