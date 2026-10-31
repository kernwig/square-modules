/**
 * Filter state and the matching logic that turns the shuffled module list into
 * the ordered list of candidates for the "next" slots.
 */

import { Module, getStart, getLevel, getDifficulty, asBoolean } from "./model.ts";
import { LEVEL_ORDER, DIFFICULTY_ORDER, Range, inRange } from "./ordering.ts";
import { compileQuery, matchesSearch } from "./search.ts";

/**
 * Boolean property filter. `true` = require the property to be true; `false` =
 * no constraint (property ignored). Rendered as a color-coded on/off chip.
 */
export type BoolFilter = boolean;

export interface FilterState {
  /** Exact-match start formation, or null for "any start". */
  start: string | null;
  /** Exact-match end formation filter, or null for "any end". */
  end: string | null;
  /** Exact-match author filter, or null for "any author". */
  author: string | null;
  /**
   * Singer filter. `null` (the default) matches only modules that do NOT have
   * the `singer` property; a string matches modules whose `singer` equals it.
   */
  singer: string | null;
  /** Call-text search query (see search.ts); empty = no constraint. */
  search: string;
  level: Range;
  difficulty: Range;
  /** Per-boolean-key filter; true = require true, false/absent = no filter. */
  booleans: Record<string, BoolFilter>;
  /** When true, selecting a module advances `start` to that module's `end`. */
  autoFollow: boolean;
}

export function defaultFilterState(): FilterState {
  return {
    start: null,
    end: null,
    author: null,
    singer: null,
    search: "",
    level: { min: null, max: null },
    difficulty: { min: null, max: null },
    booleans: {},
    autoFollow: true,
  };
}

/**
 * Does a module satisfy every active filter? `terms` is the pre-compiled search
 * query; pass it when matching many modules to avoid recompiling per module.
 */
export function matches(
  m: Module,
  f: FilterState,
  terms: RegExp[] = compileQuery(f.search),
): boolean {
  if (f.start !== null && getStart(m) !== f.start) return false;
  if (!matchesSearch(m, terms)) return false;

  if (f.author !== null) {
    const author = m.frontmatter["author"];
    if (typeof author !== "string" || author !== f.author) return false;
  }

  // The `end` filter is an exact match against the module's own end.
  if (f.end !== null) {
    const end = m.frontmatter["end"];
    if (typeof end !== "string" || end !== f.end) return false;
  }

  // Singer filter. Default (null) requires the `singer` property to be absent;
  // a chosen value requires an exact match.
  {
    const singer = m.frontmatter["singer"];
    const present = singer !== undefined && singer !== null && String(singer) !== "";
    if (f.singer === null) {
      if (present) return false;
    } else {
      if (!present || String(singer) !== f.singer) return false;
    }
  }

  if (f.level.min !== null || f.level.max !== null) {
    if (!inRange(LEVEL_ORDER, getLevel(m), f.level)) return false;
  }
  if (f.difficulty.min !== null || f.difficulty.max !== null) {
    if (!inRange(DIFFICULTY_ORDER, getDifficulty(m), f.difficulty)) return false;
  }

  for (const [key, want] of Object.entries(f.booleans)) {
    if (!want) continue; // false = no constraint
    const have = asBoolean(m.frontmatter[key]);
    // Missing boolean property is treated as false.
    const effective = have === null ? false : have;
    if (effective !== true) return false;
  }
  return true;
}

/**
 * Walk the pre-shuffled module list and return every module matching the
 * filters, preserving shuffle order. The caller pages through this for the
 * two "next" slots.
 */
export function candidates(shuffled: Module[], f: FilterState): Module[] {
  const terms = compileQuery(f.search);
  return shuffled.filter((m) => matches(m, f, terms));
}
