# level-classifier

A standalone tool that detects the square-dance **program level**
(Mainstream / Plus / A1 / A2) of an Obsidian choreography-module markdown file
by recognizing the calls in its body, then reconciles the file's `level`
frontmatter and folder with the detected level.

It is independent of `square-modules/sd-choreo-importer` — it only reads/edits the
module `.md` files in the vault.

## Why

The CALLERLAB program lists changed effective **2026-09-01**. Many calls that
used to be Mainstream moved to Plus, so modules imported under the old
definition may now be mis-leveled. Modules from other sources may not specify a
level at all. This tool classifies any module from its call content.

## How classification works

- Each level introduces a set of calls (transcribed from the 2026 CALLERLAB
  lists into `levelclassifier/vocab.py`): MS ⊂ Plus ⊂ A1 ⊂ A2.
- A module's level is the **highest** level of any call found in its body.
  (So a mostly-Mainstream routine containing one Plus call is Plus.)
- The body is tokenized line-by-line; dancer designators, fractions, directions
  and connectors are stripped; the remaining phrases are longest-matched against
  the vocabulary. Parenthetical asides are removed so a call *named* in an
  explanation doesn't count.
- Tokens that can't be classified are reported as `unknown_tokens` (for review)
  and **never** change a level on their own.

### Confidence

- `high` — driven by a recognized Plus/A1/A2 call, or the body was fully
  recognized and stays MS.
- `low` — fell back to MS only because nothing higher was recognized, but
  unrecognized tokens remain (a higher call could be hiding there). Review these.

## Workflow (two-step, auditable)

Nothing is modified until you approve a report.

```sh
# 1. Plan: classify and write a review report (no changes made).
.venv/bin/python -m levelclassifier.cli plan --mode mismatch

# Review level-report.tsv. Delete any rows you reject (e.g. false positives).

# 2. Apply the approved report (dry run first, then --apply).
.venv/bin/python -m levelclassifier.cli apply --report level-report.tsv
.venv/bin/python -m levelclassifier.cli apply --report level-report.tsv --apply
```

### Modes (`plan --mode`)

- `fill` — only modules with **no** `level`: set it to the detected level and
  move the file to that level's folder. (For future imports that omit a level.)
- `mismatch` — modules whose set `level` **disagrees** with detection: listed
  for you to confirm. (This is the MS→Plus re-review for the existing import.)
- `all` — both.

Applying sets the `level:` frontmatter and **moves** the file from
`<CurrentLevel>/…` to `<DetectedLevel>/…`, preserving everything between the
level folder and the filename (including the case of a file sitting directly
under a level folder). Only the `level:` line of the frontmatter is edited; the
body and comment are left byte-for-byte intact.

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # pytest only; runtime is stdlib
.venv/bin/python -m pytest -q
```

## Updating the vocabulary

The call lists live in `levelclassifier/vocab.py`, sourced from:

- `New-Mainstream-Program-List-2026-09-01.pdf`
- `New-Plus-Program-Teaching-Order.pdf`
- `New-Advanced-List-2026-09-01.pdf` (A1 + A2, page 1)

Add phrase variants there as you discover unmatched real-world phrasings (watch
the `unknown_tokens` column of the report for candidates).
