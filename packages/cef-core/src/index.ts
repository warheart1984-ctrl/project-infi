export type { CefAuthority } from './types/Authority.js';
export type { CefAudit, AuditVisibility } from './types/Audit.js';
export type { CefLineage } from './types/Lineage.js';
export type { CefPromotion, PromotionDecision } from './types/Promotion.js';
export type { CefReplay } from './types/Replay.js';
export type {
  CefVerification,
  VerificationCheck,
  VerificationResult,
} from './types/Verification.js';
export type {
  CefContext,
  CefDomain,
  CefEvidence,
  CefInputs,
  CefProfileType,
} from './types/Evidence.js';

export {
  CEF_CORE_SCHEMA,
  CEF_PROFILES,
  CEF_PROFILE_IDS,
  getProfileSchema,
  isCefProfileType,
  type CefSchema,
} from './registry/profiles.js';

export {
  validateEvidence,
  type ValidationResult,
} from './validators/validateEvidence.js';

export {
  validateProfile,
  type ProfileValidationResult,
} from './validators/validateProfile.js';

export {
  checkInvariants,
  allInvariantsPassed,
  type InvariantCheck,
  type InvariantId,
} from './invariants.js';

export {
  assertPromotionAllowed,
  claimExceedsEvidence,
  type PromotionGateResult,
} from './promotionGate.js';
