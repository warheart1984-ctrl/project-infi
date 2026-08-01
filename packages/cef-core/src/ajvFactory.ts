import { createRequire } from 'node:module';
import type { ErrorObject, ValidateFunction } from 'ajv';

const require = createRequire(import.meta.url);

type AjvInstance = {
  compile: (schema: object) => ValidateFunction;
  addSchema: (schema: object | object[]) => AjvInstance;
  errors?: ErrorObject[] | null;
};

type AjvConstructor = new (options?: {
  allErrors?: boolean;
  strict?: boolean;
}) => AjvInstance;

type AddFormats = (ajv: AjvInstance) => AjvInstance;

const Ajv2020 = require('ajv/dist/2020') as AjvConstructor;
const addFormats = require('ajv-formats') as AddFormats;

export type { ErrorObject, ValidateFunction };

export function createCefAjv(): AjvInstance {
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  addFormats(ajv);
  return ajv;
}
