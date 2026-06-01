import { access, mkdir, readdir, readFile, unlink, writeFile } from "fs/promises";
import path from "path";
import {
  rewriteProposalApplySchema,
  rewriteProposalExecutionSchema,
  rewriteProposalSchema,
  type RewriteProposalApply,
  type RewriteProposal,
  type RewriteProposalExecution,
  type RewriteProposalStatus,
} from "@shared/schema";
import { appendProposalApplyJournalEntry } from "./proposal-apply-journal";
import { evaluateRewriteProposalGovernance } from "./proposal-governance";

const DEFAULT_PROPOSAL_ROOT = path.join(process.cwd(), "proposals");
const STATUS_ORDER: RewriteProposalStatus[] = ["pending", "accepted", "rejected"];
const ARCHIVE_DIR_NAME = "archived";

export function resolveProposalRoot(): string {
  const configured = (process.env.SPIRAL_PROPOSAL_ROOT || "").trim();
  return configured || DEFAULT_PROPOSAL_ROOT;
}

function getStatusDir(status: RewriteProposalStatus): string {
  return path.join(resolveProposalRoot(), status);
}

function getArchiveDir(): string {
  return path.join(resolveProposalRoot(), ARCHIVE_DIR_NAME);
}

interface ListRewriteProposalsOptions {
  principalId: string;
  status?: RewriteProposalStatus;
  chatId?: string;
  limit?: number;
}

interface UpdateRewriteProposalStatusInput {
  principalId: string;
  proposalId: string;
  nextStatus: Exclude<RewriteProposalStatus, "pending">;
  decidedBy: string;
  reason?: string;
}

interface GetRewriteProposalByIdInput {
  principalId: string;
  proposalId: string;
}

interface RecordRewriteProposalExecutionInput {
  principalId: string;
  proposalId: string;
  execution: RewriteProposalExecution;
}

interface RecordRewriteProposalApplyInput {
  principalId: string;
  proposalId: string;
  apply: RewriteProposalApply;
}

interface ArchiveRewriteProposalsByIdsInput {
  principalId: string;
  proposalIds: string[];
}

interface ProposalRecordLocation {
  proposal: RewriteProposal;
  status: RewriteProposalStatus;
  fileName: string;
  filePath: string;
}

const MAX_EXECUTION_RUNS = 40;

function normalizePrincipal(value: string): string {
  return value.trim();
}

function normalizeExecutionRuns(proposal: RewriteProposal): RewriteProposalExecution[] {
  const fromRuns = Array.isArray(proposal.executionRuns) ? proposal.executionRuns : [];
  const merged = proposal.execution ? [proposal.execution, ...fromRuns] : fromRuns;
  const normalized: RewriteProposalExecution[] = [];
  const seen = new Set<string>();
  for (const candidate of merged) {
    const parsed = rewriteProposalExecutionSchema.safeParse(candidate);
    if (!parsed.success) continue;
    const fallbackRunId =
      typeof parsed.data.executedAt === "number"
        ? `legacy-${parsed.data.executedAt}-${parsed.data.engine}`
        : `legacy-${seen.size + 1}`;
    const runId = (parsed.data.runId || fallbackRunId).trim();
    if (!runId) continue;
    const key = runId.toLowerCase();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    normalized.push({
      ...parsed.data,
      runId,
    });
  }
  normalized.sort((a, b) => b.executedAt - a.executedAt);
  return normalized.slice(0, MAX_EXECUTION_RUNS);
}

async function ensureProposalDirectories(): Promise<void> {
  await Promise.all(
    [...STATUS_ORDER.map((status) => getStatusDir(status)), getArchiveDir()].map((dir) =>
      mkdir(dir, { recursive: true }),
    ),
  );
}

function buildProposalFileName(proposal: RewriteProposal): string {
  const stamp = new Date(proposal.createdAt)
    .toISOString()
    .replace(/[:.]/g, "-")
    .replace("T", "_")
    .replace("Z", "");
  return `${stamp}-${proposal.id}.json`;
}

function buildArtifactPath(status: RewriteProposalStatus, fileName: string): string {
  return path.posix.join("proposals", status, fileName);
}

function buildArchivedArtifactPath(fileName: string): string {
  return path.posix.join("proposals", ARCHIVE_DIR_NAME, fileName);
}

export async function saveRewriteProposal(proposal: RewriteProposal): Promise<RewriteProposal> {
  await ensureProposalDirectories();

  const fileName = buildProposalFileName(proposal);
  const artifactPath = buildArtifactPath(proposal.status, fileName);
  const resolved = rewriteProposalSchema.parse({
    ...proposal,
    principalId: normalizePrincipal(proposal.principalId),
    governanceCheck:
      proposal.governanceCheck || evaluateRewriteProposalGovernance(proposal.proposedChange),
    artifactPath,
  });
  const outputPath = path.join(getStatusDir(resolved.status), fileName);
  await writeFile(outputPath, JSON.stringify(resolved, null, 2), "utf8");
  return resolved;
}

async function readProposalFile(filePath: string): Promise<RewriteProposal | null> {
  try {
    const raw = await readFile(filePath, "utf8");
    const parsed = JSON.parse(raw) as unknown;
    const result = rewriteProposalSchema.safeParse(parsed);
    if (!result.success) return null;
    return result.data;
  } catch {
    return null;
  }
}

async function findProposalRecordById(proposalId: string): Promise<ProposalRecordLocation | null> {
  const normalizedId = proposalId.trim();
  if (!normalizedId) return null;

  for (const status of STATUS_ORDER) {
    const dir = getStatusDir(status);
    let files: string[];
    try {
      files = await readdir(dir);
    } catch {
      continue;
    }

    for (const fileName of files) {
      if (!fileName.toLowerCase().endsWith(".json")) continue;
      const filePath = path.join(dir, fileName);
      const proposal = await readProposalFile(filePath);
      if (!proposal || proposal.id !== normalizedId) continue;
      return { proposal, status, fileName, filePath };
    }
  }

  return null;
}

export async function listRewriteProposals(
  options: ListRewriteProposalsOptions,
): Promise<RewriteProposal[]> {
  await ensureProposalDirectories();
  const principalId = normalizePrincipal(options.principalId);
  if (!principalId) return [];

  const statuses = options.status ? [options.status] : STATUS_ORDER;
  const loaded: RewriteProposal[] = [];

  for (const status of statuses) {
    const dir = getStatusDir(status);
    let files: string[];
    try {
      files = await readdir(dir);
    } catch {
      continue;
    }

    for (const fileName of files) {
      if (!fileName.toLowerCase().endsWith(".json")) continue;
      const proposal = await readProposalFile(path.join(dir, fileName));
      if (!proposal) continue;
      if (proposal.principalId !== principalId) continue;
      if (options.chatId && proposal.chatId !== options.chatId) continue;
      loaded.push(proposal);
    }
  }

  loaded.sort((a, b) => b.createdAt - a.createdAt);
  const limit = Math.max(1, Math.min(200, options.limit ?? 50));
  return loaded.slice(0, limit);
}

export async function updateRewriteProposalStatus(
  input: UpdateRewriteProposalStatusInput,
): Promise<RewriteProposal | null> {
  await ensureProposalDirectories();
  const principalId = normalizePrincipal(input.principalId);
  const decidedBy = normalizePrincipal(input.decidedBy).slice(0, 200) || principalId;
  if (!principalId) return null;

  const located = await findProposalRecordById(input.proposalId);
  if (!located) return null;
  if (located.proposal.principalId !== principalId) return null;

  const reason =
    typeof input.reason === "string" && input.reason.trim()
      ? input.reason.trim().slice(0, 280)
      : undefined;
  const artifactPath = buildArtifactPath(input.nextStatus, located.fileName);
  const updated = rewriteProposalSchema.parse({
    ...located.proposal,
    status: input.nextStatus,
    decidedAt: Date.now(),
    decidedBy,
    governanceCheck:
      located.proposal.governanceCheck ||
      evaluateRewriteProposalGovernance(located.proposal.proposedChange),
    ...(reason ? { decisionReason: reason } : {}),
    ...(input.nextStatus === "accepted"
      ? {}
      : { execution: undefined, executionRuns: undefined, apply: undefined }),
    artifactPath,
  });

  const nextPath = path.join(getStatusDir(input.nextStatus), located.fileName);
  await writeFile(nextPath, JSON.stringify(updated, null, 2), "utf8");
  if (located.filePath !== nextPath) {
    await unlink(located.filePath).catch(() => {
      // Keep outcome idempotent when source file was already moved.
    });
  }

  return updated;
}

export async function getRewriteProposalById(
  input: GetRewriteProposalByIdInput,
): Promise<RewriteProposal | null> {
  await ensureProposalDirectories();
  const principalId = normalizePrincipal(input.principalId);
  if (!principalId) return null;

  const located = await findProposalRecordById(input.proposalId);
  if (!located) return null;
  if (located.proposal.principalId !== principalId) return null;
  return located.proposal;
}

export async function recordRewriteProposalExecution(
  input: RecordRewriteProposalExecutionInput,
): Promise<RewriteProposal | null> {
  await ensureProposalDirectories();
  const principalId = normalizePrincipal(input.principalId);
  if (!principalId) return null;

  const located = await findProposalRecordById(input.proposalId);
  if (!located) return null;
  if (located.proposal.principalId !== principalId) return null;
  if (located.proposal.status !== "accepted") return null;

  const execution = rewriteProposalExecutionSchema.parse(input.execution);
  const executionRuns = [execution, ...normalizeExecutionRuns(located.proposal)].slice(
    0,
    MAX_EXECUTION_RUNS,
  );
  const updated = rewriteProposalSchema.parse({
    ...located.proposal,
    governanceCheck:
      located.proposal.governanceCheck ||
      evaluateRewriteProposalGovernance(located.proposal.proposedChange),
    execution,
    executionRuns,
  });
  await writeFile(located.filePath, JSON.stringify(updated, null, 2), "utf8");
  return updated;
}

export async function recordRewriteProposalApply(
  input: RecordRewriteProposalApplyInput,
): Promise<RewriteProposal | null> {
  await ensureProposalDirectories();
  const principalId = normalizePrincipal(input.principalId);
  if (!principalId) return null;

  const located = await findProposalRecordById(input.proposalId);
  if (!located) return null;
  if (located.proposal.principalId !== principalId) return null;
  if (located.proposal.status !== "accepted") return null;

  const apply = rewriteProposalApplySchema.parse(input.apply);
  const updated = rewriteProposalSchema.parse({
    ...located.proposal,
    governanceCheck:
      located.proposal.governanceCheck ||
      evaluateRewriteProposalGovernance(located.proposal.proposedChange),
    apply,
  });
  await writeFile(located.filePath, JSON.stringify(updated, null, 2), "utf8");
  await appendProposalApplyJournalEntry({
    proposal: updated,
    apply,
  });
  return updated;
}

export async function archiveRewriteProposalsByIds(
  input: ArchiveRewriteProposalsByIdsInput,
): Promise<RewriteProposal[]> {
  await ensureProposalDirectories();
  const principalId = normalizePrincipal(input.principalId);
  if (!principalId) return [];

  const uniqueIds = Array.from(
    new Set(
      (Array.isArray(input.proposalIds) ? input.proposalIds : [])
        .map((id) => id.trim())
        .filter(Boolean),
    ),
  ).slice(0, 200);
  if (uniqueIds.length === 0) return [];

  const archived: RewriteProposal[] = [];
  for (const proposalId of uniqueIds) {
    const located = await findProposalRecordById(proposalId);
    if (!located) continue;
    if (located.proposal.principalId !== principalId) continue;

    let archiveFileName = located.fileName;
    let archivePath = path.join(getArchiveDir(), archiveFileName);
    const exists = await access(archivePath)
      .then(() => true)
      .catch(() => false);
    if (exists) {
      const ext = path.extname(archiveFileName) || ".json";
      const base = path.basename(archiveFileName, ext);
      archiveFileName = `${base}-${Date.now()}${ext}`;
      archivePath = path.join(getArchiveDir(), archiveFileName);
    }

    const updated = rewriteProposalSchema.parse({
      ...located.proposal,
      artifactPath: buildArchivedArtifactPath(archiveFileName),
    });

    await writeFile(archivePath, JSON.stringify(updated, null, 2), "utf8");
    await unlink(located.filePath).catch(() => {
      // Keep operation idempotent if source file already moved.
    });
    archived.push(updated);
  }

  return archived;
}
