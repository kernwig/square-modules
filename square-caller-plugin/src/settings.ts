/**
 * Persisted settings = the filter state (remembered between sessions) plus the
 * modules-root path. Serialized to the plugin's data.json via Obsidian.
 */

import { FilterState, defaultFilterState } from "./filters.ts";
import { MODULES_ROOT } from "./vault.ts";

export interface SquareCallerSettings {
  modulesRoot: string;
  filters: FilterState;
  /** Filter bar shows every filter (true) or only the short set (false). */
  filtersExpanded: boolean;
}

export function defaultSettings(): SquareCallerSettings {
  return {
    modulesRoot: MODULES_ROOT,
    filters: defaultFilterState(),
    filtersExpanded: false,
  };
}

/** Merge loaded data over defaults so new fields get sane values. */
export function normalizeSettings(data: unknown): SquareCallerSettings {
  const base = defaultSettings();
  if (!data || typeof data !== "object") return base;
  const d = data as Partial<SquareCallerSettings>;
  return {
    modulesRoot: d.modulesRoot ?? base.modulesRoot,
    filtersExpanded:
      typeof d.filtersExpanded === "boolean" ? d.filtersExpanded : base.filtersExpanded,
    filters: {
      ...base.filters,
      ...(d.filters ?? {}),
      author: d.filters?.author ?? base.filters.author,
      singer: d.filters?.singer ?? base.filters.singer,
      search: typeof d.filters?.search === "string" ? d.filters.search : base.filters.search,
      level: { ...base.filters.level, ...(d.filters?.level ?? {}) },
      difficulty: { ...base.filters.difficulty, ...(d.filters?.difficulty ?? {}) },
      booleans: coerceBooleans(d.filters?.booleans),
    },
  };
}

/** Coerce persisted boolean-filter values (may be legacy strings) to booleans. */
function coerceBooleans(raw: unknown): Record<string, boolean> {
  const out: Record<string, boolean> = {};
  if (raw && typeof raw === "object") {
    for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
      out[k] = v === true || v === "true";
    }
  }
  return out;
}
