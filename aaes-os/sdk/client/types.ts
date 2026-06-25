export interface RuntimeConfig {
  baseUrl: string;
  apiKey?: string;
}

export interface Identity {
  id: string;
  type: 'agent' | 'model' | 'operator';
  metadata?: Record<string, unknown>;
}

export interface ExecuteRequest {
  identity: Identity;
  payload: Record<string, unknown>;
}

export interface ExecuteResponse {
  ok: boolean;
  runId: string;
  result?: unknown;
  fault?: {
    invariantId: string;
    message: string;
  };
}

export interface SpanWire {
  id: string;
  runId: string;
  type: string;
  timestamp: number;
  data?: Record<string, unknown>;
}

export interface ReceiptWire {
  runId: string;
  hash: string;
  spans: SpanWire[];
  result: unknown;
  createdAt?: string;
}

export interface FaultWire {
  runId: string;
  invariantId: string;
  message: string;
  timestamp?: string;
}
