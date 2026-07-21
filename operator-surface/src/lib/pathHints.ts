const PATH_LIKE =
  /(?:^|[\s"'`(])([A-Za-z]:\\[^\s"'`]+|\.{0,2}\/?[\w./\\-]+\.(?:py|ts|tsx|js|jsx|svelte|json|yaml|yml|md|txt|ps1|cs|html|css|toml|rs|go|java|kt|xml|ini|cfg|env|sh|bat|cmd|sql|graphql|vue|scss|less|wasm|lock|mod|sum)(?:[:\d]+)?)(?=[\s"'`),;]|$)/gi;

const WORKSPACE_REL =
  /(?:^|[\s"'`(])((?:operator_kernel|operator-surface|nova|src|tests|scripts|desktop|docs|governance)(?:\/[\w.-]+)+\.(?:py|ts|tsx|js|jsx|svelte|json|yaml|yml|md|txt|ps1|cs|html|css|toml|rs|go|java|kt|xml|ini|cfg|env|sh|bat|cmd|sql|graphql|vue|scss|less|wasm|lock|mod|sum)(?:[:\d]+)?)(?=[\s"'`),;]|$)/gi;

function normalizePath(raw: string): string {
  let p = raw.trim().replace(/^['"`(]+|['"`),;]+$/g, "");
  p = p.replace(/\\/g, "/");
  if (p.startsWith("./")) p = p.slice(2);
  return p;
}

export function extractFilePaths(text: string): string[] {
  if (!text) return [];
  const found = new Set<string>();
  for (const re of [PATH_LIKE, WORKSPACE_REL]) {
    re.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(text)) !== null) {
      const p = normalizePath(m[1]);
      if (p.length >= 3 && !p.includes("..")) found.add(p);
    }
  }
  return [...found];
}

export function formatToolArgValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
