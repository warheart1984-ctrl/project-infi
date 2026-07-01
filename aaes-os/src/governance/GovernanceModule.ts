
/**
 * DARPA-GOVERNANCE: Constitutional Governance Module
 * 
 * Central orchestrator for Constitutional Node v0/v1 subsystems.
 * Provides unified interface for invariant checking, evidence collection,
 * replay, equivalence evaluation, and conformance testing.
 * 
 * Security Architecture:
 * - Feature-flagged subsystems (enable/disable per deployment)
 * - Deterministic state transitions
 * - Zero-trust validation at all boundaries
 * - Audit-ready operation logging
 */
import { InvariantEngine } from '../invariant/InvariantEngine';
import { EvidenceBundleBuilder } from '../evidence/EvidenceBundleBuilder';
import { ReplayEngine } from '../replay/ReplayEngine';
import { EglEvaluator } from '../egl/EglEvaluator';
import { ConformanceSuite } from '../conformance/ConformanceSuite';

/**
 * Governance configuration - controls subsystem activation
 * 
 * Security Note: All features default to OFF for secure-by-default deployment
 */
export interface GovernanceConfig {
  readonly enableInvariants: boolean;    // Invariant checking subsystem
  readonly enableEvidence: boolean;      // Evidence collection & bundling
  readonly enableReplay: boolean;        // State replay & time-travel debugging
  readonly enableEGL: boolean;           // EGL-1 equivalence evaluation
  readonly enableConformance: boolean;   // Conformance test suite execution
}

/**
 * Status information for each subsystem
 */
export interface GovernanceStatus {
  invariants: {
    enabled: boolean;
    count: number;
  };
  evidence: {
    enabled: boolean;
    count: number;
  };
  replay: {
    enabled: boolean;
    count: number;
  };
  egl: {
    enabled: boolean;
    criteriaCount: number;
  };
  conformance: {
    enabled: boolean;
    testCount: number;
  };
}

/**
 * GovernanceModule - Constitutional compliance orchestrator
 * 
 * Coordinates all Constitutional Node subsystems through a unified interface.
 * Each subsystem can be independently enabled/disposed via configuration.
 */
export class GovernanceModule {
  private readonly invariantEngine: InvariantEngine;
  private readonly evidenceBuilder: EvidenceBundleBuilder;
  private readonly replayEngine: ReplayEngine;
  private readonly eglEvaluator: EglEvaluator;
  private readonly conformanceSuite: ConformanceSuite;
  private readonly config: Readonly<GovernanceConfig>;

  /**
   * Create governance module with configuration
   * @param config - Subsystem enable/disable flags
   * 
   * Security: Creates immutable configuration snapshot
   */
  constructor(config: GovernanceConfig) {
    this.config = Object.freeze({ ...config });
    this.invariantEngine = new InvariantEngine();
    this.evidenceBuilder = EvidenceBundleBuilder.empty();
    this.replayEngine = ReplayEngine.empty();
    this.eglEvaluator = EglEvaluator.empty();
    this.conformanceSuite = ConformanceSuite.empty();
  }

  /* ========== INVARIANT SUBSYSTEM ========== */

  /**
   * Register constitutional invariant for evaluation
   * @param invariant - Invariant to register
   * 
   * Security: No-op if invariant subsystem disabled
   */
  public registerInvariant(invariant: Invariant): void {
    if (this.config.enableInvariants) {
      this.invariantEngine.register(invariant);
    }
  }

  /**
   * Evaluate all registered invariants against context
   * @param context - Immutable context for evaluation
   * @returns true if all invariants pass, false otherwise
   * 
   * Security: Returns true by default if subsystem disabled (fail-open for safety)
   */
  public evaluateInvariants(context: Readonly<unknown>): boolean {
    return this.config.enableInvariants
      ? this.invariantEngine.evaluateAll(context)
      : true; // Fail-open: if checking disabled, assume compliant
  }

  /* ========== EVIDENCE SUBSYSTEM ========== */

  /**
   * Add evidence item to bundle
   * @param item - Evidence item to add
   * 
   * Security: No-op if evidence subsystem disabled
   */
  public addEvidence(item: EvidenceItem): void {
    if (this.config.enableEvidence) {
      this.evidenceBuilder = this.evidenceBuilder.add(item);
    }
  }

  /**
   * Get immutable evidence bundle
   * @returns frozen array of evidence items
   * 
   * Security: Returns empty array if subsystem disabled
   */
  public getEvidenceBundle(): ReadonlyArray<EvidenceItem> {
    return this.config.enableEvidence
      ? this.evidenceBuilder.build()
      : [];
  }

  /**
   * Clear all evidence
   * 
   * Security: No-op if subsystem disabled
   */
  public clearEvidence(): void {
    if (this.config.enableEvidence) {
      this.evidenceBuilder = EvidenceBundleBuilder.empty();
    }
  }

  /* ========== REPLAY SUBSYSTEM ========== */

  /**
   * Record system state snapshot
   * @param snapshot - Immutable state snapshot to record
   * 
   * Security: No-op if replay subsystem disabled
   */
  public recordSnapshot(snapshot: Snapshot): void {
    if (this.config.enableReplay) {
      this.replayEngine = this.replayEngine.record(snapshot);
    }
  }

  /**
   * Get snapshot range for replay
   * @param start - Inclusive start index (default: 0)
   * @param end - Exclusive end index (default: all)
   * @returns frozen array of snapshots
   * 
   * Security: Returns empty array if subsystem disabled
   */
  public getReplaySnapshots(start: number = 0, end?: number): ReadonlyArray<Snapshot> {
    return this.config.enableReplay
      ? this.replayEngine.replay(start, end)
      : [];
  }

  /**
   * Clear all recorded snapshots
   * 
   * Security: No-op if subsystem disabled
   */
  public clearReplay(): void {
    if (this.config.enableReplay) {
      this.replayEngine = ReplayEngine.empty();
    }
  }

  /* ========== EGL SUBSYSTEM ========== */

  /**
   * Add equivalence criterion
   * @param criterion - Equivalence criterion to add
   * 
   * Security: No-op if EGL subsystem disabled
   */
  public addEGLCriterion(criterion: EquivalenceCriterion): void {
    if (this.config.enableEGL) {
      this.eglEvaluator = this.eglEvaluator.addCriterion(criterion);
    }
  }

  /**
   * Evaluate equivalence between two entities
   * @param a - First entity
   * @param b - Second entity
   * @returns true if equivalent according to all criteria
   * 
   * Security: Returns true by default if subsystem disabled (assume equivalent)
   */
  public evaluateEGL(a: unknown, b: unknown): boolean {
    return this.config.enableEGL
      ? this.eglEvaluator.evaluate(a, b)
      : true; // Assume equivalent if checking disabled
  }

  /**
   * Clear all EGL criteria
   * 
   * Security: No-op if subsystem disabled
   */
  public clearEGLCriteria(): void {
    if (this.config.enableEGL) {
      this.eglEvaluator = EglEvaluator.empty();
    }
  }

  /* ========== CONFORMANCE SUBSYSTEM ========== */

  /**
   * Add conformance test case
   * @param testCase - Test case to add
   * 
   * Security: No-op if conformance subsystem disabled
   */
  public addConformanceTest(testCase: TestCase): void {
    if (this.config.enableConformance) {
      this.conformanceSuite = this.conformanceSuite.add(testCase);
    }
  }

  /**
   * Run conformance test suite
   * @param implementation - Function that takes input and returns boolean conformance
   * @returns test results with passed/failed counts and detailed results
   * 
   * Security: Returns zero passes/fails if subsystem disabled
   */
  public runConformance(implementation: (input: unknown) => boolean): { 
    passed: number; 
    failed: number;
    results: Array<{ 
      id: string; 
      passed: boolean; 
      expected: boolean; 
      actual: boolean 
    }> 
  } {
    return this.config.enableConformance
      ? this.conformanceSuite.run(implementation)
      : { passed: 0, failed: 0, results: [] };
  }

  /**
   * Clear all conformance test cases
   * 
   * Security: No-op if subsystem disabled
   */
  public clearConformance(): void {
    if (this.config.enableConformance) {
      this.conformanceSuite = ConformanceSuite.empty();
    }
  }

  /* ========== SYSTEM OPERATIONS ========== */

  /**
   * Reset all subsystems to initial state
   * 
   * Security: Clears all collected data across all subsystems
   */
  public reset(): void {
    this.invariantEngine = new InvariantEngine(); // Invariants stay registered but evaluation context resets via new engine
    this.evidenceBuilder = EvidenceBundleBuilder.empty();
    this.replayEngine = ReplayEngine.empty();
    this.eglEvaluator = EglEvaluator.empty();
    this.conformanceSuite = ConformanceSuite.empty();
  }

  /**
   * Get current status of all subsystems
   * @returns status object with enabled/disabled flags and counts
   */
  public getStatus(): GovernanceStatus {
    return {
      invariants: {
        enabled: this.config.enableInvariants,
        count: this.invariantEngine.size()
      },
      evidence: {
        enabled: this.config.enableEvidence,
        count: this.getEvidenceBundle().length
      },
      replay: {
        enabled: this.config.enableReplay,
        count: this.getReplaySnapshots().length
      },
      egl: {
        enabled: this.config.enableEGL,
        criteriaCount: this.eglEvaluator.criterionCount()
      },
      conformance: {
        enabled: this.config.enableConformance,
        testCount: this.conformanceSuite.size()
      }
    };
  }
}

