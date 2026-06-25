export type GatewayEventType =
  | "heartbeat"
  | "receipt"
  | "continuity"
  | "drift"
  | "event";

export interface GatewayEvent {
  type: GatewayEventType;
  payload: Record<string, unknown>;
}

type Listener = (event: GatewayEvent) => void;

const listeners = new Set<Listener>();

export const eventsGateway = {
  emit(type: GatewayEventType, payload: Record<string, unknown>): void {
    const event: GatewayEvent = { type, payload };
    for (const listener of listeners) listener(event);
  },

  subscribe(listener: Listener): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
