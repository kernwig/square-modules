# level-classifier — Design

## Purpose

Detect the square-dance program **level** (Mainstream / Plus / A1 / A2) of an
Obsidian choreography-module `.md` file from the calls in its body, then
reconcile the file's `level` frontmatter and its folder with the detected level.

Two problems it solves:
1. The CALLERLAB lists changed effective 2026-09-01; calls that used to be
   Mainstream moved to Plus, so modules imported under the old definition may be
   mis-leveled.
2. Modules from other sources may not declare a level at all.

Standalone: it reads/edits vault `.md` files only. It does **not** import from
`square-modules/sd-choreo-importer`.

## Classification model

Levels are tiered and cumulative: `MS < Plus < A1 < A2` (`vocab.LEVEL_RANK`).
Each level's vocabulary is the set of calls *introduced* at that level.

> A module's level = the **highest** level of any call found in its body.

So a routine of mostly-Mainstream calls containing a single Plus call is Plus.
This generalizes the earlier MS→Plus denylist: the "moved to Plus" calls simply
live in `PLUS_CALLS`.

### Why "highest call wins" (not "all calls MS")

A module is danceable at a program only if every call in it belongs to that
program or below. The limiting call is the highest one present, so the module's
level is that maximum. Detecting MS therefore means proving a negative (nothing
higher appears), which drives the confidence rule below.

## Pipeline

```
vault *.md ──► mdfile.read_module ──► classifier.classify_lines ──► planner.build_plan ──► TSV report
                                                                          │
                                        (user reviews / trims report)     ▼
                                              planner.apply_report ──► rewrite level + move file
```

### Modules

- `vocab.py` — the four call lists (MS/Plus/A1/A2) as lowercase phrase sets,
  plus variant/synonym spellings, plus `NON_CALL_TOKENS` (designators,
  directions, fractions, connectors) that are stripped before matching.
  **This is the file you edit most** when phrasings are missed. Sourced from:
  `New-Mainstream-Program-List-2026-09-01.pdf`,
  `New-Plus-Program-Teaching-Order.pdf`,
  `New-Advanced-List-2026-09-01.pdf` (A1+A2, page 1), all at the repo root.
- `mdfile.py` — self-contained frontmatter parse + in-place `level:` rewrite
  (only that one line changes; body/comment untouched). Owns `LEVEL_FOLDERS`.
- `classifier.py` — the matcher and level decision + confidence.
- `planner.py` — vault scan, plan build, TSV report I/O, apply (rewrite + move).
- `cli.py` — `plan` / `apply` subcommands; `DEFAULT_VAULT` →
  `BDP-Obsidian/Square-Modules`.

## Matching algorithm (classifier.py)

1. For each body line (call lines only — everything before the `---` comment
   rule, via `mdfile`): remove parentheticals **at the line level first** (so a
   comma inside an aside like `(with each other, i.e. Slither)` doesn't leak the
   aside's words), then split on `,` / `;` / `then`.
2. For each resulting phrase, tokenize and do **greedy longest-match** against a
   phrase index sorted longest-first (ties → higher level first). Matched tokens
   are consumed.
3. Leftover tokens not in `NON_CALL_TOKENS` are `unknown_tokens` (reported,
   never used to change a level).
4. Module level = max level over all hits (default `ms` if none).

### Confidence

- `high` — a Plus/A1/A2 call drove the result, **or** the body was fully
  recognized and stays MS.
- `low` — fell back to MS only because nothing higher matched, but unknown
  tokens remain (a higher call could be hiding there).

Low confidence only matters for rows actually being changed; it's a review flag.

## Folder moves (planner._relocate)

Vault layout: `<vault>/<LevelFolder>/<maybe/sub/dirs>/<file>.md`. Apply swaps
**only** the leading `<LevelFolder>` segment to the detected level's folder and
preserves everything after it — including the empty case (a file directly under
a level folder stays directly under the new one). Files not under a recognized
level folder get nested under the detected level folder at their relative
position.

## Safety / workflow

Two-step and auditable; the vault is never touched until you approve a report.

- `plan` writes a TSV (`file, current_level, detected_level, confidence,
  deciding_call, unknown_tokens, mode, new_path`) and makes no changes.
- `apply` is dry-run until `--apply`. Delete rows from the report to skip them.
- `_Template.md`, `_`-prefixed files, and dotfiles are skipped during scan.

## Known limitations

- Vocabulary is hand-curated; novel phrasings surface as `unknown_tokens`
  rather than mis-leveling. Extend `vocab.py` when you see real misses.
- Levels above A2 (C-programs) are out of scope; their calls appear as unknown.
- Abbreviations in bodies (e.g. `R.L.G` for Right & Left Grand) are not
  expanded; they show up as unknown tokens but don't change the level.
- Classification is lexical, not a choreography parser; it recognizes call
  *names*, not formation legality.
