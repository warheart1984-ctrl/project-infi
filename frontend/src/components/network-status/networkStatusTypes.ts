export type ProviderStatus = 'online' | 'degraded' | 'offline';

export type SystemMode =
  | 'nominal'
  | 'strained'
  | 'degraded'
  | 'critical'
  | 'quarantine';

export interface NetworkStatusData {
  latency_ms: number;
  packet_loss: number;
  providers: Record<string, ProviderStatus>;
  routing: 'stable' | 'unstable' | 'failed';
  system_mode: SystemMode;
  fallback_active: boolean;
  timestamp: number;
}

export interface NetworkProviderProbe {
  id: string;
  available?: boolean;
  kind?: string;
  requested?: boolean;
  active?: boolean;
  fallback_target?: boolean;
}

export interface BuildNetworkStatusOptions {
  latency_ms?: number | null;
  providers?: NetworkProviderProbe[];
  backend_healthy?: boolean;
  fallback_active?: boolean;
  quarantined?: boolean;
  timestamp?: number;
}
