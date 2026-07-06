/**
 * Mythic: AAES-OS HTTP admission
 * Engineering: AaesOsHttpServer
 */

import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { DefaultActionEngine } from "./pipeline/action_engine.js";
import { DefaultDeliberationEngine } from "./pipeline/deliberation.js";
import { DefaultInvariantEngine } from "./engines/invariant_engine.js";
import { DefaultPerceptionEngine } from "./pipeline/perception.js";
import { DefaultPlanningEngine } from "./pipeline/planning.js";
import { DefaultPolicyEngine } from "./engines/policy_engine.js";
import { ConsoleAuditLogger } from "./governance/audit_logger.js";
import { InMemoryTraceStore } from "./storage/trace_store.js";
import { DanielModule } from "./modules/daniel/module.js";
import { AAESOrchestrator } from "./orchestrator.js";
import type { AAESRequest } from "./types.js";

const PORT = 8080;

export function createDefaultOrchestrator(): {
  orchestrator: AAESOrchestrator;
  traceStore: InMemoryTraceStore;
} {
  const traceStore = new InMemoryTraceStore();
  const auditLogger = new ConsoleAuditLogger(traceStore);
  const policyEngine = new DefaultPolicyEngine();
  const danielModule = new DanielModule();

  const orchestrator = new AAESOrchestrator({
    invariantEngine: new DefaultInvariantEngine(),
    perceptionEngine: new DefaultPerceptionEngine(),
    deliberationEngine: new DefaultDeliberationEngine(),
    planningEngine: new DefaultPlanningEngine(),
    actionEngine: new DefaultActionEngine({
      policyEngine,
      modules: [danielModule],
      auditLogger,
    }),
    auditLogger,
  });

  return { orchestrator, traceStore };
}

function readJsonBody(req: http.IncomingMessage): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8");
      if (!raw.trim()) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(raw));
      } catch (err) {
        reject(err);
      }
    });
    req.on("error", reject);
  });
}

export function createServer(): http.Server {
  const { orchestrator, traceStore } = createDefaultOrchestrator();

  return http.createServer(async (req, res) => {
    const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);

    if (req.method === "GET" && url.pathname.startsWith("/aaes/trace/")) {
      const traceId = decodeURIComponent(url.pathname.slice("/aaes/trace/".length));
      const record = traceStore.getTrace(traceId);
      res.writeHead(record ? 200 : 404, { "Content-Type": "application/json" });
      res.end(JSON.stringify(record ?? { error: "trace not found" }));
      return;
    }

    if (req.method === "POST" && url.pathname === "/aaes/execute") {
      try {
        const body = (await readJsonBody(req)) as AAESRequest;
        const result = await orchestrator.handle(body);
        res.writeHead(result.ok ? 200 : 400, { "Content-Type": "application/json" });
        res.end(JSON.stringify(result));
      } catch (err) {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(
          JSON.stringify({
            ok: false,
            error: {
              code: "AAES_BAD_REQUEST",
              message: err instanceof Error ? err.message : "invalid request body",
            },
          }),
        );
      }
      return;
    }

    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "not found" }));
  });
}

const isMain =
  typeof process.argv[1] === "string" &&
  path.resolve(fileURLToPath(import.meta.url)) === path.resolve(process.argv[1]);

if (isMain) {
  const server = createServer();
  server.listen(PORT, () => {
    console.log(`AAES-OS listening on http://localhost:${PORT}`);
  });
}
