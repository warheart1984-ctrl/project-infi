import type { CefEvidence } from './types/Evidence.js';
import { validateEvidence } from './validators/validateEvidence.js';

export type InvariantId =
  | 'claim-bound-to-evidence'
  | 'replayable'
  | 'auditable'
  | 'authority-bound'
  | 'versioned'
  | 'governed-promotion';

export type InvariantCheck = {
  id: InvariantId;
  passed: boolean;
  detail: string;
};

/**
 * Structural invariant checks for CEF core objects.
 * Article III / III-A (Reality / Epistemic Cycle) are charter axioms —
 * documented in CEF_V1_CHARTER.md; not encoded as schema keywords here.
 */
export function checkInvariants(evidence: unknown): InvariantCheck[] {
  const schema = validateEvidence(evidence);
  const e = evidence as Partial<CefEvidence>;

  const requiredPresent =
    typeof e?.id === 'string' &&
    e.id.length > 0 &&
    typeof e?.type === 'string' &&
    e.authority != null &&
    e.context != null &&
    e.inputs != null &&
    e.verification != null &&
    e.lineage != null &&
    e.replay != null &&
    e.audit != null &&
    e.promotion != null;

  return [
    {
      id: 'claim-bound-to-evidence',
      passed: schema.valid && requiredPresent,
      detail: schema.valid
        ? 'Required evidence fields present for claims'
        : 'Schema validation failed — claim may exceed evidence',
    },
    {
      id: 'replayable',
      passed:
        typeof e?.replay?.instructions === 'string' &&
        e.replay.instructions.trim().length > 0,
      detail: 'replay.instructions must be non-empty',
    },
    {
      id: 'auditable',
      passed:
        e?.audit?.visibility === 'public' || e?.audit?.visibility === 'internal',
      detail: 'audit.visibility must be public | internal',
    },
    {
      id: 'authority-bound',
      passed: Boolean(
        e?.authority?.carId && e?.authority?.actorId && e?.authority?.role,
      ),
      detail: 'authority.carId, actorId, role required',
    },
    {
      id: 'versioned',
      passed:
        typeof e?.version === 'string' &&
        /^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$/.test(e.version),
      detail: 'version must follow semver pattern',
    },
    {
      id: 'governed-promotion',
      passed:
        e?.promotion?.decision === 'approved' ||
        e?.promotion?.decision === 'rejected' ||
        e?.promotion?.decision === 'hold',
      detail: 'promotion.decision must be approved | rejected | hold',
    },
  ];
}

export function allInvariantsPassed(evidence: unknown): boolean {
  return checkInvariants(evidence).every((c) => c.passed);
}
