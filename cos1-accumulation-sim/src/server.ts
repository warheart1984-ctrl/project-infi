import express from "express";
import * as fs from "fs";
import * as readline from "readline";
import { JPSSContributionEvent } from "./domain.js";
import { applyEvent } from "./state.js";
import { createGosRouter } from "./gosApi.js";
import { initialWorldRuntime, type WorldRuntime } from "./worldState.js";
import { gameEventToContribution } from "./gosAdapter.js";

async function loadWorldFromLog(filePath: string): Promise<WorldRuntime> {
  let world = initialWorldRuntime();
  const rl = readline.createInterface({
    input: fs.createReadStream(filePath),
    crlfDelay: Infinity,
  });

  for await (const line of rl) {
    if (!line.trim()) continue;
    const raw = JSON.parse(line) as JPSSContributionEvent & {
      actorId?: string;
      type?: string;
      action?: string;
      context?: Record<string, unknown>;
    };

    if (raw.actorId && raw.type) {
      world = {
        ...world,
        kernel: applyEvent(
          world.kernel,
          gameEventToContribution({
            id: raw.id,
            actorId: raw.actorId,
            timestamp: raw.timestamp,
            type: raw.type as "ACTION" | "SYSTEM" | "GOVERNANCE",
            action: raw.action ?? raw.type,
            context: raw.context ?? {},
          }),
        ),
      };
    } else {
      world = {
        ...world,
        kernel: applyEvent(world.kernel, raw as JPSSContributionEvent),
      };
    }
  }
  return world;
}

async function main() {
  const logFile = process.env.COS1_LOG || "events.jsonl";
  let world = await loadWorldFromLog(logFile);

  const app = express();
  app.use(express.json());

  const getWorld = () => world;
  const setWorld = (w: WorldRuntime) => {
    world = w;
  };

  app.use(createGosRouter(getWorld, setWorld));

  app.get("/health", (_req, res) => {
    res.json({
      continuity: world.kernel.continuity,
      eventOrigins: world.kernel.eventOrigins,
      stewardCandidates: world.kernel.stewardCandidates,
      events: world.kernel.events.length,
      activeQuests: world.activeQuestIds,
      pla: world.kernel.continuity.pla,
    });
  });

  app.get("/", (_req, res) => {
    const c = world.kernel.continuity;
    const state = world.kernel;
    const originRows = state.events
      .map(
        (e) =>
          `<li>${e.id} (${e.actor}): <strong>${state.eventOrigins[e.id] ?? "—"}</strong> — ${e.accumulationType}</li>`,
      )
      .join("");
    res.send(`
      <html>
        <body>
          <h1>GOS-1 / CSS-2 World Dashboard</h1>
          <p><em>${c.interpretation}</em> — A(t)=${c.accumulation.value.toFixed(2)}</p>
          <h2>GOS-1 API</h2>
          <ul>
            <li>POST /events</li>
            <li>GET /continuity/health</li>
            <li>POST /world/changes</li>
            <li>GET /world/changes?id=...</li>
            <li>GET /world/history</li>
            <li>GET /world/constitution</li>
            <li>GET /world/quests/active</li>
          </ul>
          <h2>Accumulation</h2>
          <ul>
            <li>PLA: ${c.pla.plaCount} / LA: ${c.la.laCount} / SA: ${c.sa.saCount}</li>
            <li>MAT-3: ${c.mat3} | PLT-1: ${c.plt1}</li>
            <li>K4: ${c.reconstructability.k4Satisfied}</li>
          </ul>
          <h2>PLA Phenomenon Metrics</h2>
          <ul>
            <li>Clustering: ${c.pla.clustering.toFixed(2)}</li>
            <li>Cross-domain recurrence: ${c.pla.crossDomainRecurrence.toFixed(2)}</li>
            <li>Validation survival: ${c.pla.validationSurvival.toFixed(2)}</li>
            <li>Instrumentality index: ${c.pla.instrumentality.toFixed(2)}</li>
            <li>Epistemic profile: ${c.epistemic.profile}</li>
          </ul>
          <h2>Events</h2>
          <ul>${originRows}</ul>
        </body>
      </html>
    `);
  });

  const port = Number(process.env.PORT ?? 3000);
  app.listen(port, () => {
    console.log(`GOS-1 server on http://localhost:${port}`);
  });
}

main();
