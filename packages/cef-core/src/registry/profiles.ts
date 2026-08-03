import type { CefProfileType } from '../types/Evidence.js';
import coreSchema from '../schemas/cef-core-evidence.json' with { type: 'json' };
import oelSchema from '../schemas/cef-oel-evidence.json' with { type: 'json' };
import crecSchema from '../schemas/cef-crec-evidence.json' with { type: 'json' };
import celSchema from '../schemas/cef-cel-evidence.json' with { type: 'json' };
import securitySchema from '../schemas/cef-security-evidence.json' with { type: 'json' };
import modelEvalSchema from '../schemas/cef-modeleval-evidence.json' with { type: 'json' };

export type CefSchema = Record<string, unknown>;

export const CEF_CORE_SCHEMA = coreSchema as CefSchema;

export const CEF_PROFILES: Record<CefProfileType, CefSchema> = {
  CREC: crecSchema as CefSchema,
  OEL: oelSchema as CefSchema,
  CEL: celSchema as CefSchema,
  Security: securitySchema as CefSchema,
  ModelEval: modelEvalSchema as CefSchema,
};

export const CEF_PROFILE_IDS = Object.keys(CEF_PROFILES) as CefProfileType[];

export function isCefProfileType(value: string): value is CefProfileType {
  return value in CEF_PROFILES;
}

export function getProfileSchema(profile: CefProfileType): CefSchema {
  return CEF_PROFILES[profile];
}
