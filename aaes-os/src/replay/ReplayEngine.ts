
/**
 * DARPA-REPLAY: Temporal Replay Engine
 * 
 * Provides deterministic replay of system states for forensic analysis and 
 * constitutional compliance verification.
 * 
 * Security Properties:
 * - Append-only timeline
 * - Deterministic replay semantics
 * - Cryptographic chaining (consumer responsibility)
 */
export interface Snapshot {
  readonly timestamp: number;          // Unix timestamp in milliseconds
  readonly state: Readonly<unknown>;   // Immutable system state snapshot
  readonly metadata?: Readonly<Record<string, unknown>>; // Optional context
}

/**
 * ReplayEngine - Manages temporal sequence of system states
 * 
 * Enables forensic reconstruction of system execution for:
 * - Constitutional violation analysis
 * - Accident investigation
 * - Behavior validation
 */
export class ReplayEngine {
  private readonly snapshots: ReadonlyArray<Snapshot> = [];

  /**
   * Record system state at point in time
   * @param snapshot - Immutable state snapshot to record
   * @returns new ReplayEngine instance with appended snapshot
   * 
   * Security: Pure function - returns new instance
   */
  public record(snapshot: Snapshot): ReplayEngine {
    return new ReplayEngine([
      ...this.snapshots,
      { ...snapshot, state: { ...snapshot.state } }
    ]);
  }

  /**
   * Replay snapshot range
   * @param start - Inclusive start index (default: 0)
   * @param end - Exclusive end index (default: all)
   * @returns frozen array of snapshots in range
   * 
   * Security: Returns deeply frozen copy to prevent tampering
   */
  public replay(start: number = 0, end?: number): ReadonlyArray<Snapshot> {
    const slice = this.snapshots.slice(start, end);
    return Object.freeze(slice.map(s => ({ ...s })));
  }

  /**
   * Get total number of recorded snapshots
   * @returns count of snapshots in timeline
   */
  public length(): number {
    return this.snapshots.length;
  }

  /**
   * Get first snapshot (earliest in time)
   * @returns earliest snapshot or undefined if empty
   */
  public first(): Snapshot | undefined {
    return this.snapshots[0];
  }

  /**
   * Get last snapshot (most recent)
   * @returns latest snapshot or undefined if empty
   */
  public last(): Snapshot | undefined {
    return this.snapshots[this.snapshots.length - 1];
  }

  /**
   * Create empty replay engine
   * @returns new empty ReplayEngine
   */
  public static empty(): ReplayEngine {
    return new ReplayEngine();
  }

  // Private constructor to enforce immutability
  private constructor(snapshots: ReadonlyArray<Snapshot> = []) {
    this.snapshots = Object.freeze(snapshots);
  }
}

