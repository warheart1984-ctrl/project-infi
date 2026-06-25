import { z } from "zod";
import { useCockpitStore } from "../state/cockpitStore";
import { useKernelStore } from "../state/kernelStore";
import { useClusterStore } from "../state/clusterStore";
import { useDriftStore } from "../state/driftStore";

const SubsystemStatus = z.enum(["ok", "warn", "error"]);

const BaseEvent = z.object({
  type: z.string(),
  agentId: z.string().nullable(),
  ts: z.number().optional(),
});

const KernelHeartbeat = BaseEvent.extend({
  type: z.literal("kernel.heartbeat"),
  agentId: z.string(),
  payload: z.object({
    invariantEngine: SubsystemStatus,
    constraintEngine: SubsystemStatus,
    continuity: SubsystemStatus,
    ledger: SubsystemStatus,
    pitBand: z.number(),
    continuityAnchorHash: z.string(),
    ledgerPrefixHash: z.string(),
  }),
});

const KernelInvariantViolation = BaseEvent.extend({
  type: z.literal("kernel.invariantViolation"),
  agentId: z.string(),
  payload: z.object({
    invariantId: z.string(),
    message: z.string(),
    actionId: z.string(),
    severity: z.enum(["error", "warn"]),
  }),
});

const KernelReceipt = BaseEvent.extend({
  type: z.literal("kernel.receipt"),
  agentId: z.string(),
  payload: z.object({
    receiptId: z.string(),
    actionId: z.string(),
    invariantsChecked: z.array(z.string()),
    pitBand: z.number(),
    continuityHash: z.string(),
  }),
});

const KernelSnapshot = BaseEvent.extend({
  type: z.literal("kernel.snapshot"),
  agentId: z.string(),
  payload: z.object({
    snapshotId: z.string(),
    hash: z.string(),
    partial: z.boolean(),
  }),
});

const AgentPlan = BaseEvent.extend({
  type: z.literal("agent.plan"),
  agentId: z.string(),
  payload: z.object({
    planId: z.string(),
    steps: z.array(
      z.object({
        id: z.string(),
        description: z.string(),
        status: z.enum(["pending", "running", "done", "error"]).optional(),
      })
    ),
  }),
});

const AgentAction = BaseEvent.extend({
  type: z.literal("agent.action"),
  agentId: z.string(),
  payload: z.object({
    actionId: z.string(),
    stepId: z.string(),
    description: z.string(),
  }),
});

const ClusterHeartbeat = BaseEvent.extend({
  type: z.literal("cluster.heartbeat"),
  agentId: z.null(),
  payload: z.object({
    agents: z.record(
      z.object({
        kernelStatus: SubsystemStatus,
        pitBand: z.number(),
      })
    ),
  }),
});

const ClusterDriftDetected = BaseEvent.extend({
  type: z.literal("cluster.driftDetected"),
  agentId: z.null(),
  payload: z.object({
    driftId: z.string(),
    agents: z.array(z.string()),
    snapshotId: z.string(),
    driftType: z.enum(["ledger", "continuity", "pit", "constraint", "dlap"]),
  }),
});

const ClusterReplayResult = BaseEvent.extend({
  type: z.literal("cluster.replayResult"),
  agentId: z.null(),
  payload: z.object({
    perAgent: z.record(
      z.object({
        snapshots: z.array(
          z.object({
            id: z.string(),
            hash: z.string(),
            state: z.enum(["ok", "drift", "error"]).optional(),
          })
        ),
        receipts: z.array(z.unknown()),
        pitTransitions: z.array(z.unknown()),
      })
    ),
    divergences: z.array(
      z.object({
        id: z.string(),
        type: z.string(),
        snapshotId: z.string(),
        agents: z.array(z.string()),
      })
    ),
  }),
});

const AnyEvent = z.discriminatedUnion("type", [
  KernelHeartbeat,
  KernelInvariantViolation,
  KernelReceipt,
  KernelSnapshot,
  AgentPlan,
  AgentAction,
  ClusterHeartbeat,
  ClusterDriftDetected,
  ClusterReplayResult,
]);

export type GatewayEvent = z.infer<typeof AnyEvent>;

export function handleEvent(raw: unknown): void {
  const parsed = AnyEvent.safeParse(raw);
  if (!parsed.success) {
    console.warn("events-gateway: invalid event", parsed.error);
    return;
  }
  routeEvent(parsed.data);
}

function routeEvent(evt: GatewayEvent): void {
  switch (evt.type) {
    case "kernel.heartbeat":
      handleKernelHeartbeat(evt);
      break;
    case "kernel.invariantViolation":
      handleKernelViolation(evt);
      break;
    case "kernel.receipt":
      handleKernelReceipt(evt);
      break;
    case "kernel.snapshot":
      handleKernelSnapshot(evt);
      break;
    case "agent.plan":
      handleAgentPlan(evt);
      break;
    case "agent.action":
      handleAgentAction(evt);
      break;
    case "cluster.heartbeat":
      handleClusterHeartbeat(evt);
      break;
    case "cluster.driftDetected":
      handleClusterDrift(evt);
      break;
    case "cluster.replayResult":
      handleClusterReplayResult(evt);
      break;
    default: {
      const _exhaustive: never = evt;
      return _exhaustive;
    }
  }
}

function aggregateKernelStatus(
  payload: z.infer<typeof KernelHeartbeat>["payload"]
): "ok" | "warn" | "error" {
  const statuses = [
    payload.invariantEngine,
    payload.constraintEngine,
    payload.continuity,
    payload.ledger,
  ];
  if (statuses.includes("error")) return "error";
  if (statuses.includes("warn")) return "warn";
  return "ok";
}

function handleKernelHeartbeat(evt: z.infer<typeof KernelHeartbeat>): void {
  const { payload, agentId } = evt;
  const kernelActions = useKernelStore.getState().actions;
  const clusterActions = useClusterStore.getState().actions;

  kernelActions.updateHeartbeat(agentId, payload);
  clusterActions.updateAgentKernelStatus(agentId, {
    kernelStatus: aggregateKernelStatus(payload),
    pitBand: payload.pitBand,
  });
}

function handleKernelViolation(evt: z.infer<typeof KernelInvariantViolation>): void {
  const { payload, agentId } = evt;
  useCockpitStore.getState().actions.addViolationFromGateway({
    agentId,
    ...payload,
  });
}

function handleKernelReceipt(evt: z.infer<typeof KernelReceipt>): void {
  const { payload, agentId } = evt;
  const cockpitActions = useCockpitStore.getState().actions;
  const clusterActions = useClusterStore.getState().actions;

  cockpitActions.addReceiptFromGateway({ agentId, ...payload });
  clusterActions.addAgentReceipt(agentId, payload);
}

function handleKernelSnapshot(evt: z.infer<typeof KernelSnapshot>): void {
  const { payload, agentId } = evt;
  const cockpitActions = useCockpitStore.getState().actions;
  const clusterActions = useClusterStore.getState().actions;

  cockpitActions.addSnapshotFromGateway({ agentId, ...payload });
  clusterActions.addAgentSnapshot(agentId, payload);
}

function handleAgentPlan(evt: z.infer<typeof AgentPlan>): void {
  const { payload, agentId } = evt;
  useCockpitStore.getState().actions.setPlanForAgent(agentId, payload);
}

function handleAgentAction(evt: z.infer<typeof AgentAction>): void {
  const { payload, agentId } = evt;
  useCockpitStore.getState().actions.addActionLog({ agentId, ...payload });
}

function handleClusterHeartbeat(evt: z.infer<typeof ClusterHeartbeat>): void {
  useClusterStore.getState().actions.setClusterHeartbeat(evt.payload.agents);
}

function handleClusterDrift(evt: z.infer<typeof ClusterDriftDetected>): void {
  const { payload } = evt;
  const clusterActions = useClusterStore.getState().actions;
  const driftActions = useDriftStore.getState().actions;

  clusterActions.addDriftEvent(payload);
  driftActions.appendDivergence({
    id: payload.driftId,
    type: payload.driftType,
    snapshotId: payload.snapshotId,
    agents: payload.agents,
  });
}

function handleClusterReplayResult(evt: z.infer<typeof ClusterReplayResult>): void {
  const { payload } = evt;
  const driftActions = useDriftStore.getState().actions;
  driftActions.setAgents(
    Object.entries(payload.perAgent).map(([agentId, data]) => ({
      id: agentId,
      snapshots: data.snapshots.map((s) => ({
        id: s.id,
        state: s.state ?? "ok",
      })),
    }))
  );
  driftActions.setDivergences(payload.divergences);
}
