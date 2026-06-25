import {
  runEarlyBoot,
  toUcrContext,
  type EarlyBootResult,
  type TrustRootInput,
  type UCRTrustContext,
} from '@aaes-os/trust-root';
import {
  issueAttestationFromSealedTrust,
  resetUcrRegistrationForTests,
  ucrRegister,
  type UCRRegisterResult,
} from '@aaes-os/ucr-attestation';

export type ConformanceLevel = 1 | 2 | 3;
export type CorridorAdmissionReason =
  | 'CORRIDOR_UNKNOWN'
  | 'CORRIDOR_QUARANTINED'
  | 'CAPABILITY_DENIED'
  | 'LAW_EVOLUTION_CORRIDOR_REQUIRED'
  | 'TRUST_ROOT_NOT_SEALED';

export interface CorridorDefinition {
  corridorId: string;
  capabilities: string[];
}

export interface CorridorAdmissionRequest {
  corridorId: string;
  requestedCapabilities: string[];
  mutationKind?: 'law' | 'runtime' | 'none';
}

export interface CorridorAdmissionResult {
  admitted: boolean;
  corridorId: string;
  reasonCode?: CorridorAdmissionReason;
  reasonDetail?: string;
}

export interface RuntimeLawSpineOptions {
  corridors: CorridorDefinition[];
  conformanceLevel?: ConformanceLevel;
  lawEvolutionCorridorId?: string;
}

export interface RuntimeInitializationInput extends RuntimeLawSpineOptions {
  trustRootInput: TrustRootInput;
  ucrInstanceId: string;
  buildFingerprint: string;
}

export interface RuntimeInitializationResult {
  allowed: boolean;
  boot: EarlyBootResult;
  registration: UCRRegisterResult;
  runtimeContext: UCRTrustContext;
  conformanceLevel: ConformanceLevel;
}

export class RuntimeLawSpine {
  private readonly corridors: Map<string, CorridorDefinition>;
  private readonly quarantined = new Set<string>();
  private readonly conformanceLevel: ConformanceLevel;
  private readonly lawEvolutionCorridorId: string;

  constructor(options: RuntimeLawSpineOptions) {
    this.corridors = new Map(options.corridors.map((corridor) => [corridor.corridorId, corridor]));
    this.conformanceLevel = options.conformanceLevel ?? 1;
    this.lawEvolutionCorridorId = options.lawEvolutionCorridorId ?? 'law-evolution';
  }

  admit(request: CorridorAdmissionRequest): CorridorAdmissionResult {
    if (this.quarantined.has(request.corridorId)) {
      return this.deny(request.corridorId, 'CORRIDOR_QUARANTINED', 'corridor is quarantined');
    }

    const corridor = this.corridors.get(request.corridorId);
    if (!corridor) {
      if (this.conformanceLevel >= 3) {
        this.quarantined.add(request.corridorId);
      }
      return this.deny(request.corridorId, 'CORRIDOR_UNKNOWN', 'corridor is not registered');
    }

    const missingCapability = request.requestedCapabilities.find((capability) => !corridor.capabilities.includes(capability));
    if (missingCapability) {
      if (this.conformanceLevel >= 3) {
        this.quarantined.add(request.corridorId);
      }
      return this.deny(request.corridorId, 'CAPABILITY_DENIED', `capability denied: ${missingCapability}`);
    }

    if (
      request.mutationKind === 'law' &&
      this.conformanceLevel >= 3 &&
      request.corridorId !== this.lawEvolutionCorridorId
    ) {
      return this.deny(request.corridorId, 'LAW_EVOLUTION_CORRIDOR_REQUIRED', 'law mutation requires law evolution corridor');
    }

    return { admitted: true, corridorId: request.corridorId };
  }

  quarantine(corridorId: string): void {
    this.quarantined.add(corridorId);
  }

  isQuarantined(corridorId: string): boolean {
    return this.quarantined.has(corridorId);
  }

  private deny(corridorId: string, reasonCode: CorridorAdmissionReason, reasonDetail: string): CorridorAdmissionResult {
    return { admitted: false, corridorId, reasonCode, reasonDetail };
  }
}

export function initializeRuntime(input: RuntimeInitializationInput): RuntimeInitializationResult {
  resetUcrRegistrationForTests();
  const boot = runEarlyBoot(input.trustRootInput);
  const token = issueAttestationFromSealedTrust({
    ucrInstanceId: input.ucrInstanceId,
    buildFingerprint: input.buildFingerprint,
  });
  const registration = ucrRegister(token);
  const runtimeContext = toUcrContext(boot.trustRoot);

  return {
    allowed: boot.bootResult === 'OK' && registration.outcome === 'OK',
    boot,
    registration,
    runtimeContext,
    conformanceLevel: input.conformanceLevel ?? 1,
  };
}
