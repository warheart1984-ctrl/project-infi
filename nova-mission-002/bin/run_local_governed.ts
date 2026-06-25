#!/usr/bin/env node
import { readFileSync } from "fs";
import { resolve } from "path";
import { governedPredict } from "../src/runtime/governedPredict";
import type { GovernedContext } from "../src/runtime/types";

interface LocalGovernedConfig {
  model_path: string;
  operator_id: string;
  invariant_set_version: string;
  log_receipts: boolean;
  log_lineage: boolean;
}

function loadYamlConfig(filePath: string): LocalGovernedConfig {
  const text = readFileSync(filePath, "utf8");
  const raw: Record<string, string> = {};
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf(":");
    if (idx === -1) continue;
    const key = trimmed.slice(0, idx).trim();
    let value = trimmed.slice(idx + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    raw[key] = value;
  }
  return {
    model_path: raw.model_path ?? "./models/local-llm",
    operator_id: process.env.OPERATOR_ID ?? raw.operator_id ?? "local-operator-001",
    invariant_set_version: raw.invariant_set_version ?? "K0-K12-v1",
    log_receipts: raw.log_receipts !== "false",
    log_lineage: raw.log_lineage !== "false",
  };
}

async function main(): Promise<void> {
  const configPath = resolve(process.cwd(), "config/local-governed.yaml");
  const config = loadYamlConfig(configPath);
  const prompt = process.argv.slice(2).join(" ") || "Say hello, but do not violate any invariants.";

  const context: GovernedContext = {
    operator_id: config.operator_id,
    mode: "predict",
    invariant_set_version: config.invariant_set_version,
    model_path: config.model_path,
  };

  const result = await governedPredict(prompt, context);

  console.log("--- Model output ---");
  console.log(result.output);
  console.log("\n--- Receipt ---");
  console.log(
    JSON.stringify(
      {
        call_id: result.receipt.call_id,
        operator_id: result.receipt.operator_id,
        invariants_passed: result.receipt.invariants_passed,
        mode: result.receipt.mode,
        invariant_set_version: result.receipt.invariant_set_version,
      },
      null,
      2
    )
  );
  console.log("\n--- Lineage ---");
  console.log(`root_id: ${result.lineage.root_id}`);
  console.log(`entry_id: ${result.lineage.entry_id}`);
}

main().catch((err: unknown) => {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
