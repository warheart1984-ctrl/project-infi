import { AgentRuntime } from "../../../agent";
import { requireInvariant } from "../../../agent/governance/invariants";
import { invariants } from "./nova.config";

async function main() {
  for (const inv of invariants) {
    await requireInvariant(inv);
  }

  const runtime = new AgentRuntime();
  const result = await runtime.generateCode({
    prompt: "Create a TypeScript function to compute factorial.",
  });

  console.log(result.code);
  console.log("Receipts:", result.receipts.map((r) => r.id));
}

main().catch(console.error);
