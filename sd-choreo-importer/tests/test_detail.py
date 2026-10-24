from pathlib import Path

import pytest

from sdimport.detail import (
    ExcludedRecord,
    UnmappedSeqType,
    extract_beats,
    parse_detail,
)
from sdimport.mapping import map_seqtype, normalize_seqtype

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_10468_static_resolve():
    rec = parse_detail(_load("detail_10468.html"), "10468", "ms")
    assert rec.start == "home"
    assert rec.end == "home"
    assert rec.folder == "Home"
    assert rec.filename_prefix == ""
    assert rec.author == "Marcel Konath"
    assert rec.difficulty is None  # no difficulty shown
    assert rec.unvalidated is False
    assert rec.source == "ceder-10468"
    assert rec.calls[0] == "Couple #1 And #2 Right And Left Thru,"
    assert rec.calls[-1] == "R.L.G"
    assert len(rec.calls) == 11
    assert rec.comment is None
    assert rec.beats is None


def test_parse_6895_unvalidated_with_comment():
    rec = parse_detail(_load("detail_6895.html"), "6895", "ms")
    assert rec.start == "home"
    assert rec.difficulty == "easy"
    assert rec.unvalidated is True
    assert rec.calls[0] == "Heads Pass Thru,"
    assert rec.calls[-1] == "Left Allemande"
    assert rec.comment == "CDP  Published in SIO Magazine 8/1956   Named Backwater"
    # Comment is appended to the body after a horizontal rule.
    assert rec.body().endswith(
        "\n\n---\n\nCDP  Published in SIO Magazine 8/1956   Named Backwater"
    )
    assert rec.beats is None


def test_parse_6923_beats_from_comment():
    rec = parse_detail(_load("detail_6923.html"), "6923", "ms")
    assert rec.beats == 64
    assert "64 steps" in rec.comment


def test_extract_beats_variants():
    assert extract_beats("timed to exactly 64 steps") == 64
    assert extract_beats("fits 32 beat music") == 32
    assert extract_beats("no number here") is None
    assert extract_beats(None) is None


def test_mapping_resolves_special():
    pl = map_seqtype("Zero Line \u2794 Resolve")
    assert pl.start == "line-partner"
    assert pl.end == "home"
    assert pl.folder == "Resolves"
    assert pl.prefix == "PL-Resolve-"

    cb = map_seqtype("Zero Box \u2794 Resolve")
    assert cb.start == "box-corner"
    assert cb.folder == "Resolves"
    assert cb.prefix == "CB-Resolve-"


def test_mapping_zero_types():
    assert map_seqtype("Zero (Parallel Waves)").start == "waves"
    assert map_seqtype("Zero (Facing Couples)").start == "box"
    assert map_seqtype("Zero (Eight Chain Thru)").folder == "Zeros"


def test_mapping_hex_excluded():
    m = map_seqtype("Six Couples (Hex)")
    assert m is not None and m.excluded is True


def test_excluded_record_raises():
    html = (
        '<div id="pageheader">Six Couples (Hex)</div>'
        '<div class="size3A">Foo<br>Bar</div>'
    )
    with pytest.raises(ExcludedRecord):
        parse_detail(html, "1", "ms")


def test_unmapped_seqtype_raises():
    html = '<div id="pageheader">Totally Unknown Type</div>'
    with pytest.raises(UnmappedSeqType):
        parse_detail(html, "1", "ms")


def test_normalize_seqtype_arrow_and_space():
    assert normalize_seqtype("Zero Box \u2794 Resolve") == "zero box -> resolve"
    assert normalize_seqtype("  Static Set  \u2794  Zero  Line ") == "static set -> zero line"
