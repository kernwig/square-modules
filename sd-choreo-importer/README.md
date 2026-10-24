# sd-choreo-importer

Imports square dance choreography **modules** into the Obsidian vault at
`BDP-Obsidian/Square-Modules/`, conforming to the format documented in
`BDP-Obsidian/Square-Modules/SCHEMA.md`.

The first (and currently only) source is [ceder.net's choreo
database](https://www.ceder.net/choreodb/). The design is source-pluggable, so
future JSON / plain-text sources can reuse the same writer and schema.

## Setup

```bash
cd tools/sd-choreo-importer
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # runtime + pytest
# or, runtime only:
.venv/bin/pip install -r requirements.txt
```

Pinned dependencies: `requests==2.32.3`, `beautifulsoup4==4.12.3`
(dev adds `pytest==8.3.3`).

## Usage

```bash
# Safe small run (writes ~5 Mainstream modules, 1s delay between pages):
.venv/bin/python -m sdimport.cli --source ceder --level mainstream --limit 5

# Full import of a level (walks all result pages, polite delay):
.venv/bin/python -m sdimport.cli --level plus

# Preview only, write nothing:
.venv/bin/python -m sdimport.cli --level mainstream --dry-run
```

Options:

| Flag | Default | Meaning |
|---|---|---|
| `--source` | `ceder` | Import source. |
| `--level` | `mainstream` | Dance level (`mainstream`, `plus`, `a1`, `a2`, `c1`, `c2`, `c3a`, `c3b`, `c4`). |
| `--vault` | `BDP-Obsidian/Square-Modules` | Target folder. |
| `--delay` | `1.0` | Seconds between ceder page requests (be polite). |
| `--limit` | none | Stop after N records written/skipped (testing). |
| `--dry-run` | off | Parse + report, write nothing. |

The run prints a summary: `fetched / written / skipped_dup / excluded / errors`.

## How it works

1. `CederSource` asks `CederClient` to POST the search form (`FindLevel` only;
   default Mainstream) and walk every result page (200/page), pausing `--delay`
   seconds between pages.
2. For each result it follows the `ID=xxxx` link to the detail page
   (`viewsingle.php?RecordId=N`), which is the source of truth.
3. `parse_detail` builds a canonical `ModuleRecord`: start/end/folder from the
   SeqType mapping, author, difficulty, the `unvalidated` flag, the call body,
   the comment, and auto-extracted `beats` when the comment mentions
   "N steps"/"N beat". `Six Couples (Hex)` is excluded.
4. `VaultWriter` serializes to `<Level>/<Folder>/<prefix><abbrev>-<id>.md`,
   skipping any record whose `source: ceder-<id>` already exists in the vault.

## Dedup & re-runs

Imports are idempotent: a module whose `source` already exists anywhere under
the vault is skipped, so re-running never clobbers earlier imports or
hand-authored files.

## Tests

```bash
.venv/bin/python -m pytest -q
```

Tests run fully offline against saved HTML fixtures in `tests/fixtures/`
(no network access).

## Extending with a new source

Implement a class with a `name` attribute and a
`records(result: SourceResult) -> Iterator[ModuleRecord]` method (see
`sdimport/sources/base.py`), populate `ModuleRecord` fields (including `folder`
and `filename_prefix`), and wire it into `make_source` in `sdimport/cli.py`.
The writer and schema stay unchanged.
