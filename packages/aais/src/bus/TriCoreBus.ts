import { EventEmitter } from 'node:events';
import { randomUUID } from 'node:crypto';

export type TriCoreActor = 'governance' | 'runtime' | 'agent' | 'substrate';

export interface TriCoreMessage<TPayload = unknown> {
  id: string;
  from: TriCoreActor;
  to: TriCoreActor;
  type: string;
  payload: TPayload;
  timestamp: number;
  correlationId?: string;
}

export interface TriCoreBusOptions {
  frozen?: boolean;
  allowWhileFrozen?: (message: TriCoreMessage) => boolean;
}

export type TriCoreHandler<TPayload = unknown> = (message: TriCoreMessage<TPayload>) => void | Promise<void>;

/**
 * In-process actor bus for AAIS messages.
 * Routes messages to actor channels and can block routing while a constitutional freeze is active.
 */
export class TriCoreBus extends EventEmitter {
  private frozen: boolean;
  private readonly allowWhileFrozen?: (message: TriCoreMessage) => boolean;

  constructor(options: TriCoreBusOptions = {}) {
    super();
    this.frozen = options.frozen ?? false;
    this.allowWhileFrozen = options.allowWhileFrozen;
  }

  setFrozen(frozen: boolean): void {
    this.frozen = frozen;
  }

  isFrozen(): boolean {
    return this.frozen;
  }

  send<TPayload>(message: TriCoreMessage<TPayload>): TriCoreMessage<TPayload> | null {
    const sealed = {
      ...message,
      id: message.id || randomUUID(),
      timestamp: message.timestamp || Date.now(),
    };

    if (this.frozen && !this.allowWhileFrozen?.(sealed)) {
      return null;
    }

    this.emit(sealed.to, sealed);
    this.emit('message', sealed);
    return sealed;
  }

  subscribe<TPayload = unknown>(actor: TriCoreActor, handler: TriCoreHandler<TPayload>): () => void {
    this.on(actor, handler as (message: TriCoreMessage) => void);
    return () => this.off(actor, handler as (message: TriCoreMessage) => void);
  }
}
