from pathlib import Path

from sdimport.ceder_client import CederClient
from sdimport.cli import main
from sdimport.importer import run_import
from sdimport.sources.ceder import CederSource

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _single_page_results(ids):
    links = "".join(
        f'<a class="pre" href="choreodb/viewsingle.php?RecordId={i}">ID={i}</a>'
        for i in ids
    )
    return f'<html><body>{links}<span class="footnote">page 1 of 1</span></body></html>'


def _make_client(ids, detail_map, choreo_map=None):
    """A CederClient whose fetcher serves a one-page result + mapped details.

    ``choreo_map`` optionally maps RecordId -> AJAX choreo fragment HTML. When a
    record is absent, the detail HTML (which embeds the body inline in fixtures)
    is reused as the fragment.
    """
    choreo_map = choreo_map or {}

    def fetcher(method, url, data):
        if method == "POST":
            return _single_page_results(ids)
        rid = data["RecordId"]
        if "ajax_viewsingle_choreo" in url:
            return choreo_map.get(rid, detail_map[rid])
        return detail_map[rid]

    return CederClient(delay=0.0, fetcher=fetcher, sleep=lambda s: None)


def test_end_to_end_writes_files(tmp_path: Path):
    ids = ["10468", "6895", "6923"]
    detail_map = {
        "10468": _load("detail_10468.html"),
        "6895": _load("detail_6895.html"),
        "6923": _load("detail_6923.html"),
    }
    source = CederSource("mainstream", client=_make_client(ids, detail_map))
    summary = run_import(source, tmp_path)

    assert summary.fetched == 3
    assert summary.written == 3
    assert summary.skipped_dup == 0
    assert summary.excluded == 0
    assert summary.errors == 0

    # All three fixtures are Static Set -> Resolve, so all land in Home.
    home = list((tmp_path / "Mainstream" / "Home").glob("*.md"))
    assert len(home) == 3
    assert any(p.name.endswith("-10468.md") for p in home)

    # 6923 is a singing-call-style record mapped to Home with beats extracted.
    body_6923 = next(
        p for p in (tmp_path / "Mainstream" / "Home").rglob("*-6923.md")
    ).read_text()
    assert "beats: 64" in body_6923


def test_end_to_end_dedup_skips_existing(tmp_path: Path):
    # Pre-create a file carrying source ceder-10468.
    pre = tmp_path / "Mainstream" / "Home"
    pre.mkdir(parents=True)
    (pre / "existing.md").write_text(
        "---\nstart: home\nlevel: ms\nsource: ceder-10468\n---\nFoo\n",
        encoding="utf-8",
    )

    ids = ["10468", "6895"]
    detail_map = {
        "10468": _load("detail_10468.html"),
        "6895": _load("detail_6895.html"),
    }
    source = CederSource("mainstream", client=_make_client(ids, detail_map))
    summary = run_import(source, tmp_path)

    assert summary.fetched == 2
    assert summary.written == 1
    assert summary.skipped_dup == 1


def test_end_to_end_excludes_hex(tmp_path: Path):
    hex_html = (
        '<div id="pageheader">Six Couples (Hex)</div>'
        '<div class="size3A">Foo<br>Bar</div>'
    )
    ids = ["999", "6895"]
    detail_map = {"999": hex_html, "6895": _load("detail_6895.html")}
    source = CederSource("mainstream", client=_make_client(ids, detail_map))
    summary = run_import(source, tmp_path)

    assert summary.excluded == 1
    assert summary.fetched == 1
    assert summary.written == 1


def test_dry_run_writes_nothing(tmp_path: Path):
    ids = ["6895"]
    detail_map = {"6895": _load("detail_6895.html")}
    source = CederSource("mainstream", client=_make_client(ids, detail_map))
    summary = run_import(source, tmp_path, dry_run=True)

    assert summary.written == 1
    assert list(tmp_path.rglob("*.md")) == []


def test_limit_caps_processing(tmp_path: Path):
    ids = ["10468", "6895", "6923"]
    detail_map = {
        "10468": _load("detail_10468.html"),
        "6895": _load("detail_6895.html"),
        "6923": _load("detail_6923.html"),
    }
    source = CederSource("mainstream", client=_make_client(ids, detail_map))
    summary = run_import(source, tmp_path, limit=2)

    assert summary.written + summary.skipped_dup == 2
    assert len(list(tmp_path.rglob("*.md"))) == 2


def test_cli_runs_dry(tmp_path: Path, capsys, monkeypatch):
    # Patch the source factory to use mocked HTTP so no network is touched.
    ids = ["6895"]
    detail_map = {"6895": _load("detail_6895.html")}

    import sdimport.cli as cli

    def fake_make_source(args):
        return CederSource("mainstream", client=_make_client(ids, detail_map))

    monkeypatch.setattr(cli, "make_source", fake_make_source)
    rc = cli.main(
        ["--source", "ceder", "--level", "mainstream", "--vault", str(tmp_path), "--dry-run"]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "written=1" in out
    assert list(tmp_path.rglob("*.md")) == []


def test_body_from_separate_ajax_fragment(tmp_path: Path):
    # Main page carries metadata; a stripped page (no body) + AJAX fragment
    # supplies the calls/comment. Mirrors the live site behavior.
    main_no_body = (
        '<div id="pageheader">Static Set \u2794 Resolve</div>'
        '<div class="headercolor">Mainstream - Complete Dance Routine</div>'
        '<a href="https://www.ceder.net/callerdb/viewsingle.php?RecordId=1937">'
        '<span class="text16">Calvin Campbell</span></a>'
        '<span class="red">Easy</span>'
        '<span class="red nobr">*** not validated ***</span>'
    )
    source = CederSource(
        "mainstream",
        client=_make_client(
            ["6895"],
            {"6895": main_no_body},
            choreo_map={"6895": _load("choreo_6895.html")},
        ),
    )
    summary = run_import(source, tmp_path)
    assert summary.written == 1
    md = next(tmp_path.rglob("*-6895.md")).read_text()
    assert "difficulty: easy" in md
    assert "unvalidated: true" in md
    assert "author: Calvin Campbell" in md
    assert "Heads Pass Thru," in md
    assert md.rstrip().endswith("Named Backwater")
    # Abbreviation was derived (not the 'module' fallback).
    assert "module-6895.md" not in [p.name for p in tmp_path.rglob("*.md")]
