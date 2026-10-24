"""Plan building + apply (rewrite + move) over a temp vault."""
from __future__ import annotations

from pathlib import Path

from levelclassifier.planner import apply_report, build_plan, write_report

MS_FILE = """---
start: home
level: ms
source: ceder-1
---
Heads Square Thru 4,
Swing Thru,
Swing & Promenade
"""

PLUS_IN_MS_FOLDER = """---
start: home
level: ms
source: ceder-2
---
Heads Eight Chain Thru,
Swing & Promenade
"""

NO_LEVEL = """---
start: home
source: foo-3
---
Heads Spin Chain Thru,
Swing & Promenade
"""


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "Square-Modules"
    (vault / "Mainstream" / "Home").mkdir(parents=True)
    (vault / "Mainstream" / "Home" / "ok-1.md").write_text(MS_FILE, encoding="utf-8")
    (vault / "Mainstream" / "Home" / "flip-2.md").write_text(
        PLUS_IN_MS_FOLDER, encoding="utf-8"
    )
    # A file directly under a level folder (no subfolder) with no level set.
    (vault / "Plus").mkdir(parents=True)
    (vault / "Plus" / "nolevel-3.md").write_text(NO_LEVEL, encoding="utf-8")
    (vault / "_Template.md").write_text("---\nstart: home\n---\n", encoding="utf-8")
    return vault


def test_mismatch_mode_flags_only_disagreements(tmp_path: Path):
    vault = _make_vault(tmp_path)
    rows = build_plan(vault, mode="mismatch")
    # ok-1 agrees (ms==ms) -> not flagged. flip-2 is plus-in-ms -> flagged.
    # nolevel-3 has no level -> not a mismatch.
    assert len(rows) == 1
    r = rows[0]
    assert r.path.name == "flip-2.md"
    assert r.detected_level == "plus"
    # Move preserves the sub-path under the new level folder.
    assert r.new_path == vault / "Plus" / "Home" / "flip-2.md"


def test_fill_mode_targets_only_missing_level(tmp_path: Path):
    vault = _make_vault(tmp_path)
    rows = build_plan(vault, mode="fill")
    assert len(rows) == 1
    r = rows[0]
    assert r.path.name == "nolevel-3.md"
    assert r.detected_level == "plus"
    # File was directly under Plus/ already and detects plus -> stays in place.
    assert r.new_path == vault / "Plus" / "nolevel-3.md"


def test_template_is_skipped(tmp_path: Path):
    vault = _make_vault(tmp_path)
    rows = build_plan(vault, mode="all")
    assert all(r.path.name != "_Template.md" for r in rows)


def test_apply_rewrites_and_moves(tmp_path: Path):
    vault = _make_vault(tmp_path)
    rows = build_plan(vault, mode="mismatch")
    report = tmp_path / "report.tsv"
    write_report(rows, vault, report)

    res = apply_report(report, vault, dry_run=False)
    assert res.changed == 1
    assert res.moved == 1

    moved = vault / "Plus" / "Home" / "flip-2.md"
    assert moved.exists()
    assert not (vault / "Mainstream" / "Home" / "flip-2.md").exists()
    assert "level: plus" in moved.read_text(encoding="utf-8")


def test_apply_dry_run_makes_no_changes(tmp_path: Path):
    vault = _make_vault(tmp_path)
    rows = build_plan(vault, mode="mismatch")
    report = tmp_path / "report.tsv"
    write_report(rows, vault, report)

    res = apply_report(report, vault, dry_run=True)
    assert res.changed == 1  # counted, but...
    # ...file not actually moved or modified.
    assert (vault / "Mainstream" / "Home" / "flip-2.md").exists()
    assert "level: ms" in (vault / "Mainstream" / "Home" / "flip-2.md").read_text(
        encoding="utf-8"
    )
