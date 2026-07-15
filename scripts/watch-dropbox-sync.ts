import { spawn, spawnSync } from 'node:child_process';
import { existsSync, watch } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const tsxExecutable = resolve(repoRoot, 'node_modules', '.bin', process.platform === 'win32' ? 'tsx.CMD' : 'tsx');
const debounceMs = Number(process.env.REPO_DROPBOX_WATCH_DEBOUNCE_MS ?? '2500');
const minIntervalMs = Number(process.env.REPO_DROPBOX_WATCH_MIN_INTERVAL_MS ?? '15000');
const pollIntervalMs = Number(process.env.REPO_DROPBOX_WATCH_POLL_INTERVAL_MS ?? '5000');

let debounceTimer: NodeJS.Timeout | null = null;
let pollTimer: NodeJS.Timeout | null = null;
let running = false;
let pending = false;
let lastRunAt = 0;

function gitStatusDirty(): boolean {
  const result = spawnSync('git', ['-C', repoRoot, 'status', '--porcelain=v1', '--untracked-files=all'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });
  return result.status === 0 && typeof result.stdout === 'string' && result.stdout.trim().length > 0;
}

function log(message: string): void {
  process.stdout.write(`[dropbox-watch] ${message}\n`);
}

function queueSync(reason: string): void {
  pending = true;
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  debounceTimer = setTimeout(() => {
    void runSync(reason);
  }, debounceMs);
}

async function runSync(reason: string): Promise<void> {
  if (running) {
    pending = true;
    return;
  }

  const elapsed = Date.now() - lastRunAt;
  if (elapsed < minIntervalMs) {
    pending = true;
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = setTimeout(() => {
      void runSync(reason);
    }, minIntervalMs - elapsed);
    return;
  }

  if (!gitStatusDirty()) {
    pending = false;
    return;
  }

  running = true;
  pending = false;
  log(`syncing dirty working tree (${reason})`);

  await new Promise<void>((resolvePromise) => {
    const child = spawn(tsxExecutable, [resolve(repoRoot, 'release', 'repo-dropbox-sync.ts')], {
      cwd: repoRoot,
      env: {
        ...process.env,
        REPO_PATH: repoRoot,
        REPO_DROPBOX_SNAPSHOT_MODE: 'working-tree',
        REPO_DROPBOX_SYNC_OUTPUT_DIR: process.env.REPO_DROPBOX_SYNC_OUTPUT_DIR ?? '',
      },
      stdio: 'inherit',
      shell: false,
    });

    child.on('exit', (code) => {
      lastRunAt = Date.now();
      running = false;
      if (code === 0) {
        log('sync complete');
      } else {
        log(`sync exited with code ${code ?? 'unknown'}`);
      }
      resolvePromise();
    });
  });

  if (pending) {
    queueSync('follow-up');
  }
}

function startWatcher(): void {
  if (!existsSync(repoRoot)) {
    throw new Error(`repository path does not exist: ${repoRoot}`);
  }

  log(`watching ${repoRoot}`);

  try {
    process.stdin.resume();
    process.on('SIGINT', () => {
      log('stopping');
      process.exit(0);
    });
    process.on('SIGTERM', () => {
      log('stopping');
      process.exit(0);
    });

    const watcher = watch(repoRoot, { recursive: true }, (_eventType, filename) => {
      if (typeof filename === 'string' && filename.length > 0 && filename.includes('.git')) {
        return;
      }
      queueSync(typeof filename === 'string' && filename.length > 0 ? filename : 'filesystem change');
    });

    pollTimer = setInterval(() => {
      if (gitStatusDirty()) {
        queueSync('poll');
      }
    }, pollIntervalMs);

    queueSync('startup');

    process.on('exit', () => {
      watcher.close();
      if (pollTimer) {
        clearInterval(pollTimer);
      }
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
    });
  } catch (error) {
    log(`recursive watch unavailable, falling back to polling: ${error instanceof Error ? error.message : String(error)}`);
    pollTimer = setInterval(() => {
      if (gitStatusDirty()) {
        queueSync('poll');
      }
    }, pollIntervalMs);
    queueSync('startup');
  }
}

startWatcher();
