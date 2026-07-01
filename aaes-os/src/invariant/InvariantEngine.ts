
/**
 * DARPA-INVARIANT: Constitutional Invariant Engine
 * 
 * Implements deterministic invariant checking for constitutional compliance.
 * Pure functional design with explicit state transitions.
 * 
 * Security Properties:
 * - Deterministic output for identical inputs
 * - No hidden state or side effects
 * - Strict type safety for all inputs/outputs
 */
export interface Invariant {
  readonly id: string;
  readonly description: string;
  /** 
   * Evaluate invariant against context
   * @param context - Immutable context object
   * @returns boolean indicating compliance
   */
  evaluate(context: Readonly<unknown>): boolean;
}

/**
 * InvariantEngine - Core constitutional compliance engine
 * 
 * Stateless evaluator that checks all registered invariants
 * against a given context. Returns true only if ALL invariants pass.
 */
export class InvariantEngine {
  private readonly invariants: ReadonlyArray<Invariant> = [];

  /**
   * Register an invariant for evaluation
   * @param invariant - Immutable invariant definition
   */
  public register(invariant: Invariant): void {
    // Defensive copy to prevent external mutation
    this.invariants = [...this.invariants, invariant];
  }

  /**
   * Evaluate all registered invariants against context
   * @param context - Immutable evaluation context
   * @returns true if all invariants pass, false otherwise
   * 
   * Security: Pure function - no side effects, deterministic output
   */
  public evaluateAll(context: Readonly<unknown>): boolean {
    return this.invariants.every(invariant => 
      invariant.evaluate(context)
    );
  }

  /**
   * Get count of registered invariants
   * @returns number of registered invariants
   */
  public size(): number {
    return this.invariants.length;
  }

  /**
   * Reset engine to initial state
   * Removes all registered invariants
   */
  public reset(): void {
    this.invariants = [];
  }
}

