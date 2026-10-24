import { test } from "node:test";
import assert from "node:assert/strict";
import { extractBody } from "./body.ts";

const fm = "---\nstart: home\nend: home\n---\n";

test("extracts calls with trailing commas trimmed", () => {
  const text = fm + "Heads Square Thru 4,\nSwing & Promenade\n";
  assert.deepEqual(extractBody(text), ["Heads Square Thru 4", "Swing & Promenade"]);
});

test("preserves the body --- rule and comments, dropping blanks around it", () => {
  const text =
    fm +
    "Heads Square Thru 4,\nSwing & Promenade\n\n---\n\nthis is a note\n- - -\nanother note\n";
  assert.deepEqual(extractBody(text), [
    "Heads Square Thru 4",
    "Swing & Promenade",
    "---",
    "this is a note",
    "- - -",
    "another note",
  ]);
});

test("does not drop content lines adjacent to --- (only blanks)", () => {
  const text = fm + "Call One,\nCall Two\n---\nNote right after rule\n";
  assert.deepEqual(extractBody(text), [
    "Call One",
    "Call Two",
    "---",
    "Note right after rule",
  ]);
});

test("keeps internal blank lines that are NOT adjacent to a rule", () => {
  const text = fm + "Call One,\n\nCall Two\n";
  assert.deepEqual(extractBody(text), ["Call One", "", "Call Two"]);
});

test("removes trailing and leading empty lines", () => {
  const text = fm + "\n\nCall One,\nCall Two\n\n\n";
  assert.deepEqual(extractBody(text), ["Call One", "Call Two"]);
});

test("handles a file with no frontmatter", () => {
  assert.deepEqual(extractBody("Just One Call\n"), ["Just One Call"]);
});
