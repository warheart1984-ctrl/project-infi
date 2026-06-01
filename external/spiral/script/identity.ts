import { appendIdentityReflectionLog, writeIdentitySnapshot } from "../server/identity-memory";
import { collectIdentityCycleInputs, computeIdentityCycleDiff } from "../server/identity-cycle";
import { mkdir, writeFile } from "fs/promises";
import path from "path";

function getFlag(args: string[], flag: string): boolean {
  return args.includes(flag);
}

function getOptionValue(args: string[], option: string): string | undefined {
  const prefix = `${option}=`;
  const inline = args.find((arg) => arg.startsWith(prefix));
  if (inline) return inline.slice(prefix.length);
  const index = args.indexOf(option);
  if (index >= 0 && index + 1 < args.length) {
    return args[index + 1];
  }
  return undefined;
}

function parsePositiveInt(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return undefined;
  return Math.floor(parsed);
}

function formatDeltaKey(
  section: "core" | "traits" | "impulses",
  key: string,
  delta: { from: number; to: number; delta: number },
): string {
  return `${section}.${key}: ${delta.from.toFixed(3)} -> ${delta.to.toFixed(3)} (${delta.delta >= 0 ? "+" : ""}${delta.delta.toFixed(3)})`;
}

function printHelp(): void {
  console.log("Spiral identity CLI");
  console.log("Usage:");
  console.log(
    "  npm run identity:cycle -- [--dry-run] [--apply] [--principal <id>] [--signal \"text\"] [--json] [--out identity/report.json]",
  );
}

async function runCycle(args: string[]): Promise<void> {
  const apply = getFlag(args, "--apply");
  const dryRun = !apply || getFlag(args, "--dry-run");
  const asJson = getFlag(args, "--json");
  const outPath = getOptionValue(args, "--out");
  const principalId = (getOptionValue(args, "--principal") || "").trim();
  const signal = (getOptionValue(args, "--signal") || "").trim();
  const nowOverride = parsePositiveInt(getOptionValue(args, "--now"));
  const now = nowOverride || Date.now();

  const collected = await collectIdentityCycleInputs({
    principalId: principalId || undefined,
    signal: signal || undefined,
    now,
  });
  const trigger = signal ? `identity-cycle:${signal}` : "identity-cycle";
  const diff = computeIdentityCycleDiff({
    ...collected,
    trigger,
    principalId: principalId || undefined,
    dryRun,
    now,
  });

  if (!dryRun) {
    await writeIdentitySnapshot(diff.after);
    await appendIdentityReflectionLog({
      ...diff.reflection,
      dryRun: false,
    });
  }

  const payload = {
    dryRun,
    timestamp: diff.timestamp,
    cycle: diff.cycle,
    principalId: principalId || null,
    trigger,
    signals: diff.signals,
    reasons: diff.reasons,
    before: diff.before,
    after: diff.after,
    deltas: diff.deltas,
    reflection: {
      ...diff.reflection,
      dryRun,
    },
  };

  if (outPath) {
    const resolved = path.resolve(process.cwd(), outPath);
    await mkdir(path.dirname(resolved), { recursive: true });
    await writeFile(resolved, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  }

  if (asJson) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(
    `Identity cycle (${dryRun ? "dry-run" : "apply"}): cycle=${diff.cycle} mode=${diff.before.core.current_mode}->${diff.after.core.current_mode} novelty=${diff.before.core.novelty_bias.toFixed(3)}->${diff.after.core.novelty_bias.toFixed(3)} risk=${diff.before.core.risk_tolerance.toFixed(3)}->${diff.after.core.risk_tolerance.toFixed(3)} stability=${diff.before.core.self_stability.toFixed(3)}->${diff.after.core.self_stability.toFixed(3)}`,
  );
  console.log(
    `Signals: rotationInstability=${diff.signals.rotationInstability.toFixed(3)} semanticUncertainty=${diff.signals.semanticUncertainty.toFixed(3)} userPressure=${diff.signals.userPressure.toFixed(3)} confidence=${diff.signals.signalConfidence.toFixed(3)} sampleSize=${collected.userSignals.sampleSize}`,
  );

  console.log("Before core:");
  console.log(JSON.stringify(diff.before.core, null, 2));
  console.log("After core:");
  console.log(JSON.stringify(diff.after.core, null, 2));
  console.log("Before traits:");
  console.log(JSON.stringify(diff.before.traits, null, 2));
  console.log("After traits:");
  console.log(JSON.stringify(diff.after.traits, null, 2));
  console.log("Before impulses:");
  console.log(JSON.stringify(diff.before.impulses, null, 2));
  console.log("After impulses:");
  console.log(JSON.stringify(diff.after.impulses, null, 2));

  const deltaLines = [
    ...Object.entries(diff.deltas.core).map(([key, delta]) => formatDeltaKey("core", key, delta)),
    ...Object.entries(diff.deltas.traits).map(([key, delta]) => formatDeltaKey("traits", key, delta)),
    ...Object.entries(diff.deltas.impulses).map(([key, delta]) => formatDeltaKey("impulses", key, delta)),
  ];
  if (deltaLines.length === 0) {
    console.log("Deltas: none");
  } else {
    console.log(`Deltas (${deltaLines.length}):`);
    deltaLines.forEach((line) => console.log(`- ${line}`));
  }

  if (diff.reasons.length === 0) {
    console.log("Reasons: none");
  } else {
    console.log(`Reasons (${diff.reasons.length}):`);
    diff.reasons.forEach((reason, index) => {
      console.log(`${index + 1}. ${reason.key}: ${reason.detail}${Number.isFinite(reason.delta) ? ` (delta=${(reason.delta as number).toFixed(3)})` : ""}`);
    });
  }
  if (outPath) {
    console.log(`Report written: ${path.resolve(process.cwd(), outPath)}`);
  }
  if (!dryRun) {
    console.log("Identity files updated and reflection appended.");
  }
}

async function main(): Promise<void> {
  const [command = "help", ...args] = process.argv.slice(2);
  switch (command) {
    case "cycle":
      await runCycle(args);
      return;
    case "help":
    default:
      printHelp();
      if (command !== "help") {
        process.exitCode = 1;
      }
  }
}

main().catch((error) => {
  console.error("Identity CLI error:", error);
  process.exitCode = 1;
});

