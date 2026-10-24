from pathlib import Path

import pytest

from sdimport.ceder_client import (
    CederClient,
    extract_page_count,
    extract_record_ids,
    level_to_code,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_level_to_code():
    assert level_to_code("mainstream") == 20
    assert level_to_code("Mainstream") == 20
    assert level_to_code("ms") == 20
    assert level_to_code("plus") == 30
    assert level_to_code("c3a") == 80
    with pytest.raises(ValueError):
        level_to_code("bogus")


def test_extract_record_ids_from_fixture():
    ids = extract_record_ids(_load("results_page1.html"))
    assert ids == ["10468", "6890", "6895", "6950", "6957"]


def test_extract_page_count_from_fixture():
    assert extract_page_count(_load("results_page1.html")) == 13


def test_extract_page_count_defaults_to_one():
    assert extract_page_count("<html><body>no pages here</body></html>") == 1


def test_iter_record_ids_paginates_with_delay():
    page1 = _load("results_page1.html")
    # A tiny second page with two different records.
    page2 = (
        '<a class="pre" href="choreodb/viewsingle.php?RecordId=111">ID=111</a>'
        '<a class="pre" href="choreodb/viewsingle.php?RecordId=222">ID=222</a>'
    )
    calls = []
    sleeps = []

    def fetcher(method, url, data):
        calls.append((method, data["Page"]))
        return page1 if data["Page"] == "1" else page2

    # Force 13 pages via the fixture, but only pages 1 and 2 return distinct
    # records; emulate just 2 pages by trimming the count on a custom fixture.
    # Here we instead rely on the fixture's 'of 13' and stub all pages >1 to page2.
    client = CederClient(delay=0.0, fetcher=fetcher, sleep=lambda s: sleeps.append(s))
    ids = list(client.iter_record_ids("mainstream"))

    # First page ids present, plus the stubbed page-2 ids.
    assert ids[:5] == ["10468", "6890", "6895", "6950", "6957"]
    assert "111" in ids and "222" in ids
    # Page 1 fetched once; a delay slept before each subsequent page (12 times).
    assert calls[0] == ("POST", "1")
    assert len(sleeps) == 12  # pages 2..13


def test_iter_single_page_no_delay():
    single = (
        '<a class="pre" href="choreodb/viewsingle.php?RecordId=5">ID=5</a>'
        '<span class="footnote">page 1 of 1</span>'
    )
    sleeps = []
    client = CederClient(
        delay=1.0, fetcher=lambda m, u, d: single, sleep=lambda s: sleeps.append(s)
    )
    ids = list(client.iter_record_ids("mainstream"))
    assert ids == ["5"]
    assert sleeps == []  # no second page, no sleep


def test_detail_page_uses_fetcher():
    captured = {}

    def fetcher(method, url, data):
        captured["method"] = method
        captured["url"] = url
        captured["data"] = data
        return "<html>ok</html>"

    client = CederClient(fetcher=fetcher)
    assert client.detail_page("10468") == "<html>ok</html>"
    assert captured["method"] == "GET"
    assert captured["data"] == {"RecordId": "10468"}
