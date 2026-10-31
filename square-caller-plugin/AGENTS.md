# Square Caller — Agent Guide

A live square-dance calling aid, built as an Obsidian plugin. While calling, you
pick a start formation and chain choreography modules by matching one module's
`end` to the next module's `start`, on a big, high-contrast, keyboard-driven
screen.

This file is a guide: rules, decisions, and concepts. **The code is the source
of truth** for exact behavior, and the in-app help modal (the `?` button /
`SHORTCUTS`/`MOUSE_HELP` in `view.ts`) is the source of truth for bindings. Read
the code before changing it; don't treat this document as a spec.

## Working rules

- **Definition of done:** `npm run check` passes — typecheck, tests, and lint
  all green. Nothing is complete otherwise.
- **Node 24** (`.nvmrc`); `npm run build` bundles into the vault plugin folder,
  `npm run dev` watches.
- **Author in ESM; ship CJS.** Source is ESM with explicit `.ts` import
  extensions. The bundle must be CJS because Obsidian's loader requires it —
  that's a host constraint, not a preference.
- **Keep the pure logic pure.** Modules free of Obsidian/DOM imports are
  unit-tested with the Node runner (via esbuild transpile — see `esbuild.test.mjs`).
  When adding logic, prefer putting it in a pure module and testing it. The
  Obsidian-facing view is not unit-tested.
- **Discover, don't hard-code.** Formation values, author values, and the set of
  boolean "flag" properties are all derived from the vault at load. Don't
  reintroduce hard-coded vocabularies.
- **User-facing wording:** call boolean properties "flags," not "booleans."

## Key concepts

- **Module:** a markdown file under the modules folder with `start`, `end`, and
  `level` frontmatter (required — files missing these are ignored), optional
  `difficulty`/`author`/flags, and a call-list body.
- **Chaining is exact.** A module's `end` must equal the next module's `start`
  as exact strings. Formation subclasses (e.g. `line-partner` ⊂ lines,
  `box-corner` ⊂ box) are never auto-follow targets because no `end` equals
  them; they're manual entry points only. Do not loosen this to fuzzy matching.
- **Auto-follow:** when on, selecting a module sets the start filter to its
  `end` so options keep chaining. It changes only the start filter; every other
  filter (including end) stays as the caller set it.
- **Shuffle once, iterate in order.** The deck is shuffled on load / on demand;
  filtering walks that fixed order. This keeps suggestions random without
  per-display RNG; occasional repeats are acceptable.
- **Filters** (start/end/author exact, level/difficulty ranges, flags, a
  `singer` select, and a call-text search) are the real selector of "next"
  candidates. They persist across sessions in `data.json`. The `singer` filter
  defaults to "no", which matches only modules that have no `singer` property.
  Search ANDs whitespace-separated terms, `*` is a within-line wildcard, and
  only call lines (before the `---` rule) are searched.
- **Short vs long filter bar.** The short view always shows Start, End, and
  Auto-follow, plus Author/Singer/Search only while each holds a value (Search
  also while focused, so `/` can reach it). Everything else is long-view only.
  The choice persists as `filtersExpanded` in settings (not in `FilterState`).
- **2×2 grid:** top row is what you're calling plus an alternative; bottom row
  is the two next candidates. Behavior of promotion/selection lives in the
  engine — read it before changing.

## Decisions worth remembering

- Built as a plugin (not Electron) so it reads live vault metadata and writes
  frontmatter through Obsidian's own API (`processFrontMatter`) — no second
  source of truth for file contents.
- Flag filters are a simple on/off (on = require true), not tri-state.
- Level/difficulty ranges default to the full discovered span, not "any."
- Module body may contain a `---` rule followed by freeform comments; these are
  rendered (the highlighter can scroll through them) but the rule is skipped by
  the highlighter, and blank lines are not kept around it.

## Gotchas

- `npm test` runs through esbuild, not `node --experimental-strip-types`,
  because strip-only mode rejects non-erasable TS (e.g. parameter properties).
- A missing flag value counts as `false` in filters.
- The view must stay focusable (`tabindex`) for keyboard handling; keystrokes in
  form controls are intentionally ignored.
