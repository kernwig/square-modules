/**
 * Transpile the unit tests (and their imports) to a temp dir, then run them
 * with the Node test runner. Using esbuild avoids Node's strip-only TS subset
 * limitations (e.g. parameter properties) while keeping a single build tool.
 */
import esbuild from "esbuild";
import { globSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outdir = join(__dirname, ".test-build");
const tests = globSync("src/*.test.ts", { cwd: __dirname }).map((p) =>
  join(__dirname, p),
);

await esbuild.build({
  entryPoints: tests,
  outdir,
  bundle: true,
  format: "esm",
  platform: "node",
  target: "node24",
  sourcemap: "inline",
  logLevel: "info",
  // `obsidian` is only imported by non-test modules; tests don't pull it in,
  // but mark external defensively so a stray import won't break the build.
  external: ["obsidian", "node:*"],
});

const builtTests = globSync("*.test.js", { cwd: outdir }).map((p) =>
  join(outdir, p),
);

const res = spawnSync(
  process.execPath,
  ["--test", ...builtTests],
  { stdio: "inherit" },
);
process.exit(res.status ?? 1);
