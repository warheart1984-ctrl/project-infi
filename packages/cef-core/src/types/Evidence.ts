import type { CefAuthority } from './Authority.js';
import type { CefAudit } from './Audit.js';
import type { CefLineage } from './Lineage.js';
import type { CefPromotion } from './Promotion.js';
import type { CefReplay } from './Replay.js';
import type { CefVerification } from './Verification.js';

export type CefProfileType = 'CREC' | 'OEL' | 'CEL' | 'Security' | 'ModelEval';

export type CefDomain = 'ops' | 'research' | 'language' | 'security' | 'model';

export type CefContext = {
  domain: CefDomain;
  subdomain?: string;
};

export type CefInputs = {
  artifacts?: string[];
  dataRefs?: string[];
  advisoryOutputs?: Array<{
    modelId: string;
    output: Record<string, unknown>;
  }>;
};

/** CEF core evidence object (profile payloads are additional properties). */
export type CefEvidence = {
  id: string;
  type: CefProfileType;
  version: string;
  authority: CefAuthority;
  context: CefContext;
  inputs: CefInputs;
  verification: CefVerification;
  lineage: CefLineage;
  replay: CefReplay;
  audit: CefAudit;
  promotion: CefPromotion;
  oel?: Record<string, unknown>;
  crec?: Record<string, unknown>;
  cel?: Record<string, unknown>;
  security?: Record<string, unknown>;
  modelEval?: Record<string, unknown>;
};
