import type { TraceEvent, TraceSubscriber, TraceUnsubscribe } from './types.js';

/** In-memory TraceBusClient — pub/sub trace event bus. */
export class TraceBusClient {
  private readonly subscribers = new Set<TraceSubscriber>();
  private readonly log: TraceEvent[] = [];

  subscribe(handler: TraceSubscriber): TraceUnsubscribe {
    this.subscribers.add(handler);
    return () => {
      this.subscribers.delete(handler);
    };
  }

  emit(event: TraceEvent): TraceEvent {
    this.log.push(event);
    for (const handler of this.subscribers) {
      handler(event);
    }
    return event;
  }

  getLog(): readonly TraceEvent[] {
    return [...this.log];
  }

  clear(): void {
    this.log.length = 0;
  }
}
