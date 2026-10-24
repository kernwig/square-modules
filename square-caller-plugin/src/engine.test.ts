import { test } from "node:test";
import assert from "node:assert/strict";
import { Module, getEnd } from "./model.ts";
import { defaultFilterState } from "./filters.ts";
import { Engine } from "./engine.ts";

function mod(path: string, fm: Record<string, any>, lines: string[] = ["Call"]): Module {
  return { path, title: path, frontmatter: fm, lines };
}

const deck: Module[] = [
  mod("a", { start: "home", end: "lines", level: "ms", difficulty: "easy" }),
  mod("b", { start: "lines", end: "home", level: "ms", difficulty: "medium" }),
  mod("c", { start: "lines", end: "8chain", level: "plus", difficulty: "hard" }),
  mod("d", { start: "home", end: "home", level: "ms", difficulty: "easy", favorite: true }),
  mod("e", { start: "box", end: "lines", level: "ms", difficulty: "medium", hnh: true }),
];

test("exact start match only (no subclass leakage)", () => {
  const f = defaultFilterState();
  f.start = "lines";
  const e = new Engine(deck, f, 1);
  const snap = e.snapshot();
  const paths = snap.next.filter(Boolean).map((m) => (m as Module).path).sort();
  assert.deepEqual(paths, ["b", "c"]);
});

test("auto-follow advances start to selected module end", () => {
  const f = defaultFilterState();
  f.start = "home";
  const e = new Engine(deck, f, 1);
  // Pick a home-start module whose end is lines.
  const a = deck.find((m) => m.path === "a")!;
  e.selectModule(a);
  assert.equal(e.filters.start, "lines");
});

test("end:home filter clears when selecting a start:home module", () => {
  const f = defaultFilterState();
  f.end = "home";
  f.start = "home";
  const e = new Engine(deck, f, 1);
  const d = deck.find((m) => m.path === "d")!; // start home, end home
  e.selectModule(d);
  assert.equal(e.filters.end, null, "end:home should be disabled");
  assert.equal(e.filters.start, "home", "auto-follow sets start to end=home");
});

test("pickNext promotes whole bottom row and keeps positions", () => {
  const f = defaultFilterState();
  f.start = "lines";
  const e = new Engine(deck, f, 1);
  const before = e.snapshot().next;
  e.pickNext(0);
  const top = e.snapshot().top;
  assert.deepEqual(
    top.map((m) => (m ? (m as Module).path : null)),
    before.map((m) => (m ? (m as Module).path : null)),
  );
});

test("level range filter (ms..ms excludes plus)", () => {
  const f = defaultFilterState();
  f.level = { min: "ms", max: "ms" };
  f.start = "lines";
  const e = new Engine(deck, f, 1);
  const paths = e.snapshot().next.filter(Boolean).map((m) => (m as Module).path);
  assert.ok(!paths.includes("c"), "plus module c excluded");
  assert.ok(paths.includes("b"));
});

test("boolean filter favorite:true", () => {
  const f = defaultFilterState();
  f.booleans = { favorite: true };
  const e = new Engine(deck, f, 1);
  const paths = e.snapshot().next.filter(Boolean).map((m) => (m as Module).path);
  assert.deepEqual(paths, ["d"]);
});

test("author filter exact match", () => {
  const withAuthors: Module[] = [
    mod("x", { start: "home", end: "home", author: "Andy Shore" }),
    mod("y", { start: "home", end: "home", author: "Kazy Suzuki" }),
  ];
  const f = defaultFilterState();
  f.author = "Andy Shore";
  const e = new Engine(withAuthors, f, 1);
  const paths = e.snapshot().next.filter(Boolean).map((m) => (m as Module).path);
  assert.deepEqual(paths, ["x"]);
});

test("selectTop switches selected card and re-applies auto-follow", () => {
  const f = defaultFilterState();
  f.start = "lines";
  const e = new Engine(deck, f, 1);
  // Promote bottom row to top via pickNext, selecting index 0.
  e.pickNext(0);
  const top = e.snapshot().top;
  // Pick the other top card (index 1), if present.
  if (top[1]) {
    e.selectTop(1);
    assert.equal(e.snapshot().selectedIndex, 1);
    // auto-follow should set start to the newly selected card's end
    assert.equal(e.filters.start, getEnd(top[1] as Module));
  }
});

test("setStart toggles off when same value re-applied", () => {
  const f = defaultFilterState();
  const e = new Engine(deck, f, 1);
  e.setStart("lines");
  assert.equal(e.filters.start, "lines");
  e.setStart("lines");
  assert.equal(e.filters.start, null);
});

test("paging wraps around candidate pages", () => {
  const f = defaultFilterState(); // all 5 match, 3 pages
  const e = new Engine(deck, f, 1);
  assert.equal(e.snapshot().nextPage, 0);
  e.pageNext(-1);
  assert.equal(e.snapshot().nextPage, 2, "wrap to last page");
  e.pageNext(1);
  assert.equal(e.snapshot().nextPage, 0, "wrap back to first");
});
