import express, { type Request, Response, NextFunction } from "express";
import compression from "compression";
import { registerRoutes } from "./routes";
import { setupVeilChannel } from "./veil-channel.mirror";
import { startProjectSigilWatcher } from "./sigil-config";
import { serveStatic } from "./static";
import { runSelfInspectOnBoot } from "./self-inspection-boot";
import { createServer } from "http";
import { existsSync, readFileSync } from "fs";
import path from "path";

function normalizeEnvValue(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "";

  const quoted =
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"));
  if (!quoted) {
    const hashIndex = trimmed.indexOf(" #");
    return hashIndex >= 0 ? trimmed.slice(0, hashIndex).trimEnd() : trimmed;
  }

  const quote = trimmed[0];
  const inner = trimmed.slice(1, -1);
  if (quote === "'") return inner;
  return inner
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "\r")
    .replace(/\\t/g, "\t")
    .replace(/\\\\/g, "\\")
    .replace(/\\"/g, '"');
}

function loadEnvFile(filePath: string): void {
  if (!existsSync(filePath)) return;
  let content = "";
  try {
    content = readFileSync(filePath, "utf8");
  } catch {
    return;
  }

  const lines = content.split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    const normalized = trimmed.startsWith("export ")
      ? trimmed.slice("export ".length).trim()
      : trimmed;
    const eqIndex = normalized.indexOf("=");
    if (eqIndex <= 0) continue;

    const key = normalized.slice(0, eqIndex).trim();
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) continue;
    if (process.env[key] !== undefined) continue;

    const rawValue = normalized.slice(eqIndex + 1);
    process.env[key] = normalizeEnvValue(rawValue);
  }
}

function loadEnvironmentFiles(): void {
  const root = process.cwd();
  const mode = (process.env.NODE_ENV || "development").trim().toLowerCase() || "development";
  const files = [
    ".env",
    `.env.${mode}`,
    ".env.local",
    `.env.${mode}.local`,
  ];
  for (const file of files) {
    loadEnvFile(path.join(root, file));
  }
}

loadEnvironmentFiles();

const app = express();
const httpServer = createServer(app);
const jsonBodyLimit = process.env.JSON_BODY_LIMIT || "1mb";
const importJsonBodyLimit = process.env.IMPORT_JSON_BODY_LIMIT || "200mb";
const urlencodedBodyLimit = process.env.URLENCODED_BODY_LIMIT || "1mb";
const enableHttpCompression = process.env.ENABLE_HTTP_COMPRESSION !== "0";
const httpCompressionThresholdBytes = Math.max(
  0,
  Number.parseInt(process.env.HTTP_COMPRESSION_THRESHOLD || "1024", 10) || 1024,
);
const logApiResponseBody = process.env.LOG_API_RESPONSE_BODY === "1";
const apiLogBodyMaxLength = Math.max(
  80,
  Number.parseInt(process.env.LOG_API_RESPONSE_BODY_MAX || "1000", 10) || 1000,
);
const nodeEnv = (process.env.NODE_ENV || "development").trim().toLowerCase();
const sigilTraceBarrierEnvRaw = (process.env.SIGIL_TRACE_BARRIER || "true").trim().toLowerCase();
const sigilTraceBarrierEnvEnabled =
  sigilTraceBarrierEnvRaw !== "0" &&
  sigilTraceBarrierEnvRaw !== "false" &&
  sigilTraceBarrierEnvRaw !== "no";
const sigilTraceBarrierEnabled = nodeEnv === "production" ? true : sigilTraceBarrierEnvEnabled;
const sigilTraceBarrierMode = nodeEnv === "production" ? "prod-forced" : "env-controlled";

declare module "http" {
  interface IncomingMessage {
    rawBody: unknown;
  }
}

const captureRawBody = (req: Request, _res: Response, buf: Buffer) => {
  req.rawBody = buf;
};

const defaultJsonParser = express.json({
  limit: jsonBodyLimit,
  verify: captureRawBody,
});

const importJsonParser = express.json({
  limit: importJsonBodyLimit,
  verify: captureRawBody,
});

if (enableHttpCompression) {
  app.use(
    compression({
      threshold: httpCompressionThresholdBytes,
      filter: (req, res) => {
        if (req.path === "/api/chat") return false;
        if (
          req.path === "/api/import" ||
          req.path === "/api/spiral/import" ||
          req.path === "/api/save-transcript"
        ) {
          return false;
        }
        return compression.filter(req, res);
      },
    }),
  );
}

app.use((req, res, next) => {
  if (
    req.method === "POST" &&
    (req.path === "/api/import" ||
      req.path === "/api/spiral/import" ||
      req.path === "/api/save-transcript")
  ) {
    return importJsonParser(req, res, next);
  }

  return defaultJsonParser(req, res, next);
});

app.use(express.urlencoded({ extended: false, limit: urlencodedBodyLimit }));

export function log(message: string, source = "express") {
  const formattedTime = new Date().toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });

  console.log(`${formattedTime} [${source}] ${message}`);
}

function isRetriableListenError(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const code = (error as NodeJS.ErrnoException).code;
  return code === "ENOTSUP" || code === "EAFNOSUPPORT" || code === "EADDRNOTAVAIL";
}

function normalizeHost(rawHost: string): string {
  const value = rawHost.trim();
  if (!value) return "0.0.0.0";
  if (value === "localhost") return "127.0.0.1";
  return value;
}

async function listenWithHost(
  server: ReturnType<typeof createServer>,
  options: { port: number; host: string; reusePort: boolean },
): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const onError = (err: Error) => {
      server.off("listening", onListening);
      reject(err);
    };

    const onListening = () => {
      server.off("error", onError);
      resolve();
    };

    server.once("error", onError);
    server.once("listening", onListening);
    server.listen({
      port: options.port,
      host: options.host,
      ...(options.reusePort ? { reusePort: true } : {}),
    });
  });
}

interface ListenAttempt {
  host: string;
  reusePort: boolean;
}

function buildListenAttempts(
  configuredHost: string,
  fallbackHost: string,
  preferReusePort: boolean,
): ListenAttempt[] {
  const attempts: ListenAttempt[] = [];
  const pushUnique = (attempt: ListenAttempt) => {
    const exists = attempts.some(
      (entry) => entry.host === attempt.host && entry.reusePort === attempt.reusePort,
    );
    if (!exists) attempts.push(attempt);
  };

  pushUnique({ host: configuredHost, reusePort: preferReusePort });
  pushUnique({ host: configuredHost, reusePort: false });
  pushUnique({ host: fallbackHost, reusePort: false });
  pushUnique({ host: fallbackHost, reusePort: preferReusePort });
  return attempts;
}

app.use((req, res, next) => {
  const start = Date.now();
  const path = req.path;
  let capturedJsonResponse: unknown;

  if (logApiResponseBody) {
    const originalResJson = res.json;
    res.json = function (bodyJson, ...args) {
      capturedJsonResponse = bodyJson;
      return originalResJson.apply(res, [bodyJson, ...args]);
    };
  }

  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path.startsWith("/api")) {
      let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
      if (logApiResponseBody && capturedJsonResponse !== undefined) {
        const serialized = JSON.stringify(capturedJsonResponse);
        const preview =
          serialized.length > apiLogBodyMaxLength
            ? `${serialized.slice(0, apiLogBodyMaxLength)}...<truncated>`
            : serialized;
        logLine += ` :: ${preview}`;
      }

      log(logLine);
    }
  });

  next();
});

(async () => {
  const selfInspectBoot = await runSelfInspectOnBoot(process.argv.slice(2));
  if (selfInspectBoot.requested && selfInspectBoot.index) {
    log(
      `self-inspect snapshot written to ${selfInspectBoot.snapshotPath || ".local/self-inspect/latest.json"} (${selfInspectBoot.index.fileCount} files, ${selfInspectBoot.index.symbolCount} symbols)`,
      "self-inspect",
    );
  }

  await registerRoutes(httpServer, app);
  startProjectSigilWatcher();
  setupVeilChannel(httpServer);

  app.use((err: any, _req: Request, res: Response, next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";

    console.error("Internal Server Error:", err);

    if (res.headersSent) {
      return next(err);
    }

    return res.status(status).json({ message });
  });

  // importantly only setup vite in development and after
  // setting up all the other routes so the catch-all route
  // doesn't interfere with the other routes
  if (process.env.NODE_ENV === "production") {
    serveStatic(app);
  } else {
    const { setupVite } = await import("./vite");
    await setupVite(httpServer, app);
  }

  // ALWAYS serve the app on the port specified in the environment variable PORT
  // Other ports are firewalled. Default to 5000 if not specified.
  // this serves both the API and the client.
  // It is the only port that is not firewalled.
  const port = parseInt(process.env.PORT || "5000", 10);
  const configuredHost = normalizeHost(process.env.HOST || "");
  const fallbackHost = configuredHost === "127.0.0.1" ? "0.0.0.0" : "127.0.0.1";
  const preferReusePort =
    process.platform !== "win32" && (process.env.REUSE_PORT || "1").trim() !== "0";
  const listenAttempts = buildListenAttempts(configuredHost, fallbackHost, preferReusePort);

  let serverStarted = false;
  let lastRetriableError: unknown = null;

  for (let index = 0; index < listenAttempts.length; index += 1) {
    const attempt = listenAttempts[index];
    try {
      await listenWithHost(httpServer, {
        port,
        host: attempt.host,
        reusePort: attempt.reusePort,
      });
      log(
        `serving on port ${port} (host ${attempt.host}, reusePort=${attempt.reusePort ? "on" : "off"})`,
      );
      serverStarted = true;
      break;
    } catch (error) {
      if (!isRetriableListenError(error)) {
        throw error;
      }

      lastRetriableError = error;
      if (index < listenAttempts.length - 1) {
        log(
          `listen failed on ${attempt.host} (reusePort=${attempt.reusePort ? "on" : "off"}, ${(error as NodeJS.ErrnoException).code ?? "error"}), retrying`,
          "startup",
        );
      }
    }
  }

  if (!serverStarted) {
    throw lastRetriableError;
  }

  log(
    `[spiral] Barrier Mode: ${sigilTraceBarrierMode} (enabled=${sigilTraceBarrierEnabled})`,
    "startup",
  );
})();
