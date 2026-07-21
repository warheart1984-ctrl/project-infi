import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const packageDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(packageDir, '..');

const requiredFiles = [
  'Cargo.toml',
  'src/main.rs',
  'src/protocol.rs',
  'src/arena.rs',
];

const mode = process.argv[2] || 'build';

if (hasCargo()) {
  const cargoArgs = mode === 'test' ? ['test'] : mode === 'run' ? ['run'] : ['build'];
  const result = spawnSync('cargo', cargoArgs, {
    cwd: rootDir,
    stdio: 'inherit',
    shell: false,
  });
  process.exit(result.status ?? 1);
}

for (const relative of requiredFiles) {
  const absolute = path.join(rootDir, relative);
  if (!existsSync(absolute)) {
    throw new Error(`missing Nova substrate file: ${relative}`);
  }
}

const mainSource = readFileSync(path.join(rootDir, 'src/main.rs'), 'utf8');
const protocolSource = readFileSync(path.join(rootDir, 'src/protocol.rs'), 'utf8');

assertContains(mainSource, 'NovaCoda substrate listening at');
assertContains(mainSource, 'MessageType::Ping');
assertContains(mainSource, 'MessageType::ConstitutionalCheck');
assertContains(protocolSource, 'pub const MAGIC: [u8; 2] = [0xC0, 0xDA];');
assertContains(protocolSource, 'pub fn encode_header');
assertContains(protocolSource, 'pub fn decode_header');

process.stdout.write(`Nova substrate ${mode} verification completed without Cargo toolchain\n`);

function hasCargo() {
  const result = spawnSync('cargo', ['--version'], {
    cwd: rootDir,
    stdio: 'ignore',
    shell: false,
  });
  return result.status === 0;
}

function assertContains(source, needle) {
  if (!source.includes(needle)) {
    throw new Error(`Nova substrate verification failed: missing ${needle}`);
  }
}
