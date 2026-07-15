import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function main(): void {
  if (!existsSync(resolve(repoRoot, '.git'))) {
    throw new Error(`not a git repository: ${repoRoot}`);
  }

  execFileSync('git', ['-C', repoRoot, 'config', 'core.hooksPath', '.githooks'], { stdio: 'inherit' });

  console.log('Dropbox sync hooks installed at .githooks');
}

main();
