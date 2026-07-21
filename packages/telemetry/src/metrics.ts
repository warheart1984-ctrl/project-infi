export interface MetricSample {
  name: string;
  value: number;
  timestamp: number;
  labels?: Record<string, string>;
}

function createStore() {
  const samples: MetricSample[] = [];
  return {
    record(sample: MetricSample): void {
      samples.push(structuredClone(sample));
    },
    list(): MetricSample[] {
      return samples.map((sample) => structuredClone(sample));
    },
  };
}

export class GovernanceMetrics {
  private readonly store = createStore();
  recordInvariant(name: string, value: number): void {
    this.store.record({ name, value, timestamp: Date.now(), labels: { subsystem: 'governance' } });
  }
  snapshot(): MetricSample[] {
    return this.store.list();
  }
}

export class RuntimeMetrics {
  private readonly store = createStore();
  recordExecution(name: string, value: number): void {
    this.store.record({ name, value, timestamp: Date.now(), labels: { subsystem: 'runtime' } });
  }
  snapshot(): MetricSample[] {
    return this.store.list();
  }
}

export class AgentMetrics {
  private readonly store = createStore();
  recordAction(name: string, value: number): void {
    this.store.record({ name, value, timestamp: Date.now(), labels: { subsystem: 'agent' } });
  }
  snapshot(): MetricSample[] {
    return this.store.list();
  }
}

export class SubstrateMetrics {
  private readonly store = createStore();
  recordSignal(name: string, value: number): void {
    this.store.record({ name, value, timestamp: Date.now(), labels: { subsystem: 'substrate' } });
  }
  snapshot(): MetricSample[] {
    return this.store.list();
  }
}
