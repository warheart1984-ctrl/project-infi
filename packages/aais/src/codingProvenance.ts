import type { AAISPreferredModel } from './capabilities.js';

export interface CodingProvenanceRecord {
  capabilityName: string;
  filesChanged: readonly string[];
  testsRan: readonly string[];
  model: AAISPreferredModel;
  constraintsApplied: readonly string[];
  evidence: readonly string[];
}

export interface CodingProvenanceGraph {
  records: readonly CodingProvenanceRecord[];
}

export function createCodingProvenanceGraph(
  records: readonly CodingProvenanceRecord[],
): CodingProvenanceGraph {
  return {
    records: records.map((record) => ({
      capabilityName: record.capabilityName,
      filesChanged: [...record.filesChanged],
      testsRan: [...record.testsRan],
      model: record.model,
      constraintsApplied: [...record.constraintsApplied],
      evidence: [...record.evidence],
    })),
  };
}
