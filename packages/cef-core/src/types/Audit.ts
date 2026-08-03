export type AuditVisibility = 'public' | 'internal';

export type CefAudit = {
  visibility: AuditVisibility;
  disclosure?: string[];
};
