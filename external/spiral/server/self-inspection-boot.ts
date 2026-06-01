import { mkdir, writeFile } from "fs/promises";
import path from "path";
import { getSelfInspectionIndex, type SelfInspectionIndex } from "./self-inspection";

export interface SelfInspectBootResult {
  requested: boolean;
  index?: SelfInspectionIndex;
  snapshotPath?: string;
}

function toWorkspaceRelative(filePath: string): string {
  return path.relative(process.cwd(), filePath).split(path.sep).join("/");
}

export async function writeSelfInspectionSnapshot(
  index: SelfInspectionIndex,
  filePath?: string,
): Promise<string> {
  const outputPath =
    filePath ||
    path.join(process.cwd(), ".local", "self-inspect", `self-inspect-${Date.now()}.json`);
  const outputDir = path.dirname(outputPath);
  await mkdir(outputDir, { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(index, null, 2)}\n`, "utf8");
  return toWorkspaceRelative(outputPath);
}

export async function runSelfInspectOnBoot(
  argv: string[] = process.argv.slice(2),
): Promise<SelfInspectBootResult> {
  const requested = argv.includes("--self-inspect");
  if (!requested) {
    return { requested: false };
  }

  const index = await getSelfInspectionIndex({ forceRefresh: true });
  const snapshotPath = await writeSelfInspectionSnapshot(
    index,
    path.join(process.cwd(), ".local", "self-inspect", "latest.json"),
  );
  return {
    requested: true,
    index,
    snapshotPath,
  };
}
