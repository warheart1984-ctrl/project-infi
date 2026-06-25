import type { ExecuteRequest, ExecuteResponse, ReceiptWire, SpanWire } from './types.js';
import type { RuntimeConfig } from './types.js';

export class RuntimeClient {
  constructor(private readonly config: RuntimeConfig) {}

  private headers(): Record<string, string> {
    const h: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.config.apiKey) {
      h.Authorization = `Bearer ${this.config.apiKey}`;
    }
    return h;
  }

  async execute(req: ExecuteRequest): Promise<ExecuteResponse> {
    const res = await fetch(`${this.config.baseUrl}/run`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(req),
    });

    if (!res.ok) {
      throw new Error(`Runtime error: ${res.status} ${res.statusText}`);
    }

    return (await res.json()) as ExecuteResponse;
  }

  async getReceipt(runId: string): Promise<ReceiptWire> {
    const res = await fetch(`${this.config.baseUrl}/receipts/${runId}`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch receipt: ${res.status}`);
    }
    return (await res.json()) as ReceiptWire;
  }

  async getSpans(runId: string): Promise<SpanWire[]> {
    const res = await fetch(`${this.config.baseUrl}/runs/${runId}/spans`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch spans: ${res.status}`);
    }
    return (await res.json()) as SpanWire[];
  }

  async getFault(runId: string): Promise<unknown> {
    const res = await fetch(`${this.config.baseUrl}/faults/${runId}`, {
      headers: this.headers(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch fault: ${res.status}`);
    }
    return res.json();
  }
}

export type { RuntimeConfig };
