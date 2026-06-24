export interface Project {
  id: string;
  name: string;
  description: string;
  observedReality?: string;
  verifiedTruth?: string;
  preservedMemory?: string;
  transferredContinuity?: string;
  enabledEvolution?: string;
}

export interface ProjectAuditResult {
  projectId: string;
  ok: boolean;
  missing: string[];
  summary: string;
}

export function auditProject(p: Project): ProjectAuditResult {
  const missing: string[] = [];

  if (!p.observedReality) missing.push("observedReality");
  if (!p.verifiedTruth) missing.push("verifiedTruth");
  if (!p.preservedMemory) missing.push("preservedMemory");
  if (!p.transferredContinuity) missing.push("transferredContinuity");
  if (!p.enabledEvolution) missing.push("enabledEvolution");

  const ok = missing.length === 0;

  const summary = ok
    ? "Project passes the reality-earns-architecture test."
    : `Project is missing: ${missing.join(", ")}`;

  return {
    projectId: p.id,
    ok,
    missing,
    summary,
  };
}
