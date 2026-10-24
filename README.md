# square-modules

Tooling for building and using a library of square-dance **choreography
modules** stored as Obsidian markdown files. Each sub-project is independent and
has its own README.

| Sub-project | Language | What it does |
|---|---|---|
| [`sd-choreo-importer`](sd-choreo-importer/) | Python | Imports choreography modules into the vault from external sources (currently [ceder.net](https://www.ceder.net/choreodb/)), conforming to the module schema. |
| [`level-classifier`](level-classifier/) | Python | Detects the program level (Mainstream / Plus / A1 / A2) of a module from the calls in its body, and reconciles its `level` frontmatter and folder. |
| [`square-caller-plugin`](square-caller-plugin/) | TypeScript / Obsidian | A live calling aid that chains modules by exact `end`→`start` formation match on a big, keyboard-driven screen. |

A **module** is a markdown file with `start`, `end`, and `level` frontmatter
(plus optional `difficulty` / `author` / boolean flags) and a call-list body.
`sd-choreo-importer` creates them, `level-classifier` keeps their level correct,
and `square-caller-plugin` consumes them live while calling a dance.

## License

[GPL-3.0](LICENSE).
