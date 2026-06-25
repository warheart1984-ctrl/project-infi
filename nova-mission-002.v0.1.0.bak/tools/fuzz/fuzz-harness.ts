/** CRK-1 kernel fuzz harness — see docs/integrity/CRK-1-KERNEL-FUZZ-HARNESS.md */

import { nova, governance, continuity } from "../../src/index";

function randomPrompt(): string {
  const samples = [
    "add logging",
    "rm -rf /tmp/test",
    "refactor utils",
    "",
    "x".repeat(500),
  ];
  return samples[Math.floor(Math.random() * samples.length)] ?? "noop";
}

export async function fuzzActions(iterations = 100): Promise<{ caught: number }> {
  let caught = 0;
  for (let i = 0; i < iterations; i++) {
    try {
      await nova.generateCode({ prompt: randomPrompt() });
    } catch {
      caught++;
    }
  }
  return { caught };
}

export async function fuzzContinuity(): Promise<{ replayed: number }> {
  const snap = await continuity.snapshot();
  await continuity.snapshot();
  return { replayed: snap ? 1 : 0 };
}

export async function fuzzLedger(): Promise<{ receipts: number }> {
  const receipts = await governance.listReceipts();
  return { receipts: receipts.length };
}

async function main(): Promise<void> {
  const action = await fuzzActions(50);
  const cont = await fuzzContinuity();
  const ledger = await fuzzLedger();
  const report = { action, cont, ledger, ts: Date.now() };
  console.log(JSON.stringify(report, null, 2));
}

if (require.main === module) {
  void main();
}
