/**
 * The Square Caller view: a big, high-contrast, keyboard-driven 2x2 grid for
 * live calling. All filter controls are built from values discovered in the
 * vault; nothing about the formation/boolean vocabulary is hard-coded.
 */

import { ItemView, WorkspaceLeaf, Notice, Modal, App, TFile, setIcon } from "obsidian";
import { Module, asBoolean, getEnd } from "./model.ts";
import { Engine } from "./engine.ts";
import { FilterState } from "./filters.ts";
import { discoverProperties, distinctValues } from "./properties.ts";
import { LEVEL_ORDER, DIFFICULTY_ORDER, orderValues, sortFormations } from "./ordering.ts";
import { loadModules, toggleBoolean } from "./vault.ts";
import type SquareCallerPlugin from "./main.ts";

export const VIEW_TYPE = "square-caller-view";

/** Letter hotkeys mapping to a formation value. Lowercase sets `start`,
 *  uppercase (shift) sets `end`. */
const FORMATION_HOTKEYS: Record<string, string> = {
  h: "home",
  l: "lines",
  p: "line-partner",
  b: "box",
  c: "box-corner",
};

export class SquareCallerView extends ItemView {
  private engine!: Engine;
  private modules: Module[] = [];
  private startValues: string[] = [];
  private endValues: string[] = [];
  private authorValues: string[] = [];
  private booleanKeys: string[] = [];
  private highlightLine = 0;
  private lastHighlightDir = 1;

  constructor(leaf: WorkspaceLeaf, private plugin: SquareCallerPlugin) {
    super(leaf);
  }

  getViewType(): string {
    return VIEW_TYPE;
  }
  getDisplayText(): string {
    return "Square Caller";
  }
  getIcon(): string {
    return "music";
  }

  async onOpen(): Promise<void> {
    await this.reloadModules();
    // The view's content element must be focusable for keydown to fire on it.
    const root = this.containerEl.children[1] as HTMLElement;
    root.setAttribute("tabindex", "0");
    root.addClass("sqc-focus");
    this.registerDomEvent(root, "keydown", (e) => this.onKey(e));
    // Focus so keys work without a click; also refocus on any click in the view.
    this.registerDomEvent(root, "mousedown", () => root.focus());
    window.setTimeout(() => root.focus(), 0);
  }

  async onClose(): Promise<void> {
    // nothing to tear down
  }

  get filters(): FilterState {
    return this.plugin.settings.filters;
  }

  async reloadModules(): Promise<void> {
    this.modules = await loadModules(this.app, this.plugin.settings.modulesRoot);
    const props = discoverProperties(this.modules);
    this.startValues = sortFormations(distinctValues(this.modules, "start"));
    this.endValues = sortFormations(distinctValues(this.modules, "end"));
    this.authorValues = distinctValues(this.modules, "author").sort((a, b) =>
      a.localeCompare(b),
    );
    this.booleanKeys = props.booleanKeys;
    // Make sure each discovered boolean has an entry in the filter state.
    for (const k of this.booleanKeys) {
      if (!(k in this.filters.booleans)) this.filters.booleans[k] = false;
    }

    // Initialize level/difficulty ranges to full span of discovered values the
    // first time (no "any" bound). Leave user-narrowed ranges untouched.
    this.initRange(this.filters.level, this.levelValues());
    this.initRange(this.filters.difficulty, this.difficultyValues());

    if (this.engine) {
      this.engine.replaceModules(this.modules);
    } else {
      this.engine = new Engine(this.modules, this.filters);
    }
    this.render();
  }

  private async persist(): Promise<void> {
    await this.plugin.saveSettings();
  }

  // ---- keyboard ---------------------------------------------------------

  private async onKey(e: KeyboardEvent): Promise<void> {
    // Don't hijack keys while interacting with a form control (e.g. selects).
    const target = e.target as HTMLElement | null;
    if (target && (target.tagName === "SELECT" || target.tagName === "INPUT")) {
      return;
    }
    const raw = e.key; // preserve case to distinguish shift (end) from start
    const key = raw.toLowerCase();
    let handled = true;

    // Letter formation hotkeys: lowercase sets `start`, uppercase sets `end`.
    // `h`/`H` map to the "home" formation like the others.
    if (FORMATION_HOTKEYS[key]) {
      const value = FORMATION_HOTKEYS[key];
      const isUpper = raw !== raw.toLowerCase() && raw === raw.toUpperCase();
      if (isUpper) {
        if (this.endValues.includes(value)) this.engine.setEnd(value);
        else handled = false;
      } else {
        if (this.startValues.includes(value)) this.engine.setStart(value);
        else handled = false;
      }
      if (handled) {
        e.preventDefault();
        await this.persist();
        this.render();
      }
      return;
    }

    switch (key) {
      case "?":
        this.openHelp();
        break;
      case "arrowup":
        this.moveHighlight(-1);
        break;
      case "arrowdown":
        this.moveHighlight(1);
        break;
      case "arrowleft":
        this.engine.pageNext(-1);
        break;
      case "arrowright":
        this.engine.pageNext(1);
        break;
      case "1":
      case "[":
        this.engine.pickNext(0);
        this.afterSelect();
        break;
      case "2":
      case "]":
        this.engine.pickNext(1);
        this.afterSelect();
        break;
      case "s":
        this.engine.reshuffle();
        new Notice("Re-shuffled");
        break;
      case "a":
        this.engine.toggleAutoFollow();
        new Notice(`Auto-follow ${this.filters.autoFollow ? "on" : "off"}`);
        break;
      case "r":
        // Quick single-key for the common end:home filter.
        if (this.endValues.includes("home")) this.engine.setEnd("home");
        else handled = false;
        break;
      default:
        handled = false;
    }
    if (handled) {
      e.preventDefault();
      await this.persist();
      this.render();
    }
  }

  private afterSelect(): void {
    this.highlightLine = 0;
  }

  private moveHighlight(delta: number): void {
    const sel = this.engine.selected();
    if (!sel) return;
    const n = sel.lines.length;
    if (n === 0) return;
    const dir = delta >= 0 ? 1 : -1;
    this.lastHighlightDir = dir;
    let next = (this.highlightLine + delta + n) % n;
    // Skip over a `---` rule line, continuing in the same direction.
    for (let guard = 0; guard < n && sel.lines[next].trim() === "---"; guard++) {
      next = (next + dir + n) % n;
    }
    this.highlightLine = next;
  }

  // ---- rendering --------------------------------------------------------

  private render(): void {
    const root = this.containerEl.children[1] as HTMLElement;
    const hadFocus = document.activeElement === root || root.contains(document.activeElement);
    root.empty();
    root.addClass("sqc-root");
    this.renderHelpButton(root);
    this.renderFilters(root);
    this.renderGrid(root);
    if (hadFocus) root.focus();
    // Keep the highlighted line visible along with its neighbors (one line of
    // context above and below, when they exist). Scrolling both neighbors into
    // view with block:"nearest" guarantees the highlighted line between them
    // stays visible too.
    const hl = root.querySelector<HTMLElement>(".sqc-line.is-highlight");
    if (hl) {
      const prev = hl.previousElementSibling as HTMLElement | null;
      const next = hl.nextElementSibling as HTMLElement | null;
      // Scroll the neighbor opposite the travel direction first, then the one
      // in the travel direction, so the browser prioritizes revealing where
      // we're heading while still trying to keep the other neighbor visible.
      if (this.lastHighlightDir >= 0) {
        (prev ?? hl).scrollIntoView({ block: "nearest" });
        (next ?? hl).scrollIntoView({ block: "nearest" });
      } else {
        (next ?? hl).scrollIntoView({ block: "nearest" });
        (prev ?? hl).scrollIntoView({ block: "nearest" });
      }
    }
  }

  private renderHelpButton(root: HTMLElement): void {
    const btn = root.createEl("button", {
      cls: "sqc-help-btn",
      text: "?",
      attr: { "aria-label": "Help", title: "Help (?)" },
    });
    btn.onclick = () => this.openHelp();
  }

  private openHelp(): void {
    new HelpModal(this.app).open();
  }

  private renderFilters(root: HTMLElement): void {
    const bar = root.createDiv({ cls: "sqc-filters" });

    this.renderChipStrip(bar, "Start", this.startValues, this.filters.start, (v) => {
      this.engine.setStart(v);
    });
    this.renderChipStrip(bar, "End", this.endValues, this.filters.end, (v) => {
      this.engine.setEnd(v);
    });

    this.renderRange(bar, "Level", LEVEL_ORDER, this.filters.level, this.levelValues());
    this.renderRange(
      bar,
      "Difficulty",
      DIFFICULTY_ORDER,
      this.filters.difficulty,
      this.difficultyValues(),
    );

    this.renderAuthorSelect(bar);
    this.renderBooleanFilters(bar);
    this.renderAutoFollow(bar);
  }

  private levelValues(): string[] {
    return orderValues(LEVEL_ORDER, distinctValues(this.modules, "level"));
  }
  private difficultyValues(): string[] {
    return orderValues(DIFFICULTY_ORDER, distinctValues(this.modules, "difficulty"));
  }

  /** Default an unset range to the full span of available values. */
  private initRange(range: { min: string | null; max: string | null }, available: string[]): void {
    if (available.length === 0) return;
    if (range.min === null) range.min = available[0];
    if (range.max === null) range.max = available[available.length - 1];
  }

  private renderChipStrip(
    parent: HTMLElement,
    label: string,
    values: string[],
    active: string | null,
    onClick: (v: string) => void,
  ): void {
    const wrap = parent.createDiv({ cls: "sqc-strip" });
    wrap.createSpan({ cls: "sqc-strip-label", text: label });
    const chips = wrap.createDiv({ cls: "sqc-chips" });
    for (const v of values) {
      const b = chips.createEl("button", {
        cls: "sqc-chip" + (active === v ? " is-active" : ""),
        text: v,
      });
      b.onclick = async () => {
        onClick(v);
        await this.persist();
        this.render();
      };
    }
  }

  private renderRange(
    parent: HTMLElement,
    label: string,
    order: string[],
    range: { min: string | null; max: string | null },
    available: string[],
  ): void {
    const wrap = parent.createDiv({ cls: "sqc-strip" });
    wrap.createSpan({ cls: "sqc-strip-label", text: label });
    const mk = (which: "min" | "max") => {
      const sel = wrap.createEl("select", { cls: "sqc-select" });
      for (const v of available) sel.createEl("option", { text: v, value: v });
      sel.value = range[which] ?? (available[0] ?? "");
      sel.onchange = async () => {
        range[which] = sel.value;
        await this.persist();
        this.render();
      };
      return sel;
    };
    mk("min");
    wrap.createSpan({ cls: "sqc-range-dash", text: "–" });
    mk("max");
  }

  private renderAuthorSelect(parent: HTMLElement): void {
    const wrap = parent.createDiv({ cls: "sqc-strip" });
    wrap.createSpan({ cls: "sqc-strip-label", text: "Author" });
    const sel = wrap.createEl("select", { cls: "sqc-select sqc-author" });
    sel.createEl("option", { text: "any author", value: "" });
    for (const a of this.authorValues) sel.createEl("option", { text: a, value: a });
    sel.value = this.filters.author ?? "";
    sel.onchange = async () => {
      this.filters.author = sel.value === "" ? null : sel.value;
      await this.persist();
      this.render();
    };
  }

  private renderBooleanFilters(parent: HTMLElement): void {
    if (this.booleanKeys.length === 0) return;
    const wrap = parent.createDiv({ cls: "sqc-strip" });
    wrap.createSpan({ cls: "sqc-strip-label", text: "Flags" });
    const chips = wrap.createDiv({ cls: "sqc-chips" });
    for (const key of this.booleanKeys) {
      const on = this.filters.booleans[key] === true;
      const b = chips.createEl("button", {
        cls: "sqc-chip sqc-flag" + (on ? " is-on" : ""),
        text: key,
      });
      b.onclick = async () => {
        this.filters.booleans[key] = !on;
        await this.persist();
        this.render();
      };
    }
  }

  private renderAutoFollow(parent: HTMLElement): void {
    const wrap = parent.createDiv({ cls: "sqc-strip" });
    const b = wrap.createEl("button", {
      cls: "sqc-chip sqc-autofollow" + (this.filters.autoFollow ? " is-active" : ""),
      text: `Auto-follow: ${this.filters.autoFollow ? "on" : "off"}`,
    });
    b.onclick = async () => {
      this.engine.toggleAutoFollow();
      await this.persist();
      this.render();
    };
    const shuf = wrap.createEl("button", { cls: "sqc-chip sqc-shuffle", text: "Shuffle" });
    shuf.onclick = async () => {
      this.engine.reshuffle();
      this.render();
    };
  }

  private renderGrid(root: HTMLElement): void {
    const snap = this.engine.snapshot();
    const grid = root.createDiv({ cls: "sqc-grid" });

    // Top row: selected + alternative.
    const top = grid.createDiv({ cls: "sqc-row sqc-top" });
    this.renderCard(top, snap.top[0], 0 === snap.selectedIndex, true, 0);
    this.renderCard(top, snap.top[1], 1 === snap.selectedIndex, true, 1);

    // Bottom row: the two next options.
    const bottom = grid.createDiv({ cls: "sqc-row sqc-bottom" });
    this.renderNextCard(bottom, snap.next[0], 0);
    this.renderNextCard(bottom, snap.next[1], 1);

    const pager = root.createDiv({ cls: "sqc-pager" });
    const pages = Math.max(1, Math.ceil(snap.nextTotal / 2));
    pager.createSpan({
      text: `next options ${snap.nextTotal === 0 ? 0 : snap.nextPage + 1}/${pages}  (${snap.nextTotal} match)`,
    });
  }

  private renderCard(
    parent: HTMLElement,
    m: Module | null,
    isSelected: boolean,
    isTop: boolean,
    topIndex?: 0 | 1,
  ): void {
    const card = parent.createDiv({
      cls:
        "sqc-card" +
        (isSelected ? " is-selected" : "") +
        (m ? "" : " is-empty") +
        (m && isTop && !isSelected ? " sqc-selectable" : ""),
    });
    if (!m) {
      card.createDiv({ cls: "sqc-card-empty", text: "—" });
      return;
    }
    this.renderTitle(card, m);
    this.renderProps(card, m);
    const body = card.createDiv({ cls: "sqc-card-body" });
    m.lines.forEach((line, i) => {
      const highlighted = isSelected && isTop && i === this.highlightLine;
      let cls = "sqc-line";
      if (highlighted) cls += " is-highlight";
      if (line.trim() === "---" || line.trim() === "- - -") cls += " sqc-line-rule";
      if (line.trim() === "") cls += " sqc-line-blank";
      const el = body.createDiv({ cls });
      // Empty lines still need height so the highlighter can rest on them.
      el.setText(line === "" ? "\u00A0" : line);
    });
    // Clicking an unselected top card makes it the selected/calling card.
    if (isTop && !isSelected && topIndex !== undefined) {
      card.onclick = async () => {
        this.engine.selectTop(topIndex);
        this.afterSelect();
        await this.persist();
        this.render();
      };
    }
  }

  private renderNextCard(parent: HTMLElement, m: Module | null, index: 0 | 1): void {
    const card = parent.createDiv({ cls: "sqc-card sqc-next" + (m ? "" : " is-empty") });
    if (!m) {
      card.createDiv({ cls: "sqc-card-empty", text: "no match" });
      return;
    }
    this.renderTitle(card, m);
    this.renderProps(card, m);
    const body = card.createDiv({ cls: "sqc-card-body" });
    for (const line of m.lines) {
      let cls = "sqc-line";
      if (line.trim() === "---" || line.trim() === "- - -") cls += " sqc-line-rule";
      if (line.trim() === "") cls += " sqc-line-blank";
      const el = body.createDiv({ cls });
      el.setText(line === "" ? "\u00A0" : line);
    }
    card.onclick = async () => {
      this.engine.pickNext(index);
      this.afterSelect();
      await this.persist();
      this.render();
    };
  }

  /** Render a card title with a small edit icon that opens the file in a tab. */
  private renderTitle(card: HTMLElement, m: Module): void {
    const titleRow = card.createDiv({ cls: "sqc-card-title" });
    titleRow.createSpan({ cls: "sqc-card-title-text", text: m.title });
    const edit = titleRow.createEl("button", {
      cls: "sqc-card-edit",
      attr: { "aria-label": "Open module in a new tab", title: "Open in new tab" },
    });
    setIcon(edit, "pencil");
    edit.onclick = async (ev) => {
      ev.stopPropagation(); // don't select/pick the card
      const file = this.app.vault.getAbstractFileByPath(m.path);
      if (file instanceof TFile) {
        await this.app.workspace.getLeaf("tab").openFile(file);
      } else {
        new Notice(`Could not open ${m.path}`);
      }
    };
  }

  /** Render the small, clickable property row on a card. */
  private renderProps(card: HTMLElement, m: Module): void {
    const row = card.createDiv({ cls: "sqc-card-props" });
    const flow = `${m.frontmatter["start"] ?? "?"} → ${getEnd(m) ?? "?"}`;
    row.createSpan({ cls: "sqc-prop sqc-prop-flow", text: flow });
    if (m.frontmatter["level"]) {
      row.createSpan({ cls: "sqc-prop", text: String(m.frontmatter["level"]) });
    }
    if (m.frontmatter["difficulty"]) {
      row.createSpan({ cls: "sqc-prop", text: String(m.frontmatter["difficulty"]) });
    }
    // Clickable boolean properties, discovered per key.
    for (const key of this.booleanKeys) {
      const val = asBoolean(m.frontmatter[key]);
      const on = val === true;
      const chip = row.createSpan({
        cls: "sqc-prop sqc-prop-bool" + (on ? " is-on" : " is-off"),
        text: `${key}: ${on ? "✓" : "✗"}`,
      });
      chip.onclick = async (ev) => {
        ev.stopPropagation(); // don't trigger card pick
        const next = await toggleBoolean(this.app, m.path, key);
        if (next !== null) {
          m.frontmatter[key] = next;
          this.render();
        }
      };
    }
  }
}

/** Keyboard shortcut rows, shown in the help modal. */
const SHORTCUTS: [string, string][] = [
  ["↑ / ↓", "Move line highlight in the selected card"],
  ["← / →", "Page through more next-options"],
  ["1 / 2  (or [ / ])", "Pick the left / right next option"],
  ["s", "Re-shuffle the deck"],
  ["a", "Toggle auto-follow"],
  ["h / l / p / b / c", "Set START = home / lines / line-partner / box / box-corner"],
  ["H / L / P / B / C", "Set END = that same formation (shift)"],
  ["r", "Set end:home filter"],
  ["?", "Show this help"],
  ["Esc", "Close this help (or the ✕ in the corner)"],
];

const MOUSE_HELP: [string, string][] = [
  ["Click a next card", "Promote the bottom row and select it"],
  ["Click the other top card", "Make it the selected / calling card"],
  ["Click the ✎ on a title", "Open that module in a new tab"],
  ["Click a flag on a card", "Toggle that flag on/off in the file"],
  ["Start/End chips", "Click to filter; click the active one to clear"],
];

class HelpModal extends Modal {
  constructor(app: App) {
    super(app);
  }

  onOpen(): void {
    const { contentEl, modalEl } = this;
    modalEl.addClass("sqc-help-modal");
    contentEl.empty();

    contentEl.createEl("h2", { text: "Square Caller — Help" });

    this.renderOverview(contentEl);
    this.renderTable(contentEl, "Mouse", MOUSE_HELP);
    this.renderTable(contentEl, "Keyboard", SHORTCUTS);
  }

  private renderOverview(parent: HTMLElement): void {
    parent.createEl("h3", { text: "How it works", cls: "sqc-help-section" });
    const list = parent.createEl("ul", { cls: "sqc-help-overview" });
    const items: [string, string][] = [
      ["Top row", "The module you're calling now plus one alternative."],
      ["Selected card", "The highlighted top card — its calls drive the up/down line highlight."],
      ["Next options", "The bottom two cards: modules matching the current filters. Click one to call it next."],
      ["Filters", "Narrow the options by start/end formation, level and difficulty range, author, and flags."],
      ["Auto-follow", "When on, choosing a module automatically sets the start filter to its end, so the next options chain on."],
      ["Shuffle", "Randomizes the module order so suggestions vary; press again any time for fresh picks."],
    ];
    for (const [term, desc] of items) {
      const li = list.createEl("li");
      li.createEl("strong", { text: term + ": " });
      li.appendText(desc);
    }
  }

  private renderTable(parent: HTMLElement, title: string, rows: [string, string][]): void {
    parent.createEl("h3", { text: title, cls: "sqc-help-section" });
    const table = parent.createEl("table", { cls: "sqc-help-table" });
    for (const [k, desc] of rows) {
      const tr = table.createEl("tr");
      tr.createEl("td", { cls: "sqc-help-key", text: k });
      tr.createEl("td", { cls: "sqc-help-desc", text: desc });
    }
  }

  onClose(): void {
    this.contentEl.empty();
  }
}
