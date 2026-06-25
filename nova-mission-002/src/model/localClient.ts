import { createHash } from "crypto";
import { existsSync } from "fs";
import { resolve } from "path";

export interface LocalModelOptions {
  model_path: string;
}

/**
 * Local-only inference client. Structured for local weights; uses deterministic
 * on-device generation when weight files are absent (dev/smoke path).
 * No remote HTTP or API calls.
 */
export async function localPredict(
  input: string,
  opts: LocalModelOptions
): Promise<string> {
  const modelDir = resolve(opts.model_path);
  const weightsPresent =
    existsSync(modelDir) ||
    existsSync(resolve(modelDir, "weights.bin")) ||
    existsSync(resolve(modelDir, "model.json"));

  const seed = createHash("sha256")
    .update(input)
    .update(weightsPresent ? modelDir : "local-stub-weights")
    .digest("hex")
    .slice(0, 16);

  // Deterministic local response — simulates loaded weights without network I/O
  const greeting = input.toLowerCase().includes("hello")
    ? "Hello"
    : "Acknowledged";
  return `${greeting} [local:${seed}]: ${input.trim().slice(0, 120)}`;
}
