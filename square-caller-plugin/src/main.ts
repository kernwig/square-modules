import {
  App,
  Plugin,
  PluginSettingTab,
  Setting,
} from "obsidian";
import { SquareCallerView, VIEW_TYPE } from "./view.ts";
import {
  SquareCallerSettings,
  defaultSettings,
  normalizeSettings,
} from "./settings.ts";

export default class SquareCallerPlugin extends Plugin {
  settings: SquareCallerSettings = defaultSettings();

  async onload(): Promise<void> {
    await this.loadSettings();

    this.registerView(VIEW_TYPE, (leaf) => new SquareCallerView(leaf, this));

    this.addRibbonIcon("music", "Open Square Caller", () => this.activateView());

    this.addCommand({
      id: "open-square-caller",
      name: "Open Square Caller",
      callback: () => this.activateView(),
    });

    this.addCommand({
      id: "reload-square-caller-modules",
      name: "Reload modules",
      callback: () => this.forEachView((v) => v.reloadModules()),
    });

    this.addSettingTab(new SquareCallerSettingTab(this.app, this));
  }

  onunload(): void {
    // Leaves are detached automatically; nothing else to clean up.
  }

  async activateView(): Promise<void> {
    const { workspace } = this.app;
    let leaf = workspace.getLeavesOfType(VIEW_TYPE)[0];
    if (!leaf) {
      leaf = workspace.getLeaf(true);
      await leaf.setViewState({ type: VIEW_TYPE, active: true });
    }
    workspace.revealLeaf(leaf);
  }

  private forEachView(fn: (v: SquareCallerView) => void): void {
    for (const leaf of this.app.workspace.getLeavesOfType(VIEW_TYPE)) {
      const v = leaf.view;
      if (v instanceof SquareCallerView) fn(v);
    }
  }

  async loadSettings(): Promise<void> {
    this.settings = normalizeSettings(await this.loadData());
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }
}

class SquareCallerSettingTab extends PluginSettingTab {
  constructor(app: App, private plugin: SquareCallerPlugin) {
    super(app, plugin);
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "Square Caller" });

    new Setting(containerEl)
      .setName("Modules folder")
      .setDesc("Vault-relative folder containing the choreography modules.")
      .addText((t) =>
        t
          .setValue(this.plugin.settings.modulesRoot)
          .onChange(async (v) => {
            this.plugin.settings.modulesRoot = v.trim() || "Square-Modules";
            await this.plugin.saveSettings();
          }),
      );
  }
}
