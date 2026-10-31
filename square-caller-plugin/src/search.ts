/**
 * Text search over a module's call lines.
 *
 * Query syntax:
 *   - Whitespace-separated terms are ANDed; each term may match anywhere in the
 *     module (on any call line).
 *   - `*` inside a term matches any run of characters within a single line, so
 *     `walk*dodge` finds "Walk and Dodge" and "Walk & Dodge".
 *   - Matching is case-insensitive substring matching.
 *
 * Only call lines are searched: anything after the first `---` rule (freeform
 * comments) is ignored so a comment mentioning a call doesn't produce a hit.
 */

import { Module } from "./model.ts";

/** Compile a query into one regex per term. Empty/blank query => no terms. */
export function compileQuery(query: string): RegExp[] {
  return query
    .trim()
    .split(/\s+/)
    .filter((t) => t !== "" && t.replace(/\*/g, "") !== "")
    .map((term) => {
      const pattern = term
        .split("*")
        .map((part) => part.replace(/[.+?^${}()|[\]\\]/g, "\\$&"))
        .join(".*");
      return new RegExp(pattern, "i");
    });
}

/** The module's call lines: everything before the first `---` rule. */
export function callLines(m: Module): string[] {
  const out: string[] = [];
  for (const line of m.lines) {
    if (line.trim() === "---") break;
    out.push(line);
  }
  return out;
}

/** True when every compiled term matches at least one call line. */
export function matchesSearch(m: Module, terms: RegExp[]): boolean {
  if (terms.length === 0) return true;
  const lines = callLines(m);
  return terms.every((re) => lines.some((line) => re.test(line)));
}
