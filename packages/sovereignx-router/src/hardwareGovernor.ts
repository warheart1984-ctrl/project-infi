import { createHash, createPrivateKey, sign as signPayload } from 'node:crypto';

function clone<T>(value: T): T {
  return structuredClone(value);
}

function roundTo(value: number, digits: number): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function isFiniteNumber(value: number): boolean {
  return Number.isFinite(value) && !Number.isNaN(value);
}

function mean(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function sha3_512(value: string): string {
  return createHash('sha3-512').update(value).digest('hex');
}

function canonicalStringify(value: unknown): string {
  return JSON.stringify(value, (_key, current) => current, 0);
}

export interface SovereignXHardwareTelemetrySample {
  atMs: number;
  utilization: number;
}

export interface SovereignXHardwareTelemetry {
  cpuTempC: number;
  gpuTempC: number;
  cpuVolt: number;
  gpuVolt: number;
  powerDrawFraction: number;
  utilization: number;
  utilizationSamples?: SovereignXHardwareTelemetrySample[];
  observedAtMs?: number;
}

export interface SovereignXHardwareInvariants {
  maxTempC: number;
  maxVolt: number;
  maxPowerFraction: number;
  minHeadroomC: number;
  promotionWindowMs: number;
  retractionDelayMs: number;
  telemetryWindowMs: number;
}

export type SovereignXHardwareDecision = 'PROMOTE' | 'RETRACT' | 'MAINTAIN' | 'QUARANTINE';

export interface SovereignXHardwareEvidence {
  valid: boolean;
  reason: string;
  telemetryHash: string;
  observedAtMs: number;
}

export interface SovereignXHardwareTransition {
  id: string;
  kind: SovereignXHardwareDecision;
  timestamp: string;
  authority: string;
  telemetryHash: string;
  replayHash: string;
  invariantState: SovereignXHardwareInvariants;
  fromFrequencyMhz: number;
  toFrequencyMhz: number;
  fromVoltageV: number;
  toVoltageV: number;
  frequencyDeltaMhz: number;
  voltageDeltaV: number;
  evidence: SovereignXHardwareEvidence;
  replayable: boolean;
  authoritySignature: string;
  reason: string;
}

export interface SovereignXHardwareState {
  currentFrequencyMhz: number;
  currentVoltageV: number;
  lastUpdatedAtMs: number;
  lastDecision: SovereignXHardwareDecision;
}

export interface SovereignXHardwareCycle {
  decision: SovereignXHardwareDecision;
  headroomC: number;
  loadFactor: number;
  evidence: SovereignXHardwareEvidence;
  transitions: SovereignXHardwareTransition[];
  state: SovereignXHardwareState;
}

export interface SovereignXHardwareGovernanceContract {
  Contract: {
    Name: string;
    Version: string;
    Authority: string;
    IssuedBy: string;
    Purpose: string;
  };
  Invariants: {
    ThermalLimit: {
      MaxTemp: number;
      MinHeadroom: number;
      Unit: string;
      ViolationAction: 'RetractClock';
    };
    VoltageLimit: {
      MaxVolt: number;
      Unit: string;
      ViolationAction: 'RetractClock';
    };
    PowerLimit: {
      MaxPowerFraction: number;
      Unit: string;
      ViolationAction: 'RetractClock';
    };
    PromotionWindow: {
      Duration: number;
      Unit: string;
    };
    RetractionDelay: {
      Duration: number;
      Unit: string;
    };
  };
  Evidence: {
    Telemetry: {
      Fields: string[];
      HashAlgorithm: 'SHA3-512';
      ValidationMethod: string;
    };
    PromotionEvent: {
      Type: 'PROMOTION';
      SignedBy: string;
      Replayable: true;
      ReplayHash: string;
    };
    RetractionEvent: {
      Type: 'RETRACTION';
      SignedBy: string;
      Replayable: true;
      ReplayHash: string;
    };
  };
  ReplaySignature: {
    Algorithm: 'Ed25519';
    Fields: string[];
    Verification: string;
  };
  GovernanceFlow: {
    Promotion: {
      Condition: string;
      Action: string;
      Authority: string;
      Evidence: string;
    };
    Retraction: {
      Condition: string;
      Action: string;
      Authority: string;
      Evidence: string;
    };
    Validation: {
      Runtime: string;
      Method: string;
      Escalation: string;
    };
  };
  Lineage: {
    ParentContract: string;
    ChildModules: string[];
    ReplayIntegration: string;
  };
};

export interface SovereignXHardwareGovernanceContractIssue {
  field: string;
  message: string;
  severity: 'info' | 'warn' | 'error';
}

export interface SovereignXHardwareGovernanceContractValidation {
  passed: boolean;
  issues: SovereignXHardwareGovernanceContractIssue[];
}

export interface SovereignXHardwareGovernorOptions {
  clock?: () => number;
  authority?: string;
  authorityKeyPem?: string;
  initialFrequencyMhz?: number;
  initialVoltageV?: number;
  invariants?: Partial<SovereignXHardwareInvariants>;
}

export const sovereignXHardwareGovernanceContract: SovereignXHardwareGovernanceContract = {
  Contract: {
    Name: 'GOA-Constitutional-Hardware-Governance',
    Version: '1.0',
    Authority: 'SovereignX.Router',
    IssuedBy: 'PrimeArchitect',
    Purpose: 'To govern dynamic CPU/GPU frequency promotion and retraction under constitutional invariants.',
  },
  Invariants: {
    ThermalLimit: {
      MaxTemp: 85.0,
      MinHeadroom: 10.0,
      Unit: 'Celsius',
      ViolationAction: 'RetractClock',
    },
    VoltageLimit: {
      MaxVolt: 1.45,
      Unit: 'Volts',
      ViolationAction: 'RetractClock',
    },
    PowerLimit: {
      MaxPowerFraction: 0.9,
      Unit: 'FractionOfPSU',
      ViolationAction: 'RetractClock',
    },
    PromotionWindow: {
      Duration: 200,
      Unit: 'Milliseconds',
    },
    RetractionDelay: {
      Duration: 500,
      Unit: 'Milliseconds',
    },
  },
  Evidence: {
    Telemetry: {
      Fields: ['cpu_temp', 'gpu_temp', 'cpu_volt', 'gpu_volt', 'power_draw', 'utilization'],
      HashAlgorithm: 'SHA3-512',
      ValidationMethod: 'CIR.validateTelemetry',
    },
    PromotionEvent: {
      Type: 'PROMOTION',
      SignedBy: 'PrimeArchitectKey',
      Replayable: true,
      ReplayHash: 'TelemetryHash + Timestamp + FrequencyDelta',
    },
    RetractionEvent: {
      Type: 'RETRACTION',
      SignedBy: 'PrimeArchitectKey',
      Replayable: true,
      ReplayHash: 'TelemetryHash + Timestamp + FrequencyDelta',
    },
  },
  ReplaySignature: {
    Algorithm: 'Ed25519',
    Fields: ['EventType', 'TelemetryHash', 'InvariantState', 'Timestamp', 'AuthoritySignature'],
    Verification: 'CIR.verifyReplaySignature',
  },
  GovernanceFlow: {
    Promotion: {
      Condition: 'Headroom > MinHeadroom AND Utilization > 0.8',
      Action: 'IncreaseClock + IncreaseVoltage',
      Authority: 'SovereignX.Router',
      Evidence: 'PromotionEvent',
    },
    Retraction: {
      Condition: 'Headroom < MinHeadroom OR PowerDraw > MaxPowerFraction',
      Action: 'DecreaseClock + DecreaseVoltage',
      Authority: 'SovereignX.Router',
      Evidence: 'RetractionEvent',
    },
    Validation: {
      Runtime: 'CIR',
      Method: 'validateTelemetry',
      Escalation: 'FailurePathRegistry',
    },
  },
  Lineage: {
    ParentContract: 'CCS.v1.0',
    ChildModules: ['VEILTHORN.InferenceGovernor', 'SovereignX.HardwareGovernor'],
    ReplayIntegration: 'Nova.Lineage.RecordEvent',
  },
};

function buildHashPayload(
  telemetry: SovereignXHardwareTelemetry,
  invariants: SovereignXHardwareInvariants,
  observedAtMs: number,
): string {
  return canonicalStringify({
    observedAtMs,
    telemetry: {
      cpuTempC: telemetry.cpuTempC,
      gpuTempC: telemetry.gpuTempC,
      cpuVolt: telemetry.cpuVolt,
      gpuVolt: telemetry.gpuVolt,
      powerDrawFraction: telemetry.powerDrawFraction,
      utilization: telemetry.utilization,
      utilizationSamples: telemetry.utilizationSamples?.map((sample) => ({
        atMs: sample.atMs,
        utilization: sample.utilization,
      })) ?? [],
    },
    invariants,
  });
}

function buildSignature(
  payload: string,
  authorityKeyPem?: string,
): string {
  if (!authorityKeyPem) {
    return sha3_512(payload);
  }

  try {
    const key = createPrivateKey(authorityKeyPem);
    return signPayload(null, Buffer.from(payload), key).toString('base64');
  } catch {
    return sha3_512(payload);
  }
}

export function validateSovereignXHardwareGovernanceContract(
  contract: SovereignXHardwareGovernanceContract = sovereignXHardwareGovernanceContract,
): SovereignXHardwareGovernanceContractValidation {
  const issues: SovereignXHardwareGovernanceContractIssue[] = [];

  if (contract.Contract.Name !== 'GOA-Constitutional-Hardware-Governance') {
    issues.push({ field: 'Contract.Name', message: 'unexpected contract name', severity: 'error' });
  }
  if (contract.Invariants.ThermalLimit.MaxTemp <= 0) {
    issues.push({ field: 'Invariants.ThermalLimit.MaxTemp', message: 'thermal limit must be positive', severity: 'error' });
  }
  if (contract.Invariants.ThermalLimit.MinHeadroom <= 0) {
    issues.push({ field: 'Invariants.ThermalLimit.MinHeadroom', message: 'headroom must be positive', severity: 'error' });
  }
  if (contract.Invariants.VoltageLimit.MaxVolt <= 0) {
    issues.push({ field: 'Invariants.VoltageLimit.MaxVolt', message: 'voltage limit must be positive', severity: 'error' });
  }
  if (contract.Invariants.PowerLimit.MaxPowerFraction <= 0 || contract.Invariants.PowerLimit.MaxPowerFraction > 1) {
    issues.push({ field: 'Invariants.PowerLimit.MaxPowerFraction', message: 'power fraction must be within 0..1', severity: 'error' });
  }
  if (contract.ReplaySignature.Algorithm !== 'Ed25519') {
    issues.push({ field: 'ReplaySignature.Algorithm', message: 'replay signature must use Ed25519', severity: 'error' });
  }
  if (!contract.Evidence.Telemetry.Fields.includes('cpu_temp') || !contract.Evidence.Telemetry.Fields.includes('utilization')) {
    issues.push({ field: 'Evidence.Telemetry.Fields', message: 'required telemetry fields are missing', severity: 'error' });
  }

  return {
    passed: !issues.some((issue) => issue.severity === 'error'),
    issues,
  };
}

export class SovereignXHardwareGovernor {
  private readonly clock: () => number;
  private readonly authority: string;
  private readonly authorityKeyPem?: string;
  private readonly invariants: SovereignXHardwareInvariants;
  private readonly events: SovereignXHardwareTransition[] = [];
  private state: SovereignXHardwareState;

  constructor(options: SovereignXHardwareGovernorOptions = {}) {
    this.clock = options.clock ?? (() => Date.now());
    this.authority = options.authority ?? sovereignXHardwareGovernanceContract.Contract.Authority;
    this.authorityKeyPem = options.authorityKeyPem;
    this.invariants = {
      maxTempC: sovereignXHardwareGovernanceContract.Invariants.ThermalLimit.MaxTemp,
      maxVolt: sovereignXHardwareGovernanceContract.Invariants.VoltageLimit.MaxVolt,
      maxPowerFraction: sovereignXHardwareGovernanceContract.Invariants.PowerLimit.MaxPowerFraction,
      minHeadroomC: sovereignXHardwareGovernanceContract.Invariants.ThermalLimit.MinHeadroom,
      promotionWindowMs: sovereignXHardwareGovernanceContract.Invariants.PromotionWindow.Duration,
      retractionDelayMs: sovereignXHardwareGovernanceContract.Invariants.RetractionDelay.Duration,
      telemetryWindowMs: 200,
      ...options.invariants,
    };
    this.state = {
      currentFrequencyMhz: options.initialFrequencyMhz ?? 3_500,
      currentVoltageV: options.initialVoltageV ?? 1.1,
      lastUpdatedAtMs: this.clock(),
      lastDecision: 'MAINTAIN',
    };
  }

  getContract(): SovereignXHardwareGovernanceContract {
    return clone(sovereignXHardwareGovernanceContract);
  }

  getInvariants(): SovereignXHardwareInvariants {
    return clone(this.invariants);
  }

  getState(): SovereignXHardwareState {
    return clone(this.state);
  }

  listEvents(): SovereignXHardwareTransition[] {
    return this.events.map((event) => clone(event));
  }

  validateTelemetry(telemetry: SovereignXHardwareTelemetry): SovereignXHardwareEvidence {
    const observedAtMs = telemetry.observedAtMs ?? this.clock();
    const payload = buildHashPayload(telemetry, this.invariants, observedAtMs);
    const telemetryHash = sha3_512(payload);

    if (!isFiniteNumber(telemetry.cpuTempC) || !isFiniteNumber(telemetry.gpuTempC)) {
      return { valid: false, reason: 'telemetry temperature is not finite', telemetryHash, observedAtMs };
    }
    if (!isFiniteNumber(telemetry.cpuVolt) || !isFiniteNumber(telemetry.gpuVolt)) {
      return { valid: false, reason: 'telemetry voltage is not finite', telemetryHash, observedAtMs };
    }
    if (!isFiniteNumber(telemetry.powerDrawFraction) || !isFiniteNumber(telemetry.utilization)) {
      return { valid: false, reason: 'telemetry utilization is not finite', telemetryHash, observedAtMs };
    }
    if (telemetry.cpuTempC > this.invariants.maxTempC || telemetry.gpuTempC > this.invariants.maxTempC) {
      return { valid: false, reason: 'Invariant breach: temperature limit exceeded', telemetryHash, observedAtMs };
    }
    if (telemetry.cpuVolt > this.invariants.maxVolt || telemetry.gpuVolt > this.invariants.maxVolt) {
      return { valid: false, reason: 'Invariant breach: voltage limit exceeded', telemetryHash, observedAtMs };
    }
    if (telemetry.powerDrawFraction > this.invariants.maxPowerFraction) {
      return { valid: false, reason: 'Invariant breach: power limit exceeded', telemetryHash, observedAtMs };
    }
    if (telemetry.utilization < 0 || telemetry.utilization > 1) {
      return { valid: false, reason: 'telemetry utilization must be normalized', telemetryHash, observedAtMs };
    }

    if (telemetry.utilizationSamples) {
      for (const sample of telemetry.utilizationSamples) {
        if (!isFiniteNumber(sample.atMs) || !isFiniteNumber(sample.utilization)) {
          return { valid: false, reason: 'utilization samples must be finite', telemetryHash, observedAtMs };
        }
      }
    }

    return {
      valid: true,
      reason: 'telemetry is within constitutional invariants',
      telemetryHash,
      observedAtMs,
    };
  }

  step(telemetry: SovereignXHardwareTelemetry): SovereignXHardwareCycle {
    const evidence = this.validateTelemetry(telemetry);
    const headroomC = this.invariants.maxTempC - Math.max(telemetry.cpuTempC, telemetry.gpuTempC);
    const loadFactor = this.resolveLoadFactor(telemetry, evidence.observedAtMs);

    if (!evidence.valid) {
      const transition = this.recordTransition('QUARANTINE', telemetry, evidence, 'telemetry failed validation');
      this.state.lastDecision = 'QUARANTINE';
      return {
        decision: 'QUARANTINE',
        headroomC,
        loadFactor,
        evidence,
        transitions: [transition],
        state: this.getState(),
      };
    }

    if (headroomC > this.invariants.minHeadroomC && loadFactor > 0.8) {
      const promotion = this.promoteClock(evidence, telemetry);
      const retraction = this.retractClock(evidence, telemetry, evidence.observedAtMs + this.invariants.promotionWindowMs);
      return {
        decision: 'PROMOTE',
        headroomC,
        loadFactor,
        evidence,
        transitions: [promotion, retraction],
        state: this.getState(),
      };
    }

    if (headroomC < this.invariants.minHeadroomC || telemetry.powerDrawFraction > this.invariants.maxPowerFraction) {
      const retraction = this.retractClock(evidence, telemetry, evidence.observedAtMs);
      this.state.lastDecision = 'RETRACT';
      return {
        decision: 'RETRACT',
        headroomC,
        loadFactor,
        evidence,
        transitions: [retraction],
        state: this.getState(),
      };
    }

    const maintain = this.recordTransition('MAINTAIN', telemetry, evidence, 'constitutional invariants remain stable');
    this.state.lastDecision = 'MAINTAIN';
    return {
      decision: 'MAINTAIN',
      headroomC,
      loadFactor,
      evidence,
      transitions: [maintain],
      state: this.getState(),
    };
  }

  promoteClock(evidence: SovereignXHardwareEvidence, telemetry: SovereignXHardwareTelemetry): SovereignXHardwareTransition {
    const fromFrequencyMhz = this.state.currentFrequencyMhz;
    const fromVoltageV = this.state.currentVoltageV;
    const nextFrequencyMhz = roundTo(fromFrequencyMhz * 1.05, 3);
    const nextVoltageV = roundTo(Math.min(this.invariants.maxVolt, fromVoltageV + 0.02), 3);
    this.state = {
      currentFrequencyMhz: nextFrequencyMhz,
      currentVoltageV: nextVoltageV,
      lastUpdatedAtMs: evidence.observedAtMs,
      lastDecision: 'PROMOTE',
    };
    return this.recordTransition(
      'PROMOTE',
      telemetry,
      evidence,
      'headroom and utilization justify promotion',
      nextFrequencyMhz,
      nextVoltageV,
      evidence.observedAtMs,
      fromFrequencyMhz,
      fromVoltageV,
    );
  }

  retractClock(
    evidence: SovereignXHardwareEvidence,
    telemetry: SovereignXHardwareTelemetry,
    observedAtMs = evidence.observedAtMs,
  ): SovereignXHardwareTransition {
    const fromFrequencyMhz = this.state.currentFrequencyMhz;
    const fromVoltageV = this.state.currentVoltageV;
    const nextFrequencyMhz = roundTo(fromFrequencyMhz * 0.95, 3);
    const nextVoltageV = roundTo(Math.max(0, fromVoltageV - 0.02), 3);
    this.state = {
      currentFrequencyMhz: nextFrequencyMhz,
      currentVoltageV: nextVoltageV,
      lastUpdatedAtMs: observedAtMs,
      lastDecision: 'RETRACT',
    };
    return this.recordTransition(
      'RETRACT',
      telemetry,
      evidence,
      'thermal or power limits require retraction',
      nextFrequencyMhz,
      nextVoltageV,
      observedAtMs,
      fromFrequencyMhz,
      fromVoltageV,
    );
  }

  private resolveLoadFactor(telemetry: SovereignXHardwareTelemetry, observedAtMs: number): number {
    const cutoff = observedAtMs - this.invariants.telemetryWindowMs;
    const samples = telemetry.utilizationSamples?.filter((sample) => sample.atMs >= cutoff).map((sample) => sample.utilization) ?? [];
    return samples.length > 0 ? mean(samples) : telemetry.utilization;
  }

  private recordTransition(
    kind: SovereignXHardwareDecision,
    telemetry: SovereignXHardwareTelemetry,
    evidence: SovereignXHardwareEvidence,
    reason: string,
    nextFrequencyMhz = this.state.currentFrequencyMhz,
    nextVoltageV = this.state.currentVoltageV,
    observedAtMs = evidence.observedAtMs,
    fromFrequencyMhz = this.state.currentFrequencyMhz,
    fromVoltageV = this.state.currentVoltageV,
  ): SovereignXHardwareTransition {
    const payload = canonicalStringify({
      kind,
      authority: this.authority,
      observedAtMs,
      telemetryHash: evidence.telemetryHash,
      frequencyDeltaMhz: roundTo(nextFrequencyMhz - fromFrequencyMhz, 3),
      voltageDeltaV: roundTo(nextVoltageV - fromVoltageV, 3),
      invariantState: this.invariants,
    });

    const transition: SovereignXHardwareTransition = {
      id: `sovereignx-transition-${observedAtMs}-${kind.toLowerCase()}`,
      kind,
      timestamp: new Date(observedAtMs).toISOString(),
      authority: this.authority,
      telemetryHash: evidence.telemetryHash,
      replayHash: sha3_512(`${evidence.telemetryHash}:${observedAtMs}:${nextFrequencyMhz - fromFrequencyMhz}:${nextVoltageV - fromVoltageV}`),
      invariantState: clone(this.invariants),
      fromFrequencyMhz,
      toFrequencyMhz: nextFrequencyMhz,
      fromVoltageV,
      toVoltageV: nextVoltageV,
      frequencyDeltaMhz: roundTo(nextFrequencyMhz - fromFrequencyMhz, 3),
      voltageDeltaV: roundTo(nextVoltageV - fromVoltageV, 3),
      evidence: clone(evidence),
      replayable: true,
      authoritySignature: buildSignature(payload, this.authorityKeyPem),
      reason,
    };

    this.events.push(clone(transition));
    return transition;
  }
}

export function createSovereignXHardwareGovernor(options: SovereignXHardwareGovernorOptions = {}): SovereignXHardwareGovernor {
  return new SovereignXHardwareGovernor(options);
}
