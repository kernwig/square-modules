/**
 * Pure parsing of a module's call body. Kept free of Obsidian imports so it can
 * be unit-tested with the Node test runner.
 */

/**
 * Return the body lines (after frontmatter). Each line has a trailing comma and
 * surrounding trailing whitespace trimmed. A body may contain a `---` horizontal
 * rule followed by freeform comments; those lines are preserved and rendered.
 * Only leading/trailing empty lines are removed (internal blanks are kept — the
 * highlighter can pass over them, which is just a way to scroll).
 */
export function extractBody(text: string): string[] {
  let body = text;
  if (text.startsWith("---")) {
    const end = text.indexOf("\n---", 3);
    if (end !== -1) {
      const after = text.indexOf("\n", end + 1);
      body = after !== -1 ? text.slice(after + 1) : "";
    }
  }
  const lines = body.split("\n").map((l) => l.replace(/,\s*$/, "").trimEnd());
  while (lines.length > 0 && lines[lines.length - 1].trim() === "") lines.pop();
  while (lines.length > 0 && lines[0].trim() === "") lines.shift();
  // Drop blank lines immediately adjacent to a `---` rule (before and after).
  const isRule = (s: string) => s.trim() === "---";
  const out: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim() === "") {
      const prev = lines[i - 1];
      const next = lines[i + 1];
      if ((prev !== undefined && isRule(prev)) || (next !== undefined && isRule(next))) {
        continue; // skip blank adjacent to a rule
      }
    }
    out.push(line);
  }
  return out;
}
