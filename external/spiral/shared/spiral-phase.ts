export type SpiralPhaseId = "ingress" | "sigil" | "memory" | "voices" | "harmonize" | "final";

export type MemoryFragmentKind = "fractal" | "thread" | "chrono";

export interface MemoryFragment {
  kind: MemoryFragmentKind;
  text: string;
}

export interface SpiralPhase {
  id: SpiralPhaseId;
  payload: Record<string, unknown>;
}
