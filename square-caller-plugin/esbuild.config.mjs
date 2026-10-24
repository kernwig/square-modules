import esbuild from "esbuild";
import { copyFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const prod = process.argv[2] === "production";

// Output directly into the Obsidian vault's plugin folder so a reload picks it
// up. Repo root is two levels up from tools/square-caller.
const repoRoot = join(__dirname, "..", "..");
const outDir = join(
  repoRoot,
  "BDP-Obsidian",
  ".obsidian",
  "plugins",
  "square-caller",
);
mkdirSync(outDir, { recursive: true });

const context = await esbuild.context({
  entryPoints: [join(__dirname, "src", "main.ts")],
  bundle: true,
  format: "cjs",
  target: "es2021",
  platform: "browser",
  logLevel: "info",
  sourcemap: prod ? false : "inline",
  minify: prod,
  // Obsidian provides these at runtime; never bundle them.
  external: ["obsidian", "electron", "@codemirror/*", "@lezer/*", "node:*"],
  outfile: join(outDir, "main.js"),
});

function copyStatic() {
  copyFileSync(join(__dirname, "manifest.json"), join(outDir, "manifest.json"));
  copyFileSync(join(__dirname, "styles.css"), join(outDir, "styles.css"));
}

if (prod) {
  await context.rebuild();
  copyStatic();
  await context.dispose();
  console.log("Built to", outDir);
} else {
  await context.rebuild();
  copyStatic();
  await context.watch();
  console.log("Watching; output ->", outDir);
}
