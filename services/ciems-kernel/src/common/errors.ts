export class ConstitutionalViolation extends Error { constructor(readonly reasons: string[]) { super(reasons.join('; ')); this.name = 'ConstitutionalViolation'; } }
