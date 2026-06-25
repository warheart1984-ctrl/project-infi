import { sha256 } from "../../utils/hashing.js";

export interface LineageUsed {
  crr_hash: string;
  clg_hash: string;
}

export interface CAA1Receipt {
  cxd_id: string;
  timestamp: string;
  steward_id: string;
  isolation_proof: string;
  lineage_used: LineageUsed;
  pre_assimilation_judgment: string;
  post_assimilation_judgment: string;
  assimilation_delta: number;
  assimilation_threshold: number;
  continuity_passed: boolean;
  proof_bundle: string;
}

const HASH64 = /^[a-f0-9]{64}$/;

export function computeProofBundle(
  receipt: Omit<CAA1Receipt, "proof_bundle" | "timestamp"> & { timestamp?: string },
): string {
  const body = {
    cxd_id: receipt.cxd_id,
    steward_id: receipt.steward_id,
    isolation_proof: receipt.isolation_proof,
    lineage_used: receipt.lineage_used,
    pre_assimilation_judgment: receipt.pre_assimilation_judgment,
    post_assimilation_judgment: receipt.post_assimilation_judgment,
    assimilation_delta: receipt.assimilation_delta,
    assimilation_threshold: receipt.assimilation_threshold,
    continuity_passed: receipt.continuity_passed,
  };
  return sha256(body);
}

export function validateCAA1(receipt: CAA1Receipt): void {
  if (!receipt.cxd_id) throw new Error("Missing cxd_id");
  if (!receipt.steward_id) throw new Error("Missing steward_id");
  if (!receipt.lineage_used?.crr_hash || !receipt.lineage_used?.clg_hash) {
    throw new Error("Missing lineage hashes");
  }

  const { assimilation_delta, assimilation_threshold, continuity_passed } = receipt;

  if (continuity_passed !== assimilation_delta >= assimilation_threshold) {
    throw new Error("continuity_passed does not match delta >= threshold");
  }

  for (const field of [
    receipt.isolation_proof,
    receipt.lineage_used.crr_hash,
    receipt.lineage_used.clg_hash,
    receipt.pre_assimilation_judgment,
    receipt.post_assimilation_judgment,
    receipt.proof_bundle,
  ]) {
    if (!HASH64.test(field)) {
      throw new Error(`Invalid hash format: ${field}`);
    }
  }

  const expectedBundle = computeProofBundle(receipt);
  if (receipt.proof_bundle !== expectedBundle) {
    throw new Error("proof_bundle does not match receipt fields");
  }
}
