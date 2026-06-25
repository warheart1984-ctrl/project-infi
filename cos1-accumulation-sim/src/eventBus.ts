export type EventHandler<T> = (ev: T) => void;

export class EventBus<T> {
  private handlers: EventHandler<T>[] = [];

  subscribe(h: EventHandler<T>) {
    this.handlers.push(h);
  }

  publish(ev: T) {
    for (const h of this.handlers) h(ev);
  }
}
