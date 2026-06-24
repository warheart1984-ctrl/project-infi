import { createThreshold } from "./threshold";
import { markProtoThresholdAdopted } from "./proto-threshold";
import { formalizePattern } from "./patterns";
import type {
  ObservationPattern,
  ProtoThreshold,
  Threshold,
  ThresholdCreateInput,
  ThresholdDelta,
  ThresholdLifecycle,
} from "./types";

export function runThresholdLifecycle(
  pattern: ObservationPattern,
  proto: ProtoThreshold,
  adoptInput?: Partial<ThresholdCreateInput>,
): ThresholdLifecycle {
  const formalized = formalizePattern(pattern);
  const adoptedProto = markProtoThresholdAdopted(proto);
  let threshold: Threshold | null = null;
  const deltas: ThresholdDelta[] = [];

  if (adoptedProto.status === "adopted") {
    threshold = createThreshold({
      id: adoptedProto.id,
      name: adoptedProto.metric,
      domain: adoptedProto.domain,
      metric: adoptedProto.metric,
      comparator: adoptedProto.comparator,
      value: adoptedProto.value,
      unit: adoptedProto.unit,
      intent: adoptedProto.intent,
      createdBy: adoptedProto.proposedBy,
      ...adoptInput,
    });
  }

  return {
    observationPattern: formalized,
    protoThresholds: [adoptedProto],
    threshold,
    deltas,
  };
}
