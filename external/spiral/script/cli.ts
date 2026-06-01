import { importCodexAuthProfile } from "../server/auth-profiles";

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

function printHelp(): void {
  console.log("Spiral CLI");
  console.log("Usage:");
  console.log("  npm run spiral -- auth import-codex [--profile <id>] [--provider <provider>] [--source <path>] [--json]");
}

async function runAuthImportCodex(args: string[]): Promise<void> {
  const profileId = getOptionValue(args, "--profile");
  const provider = getOptionValue(args, "--provider");
  const source = getOptionValue(args, "--source");
  const asJson = getFlag(args, "--json");
  const result = await importCodexAuthProfile({
    ...(profileId ? { profileId } : {}),
    ...(provider ? { provider: provider as "openai" | "openai-codex" | "azure-openai" | "anthropic" | "google" } : {}),
    ...(source ? { codexAuthPath: source } : {}),
  });
  if (asJson) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }
  console.log(`Imported Codex auth profile: ${result.profileId}`);
  console.log(`Provider: ${result.provider}`);
  console.log(`Source: ${result.sourcePath}`);
  console.log(`Refresh token present: ${result.hasRefreshToken ? "yes" : "no"}`);
  if (result.expiresAt) {
    console.log(`Expires: ${new Date(result.expiresAt).toISOString()}`);
  }
  if (result.email) {
    console.log(`Email: ${result.email}`);
  }
}

async function main(): Promise<void> {
  const [domain = "help", action, ...args] = process.argv.slice(2);
  if (domain === "auth" && action === "import-codex") {
    await runAuthImportCodex(args);
    return;
  }
  printHelp();
  if (domain !== "help") {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error("Spiral CLI error:", error);
  process.exitCode = 1;
});
