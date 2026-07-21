export function uuid(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { randomUUID } = require("crypto") as typeof import("crypto");
  return randomUUID();
}
