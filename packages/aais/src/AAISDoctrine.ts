export interface AAISActionContext {
  actor: string;
  action: string;
  payload?: unknown;
  freezeActive?: boolean;
}

export class AAISDoctrine {
  validateAction(context: AAISActionContext): { passed: boolean; reason?: string } {
    if (context.freezeActive && context.action !== 'SUBSTRATE_CORRECTION') {
      return { passed: false, reason: 'AAIS blocked by constitutional freeze' };
    }
    return { passed: true };
  }
}
