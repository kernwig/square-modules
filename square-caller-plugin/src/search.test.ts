import { test } from "node:test";
import assert from "node:assert/strict";
import { Module } from "./model.ts";
import { compileQuery, matchesSearch, callLines } from "./search.ts";
import { defaultFilterState, candidates } from "./filters.ts";

function mod(path: string, lines: string[]): Module {
  return { path, title: path, frontmatter: { start: "home", end: "home", level: "ms" }, lines };
}

const wad = mod("wad", ["Heads Pass Thru,", "Walk and Dodge,", "Partner Trade"]);
const wad2 = mod("wad2", ["Sides Square Thru,", "Walk & Dodge,", "Bend the Line"]);
const plain = mod("plain", ["Swing Thru,", "Boys Run,", "Ferris Wheel"]);
const inComment = mod("cmt", ["Swing Thru,", "Boys Run", "---", "Try Walk and Dodge instead"]);

const q = (s: string, m: Module) => matchesSearch(m, compileQuery(s));

test("empty or blank query matches everything", () => {
  assert.equal(compileQuery("").length, 0);
  assert.equal(compileQuery("   ").length, 0);
  assert.equal(compileQuery("*").length, 0, "a bare * is not a term");
  assert.ok(q("", plain));
});

test("single word is a case-insensitive substring match", () => {
  assert.ok(q("dodge", wad));
  assert.ok(q("DODGE", wad2));
  assert.ok(!q("dodge", plain));
});

test("space-separated words are ANDed across any lines, any order", () => {
  assert.ok(q("trade walk", wad), "terms on different lines");
  assert.ok(!q("walk ferris", wad), "all terms required");
  assert.ok(q("ferris swing", plain));
});

test("* matches any characters within a single line", () => {
  assert.ok(q("walk*dodge", wad), "Walk and Dodge");
  assert.ok(q("walk*dodge", wad2), "Walk & Dodge");
  assert.ok(!q("pass*dodge", wad), "* does not span lines");
});

test("regex special characters are treated literally", () => {
  const m = mod("frac", ["Touch 1/4,", "Scoot Back (again)"]);
  assert.ok(q("1/4", m));
  assert.ok(q("(again)", m));
  assert.ok(!q("t.uch", m), ". is literal, not any-char");
});

test("comments after the --- rule are not searched", () => {
  assert.deepEqual(callLines(inComment), ["Swing Thru,", "Boys Run"]);
  assert.ok(!q("dodge", inComment));
  assert.ok(q("swing", inComment));
});

test("search combines with the other filters via candidates()", () => {
  const f = defaultFilterState();
  f.search = "walk*dodge";
  const paths = candidates([wad, wad2, plain, inComment], f).map((m) => m.path).sort();
  assert.deepEqual(paths, ["wad", "wad2"]);
});
