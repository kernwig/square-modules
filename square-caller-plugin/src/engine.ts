/**
 * The calling-session engine: holds the shuffled deck, the current filter
 * state, the selected module, and the paging position for the "next" row.
 * Pure logic, no Obsidian / DOM. The view renders from `snapshot()` and calls
 * the mutators in response to clicks and keys.
 */

import { Module, getEnd } from "./model.ts";
import { FilterState, candidates } from "./filters.ts";
import { shuffle, mulberry32, randomSeed } from "./shuffle.ts";

export interface GridSnapshot {
  /** Top row: the two options currently promoted (selected + alternative). */
  top: (Module | null)[];
  /** Which top index is the actively-selected card (0 or 1), or -1 if none. */
  selectedIndex: number;
  /** Bottom row: the two "next" options at the current page. */
  next: (Module | null)[];
  /** Total number of matching candidates for the bottom row. */
  nextTotal: number;
  /** Current page offset into the candidate list (in pairs). */
  nextPage: number;
}

export class Engine {
  private deck: Module[];
  private seed: number;
  /** Modules promoted to the top row. */
  private top: (Module | null)[] = [null, null];
  private selectedIndex = -1;
  private nextPage = 0;

  constructor(
    private all: Module[],
    public filters: FilterState,
    seed?: number,
  ) {
    this.seed = seed ?? randomSeed();
    this.deck = shuffle(all, mulberry32(this.seed));
  }

  getSeed(): number {
    return this.seed;
  }

  replaceModules(all: Module[]): void {
    this.all = all;
    this.deck = shuffle(all, mulberry32(this.seed));
    // Re-resolve the top row by path so selection survives a metadata refresh.
    this.top = this.top.map((m) =>
      m ? all.find((x) => x.path === m.path) ?? null : null,
    );
    this.nextPage = 0;
  }

  reshuffle(): void {
    this.seed = randomSeed();
    this.deck = shuffle(this.all, mulberry32(this.seed));
    this.nextPage = 0;
  }

  /** The matching candidates for the bottom "next" row, excluding top cards. */
  private nextCandidates(): Module[] {
    const promoted = new Set(this.top.filter(Boolean).map((m) => (m as Module).path));
    return candidates(this.deck, this.filters).filter((m) => !promoted.has(m.path));
  }

  snapshot(): GridSnapshot {
    const cands = this.nextCandidates();
    const start = this.nextPage * 2;
    return {
      top: [this.top[0], this.top[1]],
      selectedIndex: this.selectedIndex,
      next: [cands[start] ?? null, cands[start + 1] ?? null],
      nextTotal: cands.length,
      nextPage: this.nextPage,
    };
  }

  selected(): Module | null {
    return this.selectedIndex >= 0 ? this.top[this.selectedIndex] : null;
  }

  /** Page the next row by +/-1 page (2 options). Clamps and wraps at ends. */
  pageNext(delta: number): void {
    const total = this.nextCandidates().length;
    const pages = Math.max(1, Math.ceil(total / 2));
    this.nextPage = ((this.nextPage + delta) % pages + pages) % pages;
  }

  /**
   * Promote the bottom row to the top row and select the chosen index.
   * `index` is 0 (left / option A) or 1 (right / option B).
   */
  pickNext(index: 0 | 1): void {
    const snap = this.snapshot();
    const chosen = snap.next[index];
    if (!chosen) return;
    // Whole bottom row moves up as-is; positions carry over.
    this.top = [snap.next[0], snap.next[1]];
    this.selectedIndex = index;
    this.nextPage = 0;
    this.applyAutoFollow(chosen);
  }

  /**
   * Select an existing top-row card (0 or 1) as the active/calling card.
   * Re-applies auto-follow so the next options track the newly selected card.
   */
  selectTop(index: 0 | 1): void {
    const m = this.top[index];
    if (!m) return;
    this.selectedIndex = index;
    this.nextPage = 0;
    this.applyAutoFollow(m);
  }

  /** Directly select a module into the top row (e.g. the first pick of a tip). */
  selectModule(m: Module): void {
    this.top = [m, null];
    this.selectedIndex = 0;
    this.nextPage = 0;
    this.applyAutoFollow(m);
  }

  private applyAutoFollow(m: Module): void {
    if (!this.filters.autoFollow) return;
    const end = getEnd(m);
    if (end !== null) this.filters.start = end;
  }

  /**
   * Override the start filter (keyboard l/p/b/c or clicking a start chip).
   * Does not disturb the autoFollow toggle; it just sets start for the current
   * selection round.
   */
  setStart(value: string | null): void {
    this.filters.start = this.filters.start === value ? null : value;
    this.nextPage = 0;
  }

  setEnd(value: string | null): void {
    this.filters.end = this.filters.end === value ? null : value;
    this.nextPage = 0;
  }

  /** Set the singer filter directly (null = require the property absent). */
  setSinger(value: string | null): void {
    this.filters.singer = value;
    this.nextPage = 0;
  }

  /** Set the call-text search query (empty string = no search). */
  setSearch(query: string): void {
    this.filters.search = query;
    this.nextPage = 0;
  }

  toggleAutoFollow(): boolean {
    this.filters.autoFollow = !this.filters.autoFollow;
    return this.filters.autoFollow;
  }

  clearTop(): void {
    this.top = [null, null];
    this.selectedIndex = -1;
    this.nextPage = 0;
  }
}
