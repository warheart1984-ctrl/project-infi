export type RunId = string;

export type IdentityType = 'agent' | 'model' | 'operator';

export interface Identity {
  id: string;
  type: IdentityType;
  metadata: Record<string, unknown>;
}

export interface RunRequest {
  id?: RunId;
  identity?: Identity;
  payload: Record<string, unknown>;
}

export interface RunResult {
  ok: boolean;
  runId: RunId;
  result?: unknown;
  fault?: {
    invariantId: string;
    message: string;
  };
}

export interface RunContext {
  id: RunId;
  identity: Identity;
  payload: Record<string, unknown>;
  spans: Span[];
  createdAt: string;
}

export interface Span {
  id: string;
  runId: RunId;
  type: string;
  timestamp: number;
  data?: Record<string, unknown>;
}

export interface Receipt {
  runId: RunId;
  hash: string;
  spans: Span[];
  result: unknown;
  createdAt: string;
}

export interface Fault {
  runId: RunId;
  invariantId: string;
  message: string;
  timestamp: string;
}
