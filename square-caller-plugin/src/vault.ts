/**
 * Bridges the Obsidian vault to our pure `Module` model. Uses the metadata
 * cache for frontmatter (already parsed, always in sync) and reads the body
 * for the call lines.
 */

import { App, TFile } from "obsidian";
import { Module, FrontmatterValue, isModule } from "./model.ts";
import { extractBody } from "./body.ts";

export { extractBody, isModule };

/** Folder under the vault that holds the modules. */
export const MODULES_ROOT = "Square-Modules";

export async function loadModules(app: App, root = MODULES_ROOT): Promise<Module[]> {
  const files = app.vault.getMarkdownFiles().filter((f) => isModuleFile(f, root));
  const out: Module[] = [];
  for (const f of files) {
    const mod = await readModule(app, f);
    if (mod && isModule(mod)) out.push(mod);
  }
  return out;
}

/**
 * Could this file be a module? A markdown file under the modules root whose
 * name doesn't start with `_` (that skips _Template.md etc.). Whether it really
 * is one depends on its frontmatter (see `isModule`).
 */
export function isModuleFile(f: TFile, root = MODULES_ROOT): boolean {
  return f.extension === "md" && inRoot(f.path, root) && !f.basename.startsWith("_");
}

export function inRoot(path: string, root: string): boolean {
  return path === root || path.startsWith(root + "/");
}

export async function readModule(app: App, file: TFile): Promise<Module | null> {
  const cache = app.metadataCache.getFileCache(file);
  const fm = (cache?.frontmatter ?? {}) as Record<string, FrontmatterValue>;
  const text = await app.vault.cachedRead(file);
  const lines = extractBody(text);
  return {
    path: file.path,
    title: file.basename,
    frontmatter: { ...fm },
    lines,
  };
}

/**
 * Toggle a boolean frontmatter property on a file and persist it. Uses the
 * official frontmatter editor so formatting/other keys are preserved.
 */
export async function toggleBoolean(
  app: App,
  path: string,
  key: string,
): Promise<boolean | null> {
  const file = app.vault.getAbstractFileByPath(path);
  if (!(file instanceof TFile)) return null;
  let result: boolean | null = null;
  await app.fileManager.processFrontMatter(file, (fm) => {
    const cur = fm[key];
    const next = !(cur === true || cur === "true");
    fm[key] = next;
    result = next;
  });
  return result;
}
