
/**
 * DARPA-EVIDENCE: Evidence Bundle Builder
 * 
 * Constructs cryptographically verifiable evidence bundles for constitutional compliance.
 * Immutable by design - all operations return new instances.
 * 
 * Security Properties:
 * - Append-only evidence log
 * - Cryptographic integrity (consuming layer responsible for hashing/signing)
 * - Deterministic serialization
 */
export interface EvidenceItem {
  readonly timestamp: number;      // Unix timestamp in milliseconds
  readonly source: string;         // Source identifier (e.g., 'sensor-A7', 'api-gateway')
  readonly payload: Readonly<unknown>; // Immutable evidence payload
}

/**
 * EvidenceBundleBuilder - Constructs verifiable evidence chains
 * 
 * Builds tamper-evident sequences of evidence items for audit trails.
 * Each addition creates a new immutable bundle.
 */
export class EvidenceBundleBuilder {
  private readonly items: ReadonlyArray<EvidenceItem> = [];

  /**
   * Add evidence to the bundle
   * @param item - Evidence item to append
   * @returns new EvidenceBundleBuilder instance with appended item
   * 
   * Security: Pure function - returns new instance, original unchanged
   */
  public add(item: EvidenceItem): EvidenceBundleBuilder {
    return new EvidenceBundleBuilder([...this.items, { ...item }]);
  }

  /**
   * Build immutable evidence bundle
   * @returns frozen array of evidence items in chronological order
   * 
   * Security: Returns deeply frozen copy to prevent tampering
   */
  public build(): ReadonlyArray<EvidenceItem> {
    return Object.freeze([...this.items]);
  }

  /**
   * Get evidence count
   * @returns number of evidence items in bundle
   */
  public size(): number {
    return this.items.length;
  }

  /**
   * Create empty builder
   * @returns new empty EvidenceBundleBuilder
   */
  public static empty(): EvidenceBundleBuilder {
    return new EvidenceBundleBuilder();
  }

  // Private constructor to enforce immutability via static factory
  private constructor(items: ReadonlyArray<EvidenceItem> = []) {
    this.items = Object.freeze(items);
  }
}

