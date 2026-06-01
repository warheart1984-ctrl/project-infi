import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  ExecutorProviderSettings,
  RewriteProposal,
  RewriteProposalExecution,
} from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { isProposalApplyableDiff } from "@shared/proposal-diff";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface ProposalsPanelProps {
  currentChatId: string | null;
  executorProviderSettings: ExecutorProviderSettings | null;
  disabled?: boolean;
}

type PanelFilter = "pending" | "all";
type ProposalDecision = "accept" | "reject";

function formatWhen(timestamp: number): string {
  try {
    return new Date(timestamp).toLocaleString();
  } catch {
    return String(timestamp);
  }
}

function getExecutionRuns(proposal: RewriteProposal): RewriteProposalExecution[] {
  const fromRuns = Array.isArray(proposal.executionRuns) ? proposal.executionRuns : [];
  const merged = proposal.execution ? [proposal.execution, ...fromRuns] : fromRuns;
  const map = new Map<string, RewriteProposalExecution>();
  for (const run of merged) {
    if (!run) continue;
    const fallbackRunId =
      typeof run.executedAt === "number"
        ? `legacy-${run.executedAt}-${run.engine}`
        : `legacy-${map.size + 1}`;
    const key = (run.runId || fallbackRunId).trim();
    if (!key) continue;
    if (!map.has(key)) {
      map.set(key, {
        ...run,
        runId: key,
      });
    }
  }
  return Array.from(map.values()).sort((a, b) => b.executedAt - a.executedAt);
}

export function ProposalsPanel({
  currentChatId,
  executorProviderSettings,
  disabled = false,
}: ProposalsPanelProps) {
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [proposals, setProposals] = useState<RewriteProposal[]>([]);
  const [filter, setFilter] = useState<PanelFilter>("pending");
  const [actingId, setActingId] = useState<string | null>(null);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [applyingId, setApplyingId] = useState<string | null>(null);
  const [decisionTarget, setDecisionTarget] = useState<{
    proposal: RewriteProposal;
    decision: ProposalDecision;
  } | null>(null);
  const [decisionReason, setDecisionReason] = useState("");
  const [executionTarget, setExecutionTarget] = useState<RewriteProposal | null>(null);
  const [applyTarget, setApplyTarget] = useState<{
    proposal: RewriteProposal;
    runId: string;
  } | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<{
    ids: string[];
    label: string;
  } | null>(null);
  const [archiveBusy, setArchiveBusy] = useState(false);

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (filter !== "all") params.set("status", "pending");
    if (currentChatId) params.set("chatId", currentChatId);
    params.set("limit", "80");
    return params.toString();
  }, [currentChatId, filter]);

  const loadProposals = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiRequest("GET", `/api/proposals?${queryString}`);
      const payload = (await response.json()) as RewriteProposal[];
      setProposals(payload);
    } catch (error) {
      toast({
        title: "Could not load proposals",
        description: (error as Error).message || "Failed to load proposal ledger.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [currentChatId, queryString, toast]);

  useEffect(() => {
    if (!open) return;
    void loadProposals();
  }, [loadProposals, open]);

  useEffect(() => {
    if (!open) return;
    const interval = window.setInterval(() => {
      void loadProposals();
    }, 45_000);
    return () => window.clearInterval(interval);
  }, [loadProposals, open]);

  const requestDecision = useCallback((proposal: RewriteProposal, decision: ProposalDecision) => {
    setDecisionTarget({ proposal, decision });
    setDecisionReason("");
  }, []);

  const clearDecisionDialog = useCallback(() => {
    setDecisionTarget(null);
    setDecisionReason("");
  }, []);

  const requestExecution = useCallback((proposal: RewriteProposal) => {
    setExecutionTarget(proposal);
  }, []);

  const clearExecutionDialog = useCallback(() => {
    setExecutionTarget(null);
  }, []);

  const requestApply = useCallback((proposal: RewriteProposal, runId: string) => {
    setApplyTarget({ proposal, runId });
  }, []);

  const clearApplyDialog = useCallback(() => {
    setApplyTarget(null);
  }, []);

  const requestArchive = useCallback((ids: string[], label: string) => {
    const unique = Array.from(new Set(ids.map((id) => id.trim()).filter(Boolean)));
    if (unique.length === 0) return;
    setArchiveTarget({
      ids: unique.slice(0, 200),
      label,
    });
  }, []);

  const clearArchiveDialog = useCallback(() => {
    setArchiveTarget(null);
  }, []);

  const handleDecision = useCallback(async () => {
    if (!decisionTarget) return;
    const { proposal, decision } = decisionTarget;
    setActingId(proposal.id);
    try {
      await apiRequest(
        "POST",
        `/api/proposals/${proposal.id}/${decision}`,
        decisionReason.trim() ? { reason: decisionReason.trim() } : {},
      );
      toast({
        title: decision === "accept" ? "Proposal accepted" : "Proposal rejected",
        description: proposal.summary,
      });
      if (decision === "accept") {
        setFilter("all");
      }
      clearDecisionDialog();
      await loadProposals();
    } catch (error) {
      toast({
        title: "Decision failed",
        description: (error as Error).message || "Could not update proposal status.",
        variant: "destructive",
      });
    } finally {
      setActingId(null);
    }
  }, [clearDecisionDialog, decisionReason, decisionTarget, loadProposals, toast]);

  const decisionDialogOpen = Boolean(decisionTarget);
  const decisionBusy = Boolean(decisionTarget && actingId === decisionTarget.proposal.id);

  const executionDialogOpen = Boolean(executionTarget);
  const executionBusy = Boolean(executionTarget && executingId === executionTarget.id);
  const applyDialogOpen = Boolean(applyTarget);
  const applyBusy = Boolean(applyTarget && applyingId === applyTarget.proposal.id);
  const archiveDialogOpen = Boolean(archiveTarget);

  const handleExecute = useCallback(async () => {
    if (!executionTarget) return;
    if (!executorProviderSettings?.authProfileId?.trim()) {
      toast({
        title: "Executor auth required",
        description: "Configure an executor OAuth auth profile in Settings before execution.",
        variant: "destructive",
      });
      return;
    }
    setExecutingId(executionTarget.id);
    try {
      const response = await apiRequest("POST", `/api/proposals/${executionTarget.id}/execute`, {
        confirmed: true,
        executorProviderSettings,
      });
      const updated = (await response.json()) as RewriteProposal;
      const latestExecution = getExecutionRuns(updated)[0];
      const executionFailed = latestExecution?.status === "failed";
      toast({
        title: executionFailed ? "Execution failed" : "Execution complete",
        description:
          latestExecution?.summary ||
          "Execution finished. Review artifacts before applying anything manually.",
        ...(executionFailed ? { variant: "destructive" as const } : {}),
      });
      clearExecutionDialog();
      await loadProposals();
    } catch (error) {
      toast({
        title: "Execution failed",
        description:
          (error as Error).message || "Could not execute this proposal via Codex workflow.",
        variant: "destructive",
      });
    } finally {
      setExecutingId(null);
    }
  }, [clearExecutionDialog, executionTarget, executorProviderSettings, loadProposals, toast]);

  const handleApply = useCallback(async () => {
    if (!applyTarget) return;
    setApplyingId(applyTarget.proposal.id);
    try {
      const response = await apiRequest("POST", `/api/proposals/${applyTarget.proposal.id}/apply`, {
        confirmed: true,
        runId: applyTarget.runId,
      });
      const updated = (await response.json()) as RewriteProposal;
      toast({
        title: "Patch applied to workspace",
        description:
          updated.apply?.summary || "Patch applied successfully. Review with git diff before commit.",
      });
      clearApplyDialog();
      await loadProposals();
    } catch (error) {
      toast({
        title: "Apply failed",
        description: (error as Error).message || "Could not apply the proposal patch.",
        variant: "destructive",
      });
    } finally {
      setApplyingId(null);
    }
  }, [applyTarget, clearApplyDialog, loadProposals, toast]);

  const handleArchive = useCallback(async () => {
    if (!archiveTarget) return;
    setArchiveBusy(true);
    try {
      const response = await apiRequest("POST", "/api/proposals/archive", {
        ids: archiveTarget.ids,
      });
      const payload = (await response.json()) as { archivedCount?: number };
      const archivedCount = Number.isFinite(payload.archivedCount)
        ? Number(payload.archivedCount)
        : archiveTarget.ids.length;
      toast({
        title: "Proposals archived",
        description: `${archivedCount} archived to proposals/archived.`,
      });
      clearArchiveDialog();
      await loadProposals();
    } catch (error) {
      toast({
        title: "Archive failed",
        description: (error as Error).message || "Could not archive proposals.",
        variant: "destructive",
      });
    } finally {
      setArchiveBusy(false);
    }
  }, [archiveTarget, clearArchiveDialog, loadProposals, toast]);

  const handleExportVisible = useCallback(() => {
    if (proposals.length === 0) {
      toast({
        title: "Nothing to export",
        description: "No proposals in the current scope.",
      });
      return;
    }

    const payload = {
      exportedAt: new Date().toISOString(),
      scope: {
        filter,
        chatId: currentChatId,
      },
      count: proposals.length,
      proposals,
    };
    const json = JSON.stringify(payload, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = `proposals-export-${stamp}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    toast({
      title: "Export complete",
      description: `${proposals.length} proposals exported.`,
    });
  }, [currentChatId, filter, proposals, toast]);

  return (
    <>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button size="sm" variant="outline" disabled={disabled} data-testid="button-open-proposals-panel">
            Proposals
          </Button>
        </DialogTrigger>
        <DialogContent className="flex max-h-[92vh] w-[min(96vw,1100px)] max-w-[1100px] flex-col overflow-hidden">
          <DialogHeader className="shrink-0">
            <DialogTitle>Proposal Ledger</DialogTitle>
            <DialogDescription>
              Witness, decide, execute in isolation, then optionally apply with explicit confirmation.
            </DialogDescription>
          </DialogHeader>

          <div className="flex shrink-0 items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant={filter === "pending" ? "default" : "outline"}
                onClick={() => setFilter("pending")}
                data-testid="button-proposals-filter-pending"
              >
                Pending
              </Button>
              <Button
                type="button"
                size="sm"
                variant={filter === "all" ? "default" : "outline"}
                onClick={() => setFilter("all")}
                data-testid="button-proposals-filter-all"
              >
                All
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => handleExportVisible()}
                disabled={proposals.length === 0 || loading}
                data-testid="button-proposals-export-visible"
              >
                Export JSON
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() =>
                  requestArchive(
                    proposals.map((proposal) => proposal.id),
                    `${proposals.length} visible proposal${proposals.length === 1 ? "" : "s"}`,
                  )
                }
                disabled={proposals.length === 0 || loading}
                data-testid="button-proposals-archive-visible"
              >
                Archive Visible
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => void loadProposals()}
                disabled={loading}
                data-testid="button-proposals-refresh"
              >
                {loading ? "Refreshing..." : "Refresh"}
              </Button>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto pr-1">
            {proposals.length === 0 ? (
              <div className="rounded-md border border-border/70 px-3 py-4 text-sm text-muted-foreground">
                No proposals in this scope.
              </div>
            ) : (
              <div className="space-y-2">
                {proposals.map((proposal) => {
                  const pending = proposal.status === "pending";
                  const busy =
                    actingId === proposal.id ||
                    executingId === proposal.id ||
                    applyingId === proposal.id ||
                    archiveBusy;
                  const canExecute = proposal.status === "accepted";
                  const isAdvisoryOnly = !isProposalApplyableDiff(proposal.proposedChange.diffPreview);
                  const executionRuns = getExecutionRuns(proposal);
                  const latestExecution = executionRuns[0];
                  const canApply =
                    canExecute &&
                    !isAdvisoryOnly &&
                    latestExecution?.status === "succeeded" &&
                    Boolean(latestExecution.patchArtifactPath) &&
                    !proposal.apply;
                  const isExecuting = executingId === proposal.id;
                  const isApplying = applyingId === proposal.id;
                  return (
                    <div key={proposal.id} className="rounded-md border border-border/70 px-3 py-3 space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant={pending ? "default" : "secondary"}>{proposal.status}</Badge>
                        <span className="text-xs text-muted-foreground">{formatWhen(proposal.createdAt)}</span>
                        {proposal.signal && (
                          <span className="text-xs text-muted-foreground">signal: {proposal.signal}</span>
                        )}
                      </div>
                      <p className="text-sm font-medium leading-relaxed">{proposal.summary}</p>
                      <p className="text-xs text-muted-foreground">
                        target: <code>{proposal.proposedChange.target}</code> · kind: {proposal.proposedChange.kind}
                      </p>
                      <details className="rounded-md border border-border/60 bg-muted/20 p-2">
                        <summary className="cursor-pointer text-xs font-medium">Rationale + Diff</summary>
                        <p className="mt-2 text-xs text-muted-foreground whitespace-pre-wrap">
                          {proposal.proposedChange.rationale}
                        </p>
                        <pre className="mt-2 overflow-x-auto rounded bg-background p-2 text-[11px] leading-relaxed">
{proposal.proposedChange.diffPreview}
                        </pre>
                      </details>
                      {pending ? (
                        <div className="flex items-center gap-2">
                          <Button
                            type="button"
                            size="sm"
                            onClick={() => requestDecision(proposal, "accept")}
                            disabled={busy}
                            data-testid={`button-proposal-accept-${proposal.id}`}
                          >
                            {busy ? "Applying..." : "Accept"}
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => requestDecision(proposal, "reject")}
                            disabled={busy}
                            data-testid={`button-proposal-reject-${proposal.id}`}
                          >
                            {busy ? "Applying..." : "Reject"}
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => requestArchive([proposal.id], "this proposal")}
                            disabled={busy}
                            data-testid={`button-proposal-archive-${proposal.id}`}
                          >
                            Archive
                          </Button>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <p className="text-xs text-muted-foreground">
                            decided: {proposal.decidedBy || "n/a"} at{" "}
                            {proposal.decidedAt ? formatWhen(proposal.decidedAt) : "n/a"}
                            {proposal.decisionReason ? ` · reason: ${proposal.decisionReason}` : ""}
                          </p>
                          {latestExecution ? (
                            <div className="space-y-2">
                              <p className="text-xs text-muted-foreground">
                                last execution: {latestExecution.status} via {latestExecution.engine} at{" "}
                                {formatWhen(latestExecution.executedAt)}
                                {latestExecution.logArtifactPath
                                  ? ` · log: ${latestExecution.logArtifactPath}`
                                  : ""}
                              </p>
                              <details className="rounded-md border border-border/60 bg-muted/20 p-2">
                                <summary className="cursor-pointer text-xs font-medium">
                                  Execution history ({executionRuns.length})
                                </summary>
                                <div className="mt-2 max-h-96 space-y-2 overflow-y-auto pr-1">
                                  {executionRuns.map((run) => (
                                    <div
                                      key={run.runId || `${run.executedAt}-${run.engine}`}
                                      className="rounded border border-border/50 p-2"
                                    >
                                      <p className="text-xs font-medium">
                                        {formatWhen(run.executedAt)} · {run.status} · {run.engine}
                                      </p>
                                      <p className="mt-1 max-h-32 overflow-y-auto whitespace-pre-wrap pr-1 text-xs text-muted-foreground">
                                        {run.summary}
                                      </p>
                                      {run.command ? (
                                        <p className="mt-1 break-all text-[11px] text-muted-foreground">
                                          command: <code>{run.command}</code>
                                        </p>
                                      ) : null}
                                      {run.logArtifactPath ? (
                                        <p className="break-all text-[11px] text-muted-foreground">
                                          log: <code>{run.logArtifactPath}</code>
                                        </p>
                                      ) : null}
                                      {run.patchArtifactPath ? (
                                        <p className="break-all text-[11px] text-muted-foreground">
                                          patch: <code>{run.patchArtifactPath}</code>
                                        </p>
                                      ) : null}
                                    </div>
                                  ))}
                                </div>
                              </details>
                            </div>
                          ) : canExecute ? (
                            <p className="text-xs text-muted-foreground">
                              Not executed yet. Manual promotion remains required after execution.
                            </p>
                          ) : null}
                          {proposal.apply ? (
                            <p className="text-xs text-muted-foreground">
                              applied: {proposal.apply.appliedBy} at {formatWhen(proposal.apply.appliedAt)}
                              {proposal.apply.runId ? ` · run: ${proposal.apply.runId}` : ""}
                              {proposal.apply.patchArtifactPath
                                ? ` · patch: ${proposal.apply.patchArtifactPath}`
                                : ""}
                            </p>
                          ) : null}
                          {canExecute ? (
                            <div className="flex flex-wrap items-center gap-2">
                              <Button
                                type="button"
                                size="sm"
                                variant="outline"
                                onClick={() => requestExecution(proposal)}
                                disabled={busy}
                                data-testid={`button-proposal-execute-${proposal.id}`}
                              >
                                {isExecuting
                                  ? "Executing..."
                                  : latestExecution
                                    ? "Execute Again"
                                    : "Execute with Codex"}
                              </Button>
                              {canApply ? (
                                <Button
                                  type="button"
                                  size="sm"
                                  onClick={() =>
                                    requestApply(
                                      proposal,
                                      (latestExecution?.runId || "").trim(),
                                    )
                                  }
                                  disabled={busy}
                                  data-testid={`button-proposal-apply-${proposal.id}`}
                                >
                                  {isApplying ? "Applying..." : "Apply to Workspace"}
                                </Button>
                              ) : proposal.apply ? (
                                <Badge variant="secondary">Applied</Badge>
                              ) : isAdvisoryOnly ? (
                                <span className="text-xs text-muted-foreground">
                                  Advisory-only proposal: apply is disabled.
                                </span>
                              ) : latestExecution ? (
                                <span className="text-xs text-muted-foreground">
                                  Apply requires a successful execution run.
                                </span>
                              ) : null}
                              <Button
                                type="button"
                                size="sm"
                                variant="outline"
                                onClick={() => requestArchive([proposal.id], "this proposal")}
                                disabled={busy}
                                data-testid={`button-proposal-archive-${proposal.id}`}
                              >
                                Archive
                              </Button>
                            </div>
                          ) : (
                            <div className="flex flex-wrap items-center gap-2">
                              <Button
                                type="button"
                                size="sm"
                                variant="outline"
                                onClick={() => requestArchive([proposal.id], "this proposal")}
                                disabled={busy}
                                data-testid={`button-proposal-archive-${proposal.id}`}
                              >
                                Archive
                              </Button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
      <Dialog
        open={executionDialogOpen}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && !executionBusy) {
            clearExecutionDialog();
          }
        }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Execute with Codex</DialogTitle>
            <DialogDescription>
              This runs in an isolated proposal execution directory. No repository changes are
              auto-applied.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">{executionTarget?.summary}</p>
            <p className="text-xs text-muted-foreground">
              Continue only if you want to generate execution artifacts for manual review and
              manual promotion.
            </p>
            {executorProviderSettings?.authProfileId?.trim() ? (
              <p className="text-xs text-muted-foreground">
                executor auth profile: <code>{executorProviderSettings.authProfileId.trim()}</code>
              </p>
            ) : (
              <p className="text-xs text-destructive">
                Configure executor OAuth auth profile in Settings to enable execution.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => clearExecutionDialog()}
              disabled={executionBusy}
              data-testid="button-proposal-execution-cancel"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void handleExecute()}
              disabled={executionBusy || !executionTarget}
              data-testid="button-proposal-execution-confirm"
            >
              {executionBusy ? "Executing..." : "Execute"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={applyDialogOpen}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && !applyBusy) {
            clearApplyDialog();
          }
        }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Apply Patch to Workspace</DialogTitle>
            <DialogDescription>
              This uses <code>git apply</code> in your current repository. It edits local files but
              does not commit or push.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">{applyTarget?.proposal.summary}</p>
            <p className="text-xs text-muted-foreground">
              Apply only after reviewing execution artifacts. If the workspace has drifted, apply
              may fail with a clean conflict message.
            </p>
            {applyTarget?.runId ? (
              <p className="text-xs text-muted-foreground">
                selected run: <code>{applyTarget.runId}</code>
              </p>
            ) : null}
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => clearApplyDialog()}
              disabled={applyBusy}
              data-testid="button-proposal-apply-cancel"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void handleApply()}
              disabled={applyBusy || !applyTarget}
              data-testid="button-proposal-apply-confirm"
            >
              {applyBusy ? "Applying..." : "Apply Patch"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={archiveDialogOpen}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && !archiveBusy) {
            clearArchiveDialog();
          }
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Archive Proposals</DialogTitle>
            <DialogDescription>
              This moves proposal files to <code>proposals/archived/</code>. Nothing is deleted.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Archive {archiveTarget?.label || "selected proposals"}?
            </p>
            <p className="text-xs text-muted-foreground">
              Archived proposals are hidden from the main list and can still be exported from disk.
            </p>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => clearArchiveDialog()}
              disabled={archiveBusy}
              data-testid="button-proposal-archive-cancel"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void handleArchive()}
              disabled={archiveBusy || !archiveTarget}
              data-testid="button-proposal-archive-confirm"
            >
              {archiveBusy ? "Archiving..." : "Archive"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={decisionDialogOpen}
        onOpenChange={(nextOpen) => {
          if (!nextOpen && !decisionBusy) {
            clearDecisionDialog();
          }
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {decisionTarget?.decision === "accept" ? "Accept proposal" : "Reject proposal"}
            </DialogTitle>
            <DialogDescription>
              Reason is optional and will be stored in the proposal ledger.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">{decisionTarget?.proposal.summary}</p>
            <Textarea
              value={decisionReason}
              onChange={(event) => setDecisionReason(event.target.value)}
              placeholder="Optional reason..."
              maxLength={280}
              disabled={decisionBusy}
              data-testid="textarea-proposal-decision-reason"
            />
            <p className="text-xs text-muted-foreground">{decisionReason.length}/280</p>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => clearDecisionDialog()}
              disabled={decisionBusy}
              data-testid="button-proposal-decision-cancel"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void handleDecision()}
              disabled={decisionBusy || !decisionTarget}
              data-testid="button-proposal-decision-confirm"
            >
              {decisionBusy ? "Applying..." : decisionTarget?.decision === "accept" ? "Accept" : "Reject"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
