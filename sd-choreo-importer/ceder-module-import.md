# Implementation Plan — Square Dance Choreography Database + ceder.net Importer

## Problem Statement
Formalize an Obsidian-based database format for square dance choreography modules (so a caller can reference them live), then build a flexible importer that pulls modules from ceder.net's choreo database and writes them as Obsidian markdown files conforming to that format. The importer must be source-pluggable since future sources (JSON, plain text) will be added.

## Requirements
- **Vault layout:** `Square-Modules/<Level>/<Formation-Folder>/<module>.md`, with a `.base` providing Table/List views. Create the `Square-Modules/` folder and its `.base` if they do not yet exist. The existing `SD-Choreo/` folder is kept only as a read-only reference and is not modified.
- **Frontmatter schema (confirmed):**
  - `start` — starting formation slug: `home`, `8chain`, `lines`, `waves`, `box`, plus the Resolve-specific slugs `line-partner` and `box-corner`
  - `end` — ending formation slug (may be blank/omitted if not inferable)
  - `difficulty` — `easy` | `medium` | `hard` (lowercased from ceder) or omitted
  - `trick` — boolean, separate manual label (importer never sets it)
  - `unvalidated` — boolean `true` when ceder shows `*** not validated ***`
  - `beats` — number (auto-extracted from comment when parseable, e.g. "64 steps"/"64 beat"; else omitted). Omit the property entirely when it has no value — never write an empty or null `beats`.
  - `level` — lowercase level: `ms` for Mainstream; other levels = lowercase of ceder's name (`plus`, `a1`, `a2`, `c1`, `c2`, `c3a`, `c3b`, `c4`)
  - `author` — full caller name (optional)
  - `source` — `ceder-<RecordId>` (dedup key; only ceder uses this scheme)
  - **Body** — exact call-sequence text from source, one call per line, trailing spaces trimmed; when a comment exists, append it after a blank separator line.
- **Importer behavior (confirmed):**
  - `POST https://www.ceder.net/choreodb/` with `FindLevel` (default 20=Mainstream), `FindSeqType=-1`, `FindHandle=-1`, `Special=-1`, `FindDifficulty=-1`, `Page=N`, `Style=condensed`. Only level is required/parameterized.
  - Walk ALL pages (200/page; total pages read from the `of N` indicator). Pause between requests (polite delay).
  - For each result, extract `RecordId` from the `ID=xxxx` detail link, fetch `viewsingle.php?RecordId=N`, parse detail page as source of truth.
  - Determine `start`/`end`/folder from the detail page's SeqType via the mapping table below. **Exclude** "Six Couples (Hex)".
  - Dedup: skip if a file with that `source: ceder-<id>` already exists anywhere in the vault.
  - Filename: derive an abbreviation from the calls (≤20 chars), append `-<id>` for uniqueness. The ≤20-char limit applies to the abbreviation portion only, not to any prefix or `-<id>` suffix. Certain SeqTypes also add a fixed filename prefix (see Resolves below).
- **Level is a parameter**, Mainstream default. Format must stay source-agnostic for future importers.

### SeqType → (start, end, folder) mapping
| Ceder SeqType | start | end | Folder | Filename prefix |
|---|---|---|---|---|
| Static Set ➔ Resolve | home | home | Home | |
| Static Set ➔ Zero Line | home | lines | Home | |
| Static Set ➔ Zero Box | home | 8chain | Home | |
| Zero Line ➔ Resolve | line-partner | home | Resolves | PL-Resolve- |
| Zero Line ➔ Zero Line | lines | lines | Lines | |
| Zero Line ➔ Zero Box | lines | 8chain | Lines | |
| Zero Box ➔ Resolve | box-corner | home | Resolves | CB-Resolve- |
| Zero Box ➔ Zero Line | 8chain | lines | 8-Chain | |
| Zero Box ➔ Zero Box | 8chain | 8chain | 8-Chain | |
| Zero (Eight Chain Thru) | 8chain | 8chain | Zeros | |
| Zero (Facing Lines) | lines | lines | Zeros | |
| Zero (Parallel Waves) | waves | waves | Zeros | |
| Zero (Facing Couples) | box | box | Zeros | |
| Singing call (Corner progression) [10] | home | home | Singer-figure | |
| Singing call (R-H Lady progression) [20] | home | home | Singer-figure | |
| Singing break [30] | home | home | Singer-break | |
| Stir the bucket [40] | home | home | Patter-stir | |
| Two Couples (Facing Couples) [190] | home | home | Two-Couples | |
| Six Couples (Rectangle) [170] | home | home | Rectangle | |
| Six Couples (Hex) [180] | — | — | EXCLUDED | |

Rule of thumb: left side of `➔` → start; right side → end; "Resolve" as the right side → end=home. Zero types use the single formation for both start and end.

**Resolves are special.** Only `Zero Line ➔ Resolve` and `Zero Box ➔ Resolve` are remapped out of their usual `Lines`/`8-Chain` folders into a shared `Resolves` folder, with distinct start slugs (`line-partner`, `box-corner`) and fixed filename prefixes (`PL-Resolve-`, `CB-Resolve-`). `Static Set ➔ Resolve` is NOT special — it remains start=home, end=home, folder=Home, no prefix. Resolve filenames are `<prefix><abbrev>-<id>.md` (e.g. `PL-Resolve-<abbrev>-10201.md`), where the ≤20-char limit applies only to `<abbrev>`.

## Background (research findings)
- Confirmed POST endpoint `https://www.ceder.net/choreodb/`, field names, pagination (`Page`, 200 results/page, header shows `1 to 200 of 2404` and `of 13` pages). Pagination also works via GET with repeated `Page` (last one wins).
- Results page: each result is a `div.nopgbr.border3`. Inside is a header `span.footnote` (level in `span.bold`, SeqType text after `--`, optional ` - Complete Dance Routine`, optional `span.red` difficulty) and the detail link `a.pre[href*="viewsingle.php?RecordId="]` whose text is `ID=xxxx`. The `RecordId` is the dedup key → `source: ceder-<id>`.
- Detail page (`viewsingle.php?RecordId=N`):
  - Author: `a[href*="callerdb/viewsingle.php"] span.text16` (full name).
  - Difficulty: `span.red` (`Easy`/`Medium`/`Hard`), absent on some records.
  - Unvalidated: `span.red.nobr` containing `*** not validated ***`.
  - SeqType: `#pageheader` text (e.g. `Static Set ➔ Resolve`) plus `.headercolor` (level, optional ` - Complete Dance Routine`).
  - Choreo body: `div.size3A.bold.mar12`, calls separated by `<br>`.
  - Comment: the `<div>` after the `<hr>` following the choreo div (may contain beats like "64 steps"/"64 beat").
- Existing module `.md` files (7 samples) confirm the schema and body style. New requirement: trim trailing spaces from body lines.

## Proposed Solution
- **Language:** Python 3 with `requests` + `beautifulsoup4` (pinned versions) for robust parsing of ceder's non-semantic markup. Script under `tools/sd-choreo-importer/` in the repo, writing into `BDP-Obsidian/Square-Modules/`.
- **Architecture (pluggable):**
  - `ModuleRecord` dataclass = canonical schema (frontmatter fields + body + comment).
  - `writer.py` — serialize a `ModuleRecord` to an Obsidian `.md`; resolve `<Level>/<Folder>/<name>.md`; dedup by scanning existing `source:` values; generate filenames.
  - `sources/base.py` — `Source` interface yielding `ModuleRecord`s.
  - `sources/ceder.py` — ceder.net source: pagination, detail fetch, parsing, SeqType mapping, beats/comment extraction, polite delay.
  - `cli.py` — `--source ceder --level mainstream` (default); orchestrates fetch→dedup→write; prints summary.
  - Future JSON/plaintext sources implement `Source` and reuse `writer.py` unchanged.
- **Schema docs + template:** `Square-Modules/SCHEMA.md` and `Square-Modules/_Template.md`; the new `Square-Modules/*.base` mirrors the old `SD-Choreo` `.base` Table/List views over `start/end/difficulty/level/beats` (author/source intentionally not shown; `trick`/`unvalidated` not surfaced).

## Task Breakdown

### Task 1: Formalize the schema (docs + template)
Objective: Create the `Square-Modules/` folder (reusing the `SD-Choreo` structure as reference) with a new `.base` that mirrors the old Table/List views. Create `Square-Modules/SCHEMA.md` documenting every frontmatter property (name, type, allowed values, optionality), the folder taxonomy (incl. the special `Resolves` folder), the SeqType→(start,end,folder,prefix) mapping, and body/comment conventions. Create `Square-Modules/_Template.md` with the canonical frontmatter skeleton (omit `beats` when unset — the template must not include an empty `beats`). The `.base` surfaces `start/end/difficulty/level/beats` only (no trick/unvalidated/author/source).
Test: Manually validate the template parses as valid YAML frontmatter in Obsidian; cross-check against the 7 existing `SD-Choreo` sample files.
Demo: Open the vault; show the new `Square-Modules` folder, SCHEMA.md and the template; confirm existing reference files conform.

### Task 2: Canonical model + markdown writer with dedup (TDD)
Objective: Implement `ModuleRecord` and `writer.py` (frontmatter serialization matching existing files: numeric `beats`, omitted-when-empty optionals, booleans only when true; body trailing-space trimming; comment appended after a blank line). Implement vault scan for existing `source:` values and skip-on-conflict. Implement filename generation (≤20-char call abbreviation + `-<id>`, with the SeqType-specific prefix for Resolves applied before the abbreviation).
Test: Unit tests — serialize a known record and byte-compare to an expected `.md`; dedup skips an existing `ceder-1395`; filename abbreviation/length/uniqueness rules, including the `PL-Resolve-`/`CB-Resolve-` prefixes and that the ≤20-char cap applies only to the abbreviation.
Demo: Run writer on a hand-built sample record; show the generated `.md` and a skipped duplicate.

### Task 3: ceder.net detail-page parser (TDD against saved fixtures)
Objective: Save the two real detail-page HTMLs (RecordId 10468 and 6895) as fixtures. Implement parsing of author, difficulty (lowercased), unvalidated flag, SeqType, choreo body (split on `<br>`, trim), and comment; implement SeqType→(start,end,folder) mapping incl. Hex exclusion; implement beats auto-extraction from comment (e.g. `\b(\d+)\s*(?:beat|step)`).
Test: Unit tests asserting parsed `ModuleRecord` for both fixtures (10468 → start=home,end=home,folder=Home,author=Marcel Konath,unvalidated absent; 6895 → difficulty=easy, unvalidated=true, comment appended).
Demo: Run parser on fixtures; print resulting records.

### Task 4: ceder.net search + pagination + detail-link extraction (TDD against saved fixture)
Objective: Save the real results-page HTML as a fixture. Implement building the POST request (level param → FindLevel code), parsing total page count, extracting all `RecordId`s per page, and iterating pages with a configurable polite delay. Isolate network calls behind a small fetch function for test stubbing. Exclude Hex results.
Test: Unit tests — results fixture yields expected RecordIds and correct page-count detection; level→code mapping; delay invoked between pages (mocked).
Demo: Run against the fixture (offline) to list all IDs on page 1; dry-run count.

### Task 5: Wire the CLI end-to-end + source interface
Objective: Implement `sources/base.py` `Source` interface; make `ceder.py` implement it (search → per-ID detail fetch → `ModuleRecord`). Implement `cli.py` with `--source ceder` and `--level mainstream` default, `--dry-run`, `--limit` (for safe testing), and a summary (fetched / written / skipped-dup / excluded). Connect to `writer.py` to produce files in the vault. Pin dependencies; add a README with usage.
Test: Integration test with mocked HTTP (results fixture + detail fixtures) producing real `.md` files in a temp dir; assert counts and that a pre-existing source is skipped.
Demo: `python -m cli --source ceder --level mainstream --limit 5` performs a small real run (with delay), writing a handful of Mainstream modules into `Square-Modules/` and printing the summary.

## Level → FindLevel code reference
Mainstream=20, Plus=30, A1=40, A2=50, C1=60, C2=70, C3A=80, C3B=90, C4=100. `level` frontmatter value: `ms` for Mainstream; otherwise lowercase of the level name.
