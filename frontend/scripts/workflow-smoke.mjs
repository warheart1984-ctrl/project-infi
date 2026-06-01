import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createWriteStream, existsSync } from 'node:fs';
import { mkdir, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(frontendRoot, '..');
const runtimeRoot = path.resolve(repoRoot, '.runtime', 'workflow-smoke');
const logRoot = path.resolve(runtimeRoot, 'logs');
const dataRoot = path.resolve(runtimeRoot, 'data');
const brokerRoot = path.resolve(runtimeRoot, 'broker');
const backendUrl = process.env.SMOKE_API_URL || 'http://127.0.0.1:5100';
const frontendUrl = process.env.SMOKE_FRONTEND_URL || 'http://127.0.0.1:3100';

function resolvePython() {
  const candidates = [
    path.resolve(repoRoot, '.venv', 'Scripts', 'python.exe'),
    path.resolve(repoRoot, '.venv', 'bin', 'python'),
    process.env.PYTHON,
    'python',
    'python3',
  ].filter(Boolean);

  const firstExisting = candidates.find((candidate) => candidate === 'python' || candidate === 'python3' || existsSync(candidate));
  if (!firstExisting) {
    throw new Error('Could not find a Python interpreter. Create the repo .venv before running workflow smoke.');
  }
  return firstExisting;
}

function startProcess(name, command, args, options = {}) {
  const logPath = path.resolve(logRoot, `${name}.log`);
  const logStream = createWriteStream(logPath, { flags: 'a' });
  const child = spawn(command, args, {
    cwd: options.cwd,
    env: { ...process.env, ...options.env },
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });

  child.stdout.pipe(logStream);
  child.stderr.pipe(logStream);

  child.on('exit', (code, signal) => {
    logStream.write(`\n[process-exit] code=${code ?? 'null'} signal=${signal ?? 'null'}\n`);
    logStream.end();
  });

  return { child, logPath };
}

async function waitForHttp(url, predicate, timeoutMs = 60000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      const body = await response.text();
      if (response.ok && predicate(body, response.status)) {
        return body;
      }
      lastError = new Error(`Received ${response.status} from ${url}`);
    } catch (error) {
      lastError = error;
    }
    await delay(1000);
  }

  throw new Error(`Timed out waiting for ${url}: ${lastError?.message || 'unknown error'}`);
}

async function ensureWorkerAlive(processHandle, timeoutMs = 10000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (processHandle.child.exitCode !== null) {
      throw new Error('Workflow worker exited before the smoke test started.');
    }
    await delay(500);
  }
}

async function readLogTail(logPath) {
  try {
    const content = await readFile(logPath, 'utf8');
    return content.split(/\r?\n/).slice(-120).join('\n');
  } catch {
    return '';
  }
}

async function stopProcess(processHandle) {
  if (!processHandle?.child || processHandle.child.exitCode !== null) {
    return;
  }

  processHandle.child.kill();
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline && processHandle.child.exitCode === null) {
    await delay(250);
  }

  if (processHandle.child.exitCode === null) {
    processHandle.child.kill('SIGKILL');
  }
}

function startWorkerProcess(python, sharedEnv) {
  return startProcess(
    'worker',
    python,
    ['-m', 'celery', '-A', 'app.celery_app:celery', 'worker', '--pool=solo', '--loglevel=info'],
    {
      cwd: repoRoot,
      env: {
        ...sharedEnv,
        CELERY_FS_ROLE: 'worker',
      },
    },
  );
}

async function postJson(url, payload, options = {}) {
  const response = await fetch(url, {
    method: options.method || 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    body: payload === undefined ? undefined : JSON.stringify(payload),
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  return { response, data };
}

async function runApprovalFlow(page) {
  await page.goto(`${frontendUrl}/onboarding`, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Tell AAIS what you want to automate.' }).waitFor();
  await page.getByPlaceholder('Summarize important emails and send alerts...').fill(
    'Summarize important emails and send alerts to Slack.',
  );
  await page.getByRole('button', { name: 'email' }).click();
  await page.getByRole('button', { name: 'slack' }).click();
  await page.getByRole('button', { name: 'Continue to Templates' }).click();
  await page.waitForURL(/\/workflows\/templates$/);

  const templateCard = page.locator('.workflow-template-card').filter({ hasText: 'Email Summary to Slack' }).first();
  await templateCard.getByRole('button', { name: 'Use Template' }).click();
  await page.waitForURL(/\/workflows\?workflowId=/);
  await page.getByRole('heading', { name: 'Workflow Builder' }).waitFor();
  const workflowNameInput = page
    .locator('.workflow-sidebar .workflow-section')
    .filter({ hasText: 'Workflow Name' })
    .locator('input')
    .first();
  await workflowNameInput.waitFor();
  assert.equal(await workflowNameInput.inputValue(), 'Email Summary to Slack');

  await page.getByRole('button', { name: /Run Live/i }).click();
  await page.waitForURL(/\/workflows\/runs\/.+/);
  await page.getByRole('heading', { name: 'Email Summary to Slack' }).waitFor();

  const runStatus = page.locator('.workflow-detail-header .status-pill').first();
  await page.waitForFunction(
    (element) => element?.textContent?.trim() === 'awaiting_approval',
    await runStatus.elementHandle(),
    { timeout: 30000 },
  );

  await page.goto(`${frontendUrl}/workflows/approvals`, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Workflow Approvals' }).waitFor();
  await page.getByRole('button', { name: 'Approve' }).first().click();

  await page.waitForURL(/\/workflows\/runs\/.+/);
  const resumedStatus = page.locator('.workflow-detail-header .status-pill').first();
  await page.waitForFunction(
    (element) => element?.textContent?.trim() === 'completed',
    await resumedStatus.elementHandle(),
    { timeout: 30000 },
  );

  await page.goto(`${frontendUrl}/workflows/runs`, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Workflow Runs' }).waitFor();
  await page.getByText('Email Summary to Slack').first().waitFor();
  await page.getByText('completed').first().waitFor();
}

async function runRecoveryFlow(page, runtime) {
  await page.goto(`${frontendUrl}/workflows/templates`, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Workflow Templates' }).waitFor();
  const safeTemplateCard = page
    .locator('.workflow-template-card')
    .filter({ hasText: 'Webhook Summary to Slack (Safe Mode)' })
    .first();
  await safeTemplateCard.getByRole('button', { name: 'Use Template' }).click();
  await page.waitForURL(/\/workflows\?workflowId=/);
  await page.getByRole('heading', { name: 'Workflow Builder' }).waitFor();

  const builderUrl = new URL(page.url());
  const workflowId = builderUrl.searchParams.get('workflowId');
  assert.ok(workflowId, 'Expected workflow id after creating safe template');

  const queued = await postJson(`${backendUrl}/integrations/webhooks/${workflowId}`, {
    text: 'Critical webhook payload',
    importance: 'high',
  }, {
    headers: {
      'x-workflow-secret': 'smoke-secret',
      'x-webhook-source': 'smoke-recovery',
    },
  });

  assert.equal(queued.response.status, 202);
  assert.equal(queued.data?.status, 'queued');
  const workflowRunId = queued.data?.workflow_run_id;
  assert.ok(workflowRunId, 'Expected workflow run id for webhook-triggered run');

  await page.goto(`${frontendUrl}/workflows/runs/${workflowRunId}`, { waitUntil: 'networkidle' });
  await page.getByRole('heading', { name: 'Webhook Summary to Slack (Safe Mode)' }).waitFor();

  const statusPill = page.locator('.workflow-detail-header .status-pill').first();
  await page.waitForFunction(
    (element) => element?.textContent?.trim() === 'running',
    await statusPill.elementHandle(),
    { timeout: 30000 },
  );
  await page.getByText('Prepare Slack Alert').first().waitFor();

  await stopProcess(runtime.worker);

  await page.waitForFunction(
    (element) => ['stale', 'recovering'].includes(element?.textContent?.trim()),
    await statusPill.elementHandle(),
    { timeout: 30000 },
  );

  runtime.worker = startWorkerProcess(runtime.python, runtime.sharedEnv);
  await ensureWorkerAlive(runtime.worker);

  await page.waitForFunction(
    (element) => element?.textContent?.trim() === 'completed',
    await statusPill.elementHandle(),
    { timeout: 30000 },
  );

  const detail = await postJson(`${backendUrl}/workflows/runs/${workflowRunId}`, undefined, { method: 'GET' });
  assert.equal(detail.response.status, 200);
  assert.equal(detail.data?.run?.status, 'completed');
  const ledgerTypes = Array.isArray(detail.data?.run?.output?.ledger)
    ? detail.data.run.output.ledger.map((entry) => entry.type)
    : [];
  assert.ok(ledgerTypes.includes('stale'));
  assert.ok(ledgerTypes.includes('recovery_queued'));
  assert.equal(detail.data?.run?.output?.plannedSteps?.[0]?.attempt, 1);
  assert.equal(detail.data?.run?.output?.plannedSteps?.[1]?.attempt, 2);
  const firstStepId = detail.data?.run?.output?.plannedSteps?.[0]?.stepId;
  assert.equal(
    detail.data?.run?.output?.steps?.filter((step) => step.stepId === firstStepId).length,
    1,
  );
}

async function runBrowserSmoke(runtime) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  try {
    await runApprovalFlow(page);
    await runRecoveryFlow(page, runtime);
  } finally {
    await browser.close();
  }
}

async function main() {
  await rm(runtimeRoot, { recursive: true, force: true });
  await mkdir(logRoot, { recursive: true });
  await mkdir(dataRoot, { recursive: true });
  await mkdir(brokerRoot, { recursive: true });

  const python = resolvePython();
  const sharedEnv = {
    JARVIS_DATA_DIR: dataRoot,
    CELERY_BROKER_URL: 'filesystem://',
    CELERY_RESULT_BACKEND: 'cache+memory://',
    CELERY_FS_BASE: brokerRoot,
    APP_BEARER_TOKEN: '',
    OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
    WORKFLOW_LEASE_SECONDS: '6',
    WORKFLOW_HEARTBEAT_INTERVAL_SECONDS: '1',
    WORKFLOW_QUEUE_STALE_SECONDS: '1',
  };

  const backend = startProcess(
    'backend',
    python,
    ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '5100'],
    {
      cwd: repoRoot,
      env: {
        ...sharedEnv,
        CELERY_FS_ROLE: 'producer',
      },
    },
  );

  let worker = startWorkerProcess(python, sharedEnv);

  const frontend = startProcess(
    'frontend',
    process.execPath,
    [path.resolve(frontendRoot, 'node_modules', 'vite', 'bin', 'vite.js'), '--host', '127.0.0.1', '--port', '3100', '--strictPort'],
    {
      cwd: frontendRoot,
      env: {
        VITE_API_URL: backendUrl,
      },
    },
  );

  try {
    await waitForHttp(`${backendUrl}/health`, (body) => body.includes('"status":"ok"'));
    await ensureWorkerAlive(worker);
    await waitForHttp(frontendUrl, (body) => body.includes('AAIS - AI System'));
    await runBrowserSmoke({
      python,
      sharedEnv,
      get worker() {
        return worker;
      },
      set worker(nextWorker) {
        worker = nextWorker;
      },
    });
  } catch (error) {
    const [backendLog, workerLog, frontendLog] = await Promise.all([
      readLogTail(backend.logPath),
      readLogTail(worker.logPath),
      readLogTail(frontend.logPath),
    ]);

    console.error('\n[workflow-smoke] Failure details');
    console.error(`backend log tail:\n${backendLog}`);
    console.error(`worker log tail:\n${workerLog}`);
    console.error(`frontend log tail:\n${frontendLog}`);
    throw error;
  } finally {
    await Promise.all([stopProcess(frontend), stopProcess(worker), stopProcess(backend)]);
    if (!process.env.KEEP_WORKFLOW_SMOKE_ARTIFACTS) {
      await rm(runtimeRoot, { recursive: true, force: true });
    }
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : error);
  process.exit(1);
});
