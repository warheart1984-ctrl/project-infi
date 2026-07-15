export interface AuditLogger { record(event: { gate: string; subjectId: string; ok: boolean; reasons: string[]; at: string }): void | Promise<void> }
export const noOpAuditLogger: AuditLogger = { record: () => undefined };
