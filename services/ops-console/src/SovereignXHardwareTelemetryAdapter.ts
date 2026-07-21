import { readFileSync } from 'node:fs';
import os from 'node:os';

import type {
  SovereignXHardwareCycle,
  SovereignXHardwareGovernanceContract,
  SovereignXHardwareInvariants,
  SovereignXHardwareState,
  SovereignXHardwareTelemetry,
  SovereignXHardwareTelemetrySample,
  SovereignXHardwareTransition,
} from '@aaes-os/sovereignx-router';

import type { SovereignXThermalBridgeSnapshot } from './sovereignxHardwareThermalBridge.js';

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function toNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function normalizeSamples(samples: unknown, now: number): SovereignXHardwareTelemetrySample[] | undefined {
  if (!Array.isArray(samples)) {
    return undefined;
  }

  const normalized = samples
    .map((sample) => {
      if (!isPlainObject(sample)) {
        return null;
      }

      const atMs = toNumber(sample.atMs, now);
      const utilization = clamp(toNumber(sample.utilization, 0), 0, 1);
      return { atMs, utilization };
    })
    .filter((sample): sample is SovereignXHardwareTelemetrySample => sample !== null);

  return normalized.length > 0 ? normalized : undefined;
}

function sanitizeTelemetry(raw: unknown, now: number, fallback: SovereignXHardwareTelemetry): SovereignXHardwareTelemetry {
  if (!isPlainObject(raw)) {
    return fallback;
  }

  return {
    cpuTempC: toNumber(raw.cpuTempC, fallback.cpuTempC),
    gpuTempC: toNumber(raw.gpuTempC, fallback.gpuTempC),
    cpuVolt: toNumber(raw.cpuVolt, fallback.cpuVolt),
    gpuVolt: toNumber(raw.gpuVolt, fallback.gpuVolt),
    powerDrawFraction: clamp(toNumber(raw.powerDrawFraction, fallback.powerDrawFraction), 0, 1),
    utilization: clamp(toNumber(raw.utilization, fallback.utilization), 0, 1),
    utilizationSamples: normalizeSamples(raw.utilizationSamples, now) ?? fallback.utilizationSamples,
    observedAtMs: toNumber(raw.observedAtMs, now),
  };
}

function buildFallbackTelemetry(now: number, processUtilization: number): SovereignXHardwareTelemetry {
  const memory = process.memoryUsage();
  const memoryPressure = os.totalmem() > 0 ? clamp(memory.rss / os.totalmem(), 0, 1) : 0;
  const normalizedUtilization = clamp(processUtilization, 0, 1);

  return {
    cpuTempC: Number((38 + normalizedUtilization * 26 + memoryPressure * 8).toFixed(2)),
    gpuTempC: Number((36 + normalizedUtilization * 24 + memoryPressure * 7).toFixed(2)),
    cpuVolt: Number((1.0 + normalizedUtilization * 0.18).toFixed(3)),
    gpuVolt: Number((1.02 + normalizedUtilization * 0.16).toFixed(3)),
    powerDrawFraction: Number(clamp(0.18 + normalizedUtilization * 0.52 + memoryPressure * 0.12, 0, 1).toFixed(3)),
    utilization: Number(normalizedUtilization.toFixed(3)),
    utilizationSamples: [
      {
        atMs: now - 200,
        utilization: Number(clamp(normalizedUtilization * 0.9, 0, 1).toFixed(3)),
      },
      {
        atMs: now - 100,
        utilization: Number(normalizedUtilization.toFixed(3)),
      },
      {
        atMs: now,
        utilization: Number(clamp(normalizedUtilization * 1.05, 0, 1).toFixed(3)),
      },
    ],
    observedAtMs: now,
  };
}

export interface SovereignXHardwareTelemetrySnapshot {
  source: 'env' | 'file' | 'system';
  sourceDetail: string;
  telemetry: SovereignXHardwareTelemetry;
}

export interface SovereignXHardwareSnapshot extends SovereignXHardwareTelemetrySnapshot {
  cycle: SovereignXHardwareCycle;
  governor: {
    contract: SovereignXHardwareGovernanceContract;
    invariants: SovereignXHardwareInvariants;
    previousState: SovereignXHardwareState;
    state: SovereignXHardwareState;
    recentEvents: SovereignXHardwareTransition[];
  };
  thermalBridge?: SovereignXThermalBridgeSnapshot;
}

export interface SovereignXHardwareTelemetryAdapterOptions {
  clock?: () => number;
  env?: NodeJS.ProcessEnv;
  filePath?: string;
}

export class SovereignXHardwareTelemetryAdapter {
  private readonly clock: () => number;
  private readonly env: NodeJS.ProcessEnv;
  private readonly filePath?: string;
  private lastWallClockMs: number;
  private lastCpuUsage = process.cpuUsage();

  constructor(options: SovereignXHardwareTelemetryAdapterOptions = {}) {
    this.clock = options.clock ?? (() => Date.now());
    this.env = options.env ?? process.env;
    this.filePath = options.filePath ?? this.env.SOVEREIGNX_HARDWARE_TELEMETRY_PATH;
    this.lastWallClockMs = this.clock();
  }

  snapshot(): SovereignXHardwareTelemetrySnapshot {
    const now = this.clock();

    const envTelemetry = this.readEnvTelemetry(now);
    if (envTelemetry) {
      return envTelemetry;
    }

    const fileTelemetry = this.readFileTelemetry(now);
    if (fileTelemetry) {
      return fileTelemetry;
    }

    const systemUtilization = this.resolveProcessUtilization(now);
    return {
      source: 'system',
      sourceDetail: 'process cpu and memory signals',
      telemetry: buildFallbackTelemetry(now, systemUtilization),
    };
  }

  private readEnvTelemetry(now: number): SovereignXHardwareTelemetrySnapshot | null {
    const raw = this.env.SOVEREIGNX_HARDWARE_TELEMETRY_JSON;
    if (!raw) {
      return null;
    }

    try {
      const parsed = JSON.parse(raw) as unknown;
      return {
        source: 'env',
        sourceDetail: 'SOVEREIGNX_HARDWARE_TELEMETRY_JSON',
        telemetry: sanitizeTelemetry(parsed, now, buildFallbackTelemetry(now, this.resolveProcessUtilization(now))),
      };
    } catch {
      return {
        source: 'env',
        sourceDetail: 'SOVEREIGNX_HARDWARE_TELEMETRY_JSON (invalid JSON, fallback used)',
        telemetry: buildFallbackTelemetry(now, this.resolveProcessUtilization(now)),
      };
    }
  }

  private readFileTelemetry(now: number): SovereignXHardwareTelemetrySnapshot | null {
    if (!this.filePath) {
      return null;
    }

    try {
      const parsed = JSON.parse(readFileSync(this.filePath, 'utf8')) as unknown;
      return {
        source: 'file',
        sourceDetail: this.filePath,
        telemetry: sanitizeTelemetry(parsed, now, buildFallbackTelemetry(now, this.resolveProcessUtilization(now))),
      };
    } catch {
      return {
        source: 'file',
        sourceDetail: `${this.filePath} (invalid or unreadable, fallback used)`,
        telemetry: buildFallbackTelemetry(now, this.resolveProcessUtilization(now)),
      };
    }
  }

  private resolveProcessUtilization(now: number): number {
    const cpu = process.cpuUsage(this.lastCpuUsage);
    const wallDeltaMs = Math.max(1, now - this.lastWallClockMs);
    const cpuDeltaMs = (cpu.user + cpu.system) / 1000;
    const cores = Math.max(1, os.cpus().length);

    this.lastWallClockMs = now;
    this.lastCpuUsage = process.cpuUsage();

    return clamp(cpuDeltaMs / (wallDeltaMs * cores), 0, 1);
  }
}

export function createSovereignXHardwareTelemetryAdapter(
  options: SovereignXHardwareTelemetryAdapterOptions = {},
): SovereignXHardwareTelemetryAdapter {
  return new SovereignXHardwareTelemetryAdapter(options);
}
