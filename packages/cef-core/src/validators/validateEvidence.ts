import { CEF_CORE_SCHEMA } from '../registry/profiles.js';
import {
  createCefAjv,
  type ErrorObject,
  type ValidateFunction,
} from '../ajvFactory.js';

export type ValidationResult = {
  valid: boolean;
  errors: ErrorObject[] | null | undefined;
};

const ajv = createCefAjv();
const validateCore: ValidateFunction = ajv.compile(CEF_CORE_SCHEMA);

/**
 * Validate an unknown value against the CEF core evidence schema.
 * Profile-specific fields are allowed via additionalProperties on the core schema.
 */
export function validateEvidence(evidence: unknown): ValidationResult {
  const valid = validateCore(evidence);
  return { valid: Boolean(valid), errors: validateCore.errors };
}
