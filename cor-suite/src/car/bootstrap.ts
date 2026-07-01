import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import fg from "fast-glob";
import { REPO_ROOT, COR_SUITE_PATHS } from "../paths.js";
import type { CarArtifact, CarArtifactKind, CarRegistry } from "../types/car.js";
import { REQUIREMENT_NAMESPACES, resolveNamespace } from "../cor/requirement-map.js";
import { saveCarRegistry } from "./registry.js";

const IGNORE = [
  "**/node_modules/**",
  "**/.venv/**",
  "**/.venv-test/**",
  "**/dist/**",
  "**/build/**",
  "**/.runtime/**",
  "**/.cursor/**",
  "**/.git/**",
  "**/cor-suite/out/**",
];

const KIND_PREFIX: Record<CarArtifactKind, string> = {
  requirement: "REQ",
  specification: "SPEC",
  implementation: "IMPL",
  verification: "VER",
  evidence: "EV",
  governance_receipt: "GOVRCPT",
  schema: "SCHEMA",
  registry: "REG",
};

function hashFile(buf: Buffer): string {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

async function hashPath(relPath: string): Promise<string> {
  const abs = path.join(REPO_ROOT, relPath);
  const buf = await fs.promises.readFile(abs);
  return hashFile(buf);
}

function classifyPath(relPath: string): CarArtifactKind | null {
  const p = relPath.replace(/\\/g, "/");
  if (p === "cor-suite/car/car-1.0.json") return "registry";
  if (p.startsWith("cor-suite/spec/") && p.endsWith(".json")) return "schema";
  if (p.includes("/evidence/") && /\.(json|yaml|txt)$/.test(p)) return "evidence";
  if (p.includes("/tests/") && p.endsWith(".ts")) return "verification";
  if (p.includes("/docs/") && p.endsWith(".md")) return "specification";
  if (p.includes("/src/types/") && p.endsWith(".ts")) return "specification";
  if (/spec.*\.md$/i.test(p)) return "specification";
  if (p.endsWith(".ts") && (p.includes("/src/") || p.includes("/services/"))) return "implementation";
  return null;
}

async function loadScanCandidates(): Promise<Array<{ path: string; kind: CarArtifactKind; namespace: string; authority: string }>> {
  const patterns = [
    "aaes-os/docs/**/*.md",
    "aaes-os/packages/*/src/types/**/*.ts",
    "**/*spec*.md",
    "aaes-os/packages/*/src/**/*.ts",
    "aaes-os/services/ops-console/**/*.ts",
    "operator-surface/src/**/*.ts",
    "frontend/src/**/*.ts",
    "aaes-os/tests/**/*.ts",
    "operator-surface/tests/**/*.ts",
    "frontend/tests/**/*.ts",
    "**/evidence/*.json",
    "**/evidence/*.yaml",
    "**/evidence/*.txt",
    "cor-suite/spec/**/*.json",
  ];

  const files = await fg(patterns, { cwd: REPO_ROOT, absolute: false, ignore: IGNORE });
  const rows: Array<{ path: string; kind: CarArtifactKind; namespace: string; authority: string }> = [];

  for (const file of files) {
    const rel = file.replace(/\\/g, "/");
    const kind = classifyPath(rel);
    if (!kind || kind === "requirement" || kind === "governance_receipt") continue;
    const ns = resolveNamespace(rel);
    if (!ns) continue;
    rows.push({ path: rel, kind, namespace: ns.namespace, authority: ns.authority });
  }

  return rows;
}

export async function bootstrapCarRegistry(options?: { dryRun?: boolean }): Promise<CarRegistry> {
  const now = new Date().toISOString();
  const requirementStubs: Array<{ namespace: string; authority: string; path: string }> = [];

  for (const row of REQUIREMENT_NAMESPACES) {
    requirementStubs.push({
      namespace: row.namespace,
      authority: row.authority,
      path: `cor-suite/car/requirements/${row.namespace.toLowerCase()}.md`,
    });
  }

  if (!options?.dryRun) {
    for (const stub of requirementStubs) {
      const reqPath = path.join(REPO_ROOT, stub.path);
      fs.mkdirSync(path.dirname(reqPath), { recursive: true });
      if (!fs.existsSync(reqPath)) {
        fs.writeFileSync(
          reqPath,
          `# ${stub.namespace} Core Requirement\n\nCanonical requirement stub for CAR-1.0.\n`,
          "utf8",
        );
      }
    }
  }

  const candidates = await loadScanCandidates();
  const counters = new Map<string, number>();
  const artifacts: CarArtifact[] = [];

  const nextId = (namespace: string, kind: CarArtifactKind): string => {
    const key = `${namespace}:${kind}`;
    const n = (counters.get(key) ?? 0) + 1;
    counters.set(key, n);
    return `${namespace}.${KIND_PREFIX[kind]}-${String(n).padStart(3, "0")}`;
  };

  for (const stub of requirementStubs) {
    const hasArtifacts = candidates.some((c) => c.namespace === stub.namespace);
    if (!hasArtifacts) continue;
    const hash = options?.dryRun
      ? hashFile(Buffer.from(`requirement:${stub.namespace}`, "utf8"))
      : await hashPath(stub.path);
    artifacts.push({
      id: `${stub.namespace}.REQ-001`,
      namespace: stub.namespace,
      kind: "requirement",
      version: "1.0.0",
      status: "active",
      authority: stub.authority,
      schemaRef: "cor-suite/spec/cor-state-vector.schema.json",
      path: stub.path,
      hash,
      lifecycle: { createdAt: now, updatedAt: now },
      links: { related: [] },
    });
  }

  for (const row of candidates) {
    const hash = options?.dryRun ? "dry-run" : await hashPath(row.path);
    artifacts.push({
      id: nextId(row.namespace, row.kind),
      namespace: row.namespace,
      kind: row.kind,
      version: "1.0.0",
      status: "active",
      authority: row.authority,
      path: row.path,
      hash,
      lifecycle: { createdAt: now, updatedAt: now },
    });
  }

  if (!options?.dryRun) {
    artifacts.push({
      id: "COR-SUITE.SCHEMA-CAR",
      namespace: "COR-SUITE",
      kind: "schema",
      version: "1.0.0",
      status: "active",
      authority: "CAR-1.0",
      schemaRef: "cor-suite/spec/car-1.0.schema.json",
      path: "cor-suite/spec/car-1.0.schema.json",
      hash: await hashPath("cor-suite/spec/car-1.0.schema.json"),
      lifecycle: { createdAt: now, updatedAt: now },
    });
  }

  const registry: CarRegistry = {
    carVersion: "1.0.0",
    generatedAt: now,
    artifacts,
  };

  if (!options?.dryRun) {
    saveCarRegistry(registry);
  }

  return registry;
}
