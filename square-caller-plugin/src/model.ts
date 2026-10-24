/**
 * Core data model for Square Caller. Kept free of any Obsidian imports so the
 * logic (matching, shuffling, filtering) can be unit-tested with `node --test`.
 */

export type FrontmatterValue = string | number | boolean | null;

/** A single choreography module parsed from a vault markdown file. */
export interface Module {
  /** Vault-relative path, unique id for the module. */
  path: string;
  /** Basename without extension, used as the display title. */
  title: string;
  /** Raw frontmatter map (keys lowercased on read is NOT done; keys as authored). */
  frontmatter: Record<string, FrontmatterValue>;
  /** The call body lines below the frontmatter, trimmed, blank lines removed. */
  lines: string[];
}

/** Convenience getters for the well-known properties. */
export function getStart(m: Module): string | null {
  return asString(m.frontmatter["start"]);
}
export function getEnd(m: Module): string | null {
  return asString(m.frontmatter["end"]);
}
export function getLevel(m: Module): string | null {
  return asString(m.frontmatter["level"]);
}
export function getDifficulty(m: Module): string | null {
  return asString(m.frontmatter["difficulty"]);
}

export function asString(v: FrontmatterValue | undefined): string | null {
  if (v === undefined || v === null) return null;
  if (typeof v === "string") return v;
  return String(v);
}

export function asBoolean(v: FrontmatterValue | undefined): boolean | null {
  if (v === true || v === false) return v;
  if (typeof v === "string") {
    const s = v.trim().toLowerCase();
    if (s === "true") return true;
    if (s === "false") return false;
  }
  return null;
}

/** True when the frontmatter value is a boolean (or a boolean-ish string). */
export function isBooleanValue(v: FrontmatterValue | undefined): boolean {
  return asBoolean(v) !== null;
}

/** Required frontmatter keys for a file to count as a module. */
export const REQUIRED_KEYS = ["start", "end", "level"] as const;

/** True when a parsed file has all the required module properties set. */
export function isModule(m: Module): boolean {
  return REQUIRED_KEYS.every((k) => {
    const v = m.frontmatter[k];
    return v !== undefined && v !== null && String(v).trim() !== "";
  });
}
