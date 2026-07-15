import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const scriptPath = resolve(repoRoot, 'scripts', 'install-dropbox-service.ps1');

function normalizeArgs(argv: string[]): string[] {
  const args: string[] = [];
  for (const arg of argv) {
    if (arg === '--') {
      continue;
    }
    if (arg.startsWith('--')) {
      args.push(`-${arg.slice(2)}`);
      continue;
    }
    args.push(arg);
  }
  return args;
}

function main(): void {
  const normalizedArgs = normalizeArgs(process.argv.slice(2));
  const result = spawnSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', scriptPath, ...normalizedArgs], {
    cwd: repoRoot,
    encoding: 'utf8',
    stdio: 'inherit',
  });

  if (result.error) {
    throw result.error;
  }

  if (typeof result.status === 'number' && result.status !== 0) {
    throw new Error(`service installer exited with code ${result.status}`);
  }
}

main();
