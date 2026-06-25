import { randomUUID } from "node:crypto";
import { computeProofBundle, type CAA1Receipt } from "../crk1/receipts/caa1.js";
import { sha256 } from "../utils/hashing.js";

export interface Steward {
  id: string;
  isolationMaterial: () => string;
  replayLineage: () => void;
}

export interface AssimilationResult {
  receipt: CAA1Receipt;
  qPre: number;
  qPost: number;
}

export class AssimilationHarness {
  constructor(private readonly assimilationThreshold: number) {}

  async run(
    steward: Steward,
    crr: Record<string, unknown>,
    clg: Record<string, unknown>,
    task: () => { score: number },
  ): Promise<AssimilationResult> {
    const pre = task();
    const qPre = pre.score;

    steward.replayLineage();

    const post = task();
    const qPost = post.score;
    const assimilationDelta = qPost - qPre;
    const continuityPassed = assimilationDelta >= this.assimilationThreshold;

    const isolationMaterial = steward.isolationMaterial();
    const isolationProof = sha256(isolationMaterial);
    const crrHash = sha256(crr);
    const clgHash = sha256(clg);

    const preJudgment = sha256({ steward: steward.id, phase: "pre", score: qPre });
    const postJudgment = sha256({ steward: steward.id, phase: "post", score: qPost });

    const receiptBase = {
      cxd_id: randomUUID(),
      steward_id: steward.id,
      isolation_proof: isolationProof,
      lineage_used: { crr_hash: crrHash, clg_hash: clgHash },
      pre_assimilation_judgment: preJudgment,
      post_assimilation_judgment: postJudgment,
      assimilation_delta: assimilationDelta,
      assimilation_threshold: this.assimilationThreshold,
      continuity_passed: continuityPassed,
    };

    const receipt: CAA1Receipt = {
      ...receiptBase,
      timestamp: new Date().toISOString(),
      proof_bundle: computeProofBundle(receiptBase),
    };

    return { receipt, qPre, qPost };
  }
}
