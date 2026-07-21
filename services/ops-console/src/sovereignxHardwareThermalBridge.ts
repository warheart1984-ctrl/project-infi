import { readFileSync } from 'node:fs';
import os from 'node:os';

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function toNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

export type SovereignXThermalSensorReading = {
  name: string;
  temperatureC: number;
  fanRpm: number;
  voltageV: number;
  powerWatts: number;
  status: 'ok' | 'warn' | 'critical';
};

export type SovereignXThermalBridgeSnapshot = {
  source: 'env' | 'file' | 'system';
  sourceDetail: string;
  vendor: string;
  deviceFamily: string;
  observedAtMs: number;
  healthy: boolean;
  sensors: SovereignXThermalSensorReading[];
  summary: {
    hottestSensor: string;
    hottestTemperatureC: number;
    averageTemperatureC: number;
    alertCount: number;
  };
};

export interface SovereignXHardwareThermalBridgeAdapterOptions {
  clock?: () => number;
  env?: NodeJS.ProcessEnv;
  filePath?: string;
  vendor?: string;
}

export class SovereignXHardwareThermalBridgeAdapter {
  private readonly clock: () => number;
  private readonly env: NodeJS.ProcessEnv;
  private readonly filePath?: string;
  private readonly vendor: string;

  constructor(options: SovereignXHardwareThermalBridgeAdapterOptions = {}) {
    this.clock = options.clock ?? (() => Date.now());
    this.env = options.env ?? process.env;
    this.filePath = options.filePath ?? this.env.SOVEREIGNX_THERMAL_SENSOR_PATH;
    this.vendor = options.vendor ?? this.env.SOVEREIGNX_THERMAL_SENSOR_VENDOR ?? 'generic-vendor';
  }

  snapshot(): SovereignXThermalBridgeSnapshot {
    const observedAtMs = this.clock();
    const envSnapshot = this.readEnvSnapshot(observedAtMs);
    if (envSnapshot) {
      return envSnapshot;
    }

    const fileSnapshot = this.readFileSnapshot(observedAtMs);
    if (fileSnapshot) {
      return fileSnapshot;
    }

    return buildSystemSnapshot(observedAtMs, this.vendor);
  }

  private readEnvSnapshot(observedAtMs: number): SovereignXThermalBridgeSnapshot | null {
    const raw = this.env.SOVEREIGNX_THERMAL_SENSOR_JSON;
    if (!raw) {
      return null;
    }

    try {
      const parsed = JSON.parse(raw) as unknown;
      return sanitizeThermalBridgeSnapshot(parsed, observedAtMs, 'env', 'SOVEREIGNX_THERMAL_SENSOR_JSON', this.vendor);
    } catch {
      return {
        ...buildSystemSnapshot(observedAtMs, this.vendor),
        source: 'env',
        sourceDetail: 'SOVEREIGNX_THERMAL_SENSOR_JSON (invalid JSON, fallback used)',
      };
    }
  }

  private readFileSnapshot(observedAtMs: number): SovereignXThermalBridgeSnapshot | null {
    if (!this.filePath) {
      return null;
    }

    try {
      const parsed = JSON.parse(readFileSync(this.filePath, 'utf8')) as unknown;
      return sanitizeThermalBridgeSnapshot(parsed, observedAtMs, 'file', this.filePath, this.vendor);
    } catch {
      return {
        ...buildSystemSnapshot(observedAtMs, this.vendor),
        source: 'file',
        sourceDetail: `${this.filePath} (invalid or unreadable, fallback used)`,
      };
    }
  }
}

export function createSovereignXHardwareThermalBridge(
  options: SovereignXHardwareThermalBridgeAdapterOptions = {},
): SovereignXHardwareThermalBridgeAdapter {
  return new SovereignXHardwareThermalBridgeAdapter(options);
}

function sanitizeThermalBridgeSnapshot(
  raw: unknown,
  observedAtMs: number,
  source: 'env' | 'file',
  sourceDetail: string,
  fallbackVendor: string,
): SovereignXThermalBridgeSnapshot {
  if (!isPlainObject(raw)) {
    return buildSystemSnapshot(observedAtMs, fallbackVendor);
  }

  const vendor = typeof raw.vendor === 'string' && raw.vendor.trim() ? raw.vendor.trim() : fallbackVendor;
  const deviceFamily = typeof raw.deviceFamily === 'string' && raw.deviceFamily.trim()
    ? raw.deviceFamily.trim()
    : 'thermal-bridge';
  const sensors = normalizeSensors(raw.sensors, observedAtMs, vendor);
  const summary = summarizeSensors(sensors);

  return {
    source,
    sourceDetail,
    vendor,
    deviceFamily,
    observedAtMs: toNumber(raw.observedAtMs, observedAtMs),
    healthy: summary.alertCount === 0,
    sensors,
    summary,
  };
}

function normalizeSensors(value: unknown, observedAtMs: number, vendor: string): SovereignXThermalSensorReading[] {
  if (!Array.isArray(value)) {
    return buildSyntheticSensors(observedAtMs, vendor);
  }

  const sensors = value
    .map((entry, index) => {
      if (!isPlainObject(entry)) {
        return null;
      }

      const temperatureC = toNumber(entry.temperatureC, 0);
      const fanRpm = Math.max(0, Math.round(toNumber(entry.fanRpm, 0)));
      const voltageV = Number(toNumber(entry.voltageV, 0).toFixed(3));
      const powerWatts = Number(toNumber(entry.powerWatts, 0).toFixed(2));
      const name = typeof entry.name === 'string' && entry.name.trim() ? entry.name.trim() : `${vendor}-sensor-${index + 1}`;
      const status = resolveSensorStatus(temperatureC);
      return {
        name,
        temperatureC,
        fanRpm,
        voltageV,
        powerWatts,
        status,
      } satisfies SovereignXThermalSensorReading;
    })
    .filter((sensor): sensor is SovereignXThermalSensorReading => sensor !== null);

  return sensors.length > 0 ? sensors : buildSyntheticSensors(observedAtMs, vendor);
}

function buildSyntheticSensors(observedAtMs: number, vendor: string): SovereignXThermalSensorReading[] {
  const systemLoad = clamp(os.loadavg()[0] / Math.max(1, os.cpus().length), 0, 1);
  const memoryPressure = os.totalmem() > 0 ? clamp(process.memoryUsage().rss / os.totalmem(), 0, 1) : 0;
  const cpuTempC = Number((40 + systemLoad * 26 + memoryPressure * 6).toFixed(1));
  const gpuTempC = Number((38 + systemLoad * 24 + memoryPressure * 7).toFixed(1));
  const boardTempC = Number((36 + systemLoad * 18 + memoryPressure * 5).toFixed(1));

  return [
    {
      name: `${vendor}-cpu-package`,
      temperatureC: cpuTempC,
      fanRpm: Math.round(900 + systemLoad * 1500),
      voltageV: Number((1.0 + systemLoad * 0.08).toFixed(3)),
      powerWatts: Number((38 + systemLoad * 22).toFixed(2)),
      status: resolveSensorStatus(cpuTempC),
    },
    {
      name: `${vendor}-gpu-hotspot`,
      temperatureC: gpuTempC,
      fanRpm: Math.round(1100 + systemLoad * 1700),
      voltageV: Number((1.02 + systemLoad * 0.06).toFixed(3)),
      powerWatts: Number((46 + systemLoad * 30).toFixed(2)),
      status: resolveSensorStatus(gpuTempC),
    },
    {
      name: `${vendor}-board-vrm`,
      temperatureC: boardTempC,
      fanRpm: Math.round(700 + systemLoad * 900),
      voltageV: Number((0.9 + memoryPressure * 0.1).toFixed(3)),
      powerWatts: Number((14 + memoryPressure * 12).toFixed(2)),
      status: resolveSensorStatus(boardTempC),
    },
  ];
}

function buildSystemSnapshot(observedAtMs: number, vendor: string): SovereignXThermalBridgeSnapshot {
  const sensors = buildSyntheticSensors(observedAtMs, vendor);
  const summary = summarizeSensors(sensors);
  return {
    source: 'system',
    sourceDetail: 'process load, memory, and synthetic thermal bridge',
    vendor,
    deviceFamily: 'thermal-bridge',
    observedAtMs,
    healthy: summary.alertCount === 0,
    sensors,
    summary,
  };
}

function summarizeSensors(sensors: SovereignXThermalSensorReading[]): SovereignXThermalBridgeSnapshot['summary'] {
  const hottest = sensors.reduce<SovereignXThermalSensorReading | null>((current, sensor) => {
    if (!current || sensor.temperatureC > current.temperatureC) {
      return sensor;
    }
    return current;
  }, null);
  const averageTemperatureC = sensors.length > 0
    ? sensors.reduce((sum, sensor) => sum + sensor.temperatureC, 0) / sensors.length
    : 0;
  const alertCount = sensors.filter((sensor) => sensor.status !== 'ok').length;

  return {
    hottestSensor: hottest?.name ?? 'none',
    hottestTemperatureC: Number((hottest?.temperatureC ?? 0).toFixed(1)),
    averageTemperatureC: Number(averageTemperatureC.toFixed(1)),
    alertCount,
  };
}

function resolveSensorStatus(temperatureC: number): SovereignXThermalSensorReading['status'] {
  if (temperatureC >= 85) {
    return 'critical';
  }
  if (temperatureC >= 72) {
    return 'warn';
  }
  return 'ok';
}
