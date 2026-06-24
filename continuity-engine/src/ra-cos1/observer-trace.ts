import type { Id, ISOTime } from "../css2/types";
import type { Observation } from "../observer-evidence/observation";
import type { ObservationPattern, ProtoThreshold, ThresholdDelta } from "../css2/types";
import type { ObserverProfile } from "../css2/types";

export type ObserverTraceEventType =
  | "observation"
  | "pattern"
  | "proto_threshold"
  | "threshold_delta"
  | "observer_drift"
  | "observer_capture";

export interface ObserverTraceEvent {
  id: Id;
  type: ObserverTraceEventType;
  timestamp: ISOTime;
  actorId: Id;
  payload: unknown;
}

export interface ObserverTraceStore {
  append(event: ObserverTraceEvent): Promise<void>;
  queryByObserver(observerId: Id): Promise<ObserverTraceEvent[]>;
  queryByType(type: ObserverTraceEventType): Promise<ObserverTraceEvent[]>;
  queryByRelatedId(id: Id): Promise<ObserverTraceEvent[]>;
}

export class InMemoryObserverTraceStore implements ObserverTraceStore {
  private events: ObserverTraceEvent[] = [];

  async append(event: ObserverTraceEvent): Promise<void> {
    this.events.push(event);
  }

  async queryByObserver(observerId: Id): Promise<ObserverTraceEvent[]> {
    return this.events.filter((e) => e.actorId === observerId);
  }

  async queryByType(type: ObserverTraceEventType): Promise<ObserverTraceEvent[]> {
    return this.events.filter((e) => e.type === type);
  }

  async queryByRelatedId(id: Id): Promise<ObserverTraceEvent[]> {
    return this.events.filter((e) => JSON.stringify(e.payload).includes(id));
  }
}

export function makeObservationTrace(e: Observation): ObserverTraceEvent {
  return {
    id: `otrace-obs-${e.id}`,
    type: "observation",
    timestamp: e.timestamp,
    actorId: e.observerId,
    payload: e,
  };
}

export function makePatternTrace(p: ObservationPattern): ObserverTraceEvent {
  return {
    id: `otrace-pat-${p.id}`,
    type: "pattern",
    timestamp: p.createdAt,
    actorId: p.proposedBy,
    payload: p,
  };
}

export function makeProtoThresholdTrace(pt: ProtoThreshold): ObserverTraceEvent {
  return {
    id: `otrace-proto-${pt.id}`,
    type: "proto_threshold",
    timestamp: pt.createdAt,
    actorId: pt.proposedBy,
    payload: pt,
  };
}

export function makeThresholdDeltaTrace(
  d: ThresholdDelta,
  actorId: Id,
  ts: ISOTime,
): ObserverTraceEvent {
  return {
    id: `otrace-delta-${d.thresholdId}-${d.before.version}`,
    type: "threshold_delta",
    timestamp: ts,
    actorId,
    payload: d,
  };
}

export function makeObserverDriftTrace(observer: ObserverProfile, ts: ISOTime): ObserverTraceEvent {
  return {
    id: `otrace-odrift-${observer.id}-${ts}`,
    type: "observer_drift",
    timestamp: ts,
    actorId: observer.id,
    payload: {
      observerId: observer.id,
      driftScore: observer.driftScore,
      flags: observer.flags,
    },
  };
}
