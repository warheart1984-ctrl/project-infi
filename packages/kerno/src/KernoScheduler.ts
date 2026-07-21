import { EventEmitter } from 'node:events';

export type SlotId = string;

export interface KernoSlot {
  slot_id: SlotId;
  reserved_at: string;
  actor_id: string;
  intent_class: string;
  released: boolean;
}

export interface ImmuneRuntimeAlert {
  cache_hit_rate: number;
  consecutive_low_steps: number;
  message: string;
}

export class KernoScheduler extends EventEmitter {
  private slots = new Map<SlotId, KernoSlot>();
  private maxConcurrent: number;
  private intentHistory: string[] = [];
  private cacheHitCount = 0;
  private cacheMissCount = 0;
  private consecutiveLowHitRate = 0;
  private readonly LOW_HIT_RATE_THRESHOLD = 0.40;
  private readonly LOW_HIT_RATE_WINDOW = 5;

  constructor(maxConcurrent = 4) {
    super();
    this.maxConcurrent = maxConcurrent;
  }

  reserve(actorId: string, intentClass: string): SlotId {
    if (this.slots.size >= this.maxConcurrent) {
      throw new Error(`KERNO: slot pool exhausted (max ${this.maxConcurrent} concurrent)`);
    }

    const slot_id = `slot_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    this.slots.set(slot_id, {
      slot_id,
      reserved_at: new Date().toISOString(),
      actor_id: actorId,
      intent_class: intentClass,
      released: false,
    });

    const lastIntent = this.intentHistory[this.intentHistory.length - 1];
    if (lastIntent === intentClass) {
      this.cacheHitCount++;
    } else {
      this.cacheMissCount++;
    }
    this.intentHistory.push(intentClass);
    if (this.intentHistory.length > 20) {
      this.intentHistory.shift();
    }

    this.checkCacheHitRate();
    return slot_id;
  }

  release(slotId: SlotId): void {
    const slot = this.slots.get(slotId);
    if (!slot) {
      throw new Error(`KERNO: unknown slot ${slotId}`);
    }
    slot.released = true;
    this.slots.delete(slotId);
  }

  getCacheHitRate(): number {
    const total = this.cacheHitCount + this.cacheMissCount;
    if (total === 0) {
      return 1.0;
    }
    return this.cacheHitCount / total;
  }

  private checkCacheHitRate(): void {
    if (this.getCacheHitRate() < this.LOW_HIT_RATE_THRESHOLD) {
      this.consecutiveLowHitRate++;
      if (this.consecutiveLowHitRate === this.LOW_HIT_RATE_WINDOW) {
        const alert: ImmuneRuntimeAlert = {
          cache_hit_rate: this.getCacheHitRate(),
          consecutive_low_steps: this.consecutiveLowHitRate,
          message: 'KERNO: cache-hit-rate below 0.40 for 5+ steps — Immune Runtime notified',
        };
        this.emit('IMMUNE_RUNTIME_ALERT', alert);
      }
    } else {
      this.consecutiveLowHitRate = 0;
    }
  }
}
