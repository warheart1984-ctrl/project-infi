import {
  CEF_CORE_SCHEMA,
  CEF_PROFILES,
  isCefProfileType,
  type CefSchema,
} from '../registry/profiles.js';
import type { CefProfileType } from '../types/Evidence.js';
import {
  createCefAjv,
  type ErrorObject,
  type ValidateFunction,
} from '../ajvFactory.js';

export type ProfileValidationResult = {
  valid: boolean;
  errors: ErrorObject[] | null | undefined;
  profile?: CefProfileType;
};

const ajv = createCefAjv();
ajv.addSchema(CEF_CORE_SCHEMA);

const compiled = new Map<CefProfileType, ValidateFunction>();

function getValidator(profile: CefProfileType): ValidateFunction {
  const existing = compiled.get(profile);
  if (existing) {
    return existing;
  }
  const schema = CEF_PROFILES[profile] as CefSchema;
  const validate = ajv.compile(schema);
  compiled.set(profile, validate);
  return validate;
}

/**
 * Validate evidence against a named CEF profile schema (includes core via $ref).
 */
export function validateProfile(
  profile: string,
  evidence: unknown,
): ProfileValidationResult {
  if (!isCefProfileType(profile)) {
    return {
      valid: false,
      errors: [
        {
          instancePath: '',
          schemaPath: '#/profile',
          keyword: 'enum',
          params: { allowedValues: Object.keys(CEF_PROFILES) },
          message: `unknown CEF profile: ${profile}`,
        },
      ],
    };
  }

  const validate = getValidator(profile);
  const valid = validate(evidence);
  return {
    valid: Boolean(valid),
    errors: validate.errors,
    profile,
  };
}
