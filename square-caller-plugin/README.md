# square-caller-plugin

An [Obsidian](https://obsidian.md) plugin: a live **square-dance calling aid**.
While calling at the mic, you pick a start formation and chain choreography
**modules** by matching one module's `end` formation to the next module's
`start`. The UI is a big, high-contrast, keyboard-driven 2×2 grid meant to be
read while standing a couple of feet from a 13" laptop.

It reads the choreography modules in your vault (the same modules produced by
`sd-choreo-importer` and classified by `level-classifier`) directly through
Obsidian's metadata cache — there is no second copy of the data.

## What it does

- **Chains modules by exact formation match.** A module's `end` must equal the
  next module's `start` as an exact string, so the suggested "next" options
  always flow from what you just called.
- **2×2 grid.** The top row is the module you're calling plus an alternative;
  the bottom row is the two next candidates. Selecting a bottom card promotes it
  to the top.
- **Auto-follow (toggle).** When on, selecting a module moves the start filter
  to that module's `end` so options keep chaining automatically.
- **Discovered, filterable properties.** Start/end formations, authors, level
  and difficulty ranges, a `singer` select, and boolean "flag" properties (e.g.
  favorite, hnh) are all discovered from the vault at load — nothing is
  hard-coded. The `singer` filter defaults to "no", which matches modules that
  have no `singer` property.
- **Call search.** Type words to find modules whose calls contain all of them
  (any order); `*` matches anything within a line, e.g. `walk*dodge`.
- **Keyboard-first.** Shuffle, formation selection, option paging, and
  line-by-line highlight scrolling all have shortcuts. Press `?` in the view (or
  click the `?` button) for the full list.
- **Remembers filters** across sessions.

A **module** is a markdown file under the configured modules folder with `start`,
`end`, and `level` frontmatter (required — files missing these are ignored),
optional `difficulty` / `author` / flag properties, and a call-list body.

## Requirements

- [Node 24](.nvmrc)
- An Obsidian vault containing choreography modules (default folder:
  `Square-Modules`, configurable in the plugin settings).

## Setup

```sh
cd square-modules/square-caller-plugin
nvm use            # Node 24, per .nvmrc
npm install
npm run check      # typecheck + tests + lint — must pass
```

## Scripts

| Command | What it does |
|---|---|
| `npm run build` | Typecheck, then bundle the plugin into the vault's plugin folder. |
| `npm run dev` | Rebuild on change (watch mode). |
| `npm run typecheck` | `tsc --noEmit`. |
| `npm test` | Run the unit tests (via esbuild transpile). |
| `npm run lint` | ESLint. |
| `npm run check` | Typecheck + test + lint. **Definition of done.** |

`npm run build` writes `main.js`, `manifest.json`, and `styles.css` into
`BDP-Obsidian/.obsidian/plugins/square-caller/`. To load changes in Obsidian,
toggle the plugin off and on under Community Plugins.

## Architecture

- **Author in ESM, ship CJS.** Source is ESM with explicit `.ts` import
  extensions; the bundle is CJS because Obsidian's loader requires it.
- **Pure logic is Obsidian-free and unit-tested.** `model`, `ordering`,
  `shuffle`, `properties`, `filters`, `engine`, and `body` have no Obsidian/DOM
  imports and carry the test suite. `view.ts` / `main.ts` are the
  Obsidian-facing layer and are not unit-tested.
- Tests run through esbuild (`esbuild.test.mjs`), not
  `node --experimental-strip-types`, because strip-only mode rejects
  non-erasable TypeScript such as parameter properties.

See [`AGENTS.md`](AGENTS.md) for the maintenance guide (rules, decisions, and
concepts). The code is the source of truth for exact behavior, and the in-app
help modal is the source of truth for key bindings.
