import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const sensitiveFiles = new Set([
  'src/index.ts',
  'src/thetaCodec.test.ts',
  'profile/theta-bip39-profile.v0.1.json',
  'profile/repro-lock-v0.1.json',
  'profile/ci-pipeline.yml',
]);

function readText(path: string): string {
  try {
    return readFileSync(path, 'utf8');
  } catch {
    return '';
  }
}

function diffLines(oldText: string, newText: string): string[] {
  const oldLines = oldText.split(/\r?\n/);
  const newLines = newText.split(/\r?\n/);
  const output: string[] = [];
  const max = Math.max(oldLines.length, newLines.length);

  for (let index = 0; index < max; index += 1) {
    const left = oldLines[index] ?? '';
    const right = newLines[index] ?? '';
    if (left !== right) {
      output.push(`-${left}`);
      output.push(`+${right}`);
    }
  }
  return output;
}

function listFiles(root: string): string[] {
  const files: string[] = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) {
      files.push(...listFiles(path));
    } else {
      files.push(path);
    }
  }
  return files;
}

function main(): void {
  const [oldDir, newDir] = process.argv.slice(2);
  if (!oldDir || !newDir) {
    throw new Error('Usage: tsx scripts/profile-diff.ts <old-profile-dir> <new-profile-dir>');
  }

  console.log('=== SPEC-CRITICAL FILES ===');
  for (const name of sensitiveFiles) {
    const changes = diffLines(readText(join(oldDir, name)), readText(join(newDir, name)));
    if (changes.length) {
      console.log(`\n=== DIFF: ${name} ===`);
      console.log(changes.join('\n'));
    }
  }

  console.log('\n=== ALL FILES IN NEW PROFILE ===');
  for (const file of listFiles(newDir)) {
    console.log(file);
  }
}

main();
