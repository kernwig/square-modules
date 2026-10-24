# Square-Modules — Database Format

This documents the format of the square dance choreography **module** notes that
the importer writes into the Obsidian vault at `BDP-Obsidian/Square-Modules/`.
Each note has YAML frontmatter (queryable by the `.base` views) plus a body
holding the exact call sequence.

The layout is:

```
Square-Modules/<Level>/<Formation-Folder>/<module>.md
```

## Frontmatter properties

| Property | Type | Allowed values | Required | Notes |
|---|---|---|---|---|
| `start` | string (slug) | `home`, `8chain`, `lines`, `waves`, `box`, `line-partner`, `box-corner` | yes | Starting formation. `line-partner`/`box-corner` are used only by the Resolve types. |
| `end` | string (slug) | `home`, `8chain`, `lines`, `waves`, `box` | no | Ending formation. Omit when it cannot be inferred. |
| `difficulty` | string | `easy`, `medium`, `hard` | no | Lowercased from the source. Omit when absent. |
| `trick` | boolean | `true` | no | A manual label for trick/gimmick modules. The importer never sets this. Only present when `true`. |
| `unvalidated` | boolean | `true` | no | Set `true` when the source marks the sequence `*** not validated ***`. Only present when `true`. |
| `beats` | number | integer | no | Beat/step count (e.g. for singing calls). Auto-extracted from the source comment when parseable. **Omit the property entirely when unset — never write an empty or null `beats`.** |
| `level` | string | `ms`, `plus`, `a1`, `a2`, `c1`, `c2`, `c3a`, `c3b`, `c4` | yes | `ms` = Mainstream; other levels are the lowercase of the level name. |
| `author` | string | — | no | Full caller name. Omit when unknown. |
| `source` | string | `ceder-<RecordId>` for ceder imports | no | Provenance / dedup key. Only ceder uses the `ceder-<id>` scheme; future sources may differ. |

### Omit-when-empty rule

Optional properties (`end`, `difficulty`, `trick`, `unvalidated`, `beats`,
`author`, `source`) are left out of the frontmatter entirely when they have no
value. Booleans (`trick`, `unvalidated`) appear only when `true`.

## Base views

`00-Square-Modules.base` provides Table and List views, scoped to this folder
subtree via `file.inFolder("Square-Modules")`.

`unvalidated` is a boolean, which Bases would normally render as an *editable*
checkbox in the table. To keep it read-only (so a caller can't accidentally
toggle a note's validation state while scanning the table live), the Table view
shows a **formula column** instead of the raw property:

```yaml
formulas:
  validate_flag: 'if(unvalidated, "⚠", "✓")'
properties:
  formula.validate_flag:
    displayName: Validate
```

Formula columns are display-only in Bases, so the "Validate" cell shows `✓`
when the module is validated (i.e. `unvalidated` is false or absent) and `⚠`
for unvalidated notes, with no interactive control. The underlying
`unvalidated` frontmatter property remains the source of truth and is still what
the importer writes; the formula only reads it.

## Body

The body is the exact call-sequence text from the source, one call per line,
with trailing whitespace trimmed from each line. When the source carries a
comment (notes, attribution, history), it is appended after the call sequence,
separated by a Markdown horizontal rule (`---`) on its own line (blank line,
`---`, blank line, then the comment).

## Folder taxonomy

Modules are filed by level, then by a formation/type folder:

- `Home` — Static Set starts
- `Lines` — Zero Line starts (except Resolve)
- `8-Chain` — Zero Box starts (except Resolve)
- `Resolves` — the Zero Line/Zero Box → Resolve types (see below)
- `Zeros` — Zero (Eight Chain Thru / Facing Lines / Parallel Waves / Facing Couples)
- `Singer-figure` — singing call figures (corner / r-h lady progression)
- `Singer-break` — singing breaks
- `Patter-stir` — stir the bucket
- `Two-Couples` — two-couple (facing couples)
- `Rectangle` — six couples (rectangle)

## SeqType → (start, end, folder, filename prefix) mapping

| Ceder SeqType | start | end | Folder | Filename prefix |
|---|---|---|---|---|
| Static Set ➔ Resolve | home | home | Home | |
| Static Set ➔ Zero Line | home | lines | Home | |
| Static Set ➔ Zero Box | home | 8chain | Home | |
| Zero Line ➔ Resolve | line-partner | home | Resolves | `PL-Resolve-` |
| Zero Line ➔ Zero Line | lines | lines | Lines | |
| Zero Line ➔ Zero Box | lines | 8chain | Lines | |
| Zero Box ➔ Resolve | box-corner | home | Resolves | `CB-Resolve-` |
| Zero Box ➔ Zero Line | 8chain | lines | 8-Chain | |
| Zero Box ➔ Zero Box | 8chain | 8chain | 8-Chain | |
| Zero (Eight Chain Thru) | 8chain | 8chain | Zeros | |
| Zero (Facing Lines) | lines | lines | Zeros | |
| Zero (Parallel Waves) | waves | waves | Zeros | |
| Zero (Facing Couples) | box | box | Zeros | |
| Singing call (Corner progression) | home | home | Singer-figure | |
| Singing call (R-H Lady progression) | home | home | Singer-figure | |
| Singing break | home | home | Singer-break | |
| Stir the bucket | home | home | Patter-stir | |
| Two Couples (Facing Couples) | home | home | Two-Couples | |
| Six Couples (Rectangle) | home | home | Rectangle | |
| Six Couples (Hex) | — | — | EXCLUDED | |

Rule of thumb: the left side of `➔` is the start, the right side is the end;
`Resolve` as the right side means `end = home`. Zero types use the single
formation for both start and end.

### Resolves are special

Only `Zero Line ➔ Resolve` and `Zero Box ➔ Resolve` are remapped out of their
usual `Lines` / `8-Chain` folders into a shared `Resolves` folder, with distinct
start slugs (`line-partner`, `box-corner`) and fixed filename prefixes
(`PL-Resolve-`, `CB-Resolve-`). `Static Set ➔ Resolve` is **not** special — it
stays `home`/`home`/`Home` with no prefix.

## Filenames

Imported filenames are `<prefix><abbrev>-<id>.md`:

- `<prefix>` — empty except for the Resolve types above.
- `<abbrev>` — a short abbreviation derived from the calls, **≤ 20 characters**
  (the limit applies to the abbreviation only, not the prefix or the `-<id>`
  suffix).
- `<id>` — the source record id, for uniqueness (e.g. `10201`).

Example: `PL-Resolve-SqThru-ST-10201.md`.

Hand-authored notes may use any descriptive filename.
