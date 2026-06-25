#!/usr/bin/env node
import { program } from "commander";
import { nova, governance, runtime, continuity } from "./index";
import { invariants } from "../config/nova.config";

async function bootstrapGovernance(): Promise<void> {
  for (const inv of invariants) {
    await governance.requireInvariant(inv);
  }
}

program.name("nova").description("Nova SDK CLI — constitutional coding agent");

program
  .command("init")
  .description("Initialize a Nova-governed project")
  .action(async () => {
    console.log("Nova project initialized (config + invariants).");
    console.log("Edit config/nova.config.ts to register custom invariants.");
  });

program
  .command("generate")
  .description("Generate code with governance receipts")
  .argument("<prompt>", "Prompt for code generation")
  .action(async (prompt: string) => {
    await bootstrapGovernance();
    try {
      const result = await nova.generateCode({ prompt });
      console.log(result.code);
      console.log("\nReceipts:");
      console.log(JSON.stringify(result.receipts, null, 2));
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error("BLOCKED:", message);
      const receipts = await governance.listReceipts();
      const last = receipts[receipts.length - 1];
      if (last) {
        console.log("\nReceipts:");
        console.log(JSON.stringify([last], null, 2));
      }
      process.exit(1);
    }
  });

program
  .command("plan")
  .description("Generate a governed plan for a goal")
  .argument("<goal>", "Goal description")
  .action(async (goal: string) => {
    await bootstrapGovernance();
    const ctx = await runtime.getContext();
    const result = await nova.plan({ goal, context: ctx });
    console.log(JSON.stringify(result.plan, null, 2));
  });

program
  .command("continuity")
  .description("Show current continuity snapshot")
  .action(async () => {
    const snap = await continuity.snapshot();
    console.log(JSON.stringify(snap, null, 2));
  });

program
  .command("receipts")
  .description("List recent governance receipts")
  .action(async () => {
    const receipts = await governance.listReceipts();
    console.log(JSON.stringify(receipts, null, 2));
  });

program
  .command("invariants")
  .description("List registered invariants")
  .action(async () => {
    await bootstrapGovernance();
    const invs = governance.getInvariants();
    console.log(JSON.stringify(invs.map((i) => ({ id: i.id, description: i.description, severity: i.severity })), null, 2));
  });

program.parse(process.argv);
