import { access } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import { spawn } from "node:child_process";
import { once } from "node:events";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const siteRoot = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(siteRoot, "..");
const docsHost = getArg("--docs-host", "127.0.0.1");
const docsPort = Number(getArg("--docs-port", "3000"));
const apiHost = getArg("--api-host", "127.0.0.1");
const apiPort = Number(getArg("--api-port", "8787"));
const ledgerPath = getArg("--ledger-path", "");
const browserMode = getArg("--browser", hasFlag("--no-open") ? "headless" : "auto");
const browserPath = normalizeBrowserPath(getArg("--browser-path", "/docs/visualizer/sovereign-ide"));
const browserDocsHost = browserHost(docsHost);
const browserApiHost = browserHost(apiHost);

if (!["auto", "open", "headless"].includes(browserMode)) {
  throw new Error(`Invalid --browser value: ${browserMode}. Expected auto, open, or headless.`);
}

function getArg(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
}

function hasFlag(name) {
  return process.argv.includes(name);
}

function normalizeBrowserPath(route) {
  if (!route) {
    return "/docs/visualizer/sovereign-ide";
  }
  return route.startsWith("/") ? route : `/${route}`;
}

function browserHost(bindHost) {
  if (bindHost === "0.0.0.0" || bindHost === "::") {
    return "127.0.0.1";
  }
  return bindHost;
}

async function fileExists(filePath) {
  try {
    await access(filePath, fsConstants.X_OK);
    return true;
  } catch {
    return false;
  }
}

async function resolvePython() {
  const candidates = [
    process.env.SOVEREIGN_IDE_PYTHON,
    path.join(repoRoot, ".venv", "Scripts", "python.exe"),
    path.join(repoRoot, ".venv-test", "Scripts", "python.exe"),
    "python",
    "py",
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (candidate === "python" || candidate === "py") {
      return candidate;
    }
    if (await fileExists(candidate)) {
      return candidate;
    }
  }

  throw new Error("Unable to locate a Python executable for sovereign-ide");
}

function spawnProcess(command, args, options = {}) {
  const child = spawn(command, args, {
    stdio: "inherit",
    shell: false,
    ...options,
  });
  child.on("error", (error) => {
    console.error(error);
    process.exitCode = 1;
  });
  return child;
}

async function runCommand(command, args, options = {}) {
  const child = spawnProcess(command, args, options);
  const [code] = await once(child, "close");
  if (code !== 0) {
    throw new Error(`${command} exited with code ${code}`);
  }
}

async function waitForEndpoint(url, timeoutMs = 30000, intervalMs = 500) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch {
      // keep polling
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

function openBrowser(url) {
  const platform = process.platform;
  if (platform === "win32") {
    const child = spawn("cmd", ["/c", "start", "", url], {
      detached: true,
      stdio: "ignore",
      windowsHide: true,
    });
    child.on("error", () => {
      console.warn(`Unable to open browser for ${url}`);
    });
    child.unref();
    return true;
  }
  if (platform === "darwin") {
    const child = spawn("open", [url], {
      detached: true,
      stdio: "ignore",
    });
    child.on("error", () => {
      console.warn(`Unable to open browser for ${url}`);
    });
    child.unref();
    return true;
  }
  const opener = spawn("xdg-open", [url], {
    detached: true,
    stdio: "ignore",
  });
  opener.on("error", () => {
    console.warn(`Unable to open browser for ${url}`);
  });
  opener.unref();
  return true;
}

async function main() {
  await runCommand(process.execPath, [path.join(scriptDir, "build-docs-site.mjs")], {
    cwd: siteRoot,
  });

  const python = await resolvePython();
  const apiArgs = ["-m", "sovereign_ide", "--serve-api", "--api-host", apiHost, "--api-port", String(apiPort)];
  if (ledgerPath) {
    apiArgs.push("--ledger-path", ledgerPath);
  }
  const apiChild = spawnProcess(python, apiArgs, {
    cwd: path.join(repoRoot, "sovereign-ide"),
    env: {
      ...process.env,
      SOVEREIGN_IDE_API_BASE_URL: `http://${browserApiHost}:${apiPort}`,
    },
  });

  const docsChild = spawnProcess(process.execPath, [path.join(scriptDir, "serve-docs-site.mjs"), "--host", docsHost, "--port", String(docsPort)], {
    cwd: siteRoot,
    env: {
      ...process.env,
      SOVEREIGN_IDE_API_BASE_URL: `http://${browserApiHost}:${apiPort}`,
    },
  });

  const docsUrl = `http://${browserDocsHost}:${docsPort}${browserPath}`;
  const apiUrl = `http://${apiHost}:${apiPort}/health`;
  const readySignal = Promise.all([waitForEndpoint(docsUrl), waitForEndpoint(apiUrl)]);
  readySignal
    .then(() => {
      if (browserMode === "auto" || browserMode === "open") {
        openBrowser(docsUrl);
      }
    })
    .catch((error) => {
      console.warn(error instanceof Error ? error.message : error);
    });

  const shutdown = () => {
    for (const child of [docsChild, apiChild]) {
      if (!child.killed) {
        child.kill();
      }
    }
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  const exitCode = await Promise.race([
    once(docsChild, "close").then(([code]) => code ?? 0),
    once(apiChild, "close").then(([code]) => code ?? 0),
  ]);

  shutdown();
  process.exitCode = exitCode;
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
