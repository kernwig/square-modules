import { test } from "node:test";
import assert from "node:assert/strict";
import { Module } from "./model.ts";
import { discoverProperties, distinctValues } from "./properties.ts";

function mod(fm: Record<string, any>): Module {
  return { path: Math.random().toString(), title: "t", frontmatter: fm, lines: [] };
}

test("discovers boolean keys regardless of true/false mix", () => {
  const mods = [
    mod({ favorite: true, hnh: false }),
    mod({ favorite: false, hnh: true }),
    mod({ favorite: true }),
  ];
  const p = discoverProperties(mods);
  assert.deepEqual(p.booleanKeys, ["favorite", "hnh"]);
});

test("boolean-ish strings count as boolean", () => {
  const mods = [mod({ unvalidated: "true" }), mod({ unvalidated: "false" })];
  const p = discoverProperties(mods);
  assert.ok(p.booleanKeys.includes("unvalidated"));
});

test("a key with any non-boolean value is NOT a boolean key", () => {
  const mods = [mod({ level: "ms" }), mod({ level: "plus" })];
  const p = discoverProperties(mods);
  assert.ok(!p.booleanKeys.includes("level"));
  assert.deepEqual(p.stringValues.get("level"), ["ms", "plus"]);
});

test("distinctValues preserves discovery order", () => {
  const mods = [
    mod({ start: "home" }),
    mod({ start: "lines" }),
    mod({ start: "home" }),
    mod({ start: "box" }),
  ];
  assert.deepEqual(distinctValues(mods, "start"), ["home", "lines", "box"]);
});
