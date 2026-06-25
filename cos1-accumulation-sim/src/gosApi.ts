import { Router, type Request, type Response } from "express";
import type { WorldRuntime } from "./worldState.js";
import {
  getActiveQuests,
  getContinuityHealth,
  getWorldHistory,
  ingestGameEvent,
  proposeWorldChange,
} from "./worldState.js";
import type { GameEvent, WorldChangeProposal } from "./wck.js";

export function createGosRouter(getWorld: () => WorldRuntime, setWorld: (w: WorldRuntime) => void): Router {
  const router = Router();

  router.post("/events", (req: Request, res: Response) => {
    const body = req.body as GameEvent;
    if (!body?.id || !body?.actorId || !body?.timestamp) {
      res.status(400).json({ error: "Missing required fields: id, actorId, timestamp" });
      return;
    }
    const world = ingestGameEvent(getWorld(), body);
    setWorld(world);
    res.status(201).json({
      eventId: body.id,
      origin: world.kernel.eventOrigins[body.id] ?? null,
      continuity: getContinuityHealth(world),
    });
  });

  router.get("/continuity/health", (_req: Request, res: Response) => {
    res.json(getContinuityHealth(getWorld()));
  });

  router.post("/world/changes", (req: Request, res: Response) => {
    const proposal = req.body as WorldChangeProposal;
    if (!proposal?.id || !proposal?.description || !proposal?.proposedBy || !proposal?.origin) {
      res.status(400).json({
        error: "Missing required fields: id, description, proposedBy, origin",
      });
      return;
    }
    const world = proposeWorldChange(getWorld(), proposal);
    setWorld(world);
    res.status(201).json(world.worldChanges[proposal.id]);
  });

  router.get("/world/changes", (req: Request, res: Response) => {
    const id = req.query.id as string | undefined;
    const world = getWorld();
    if (id) {
      const change = world.worldChanges[id];
      if (!change) {
        res.status(404).json({ error: "Change not found" });
        return;
      }
      res.json(change);
      return;
    }
    res.json(Object.values(world.worldChanges));
  });

  router.get("/world/history", (req: Request, res: Response) => {
    const status = req.query.status as
      | "VALIDATED"
      | "ROLLED_BACK"
      | "REJECTED"
      | "PROVISIONAL"
      | undefined;
    const world = getWorld();
    if (status) {
      res.json(getWorldHistory(world, status));
      return;
    }
    res.json({
      validated: getWorldHistory(world, "VALIDATED"),
      rolledBack: getWorldHistory(world, "ROLLED_BACK"),
      rejected: getWorldHistory(world, "REJECTED"),
      provisional: getWorldHistory(world, "PROVISIONAL"),
    });
  });

  router.get("/world/constitution", (_req: Request, res: Response) => {
    res.json(getWorld().constitution);
  });

  router.get("/world/players", (_req: Request, res: Response) => {
    res.json(Object.values(getWorld().players));
  });

  router.get("/world/quests/active", (_req: Request, res: Response) => {
    res.json(getActiveQuests(getWorld()));
  });

  router.get("/world/quests/templates", (_req: Request, res: Response) => {
    res.json(getWorld().questTemplates);
  });

  return router;
}
