import { useQuery } from "@tanstack/react-query";

interface DriftWindowMetrics {
  count: number;
  driftVelocity: number;
  stabilityIndex: number;
  refactorDensity: number;
  invariantPressure: number;
}

interface EvolutionStatusResponse {
  timestamp: number;
  trajectory: {
    sampleCount: number;
    windows: Record<"5c" | "10c" | "20c", DriftWindowMetrics>;
    latest: DriftWindowMetrics;
  };
  autonomy: {
    triggered: boolean;
    reasonCodes: string[];
    metrics: {
      driftVelocity: number;
      stabilityIndex: number;
      invariantPressure: number;
      structuralEntropy: number;
      recursivePressure: number;
    };
    shadow: {
      findings: {
        structuralEntropyScore: number;
        recursivePressureScore: number;
        identityConsistency: "pass" | "warn";
        deadCodeSignal: "none" | "possible";
        notes: string[];
      };
    };
  };
}

export function useEvolutionStatus(enabled = true) {
  return useQuery<EvolutionStatusResponse>({
    queryKey: ["/api/evolution-status"],
    enabled,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}
