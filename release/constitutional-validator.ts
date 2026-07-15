import { getCoriAlphaRoot, syncCoriAlphaSummary } from '../services/sovereign-control-plane/src/coriAlpha.ts';

function main(): void {
  const root = process.env.CORI_ALPHA_ROOT ?? getCoriAlphaRoot();
  const summary = syncCoriAlphaSummary(root);

  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);

  if (!summary.validation.valid) {
    throw new Error(`constitutional validator failed: ${summary.validation.issues.join('; ')}`);
  }
}

try {
  main();
} catch (error: unknown) {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
}
