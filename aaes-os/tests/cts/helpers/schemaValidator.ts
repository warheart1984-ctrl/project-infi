import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

const schemaPath = path.join(
  fileURLToPath(new URL('../../../schemas/cas-1.0.json', import.meta.url)),
);
const schema = JSON.parse(readFileSync(schemaPath, 'utf8')) as {
  $id: string;
};

const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
ajv.addSchema(schema);

const CAS_SCHEMA_ID = schema.$id;

export type CasDefName =
  | 'Identity'
  | 'Run'
  | 'Span'
  | 'Receipt'
  | 'Fault'
  | 'ExecuteRequest'
  | 'ExecuteResponse'
  | 'InvariantInfo';

function refFor(defName: CasDefName): string {
  return `${CAS_SCHEMA_ID}#/$defs/${defName}`;
}

/** Validate a single CAS object against its JSON Schema $def. */
export function validateCasObject(defName: CasDefName, data: unknown): boolean {
  return ajv.validate(refFor(defName), data) as boolean;
}

/** Wrapper form: `validate({ Identity: obj })` for CTS readability. */
export function validate(wrapper: Partial<Record<CasDefName, unknown>>): boolean {
  const entries = Object.entries(wrapper) as [CasDefName, unknown][];
  if (entries.length !== 1) {
    return false;
  }
  const [defName, data] = entries[0]!;
  return validateCasObject(defName, data);
}

export function formatValidationErrors(): string {
  return (ajv.errors ?? [])
    .map((error) => `${error.instancePath || '/'} ${error.message ?? 'invalid'}`)
    .join('; ');
}
