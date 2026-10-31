/** Ordering for the range filters (level, difficulty). */

/** Level for a module whose `level` is missing or not a recognized level. */
export const UNKNOWN_LEVEL = "unk";
/** Difficulty for a module whose `difficulty` is unset or not recognized. */
export const UNKNOWN_DIFFICULTY = "unknown";

// The unknown value sits last so it can be included or excluded by the range
// like any other value.
export const LEVEL_ORDER = ["ms", "plus", "a1", "a2", "c1", "c2", "c3", "c4", UNKNOWN_LEVEL];
export const DIFFICULTY_ORDER = ["easy", "medium", "hard", UNKNOWN_DIFFICULTY];

/**
 * Map a raw value onto its ordering: a recognized value comes back as the
 * ordering's own (lowercase) spelling; a missing or unrecognized value becomes
 * the last entry of the ordering (the "unknown" value).
 */
export function normalizeTo(order: string[], value: string | null): string {
  const i = value === null ? -1 : order.indexOf(value.trim().toLowerCase());
  return i === -1 ? order[order.length - 1] : order[i];
}

export function normalizeLevel(value: string | null): string {
  return normalizeTo(LEVEL_ORDER, value);
}
export function normalizeDifficulty(value: string | null): string {
  return normalizeTo(DIFFICULTY_ORDER, value);
}

/** Preferred display order for the known single-word formations. Anything not
 *  listed is appended after, with non-hyphenated values before hyphenated ones
 *  (a general rule so subclasses like `x-corner` sort after plain `x`). */
export const FORMATION_ORDER = ["home", "lines", "box", "8chain", "waves"];

/**
 * Sort formation values. Values in FORMATION_ORDER come first in that order.
 * Remaining values follow a general rule: non-hyphenated before hyphenated,
 * alphabetical within each group.
 */
export function sortFormations(values: string[]): string[] {
  const distinct: string[] = [];
  for (const v of values) if (!distinct.includes(v)) distinct.push(v);
  return distinct.sort((a, b) => {
    const ra = rankIn(FORMATION_ORDER, a);
    const rb = rankIn(FORMATION_ORDER, b);
    if (ra !== rb) return ra - rb; // known-list values first, in list order
    if (ra !== Number.POSITIVE_INFINITY) return 0; // both known & equal (n/a)
    // Both unknown: non-hyphenated before hyphenated, then alphabetical.
    const ha = a.includes("-") ? 1 : 0;
    const hb = b.includes("-") ? 1 : 0;
    if (ha !== hb) return ha - hb;
    return a.localeCompare(b);
  });
}

/**
 * Rank of a value in an ordering. Unknown values rank after all known ones,
 * preserving their first-seen discovery order (passed in via `extras`).
 */
export function rankIn(order: string[], value: string | null): number {
  if (value === null) return Number.POSITIVE_INFINITY;
  const i = order.indexOf(value.toLowerCase());
  return i === -1 ? Number.POSITIVE_INFINITY : i;
}

/**
 * Build an ordered list of distinct values from the vault, sorted by a known
 * ordering first and then by discovery order for anything unknown.
 */
export function orderValues(order: string[], seen: Iterable<string>): string[] {
  const discovered: string[] = [];
  for (const v of seen) if (!discovered.includes(v)) discovered.push(v);
  return discovered.sort((a, b) => {
    const ra = rankIn(order, a);
    const rb = rankIn(order, b);
    if (ra !== rb) return ra - rb;
    // both unknown (or equal rank): keep discovery order
    return discovered.indexOf(a) - discovered.indexOf(b);
  });
}

/** A [min,max] inclusive range over an ordering; null bound means open. */
export interface Range {
  min: string | null;
  max: string | null;
}

export function inRange(order: string[], value: string | null, range: Range): boolean {
  if (value === null) return false;
  const r = rankIn(order, value);
  if (r === Number.POSITIVE_INFINITY) return false;
  if (range.min !== null && r < rankIn(order, range.min)) return false;
  if (range.max !== null && r > rankIn(order, range.max)) return false;
  return true;
}
