import { test } from "node:test";
import assert from "node:assert/strict";
import { sortFormations, normalizeLevel, normalizeDifficulty } from "./ordering.ts";

test("normalize maps missing/unrecognized values to the unknown entry", () => {
  assert.equal(normalizeLevel("MS"), "ms");
  assert.equal(normalizeLevel("basic"), "unk");
  assert.equal(normalizeLevel(null), "unk");
  assert.equal(normalizeDifficulty("Hard"), "hard");
  assert.equal(normalizeDifficulty(null), "unknown");
  assert.equal(normalizeDifficulty("tricky"), "unknown");
});

test("formations sort in preferred order, unknowns appended", () => {
  const input = ["waves", "box-corner", "home", "8chain", "box", "lines", "line-partner"];
  assert.deepEqual(sortFormations(input), [
    "home",
    "lines",
    "box",
    "8chain",
    "waves",
    "box-corner",
    "line-partner",
  ]);
});

test("non-hyphenated unknowns sort before hyphenated, alphabetical within", () => {
  const input = ["z-sub", "mystery", "a-sub", "another"];
  assert.deepEqual(sortFormations(input), ["another", "mystery", "a-sub", "z-sub"]);
});

test("unknown formation values keep discovery order after known ones", () => {
  const input = ["mystery", "home", "another", "lines"];
  // mystery/another are non-hyphenated unknowns -> alphabetical after known.
  assert.deepEqual(sortFormations(input), ["home", "lines", "another", "mystery"]);
});
