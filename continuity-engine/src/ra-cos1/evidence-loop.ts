import type { Observation } from "../observer-evidence/observation";
import type { Case } from "../observer-evidence/case";
import type { Evidence } from "../observer-evidence/evidence";
import type { Audit } from "../observer-evidence/audit";
import type { Transfer } from "../observer-evidence/transfer";
import type { Extension } from "../observer-evidence/extension";

export interface EvidenceLoopHandlers {
  receiveObservation(): Promise<Observation | null>;
  buildCase(obs: Observation): Promise<Case>;
  generateEvidence(c: Case): Promise<Evidence[]>;
  runAudit(evidence: Evidence[]): Promise<Audit>;
  planTransfer(audit: Audit): Promise<Transfer>;
  deriveExtension(transfer: Transfer): Promise<Extension | null>;
  persistAll(objects: {
    observation: Observation;
    caseObj: Case;
    evidence: Evidence[];
    audit: Audit;
    transfer: Transfer;
    extension?: Extension | null;
  }): Promise<void>;
}

export interface EvidenceLoopOptions {
  maxIterations?: number;
}

export async function runEvidenceLoop(
  handlers: EvidenceLoopHandlers,
  options: EvidenceLoopOptions = {},
): Promise<void> {
  const max = options.maxIterations ?? 1;
  let iterations = 0;

  while (iterations < max) {
    const obs = await handlers.receiveObservation();
    if (!obs) break;

    const caseObj = await handlers.buildCase(obs);
    const evidence = await handlers.generateEvidence(caseObj);
    const audit = await handlers.runAudit(evidence);
    const transfer = await handlers.planTransfer(audit);
    const extension = await handlers.deriveExtension(transfer);

    await handlers.persistAll({
      observation: obs,
      caseObj,
      evidence,
      audit,
      transfer,
      extension: extension ?? undefined,
    });

    iterations += 1;
  }
}
