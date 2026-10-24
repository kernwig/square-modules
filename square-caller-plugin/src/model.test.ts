import { test } from "node:test";
import assert from "node:assert/strict";
import { Module, isModule } from "./model.ts";

function mod(fm: Record<string, unknown>): Module {
  return { path: "p", title: "t", frontmatter: fm as never, lines: [] };
}

test("isModule requires start, end, and level", () => {
  assert.equal(isModule(mod({ start: "home", end: "home", level: "ms" })), true);
});

test("isModule rejects files missing any required key", () => {
  assert.equal(isModule(mod({ start: "home", end: "home" })), false);
  assert.equal(isModule(mod({ start: "home", level: "ms" })), false);
  assert.equal(isModule(mod({ end: "home", level: "ms" })), false);
  assert.equal(isModule(mod({})), false);
});

test("isModule rejects empty-string or null required values", () => {
  assert.equal(isModule(mod({ start: "", end: "home", level: "ms" })), false);
  assert.equal(isModule(mod({ start: "home", end: null, level: "ms" })), false);
});
