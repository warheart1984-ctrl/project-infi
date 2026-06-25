import type { AaesError, Result } from "./types.js";

export function err<T>(code: string, message: string): Result<T> {
  return { ok: false, error: { code, message } };
}

export function ok<T>(value: T): Result<T> {
  return { ok: true, value };
}

export function notImplemented<T>(surface: string): Result<T> {
  return err("AAES_NOT_IMPLEMENTED", `${surface} is not implemented in stub`);
}

export function isAaesError(value: unknown): value is AaesError {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    "message" in value &&
    typeof (value as AaesError).code === "string" &&
    typeof (value as AaesError).message === "string"
  );
}
