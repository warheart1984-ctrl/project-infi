export interface InvariantSet {
  ids: string[];
  /** Invariant id → active weight */
  weights: Record<string, number>;
}
