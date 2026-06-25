import { useClusterStore } from "../state/clusterStore";
import { useDriftStore } from "../state/driftStore";
import { handleEvent } from "./events-gateway";

const WS_URL = "ws://127.0.0.1:8787/events";

let connected = false;
let inProcessUnsub: (() => void) | null = null;

export function connectClusterBridge(): void {
  if (connected) return;
  connected = true;

  useClusterStore.getState().actions.seedDemoAgents();
  syncDriftFromCluster();

  try {
    const ws = new WebSocket(WS_URL);
    ws.onmessage = (msg) => {
      handleEvent(JSON.parse(msg.data as string));
    };
  } catch {
    /* WebSocket unavailable */
  }

  inProcessUnsub = subscribeInProcessEvents();
}

function syncDriftFromCluster(): void {
  const agents = useClusterStore.getState().agents;
  useDriftStore.getState().actions.syncFromCluster(agents);
}

function subscribeInProcessEvents(): () => void {
  const interval = setInterval(() => syncDriftFromCluster(), 2000);
  return () => clearInterval(interval);
}

export function disconnectClusterBridge(): void {
  inProcessUnsub?.();
  inProcessUnsub = null;
  connected = false;
}
