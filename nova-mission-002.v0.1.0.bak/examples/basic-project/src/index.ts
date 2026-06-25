import { nova } from "../../../src/core/agent";
import { requireInvariant } from "../../../src/governance/invariants";
import { invariants } from "./nova.config";

async function main() {
  for (const inv of invariants) {
    await requireInvariant(inv);
  }

  const result = await nova.generateCode({
    prompt: "Create a TypeScript function to compute factorial.",
  });

  console.log(result.code);
  console.log("Receipts:", result.receipts.map((r) => r.id));
}

main().catch(console.error);
