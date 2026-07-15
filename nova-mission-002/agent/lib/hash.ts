export async function sha256(input: string): Promise<string> {
  if (typeof globalThis.crypto?.subtle !== "undefined") {
    const data = new TextEncoder().encode(input);
    const buf = await globalThis.crypto.subtle.digest("SHA-256", data);
    return Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }
  const { createHash } = await import("crypto");
  return createHash("sha256").update(input).digest("hex");
}

export function sha256Sync(input: string): string {
  try {
    const { createHash } = require("crypto") as typeof import("crypto");
    return createHash("sha256").update(input).digest("hex");
  } catch {
    // Browser without Node crypto — non-cryptographic fallback only.
    let h = 0;
    for (let i = 0; i < input.length; i++) {
      h = (Math.imul(31, h) + input.charCodeAt(i)) | 0;
    }
    return Math.abs(h).toString(16).padStart(16, "0");
  }
}
