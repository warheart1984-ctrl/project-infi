import {
  appendDriftTrajectoryMetrics,
  computeDriftTrajectoryPreview,
  type DriftModeFilter,
} from "../server/evolution-drift";
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

function parseModeFilter(value: string | undefined): DriftModeFilter {
  const normalized = (value || "").trim().toLowerCase();
  if (normalized === "still" || normalized === "wild" || normalized === "all") return normalized;
  return "all";
}

function printHelp(): void {
  console.log("Spiral evolution drift CLI");
  console.log("Usage:");
  console.log(
    "  npm run evolution:drift -- [--preview] [--apply] [--principal <id>] [--mode all|still|wild] [--json] [--out .local/evolution-drift-report.json]",
  );
}

async function run(args: string[]): Promise<void> {
  const apply = getFlag(args, "--apply");
  const preview = !apply || getFlag(args, "--preview");
  const asJson = getFlag(args, "--json");
  const outPath = getOptionValue(args, "--out");
  const principalId = (getOptionValue(args, "--principal") || "").trim();
  const modeFilter = parseModeFilter(getOptionValue(args, "--mode"));
  const nowOption = getOptionValue(args, "--now");
  const now = Number.isFinite(Number(nowOption)) && Number(nowOption) > 0 ? Number(nowOption) : Date.now();

  const report = await computeDriftTrajectoryPreview({
    principalId: principalId || undefined,
    modeFilter,
    now,
  });

  if (!preview) {
    await appendDriftTrajectoryMetrics(report);
  }

  if (outPath) {
    const resolved = path.resolve(process.cwd(), outPath);
    await mkdir(path.dirname(resolved), { recursive: true });
    await writeFile(resolved, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  }

  if (asJson) {
    console.log(JSON.stringify(report, null, 2));
    return;
  }

  console.log(
    `Evolution drift (${preview ? "preview" : "apply"}): samples=${report.sampleCount} latestCycle=${report.latestCycleId || "-"} modeFilter=${report.modeFilter}${report.principalId ? ` principal=${report.principalId}` : ""}`,
  );
  console.log(
    `Config: velocityWindow=${report.config.velocityWindow} densityWindow=${report.config.densityWindow} pressureWindow=${report.config.pressureWindow} repoSizeBaseline=${report.config.repoSizeBaseline} churnNormalization=${report.config.churnNormalization} fileWeight=${report.config.fileWeight}`,
  );
  console.log(
    `Formulas: driftVelocity=${report.formulas.driftVelocity} | stabilityIndex=${report.formulas.stabilityIndex} | refactorDensity=${report.formulas.refactorDensity} | invariantPressure=${report.formulas.invariantPressure}`,
  );
  console.log(
    `Latest: driftVelocity=${report.latest.driftVelocity.toFixed(6)} stabilityIndex=${report.latest.stabilityIndex.toFixed(6)} refactorDensity=${report.latest.refactorDensity.toFixed(6)} invariantPressure=${report.latest.invariantPressure.toFixed(6)} (count=${report.latest.count})`,
  );
  for (const key of ["5c", "10c", "20c"] as const) {
    const window = report.windows[key];
    console.log(
      `Window ${key}: driftVelocity=${window.driftVelocity.toFixed(6)} stabilityIndex=${window.stabilityIndex.toFixed(6)} refactorDensity=${window.refactorDensity.toFixed(6)} invariantPressure=${window.invariantPressure.toFixed(6)} count=${window.count}`,
    );
  }
  if (outPath) {
    console.log(`Report written: ${path.resolve(process.cwd(), outPath)}`);
  }
  if (!preview) {
    console.log("Drift trajectory record appended.");
  }
}

async function main(): Promise<void> {
  const [command = "preview", ...args] = process.argv.slice(2);
  switch (command) {
    case "preview":
    case "run":
      await run(args);
      return;
    case "help":
      printHelp();
      return;
    default:
      printHelp();
      process.exitCode = 1;
      return;
  }
}

main().catch((error) => {
  console.error("Evolution drift CLI error:", error);
  process.exitCode = 1;
});

