from pathlib import Path

from sdimport.model import ModuleRecord
from sdimport.writer import (
    VaultWriter,
    abbreviate_calls,
    build_filename,
    render_markdown,
    scan_existing_sources,
)


def test_render_matches_reference_style():
    # Modeled on SD-Choreo/Mainstream/Lines/SQ2-ST-TB-TQ-Split.md
    rec = ModuleRecord(
        start="lines",
        end="home",
        difficulty="medium",
        level="ms",
        author="Jeff Seidel",
        source="ceder-10201",
        calls=[
            "Square Thru 2",
            "Centers Swing Thru,",
            "Trade By,",
            "R.L.G",
        ],
        folder="Lines",
    )
    expected = (
        "---\n"
        "start: lines\n"
        "end: home\n"
        "difficulty: medium\n"
        "level: ms\n"
        "author: Jeff Seidel\n"
        "source: ceder-10201\n"
        "---\n"
        "Square Thru 2\n"
        "Centers Swing Thru,\n"
        "Trade By,\n"
        "R.L.G\n"
    )
    assert render_markdown(rec) == expected


def test_beats_omitted_when_unset_and_included_when_set():
    rec = ModuleRecord(start="home", level="ms", calls=["Promenade"])
    assert "beats:" not in render_markdown(rec)

    rec_b = ModuleRecord(start="home", level="ms", beats=64, calls=["Promenade"])
    md = render_markdown(rec_b)
    assert "beats: 64\n" in md


def test_booleans_only_when_true():
    rec = ModuleRecord(
        start="home", level="ms", trick=True, unvalidated=True, calls=["A"]
    )
    md = render_markdown(rec)
    assert "trick: true\n" in md
    assert "unvalidated: true\n" in md

    rec2 = ModuleRecord(start="home", level="ms", calls=["A"])
    md2 = render_markdown(rec2)
    assert "trick:" not in md2
    assert "unvalidated:" not in md2


def test_singer_rendered_after_level_and_omitted_when_unset():
    rec = ModuleRecord(
        start="home",
        end="home",
        level="ms",
        singer="corner-progression",
        calls=["Heads Square Thru 4,", "Swing & Promenade"],
        folder="Singer-figure",
    )
    md = render_markdown(rec)
    assert "singer: corner-progression\n" in md
    # `singer` is written immediately after `level`.
    assert "level: ms\nsinger: corner-progression\n" in md

    rec_break = ModuleRecord(start="home", level="ms", singer="break", calls=["A"])
    assert "singer: break\n" in render_markdown(rec_break)

    rec_none = ModuleRecord(start="home", level="ms", calls=["A"])
    assert "singer:" not in render_markdown(rec_none)


def test_comment_appended_after_hr():
    rec = ModuleRecord(
        start="home",
        level="ms",
        calls=["Pass Thru,", "Trade By"],
        comment="CDP  Named Backwater",
    )
    body = rec.body()
    assert body == "Pass Thru,\nTrade By\n\n---\n\nCDP  Named Backwater"


def test_body_trailing_space_trimmed():
    rec = ModuleRecord(start="home", level="ms", calls=["Pass Thru,   ", "R.L.G  "])
    assert rec.body() == "Pass Thru,\nR.L.G"


def test_abbreviate_calls_within_limit():
    calls = ["Square Thru 2", "Star Thru", "Trade By", "Right & Left Grand"]
    abbr = abbreviate_calls(calls, limit=20)
    assert len(abbr) <= 20
    assert abbr  # non-empty


def test_build_filename_with_prefix_caps_abbrev_only():
    rec = ModuleRecord(
        start="line-partner",
        end="home",
        level="ms",
        calls=["Square Thru 2", "Star Thru", "Trade By"],
        folder="Resolves",
        filename_prefix="PL-Resolve-",
    )
    name = build_filename(rec, "10201")
    assert name.startswith("PL-Resolve-")
    assert name.endswith("-10201.md")
    # The abbreviation portion only must be <= 20 chars.
    abbrev = name[len("PL-Resolve-") : -len("-10201.md")]
    assert len(abbrev) <= 20


def test_dedup_skips_existing_source(tmp_path: Path):
    writer = VaultWriter(tmp_path, existing_sources={"ceder-1395"})
    rec = ModuleRecord(
        start="8chain", end="8chain", level="ms", source="ceder-1395",
        calls=["Pass Thru,", "Trade By"], folder="Zeros",
    )
    assert writer.write(rec) is None


def test_write_creates_file_and_path(tmp_path: Path):
    writer = VaultWriter(tmp_path, existing_sources=set())
    rec = ModuleRecord(
        start="home", end="home", level="ms", source="ceder-6734",
        difficulty="easy", author="Vic Ceder",
        calls=["Heads Square Thru 3,", "Swing & Promenade"],
        folder="Singer-figure",
    )
    path = writer.write(rec)
    assert path is not None
    assert path.exists()
    assert path.parent == tmp_path / "Mainstream" / "Singer-figure"
    assert path.name.endswith("-6734.md")
    # Second write of same source is now skipped.
    assert writer.write(rec) is None


def test_scan_existing_sources(tmp_path: Path):
    d = tmp_path / "Mainstream" / "Zeros"
    d.mkdir(parents=True)
    (d / "a.md").write_text(
        "---\nstart: 8chain\nlevel: ms\nsource: ceder-1395\n---\nPass Thru\n",
        encoding="utf-8",
    )
    (d / "b.md").write_text(
        "---\nstart: home\nlevel: ms\n---\nPromenade\n", encoding="utf-8"
    )
    found = scan_existing_sources(tmp_path)
    assert found == {"ceder-1395"}
