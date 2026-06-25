export interface DriftReport {
  agentA: string;
  agentB: string;
  ledgerMismatch: boolean;
  continuityMismatch: boolean;
  pitMismatch: boolean;
}

export function detectDrift(
  receiptsA: { hash: string }[],
  receiptsB: { hash: string }[]
): DriftReport {
  const ledgerMismatch =
    receiptsA.length !== receiptsB.length ||
    receiptsA.some((r, i) => r.hash !== receiptsB[i]?.hash);
  return {
    agentA: "a",
    agentB: "b",
    ledgerMismatch,
    continuityMismatch: false,
    pitMismatch: false,
  };
}
