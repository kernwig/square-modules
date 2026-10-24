"""Frontmatter parsing + level rewrite behavior."""
from __future__ import annotations

from pathlib import Path

from levelclassifier.mdfile import read_module, rewrite_level

MODULE = """---
start: home
end: home
difficulty: medium
level: ms
author: Andy Shore
source: ceder-260
---
Heads Square Thru 4,
Swing Thru,
Swing & Promenade

---

Some comment with Spin Chain Thru mentioned here.
"""

MODULE_NO_LEVEL = """---
start: home
end: home
source: foo-1
---
Heads Pass Thru,
Swing & Promenade
"""


def test_read_level_and_call_lines(tmp_path: Path):
    p = tmp_path / "m.md"
    p.write_text(MODULE, encoding="utf-8")
    mod = read_module(p)
    assert mod.level == "ms"
    # Comment after the '---' rule is excluded from call lines.
    assert mod.call_lines == [
        "Heads Square Thru 4,",
        "Swing Thru,",
        "Swing & Promenade",
    ]


def test_missing_level_is_none(tmp_path: Path):
    p = tmp_path / "m.md"
    p.write_text(MODULE_NO_LEVEL, encoding="utf-8")
    mod = read_module(p)
    assert mod.level is None


def test_rewrite_level_replaces_in_place():
    out = rewrite_level(MODULE, "plus")
    assert "level: plus" in out
    assert "level: ms" not in out
    # Body and comment untouched.
    assert "Spin Chain Thru mentioned" in out
    assert out.count("---") == MODULE.count("---")


def test_rewrite_inserts_level_when_absent():
    out = rewrite_level(MODULE_NO_LEVEL, "ms")
    assert "level: ms" in out
    # Inserted inside frontmatter, before body.
    head = out.split("---", 2)
    assert "level: ms" in head[1]
