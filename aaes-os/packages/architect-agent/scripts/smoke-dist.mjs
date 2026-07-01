import { strict as assert } from 'node:assert';
import { spawnSync } from 'node:child_process';
import {
  cp,
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  rm,
  writeFile,
} from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const packageDirectory = path.resolve(scriptDirectory, '..');
const workspaceDirectory = path.resolve(packageDirectory, '../..');
const harnessPath = path.join(packageDirectory, 'test', 'smoke-dist-consumer.mjs');
const corepackCommand = process.platform === 'win32' ? process.execPath : 'corepack';
const corepackPrefixArgs = process.platform === 'win32'
  ? [path.join(path.dirname(process.execPath), 'node_modules', 'corepack', 'dist', 'corepack.js')]
  : [];
const temporaryPrefix = 'aaes-architect-agent-smoke-';
let temporaryDirectory;

function runCommand(phase, command, args, cwd) {
  const result = spawnSync(command, args, {
    cwd,
    encoding: 'utf8',
    env: { ...process.env },
    maxBuffer: 10 * 1024 * 1024,
    shell: false,
  });

  if (result.error || result.status !== 0) {
    const details = [
      `${phase} failed`,
      `command: ${command} ${args.join(' ')}`,
      `status: ${String(result.status)}`,
      `stdout:\n${result.stdout ?? ''}`,
      `stderr:\n${result.stderr ?? ''}`,
    ].join('\n');
    throw new Error(details, result.error ? { cause: result.error } : undefined);
  }

  return result.stdout.trim();
}

function runPnpm(phase, args, cwd = workspaceDirectory) {
  return runCommand(phase, corepackCommand, [...corepackPrefixArgs, 'pnpm', ...args], cwd);
}

async function discoverWorkspacePackages() {
  const packages = new Map();
  for (const workspaceRoot of ['packages', 'services']) {
    const rootDirectory = path.join(workspaceDirectory, workspaceRoot);
    let entries;
    try {
      entries = await readdir(rootDirectory, { withFileTypes: true });
    } catch (error) {
      if (error?.code === 'ENOENT') continue;
      throw error;
    }

    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const directory = path.join(rootDirectory, entry.name);
      const manifestPath = path.join(directory, 'package.json');
      try {
        const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
        if (typeof manifest.name === 'string' && typeof manifest.version === 'string') {
          packages.set(manifest.name, { directory, manifest });
        }
      } catch (error) {
        if (error?.code !== 'ENOENT') throw error;
      }
    }
  }
  return packages;
}

function resolveRuntimeClosure(rootPackageName, workspacePackages) {
  const resolved = [];
  const visited = new Set();
  const visiting = new Set();

  function visit(packageName) {
    if (visited.has(packageName)) return;
    if (visiting.has(packageName)) {
      throw new Error(`workspace runtime dependency cycle detected at ${packageName}`);
    }
    const workspacePackage = workspacePackages.get(packageName);
    if (!workspacePackage) {
      throw new Error(`workspace package is missing: ${packageName}`);
    }

    visiting.add(packageName);
    for (const [dependencyName, dependencyRange] of Object.entries(
      workspacePackage.manifest.dependencies ?? {},
    )) {
      if (String(dependencyRange).startsWith('workspace:')) {
        visit(dependencyName);
      }
    }
    visiting.delete(packageName);
    visited.add(packageName);
    resolved.push(workspacePackage);
  }

  visit(rootPackageName);
  return resolved;
}

function createPublishManifest(workspacePackage, workspacePackages) {
  const manifest = structuredClone(workspacePackage.manifest);
  for (const field of [
    'dependencies',
    'optionalDependencies',
    'peerDependencies',
    'devDependencies',
  ]) {
    if (manifest[field]) {
      manifest[field] = Object.fromEntries(
        Object.entries(manifest[field]).map(([dependencyName, dependencyRange]) => {
        if (!String(dependencyRange).startsWith('workspace:')) {
          return [dependencyName, dependencyRange];
        }
        const dependency = workspacePackages.get(dependencyName);
        if (!dependency) {
          throw new Error(`cannot publish unresolved workspace dependency: ${dependencyName}`);
        }
        return [dependencyName, dependency.manifest.version];
        }),
      );
    }
  }
  return manifest;
}

async function copyOptionalFile(source, destination) {
  try {
    await copyFile(source, destination);
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
}

async function stageWorkspacePackage(workspacePackage, workspacePackages, stageRoot) {
  const safeName = workspacePackage.manifest.name.replaceAll('@', '').replaceAll('/', '-');
  const stageDirectory = path.join(stageRoot, safeName);
  await mkdir(stageDirectory, { recursive: true });
  await cp(path.join(workspacePackage.directory, 'dist'), path.join(stageDirectory, 'dist'), {
    recursive: true,
  });
  await writeFile(
    path.join(stageDirectory, 'package.json'),
    `${JSON.stringify(createPublishManifest(workspacePackage, workspacePackages), null, 2)}\n`,
    'utf8',
  );
  await copyOptionalFile(
    path.join(workspacePackage.directory, 'README.md'),
    path.join(stageDirectory, 'README.md'),
  );
  await copyOptionalFile(
    path.join(workspacePackage.directory, 'SECURITY.md'),
    path.join(stageDirectory, 'SECURITY.md'),
  );
  return stageDirectory;
}

async function packStagedPackage(workspacePackage, stageDirectory, packDirectory) {
  const before = new Set(await readdir(packDirectory));
  runPnpm(`pack ${workspacePackage.manifest.name}`, ['pack', '--pack-destination', packDirectory], stageDirectory);
  const created = (await readdir(packDirectory)).filter(
    (entry) => entry.endsWith('.tgz') && !before.has(entry),
  );
  assert.equal(
    created.length,
    1,
    `packing ${workspacePackage.manifest.name} must create exactly one tarball`,
  );
  return path.join(packDirectory, created[0]);
}

function toFileDependency(consumerDirectory, tarballPath) {
  const relativePath = path.relative(consumerDirectory, tarballPath).replaceAll('\\', '/');
  return `file:${relativePath}`;
}

async function main() {
  temporaryDirectory = await mkdtemp(path.join(tmpdir(), temporaryPrefix));
  const packDirectory = path.join(temporaryDirectory, 'packs');
  const stageRoot = path.join(temporaryDirectory, 'stage');
  const consumerDirectory = path.join(temporaryDirectory, 'consumer');
  await mkdir(packDirectory, { recursive: true });
  await mkdir(stageRoot, { recursive: true });
  await mkdir(consumerDirectory, { recursive: true });

  const workspacePackages = await discoverWorkspacePackages();
  const runtimeClosure = resolveRuntimeClosure(
    '@aaes-os/architect-agent',
    workspacePackages,
  );
  const tarballs = new Map();
  for (const workspacePackage of runtimeClosure) {
    runPnpm(
      `build ${workspacePackage.manifest.name}`,
      ['--filter', workspacePackage.manifest.name, 'run', 'build'],
    );
    const stageDirectory = await stageWorkspacePackage(
      workspacePackage,
      workspacePackages,
      stageRoot,
    );
    tarballs.set(
      workspacePackage.manifest.name,
      await packStagedPackage(workspacePackage, stageDirectory, packDirectory),
    );
  }
  const localDependencies = Object.fromEntries(
    [...tarballs].map(([packageName, tarballPath]) => [
      packageName,
      toFileDependency(consumerDirectory, tarballPath),
    ]),
  );
  const consumerManifest = {
    name: 'architect-agent-dist-smoke-consumer',
    version: '1.0.0',
    private: true,
    type: 'module',
    packageManager: 'pnpm@10.15.0',
    dependencies: localDependencies,
    pnpm: {
      overrides: localDependencies,
    },
  };

  await writeFile(
    path.join(consumerDirectory, 'package.json'),
    `${JSON.stringify(consumerManifest, null, 2)}\n`,
    'utf8',
  );
  await copyFile(harnessPath, path.join(consumerDirectory, 'smoke-dist-consumer.mjs'));

  const installFlags = ['--offline', '--ignore-scripts', '--config.node-linker=isolated'];
  runPnpm(
    'create frozen consumer lockfile',
    ['install', '--lockfile-only', ...installFlags],
    consumerDirectory,
  );
  runPnpm(
    'install frozen consumer dependencies',
    ['install', '--frozen-lockfile', ...installFlags],
    consumerDirectory,
  );

  const output = runCommand(
    'execute packed consumer',
    process.execPath,
    ['smoke-dist-consumer.mjs'],
    consumerDirectory,
  );
  const record = JSON.parse(output);
  assert.equal(record.status, 'ok');
  assert.equal(record.egl, 'EGL-1');
  process.stdout.write(`${JSON.stringify(record)}\n`);
}

try {
  await main();
} finally {
  if (temporaryDirectory) {
    const expectedPrefix = path.join(tmpdir(), temporaryPrefix);
    assert.ok(
      temporaryDirectory.startsWith(expectedPrefix),
      'refusing to remove an unexpected smoke directory',
    );
    await rm(temporaryDirectory, { recursive: true, force: true });
  }
}
