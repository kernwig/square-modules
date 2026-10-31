/**
 * Property discovery: scan all modules to learn which frontmatter keys exist,
 * which are booleans, and the distinct values of string-valued keys. This is
 * what lets the UI build its filter strips without any hard-coded schema.
 */

import { Module, asBoolean, asString, FrontmatterValue } from "./model.ts";

/** Keys that are modeled explicitly and should not appear as generic chips. */
export const RESERVED_KEYS = new Set([
  "start",
  "end",
  "level",
  "difficulty",
  "author",
  "singer",
]);

export interface DiscoveredProperties {
  /** Distinct values per string-valued key, in discovery order. */
  stringValues: Map<string, string[]>;
  /** Keys that only ever hold boolean (or boolean-ish) values. */
  booleanKeys: string[];
  /** Every key seen, with the count of files that have it. */
  keyCounts: Map<string, number>;
}

export function discoverProperties(modules: Module[]): DiscoveredProperties {
  const stringValues = new Map<string, string[]>();
  const keyCounts = new Map<string, number>();
  // Track, per key, whether every non-null value seen was boolean-ish.
  const booleanOnly = new Map<string, boolean>();
  const hasAnyValue = new Map<string, boolean>();

  for (const m of modules) {
    for (const [key, raw] of Object.entries(m.frontmatter)) {
      keyCounts.set(key, (keyCounts.get(key) ?? 0) + 1);
      const isBool = asBoolean(raw) !== null;
      const prev = booleanOnly.get(key);
      booleanOnly.set(key, prev === undefined ? isBool : prev && isBool);
      if (raw !== null && raw !== undefined) hasAnyValue.set(key, true);

      if (!isBool) {
        const s = asString(raw);
        if (s !== null) addDistinct(stringValues, key, s);
      }
    }
  }

  const booleanKeys: string[] = [];
  for (const [key, onlyBool] of booleanOnly) {
    if (onlyBool && hasAnyValue.get(key)) booleanKeys.push(key);
  }
  booleanKeys.sort();

  return { stringValues, booleanKeys, keyCounts };
}

function addDistinct(map: Map<string, string[]>, key: string, value: string): void {
  let list = map.get(key);
  if (!list) {
    list = [];
    map.set(key, list);
  }
  if (!list.includes(value)) list.push(value);
}

/** Distinct values of a single key across modules, in discovery order. */
export function distinctValues(modules: Module[], key: string): string[] {
  const out: string[] = [];
  for (const m of modules) {
    const s = asString(m.frontmatter[key] as FrontmatterValue | undefined);
    if (s !== null && !out.includes(s)) out.push(s);
  }
  return out;
}
