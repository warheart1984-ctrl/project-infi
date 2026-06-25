import { createHash } from "node:crypto";

function sortKeys(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortKeys);
  }
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    return Object.keys(record)
      .sort()
      .reduce<Record<string, unknown>>((acc, key) => {
        acc[key] = sortKeys(record[key]);
        return acc;
      }, {});
  }
  return value;
}

export function sha256(payload: string | Buffer | Record<string, unknown>): string {
  let body: Buffer;
  if (typeof payload === "object" && !Buffer.isBuffer(payload)) {
    body = Buffer.from(JSON.stringify(sortKeys(payload)), "utf-8");
  } else if (typeof payload === "string") {
    body = Buffer.from(payload, "utf-8");
  } else {
    body = payload;
  }
  return createHash("sha256").update(body).digest("hex");
}
