import { randomUUID } from 'node:crypto';

import { TriCoreBus, type TriCoreMessage } from '@aaes-os/tri-core-protocol';

export interface NovaGovernanceBridgeOptions {
  bus?: TriCoreBus;
}

export class NovaGovernanceBridge {
  constructor(private readonly options: NovaGovernanceBridgeOptions = {}) {}

  private get bus(): TriCoreBus {
    return this.options.bus ?? new TriCoreBus();
  }

  forwardRuntimeOp(op: string, payload: unknown = {}): TriCoreMessage | null {
    return this.bus.send({
      id: randomUUID(),
      from: 'runtime',
      to: 'governance',
      type: op,
      payload,
      timestamp: Date.now(),
    });
  }
}
