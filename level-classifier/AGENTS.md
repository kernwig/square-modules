# AGENTS.md — level-classifier

Guidance for an agent maintaining this tool in a fresh session. Read
`DESIGN.md` for the full rationale; this file is the operational quick-start.

## What this is

A standalone Python tool (`square-modules/level-classifier/`) that classifies the dance
level (MS/Plus/A1/A2) of Obsidian choreography modules and reconciles their
`level` frontmatter + folder. Independent of `square-modules/sd-choreo-importer`.

## Project facts

- Pure stdlib at runtime; `pytest` is the only dev dependency.
- Python 3; venv at `.venv/` (git-ignored — recreate if missing).
- Package: `levelclassifier/` (`vocab`, `mdfile`, `classifier`, `planner`, `cli`).
- Default vault: `BDP-Obsidian/Square-Modules` (`cli.DEFAULT_VAULT`).
- Call lists are sourced from three PDFs at the **repo root**
  (`New-Mainstream-Program-List-2026-09-01.pdf`,
  `New-Plus-Program-Teaching-Order.pdf`,
  `New-Advanced-List-2026-09-01.pdf`). Extract with `pypdf` if you need to
  re-check the vocabulary against them.

## Setup & test (run from this directory)

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q          # must stay green (23+ tests)
```

## Run

```sh
# Plan only (writes level-report.tsv; no vault changes):
.venv/bin/python -m levelclassifier.cli plan --mode mismatch   # or: fill | all
# Apply an approved/trimmed report (dry-run until --apply):
.venv/bin/python -m levelclassifier.cli apply --report level-report.tsv --apply
```

Modes: `fill` = modules with no level; `mismatch` = set level disagrees with
detection; `all` = both.

## Golden rules

1. **Never modify the vault without the two-step flow.** `plan` → human review
   → `apply --apply`. Don't add a mode that writes during `plan`.
2. **`apply` edits only the `level:` frontmatter line** and moves the file.
   Keep body/comment byte-for-byte intact (`mdfile.rewrite_level`).
3. **Folder moves preserve the sub-path** between level folder and filename,
   including the empty case. Don't regress `planner._relocate`.
4. **Unknown tokens are reported, never auto-applied.** Keep it that way.
5. **Confidence semantics**: `high` = driven by a recognized higher call or a
   fully-recognized MS body; `low` = MS-by-absence with leftover unknowns.

## Most common maintenance task: a call isn't recognized

Symptom: a module is mis-leveled, or a real call shows up in `unknown_tokens`.

1. Find the phrasing in the report's `unknown_tokens` / `deciding_call`.
2. Add the lowercase phrase (and realistic variants/synonyms) to the correct
   set in `vocab.py` — `MS_CALLS` / `PLUS_CALLS` / `A1_CALLS` / `A2_CALLS`.
   Put each call in the single level where it is *introduced*.
3. If it's noise (a designator/fraction/direction), add it to the relevant set
   in `NON_CALL_TOKENS` instead.
4. Add a regression test in `tests/test_classifier.py`, then re-run pytest and a
   live `plan` dry-run to confirm no new false positives.

### Matcher gotchas (already fixed — don't reintroduce)

- Strip parentheticals at the **line** level before splitting on commas, else an
  aside like `(with each other, i.e. Slither)` leaks words into the call stream.
- Avoid overly loose phrases: bare `"eight chain"` wrongly matched "Eight Chain
  Down the Line". Prefer the specific call form (`eight chain thru`, numbered).
- `Spin the Top` is MS; `Spin Chain Thru` is Plus. Keep them distinct.
- `See Saw` must not be matched by `Sashay`/`Dosado`. `Circle to a Line` is Plus
  but bare `Circle Left/Right` is MS.

## Validation checklist before finishing a change

- `pytest -q` green.
- `plan --mode mismatch` dry-run over the real vault: inspect each proposed flip
  against the actual file body; confirm no false positives before suggesting
  `apply`.
- Temp report files cleaned up (`level-report.tsv` is git-ignored).
