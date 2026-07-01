
/**
 * DARPA-EGL: Equivalence Grounding Logic Evaluator
 * 
 * Implements EGL-1 equivalence checking for constitutional compliance validation.
 * Provides deterministic semantic equivalence checking between system states.
 * 
 * Security Properties:
 * - Deterministic equivalence decisions
 * - Side-effect free evaluation
 * - Composable criterion system
 */
export interface EquivalenceCriterion {
  readonly id: string;                     // Unique criterion identifier
  readonly description: string;            // Human-readable description
  readonly evaluate: (a: unknown, b: unknown) => boolean; // Equivalence function
}

/**
 * EglEvaluator - Evaluates semantic equivalence using EGL-1 criterion
 * 
 * Implements the Constitutional Node's equivalence grounding logic.
 * Allows pluggable equivalence criteria for different domains.
 */
export class EglEvaluator {
  private readonly criteria: ReadonlyArray<EquivalenceCriterion> = [];

  /**
   * Add equivalence criterion to evaluation set
   * @param criterion - Equivalence criterion to add
   * @returns new EglEvaluator instance with added criterion
   * 
   * Security: Pure function - returns new instance
   */
  public addCriterion(criterion: EquivalenceCriterion): EglEvaluator {
    return new EglEvaluator([
      ...this.criteria,
      { ...criterion }
    ]);
  }

  /**
   * Evaluate equivalence between two entities
   * @param a - First entity to compare
   * @param b - Second entity to compare
   * @returns true if all criteria indicate equivalence, false otherwise
   * 
   * Security: Pure deterministic function - same inputs always yield same output
   */
  public evaluate(a: unknown, b: unknown): boolean {
    return this.criteria.every(criterion => 
      criterion.evaluate(a, b)
    );
  }

  /**
   * Get number of active criteria
   * @returns count of equivalence criteria
   */
  public criterionCount(): number {
    return this.criteria.length;
  }

  /**
   * Check if specific criterion ID exists
   * @param id - Criterion identifier to check
   * @returns true if criterion exists
   */
  public hasCriterion(id: string): boolean {
    return this.criteria.some(c => c.id === id);
  }

  /**
   * Create empty evaluator
   * @returns new empty EglEvaluator
   */
  public static empty(): EglEvaluator {
    return new EglEvaluator();
  }

  // Private constructor to enforce immutability
  private constructor(criteria: ReadonlyArray<EquivalenceCriterion> = []) {
    this.criteria = Object.freeze(criteria);
  }
}

