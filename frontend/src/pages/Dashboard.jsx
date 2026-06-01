import React, { useCallback, useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { Link } from 'react-router-dom';
import {
  FiActivity,
  FiArchive,
  FiArrowRight,
  FiBookOpen,
  FiCheckCircle,
  FiCompass,
  FiFlag,
  FiGitPullRequest,
  FiLayers,
  FiPlay,
  FiPlus,
  FiRefreshCw,
  FiSearch,
  FiShield,
  FiTarget,
  FiZap,
} from 'react-icons/fi';
import { apiGet, apiPatch, apiPost, getApiErrorMessage } from '../lib/api';
import { getActiveJarvisSessionId } from '../lib/jarvis';
import './Dashboard.css';

function createMissionDraft(overrides = {}) {
  return {
    title: '',
    objective: '',
    next_step: '',
    ...overrides,
  };
}

function createMemoryDraft(overrides = {}) {
  return {
    content: '',
    category: 'general',
    priority: 50,
    why: '',
    ...overrides,
  };
}

function clipText(value, limit = 140) {
  const cleaned = String(value || '').replace(/\s+/g, ' ').trim();
  if (cleaned.length <= limit) {
    return cleaned;
  }
  return `${cleaned.slice(0, limit - 3).trimEnd()}...`;
}

function formatStamp(value) {
  if (!value) {
    return 'Unknown';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'Unknown';
  }
  return date.toLocaleString();
}

function toneForState(value) {
  const normalized = String(value || '').trim().toLowerCase();
  if (['completed', 'accepted', 'active', 'aligned', 'healthy', 'ready', 'open'].includes(normalized)) {
    return 'connected';
  }
  if (['blocked', 'failed', 'rejected', 'drifted', 'unreachable', 'archived'].includes(normalized)) {
    return 'error';
  }
  return 'warning';
}

function toneForBadge(value) {
  const normalized = String(value || '').trim().toLowerCase();
  if (['success', 'info'].includes(normalized)) {
    return 'connected';
  }
  if (normalized === 'muted') {
    return 'ghost';
  }
  if (normalized === 'warning') {
    return 'warning';
  }
  return 'ghost';
}

function toneForDecision(value) {
  const normalized = String(value || '').trim().toLowerCase();
  if ([
    'followed',
    'not invoked',
    'clean',
    'local-only',
    'hybrid',
    'external-allowed',
    'none',
    'recovered',
  ].includes(normalized)) {
    return 'connected';
  }
  if (normalized.includes('blocked') || normalized.includes('fallback') || normalized.includes('pending')) {
    return 'warning';
  }
  return 'ghost';
}

function describeAuthorityMode(knowledgeAuthority) {
  const summary = knowledgeAuthority?.summary || {};
  if (summary.mode) {
    return summary.mode;
  }
  if ((summary.live_research_count || 0) > 0) {
    return 'external-allowed';
  }
  if ((summary.document_count || 0) > 0 || (summary.doctrine_count || 0) > 0) {
    return 'hybrid';
  }
  return 'local-only';
}

function buildAuthorityRows(knowledgeAuthority) {
  const summary = knowledgeAuthority?.summary || {};
  const doctrine = knowledgeAuthority?.doctrine || [];
  const workspaceProjects = knowledgeAuthority?.workspace?.projects || [];
  const documentEntries = knowledgeAuthority?.documents || [];
  const researchSources = knowledgeAuthority?.live_research?.sources || [];

  return [
    {
      name: 'Live operator memories',
      type: 'runtime',
      version: `${summary.memory_count || 0} record(s)`,
      status: (summary.memory_count || 0) > 0 ? 'active' : 'shadow',
      scope: 'session',
      surface_priority: false,
    },
    {
      name: 'Workspace truth',
      type: 'runtime',
      version: `${workspaceProjects.length} project(s)`,
      status: workspaceProjects.length > 0 ? 'active' : 'shadow',
      scope: 'mission',
      surface_priority: false,
    },
    {
      name: 'Canonical docs',
      type: 'file',
      version: `${doctrine.length} doc(s)`,
      status: doctrine.length > 0 ? 'active' : 'shadow',
      scope: 'global',
      surface_priority: false,
    },
    {
      name: 'Document knowledge',
      type: 'db',
      version: `${documentEntries.length} source(s)`,
      status: documentEntries.length > 0 ? 'active' : 'shadow',
      scope: 'global',
      surface_priority: false,
    },
    {
      name: 'Live research',
      type: 'runtime',
      version: `${researchSources.length} source(s)`,
      status: researchSources.length > 0 ? 'active' : 'disabled',
      scope: 'turn',
      surface_priority: false,
    },
  ];
}

function collectRecentMergeEvents(memories, limit = 6) {
  const events = [];
  (memories || []).forEach((memory) => {
    (memory.history || []).forEach((entry) => {
      const eventType = String(entry?.type || '').trim().toLowerCase();
      if (!['merged', 'merged_into'].includes(eventType)) {
        return;
      }
      events.push({
        id: `${memory.id}:${entry.id || entry.at || eventType}`,
        memoryId: memory.id,
        timestamp: entry.at || memory.updated_at,
        source: memory.state_class || 'live',
        action: eventType === 'merged_into' ? 'merged' : eventType,
        reason: entry.note || entry.why || 'ok',
        label: clipText(memory.content || memory.text || memory.id, 84),
      });
    });
  });
  return events
    .sort((left, right) => String(right.timestamp || '').localeCompare(String(left.timestamp || '')))
    .slice(0, limit);
}

const EMPTY_KNOWLEDGE_AUTHORITY = {
  authority_order: [],
  active_authorities: [],
  preferences: {},
  presets: [],
  summary: {},
  current_contract: '',
  conflict_policy: {},
  surface_priority: {},
  sovereignty_guard: {},
  conflict_inbox: [],
  conflict_decisions: { deferred_conflicts: [] },
  doctrine: [],
  documents: [],
  live_research: { sources: [] },
  workspace: { projects: [] },
};

function Dashboard() {
  const [snapshot, setSnapshot] = useState(null);
  const [stateHygieneSnapshot, setStateHygieneSnapshot] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [truthScope, setTruthScope] = useState('live');
  const [selectedReviewId, setSelectedReviewId] = useState('');
  const [selectedRunId, setSelectedRunId] = useState('');
  const [selectedMemoryId, setSelectedMemoryId] = useState('');
  const [selectedReview, setSelectedReview] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [selectedMemory, setSelectedMemory] = useState(null);
  const [patchPreview, setPatchPreview] = useState(null);
  const [stateDiff, setStateDiff] = useState(null);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState('');
  const [repoMap, setRepoMap] = useState(null);
  const [symbols, setSymbols] = useState([]);
  const [symbolDetail, setSymbolDetail] = useState(null);
  const [symbolQuery, setSymbolQuery] = useState('');
  const [repoGoal, setRepoGoal] = useState('Trace the current workbench execution lane.');
  const [missionDraft, setMissionDraft] = useState(() => createMissionDraft());
  const [memoryDraft, setMemoryDraft] = useState(() => createMemoryDraft());
  const [memoryEditor, setMemoryEditor] = useState(() => createMemoryDraft());
  const [mergeSourceIds, setMergeSourceIds] = useState([]);
  const [busyKey, setBusyKey] = useState('');

  const loadSelectedMemoryDetail = useCallback(async (memoryId, { quiet = false } = {}) => {
    if (!memoryId) {
      setSelectedMemory(null);
      setMemoryEditor(createMemoryDraft());
      setMergeSourceIds([]);
      return null;
    }
    try {
      const response = await apiGet(`/api/jarvis/memory/${memoryId}`);
      const memory = response.data.memory;
      setSelectedMemory(memory);
      setMemoryEditor(createMemoryDraft({
        content: memory.content || memory.text || '',
        category: memory.category || 'general',
        priority: memory.priority ?? 50,
        why: memory.why || '',
      }));
      setMergeSourceIds([]);
      return memory;
    } catch (error) {
      if (!quiet) {
        toast.error(`Could not load memory detail: ${getApiErrorMessage(error)}`);
      }
      setSelectedMemory(null);
      setMemoryEditor(createMemoryDraft());
      setMergeSourceIds([]);
      return null;
    }
  }, []);

  const loadWorkbench = useCallback(async (showSpinner = true) => {
    if (showSpinner) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    try {
      const activeSessionId = getActiveJarvisSessionId();
      const requests = [
        apiGet('/api/jarvis/workbench', {
          params: {
            truth_scope: truthScope,
            ...(activeSessionId ? { session_id: activeSessionId } : {}),
          },
        }),
        apiGet('/api/jarvis/state-hygiene', { params: { truth_scope: truthScope } }),
      ];
      if (activeSessionId) {
        requests.push(apiGet(`/api/chat/sessions/${activeSessionId}`));
      }

      const [workbenchResult, hygieneResult, sessionResult] = await Promise.allSettled(requests);

      if (workbenchResult.status !== 'fulfilled') {
        throw workbenchResult.reason;
      }

      const nextSnapshot = workbenchResult.value.data;
      setSnapshot(nextSnapshot);
      setSelectedReviewId((current) => (
        current && (nextSnapshot.patch_reviews || []).some((review) => review.id === current)
          ? current
          : (nextSnapshot.patch_reviews?.[0]?.id || '')
      ));
      setSelectedRunId((current) => (
        current && (nextSnapshot.runs || []).some((run) => run.id === current)
          ? current
          : (nextSnapshot.runs?.[0]?.id || '')
      ));
      setSelectedMemoryId((current) => (
        current && (nextSnapshot.memory_bank?.memories || []).some((memory) => memory.id === current)
          ? current
          : (nextSnapshot.memory_bank?.memories?.[0]?.id || '')
      ));
      setStateHygieneSnapshot(
        hygieneResult.status === 'fulfilled'
          ? (hygieneResult.value.data?.state_hygiene || null)
          : null,
      );
      setActiveSession(
        sessionResult?.status === 'fulfilled'
          ? sessionResult.value.data
          : null,
      );
    } catch (error) {
      toast.error(`Could not load the workbench: ${getApiErrorMessage(error)}`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [truthScope]);

  useEffect(() => {
    loadWorkbench(true);
  }, [loadWorkbench]);

  useEffect(() => {
    if (!selectedReviewId) {
      setSelectedReview(null);
      setPatchPreview(null);
      return;
    }

    let active = true;
    apiGet(`/api/jarvis/patch/reviews/${selectedReviewId}`)
      .then((response) => {
        if (active) {
          setSelectedReview(response.data.review);
        }
      })
      .catch((error) => {
        if (active) {
          toast.error(`Could not load patch review: ${getApiErrorMessage(error)}`);
          setSelectedReview(null);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedReviewId]);

  useEffect(() => {
    if (!selectedRunId) {
      setSelectedRun(null);
      return;
    }

    let active = true;
    apiGet(`/api/jarvis/runs/${selectedRunId}`)
      .then((response) => {
        if (active) {
          setSelectedRun(response.data.run);
        }
      })
      .catch((error) => {
        if (active) {
          toast.error(`Could not load run detail: ${getApiErrorMessage(error)}`);
          setSelectedRun(null);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedRunId]);

  useEffect(() => {
    let active = true;
    loadSelectedMemoryDetail(selectedMemoryId)
      .then((memory) => {
        if (!active || memory) {
          return;
        }
        setSelectedMemory(null);
      })
      .catch((error) => {
        if (active) {
          toast.error(`Could not load memory detail: ${getApiErrorMessage(error)}`);
          setSelectedMemory(null);
          setMemoryEditor(createMemoryDraft());
        }
      });

    return () => {
      active = false;
    };
  }, [loadSelectedMemoryDetail, selectedMemoryId]);

  useEffect(() => {
    const snapshots = activeSession?.state_snapshots || [];
    if (!snapshots.length) {
      setSelectedSnapshotId('');
      setStateDiff(null);
      return;
    }
    setSelectedSnapshotId((current) => (
      current && snapshots.some((snapshot) => snapshot.id === current)
        ? current
        : snapshots[snapshots.length - 1].id
    ));
  }, [activeSession?.state_snapshots]);

  const knowledgeAuthority = snapshot?.knowledge_authority || EMPTY_KNOWLEDGE_AUTHORITY;
  const authorityPreferences = activeSession?.authority_preferences || knowledgeAuthority.preferences || {};
  const truthScopeLock = authorityPreferences.truth_scope_lock || null;

  useEffect(() => {
    const lockedScope = truthScopeLock?.scope;
    if (lockedScope && lockedScope !== truthScope) {
      setTruthScope(lockedScope);
    }
  }, [truthScopeLock?.scope, truthScope]);

  const missionBoard = snapshot?.mission_board || { missions: [] };
  const memoryBank = snapshot?.memory_bank || { summary: {}, memories: [], governance: {} };
  const reviews = snapshot?.patch_reviews || [];
  const runs = snapshot?.runs || [];
  const otemCatalog = snapshot?.otem || { workflow_catalog: [], tool_registry: [], execution_boundaries: [] };
  const forge = snapshot?.forge || {
    contractor: { kinds: [], latest: null },
    evaluator: { modes: [], latest: null },
  };
  const hygieneSnapshot = stateHygieneSnapshot || snapshot?.state_hygiene || {
    truth_scope: truthScope,
    memory: {},
    reviews: {},
    runs: {},
    governance: {},
  };
  const governance = snapshot?.governance || { active_break_glass: {}, open_policy_requests: [], recent_events: [] };
  const workspaceLane = snapshot?.workspace_lane || { profile: {}, projects: [] };
  const health = snapshot?.health || {};
  const authorityPresets = knowledgeAuthority.presets || [];
  const knowledgeConflictInbox = knowledgeAuthority.conflict_inbox || [];
  const authoritySurfacePriority = knowledgeAuthority.surface_priority || {};
  const authoritySovereigntyGuard = knowledgeAuthority.sovereignty_guard || {};
  const executionCockpit = useMemo(
    () => snapshot?.execution_cockpit || {},
    [snapshot],
  );
  const memoryGovernance = memoryBank.governance || {
    counts: {},
    merge_suggestions: [],
    conflicts: [],
    why_gaps: [],
    archive_review: [],
  };
  const recentApplyRuns = useMemo(
    () => executionCockpit.recent_apply_runs || [],
    [executionCockpit],
  );
  const activeSessionId = activeSession?.session_id || '';
  const activeOtemState = activeSession?.otem_state || null;
  const activeOtemPlan = activeOtemState?.session_context?.plan || activeOtemState?.plan || [];
  const activeOtemRecommendations = activeOtemState?.execution_awareness?.recommendations || [];
  const activeOtemToolSuggestions = activeOtemState?.tool_awareness?.suggestions || [];
  const activeOtemWorkflowHandoff = activeOtemState?.workflow_handoff || null;
  const activeOtemRejected = String(activeOtemState?.status || '').toLowerCase() === 'rejected';
  const activeSessionModeGuidance = activeSession?.mode_guidance || {};
  const activeSessionTrace = activeSession?.response_trace || {};
  const activeTurnContract = activeSession?.turn_contract || {};
  const activeThreadContract = activeSession?.thread_contract || {};
  const activeDriftState = activeSession?.drift_state || {};
  const activeSovereigntyContract = activeSession?.sovereignty_contract || {};
  const activeModeFreeze = activeSession?.mode_freeze || null;
  const sessionSnapshots = activeSession?.state_snapshots || [];
  const activeSessionProviderNotice = activeSession?.provider_notice || {};
  const authorityRows = useMemo(
    () => (knowledgeAuthority.active_authorities?.length
      ? knowledgeAuthority.active_authorities
      : buildAuthorityRows(knowledgeAuthority)),
    [knowledgeAuthority],
  );
  const authorityMode = useMemo(
    () => describeAuthorityMode(knowledgeAuthority),
    [knowledgeAuthority],
  );
  const recentMergeEvents = useMemo(
    () => collectRecentMergeEvents(memoryBank.memories || []),
    [memoryBank.memories],
  );
  const latestUserTurn = useMemo(
    () => [...(activeSession?.turns || [])].reverse().find((turn) => turn.role === 'user') || null,
    [activeSession],
  );
  const memoryState = useMemo(() => {
    if (memoryGovernance.conflicts?.length) {
      return { label: 'blocked-merge', tone: 'warning' };
    }
    if (memoryGovernance.merge_suggestions?.length || recentMergeEvents.length) {
      return { label: 'pending-merge', tone: 'warning' };
    }
    return { label: 'clean', tone: 'connected' };
  }, [memoryGovernance.conflicts, memoryGovernance.merge_suggestions, recentMergeEvents.length]);
  const fallbackState = useMemo(() => {
    if (activeSessionProviderNotice?.status === 'fallback') {
      return { label: 'in-fallback', tone: 'warning' };
    }
    if (activeSessionTrace?.fallback) {
      return { label: 'recovered', tone: 'connected' };
    }
    return { label: 'none', tone: 'connected' };
  }, [activeSessionProviderNotice?.status, activeSessionTrace?.fallback]);
  const authorityContract = useMemo(() => {
    const explicitContract = String(knowledgeAuthority?.current_contract || '').trim();
    if (explicitContract) {
      return explicitContract;
    }
    const contract = String(activeSessionTrace?.contract || '').trim();
    if (contract) {
      return `Final answer follows the ${contract.replace(/_/g, ' ')} contract, with shared authority precedence applied ahead of display.`;
    }
    return knowledgeAuthority?.conflict_policy?.winner_rule
      || 'Higher-precedence authority wins, and the UI renders the same shared truth order as the backend.';
  }, [activeSessionTrace?.contract, knowledgeAuthority?.conflict_policy?.winner_rule, knowledgeAuthority?.current_contract]);
  const authorityWarnings = useMemo(() => {
    const warnings = [];
    if (activeSessionProviderNotice?.status === 'fallback') {
      warnings.push('Fallback changed provider, not the turn contract.');
    }
    if (activeSessionModeGuidance?.status === 'auto_routed') {
      warnings.push(activeSessionModeGuidance.summary || 'Selector auto-routed the turn.');
    }
    if ((activeSessionTrace?.research_sources || 0) > 0 && !(knowledgeAuthority?.live_research?.sources || []).length) {
      warnings.push('Live research influenced the turn without a current research source snapshot.');
    }
    return warnings;
  }, [
    activeSessionModeGuidance?.status,
    activeSessionModeGuidance?.summary,
    activeSessionProviderNotice?.status,
    activeSessionTrace?.research_sources,
    knowledgeAuthority?.live_research?.sources,
  ]);
  const selectorSignals = useMemo(
    () => (activeSessionModeGuidance?.signals || []).map((signal) => String(signal)),
    [activeSessionModeGuidance?.signals],
  );
  const antiDebugSignals = useMemo(
    () => selectorSignals.filter((signal) => signal.includes('anti_debug') || signal.includes('operator_override')),
    [selectorSignals],
  );
  const explicitModeSignals = useMemo(
    () => selectorSignals.filter((signal) => !antiDebugSignals.includes(signal)),
    [antiDebugSignals, selectorSignals],
  );
  const providerMindStatus = useMemo(() => {
    const enginePath = String(activeSession?.provider_mind?.engine_path || '').trim().toLowerCase();
    if (!enginePath) {
      return 'not recorded';
    }
    if (activeSessionModeGuidance?.resolved_scope === 'debugging' && !enginePath.includes('debug')) {
      return 'attempted override (blocked)';
    }
    if (activeSessionModeGuidance?.resolved_scope !== 'debugging' && enginePath.includes('debug')) {
      return 'attempted override (blocked)';
    }
    return 'followed';
  }, [activeSession?.provider_mind?.engine_path, activeSessionModeGuidance?.resolved_scope]);
  const memoryObedience = useMemo(() => (
    memoryState.label === 'blocked-merge' ? 'attempted override (blocked)' : 'followed'
  ), [memoryState.label]);

  const selectedReviewApplyGate = useMemo(
    () => selectedReview?.apply_gate || {},
    [selectedReview],
  );
  const selectedRunArtifacts = useMemo(() => {
    const artifacts = selectedRun?.artifacts || [];
    return {
      patchApply: artifacts.find((artifact) => artifact.kind === 'patch_apply')?.payload || null,
      verificationPlan: artifacts.find((artifact) => artifact.kind === 'verification_plan')?.payload || null,
      preview: artifacts.find((artifact) => artifact.kind === 'patch_preview')?.payload || null,
    };
  }, [selectedRun]);

  const selectedRunReviewId = useMemo(
    () => selectedRun?.meta?.review_id || selectedRunArtifacts.patchApply?.review_id || '',
    [selectedRun, selectedRunArtifacts],
  );

  const availableMergeSources = useMemo(
    () => (memoryBank.memories || []).filter((memory) => memory.id !== selectedMemoryId),
    [memoryBank.memories, selectedMemoryId],
  );

  const latestMemoryHistory = useMemo(() => {
    const history = selectedMemory?.history || [];
    return history.length ? history[history.length - 1] : null;
  }, [selectedMemory]);

  const memoryStatusNotice = useMemo(() => {
    if (!selectedMemory) {
      return null;
    }
    if (selectedMemory.active === false) {
      return {
        tone: 'warning',
        title: 'Memory archived',
        body: selectedMemory.archived_reason || 'This note is archived and no longer participates in the active memory lane.',
      };
    }
    if (latestMemoryHistory?.type === 'merged') {
      const mergedCount = (selectedMemory.merged_from || []).length;
      return {
        tone: 'connected',
        title: 'Merge complete',
        body: mergedCount > 0
          ? `${mergedCount} source memory record(s) were folded into this canonical note.`
          : 'This memory now reflects the merged canonical note.',
      };
    }
    if (latestMemoryHistory?.type === 'rewritten') {
      return {
        tone: 'connected',
        title: 'Rewrite saved',
        body: 'The editor is showing the latest persisted memory text and rationale.',
      };
    }
    return null;
  }, [latestMemoryHistory, selectedMemory]);

  const executionStatusNotice = useMemo(() => {
    const selectedRunMatchesReview = Boolean(selectedReviewId)
      && selectedRunReviewId === selectedReviewId;
    const latestReviewApplyRun = recentApplyRuns.find((run) => run.review_id === selectedReviewId);

    if (
      selectedRunMatchesReview
      && selectedRunArtifacts.patchApply?.status === 'applied'
      && selectedRun?.status === 'completed'
    ) {
      const changedFiles = (selectedRunArtifacts.patchApply.changed_files || []).length;
      return {
        tone: 'connected',
        title: 'Patch applied',
        body: `Run ${selectedRun.id} completed with ${changedFiles} changed file(s). The verification lane is ready below.`,
      };
    }
    if (latestReviewApplyRun?.status === 'completed') {
      return {
        tone: 'connected',
        title: 'Latest apply recorded',
        body: `Run ${latestReviewApplyRun.id} already completed for this review. Inspect the run history before forcing another apply.`,
      };
    }
    if (selectedReviewApplyGate.ready) {
      return {
        tone: 'connected',
        title: 'Apply gate open',
        body: 'This review is accepted and ready to move through the guarded apply lane.',
      };
    }
    if (patchPreview?.status === 'aligned') {
      return {
        tone: 'connected',
        title: 'Preview aligned',
        body: patchPreview.summary || 'The current workspace still matches this proposed patch.',
      };
    }
    if (selectedReviewApplyGate.blockers?.length) {
      return {
        tone: 'warning',
        title: 'Apply blocked',
        body: selectedReviewApplyGate.blockers[0],
      };
    }
    return null;
  }, [patchPreview, recentApplyRuns, selectedReviewApplyGate, selectedReviewId, selectedRun, selectedRunArtifacts, selectedRunReviewId]);

  const executionSteps = useMemo(() => {
    const reviewState = selectedReview?.current_decision?.state || 'proposed';
    const applyState = selectedRun?.status || selectedRunArtifacts.patchApply?.status || 'pending';
    const verifyState = selectedRunArtifacts.verificationPlan
      ? 'planned'
      : (selectedReview?.patch_plan?.verification_checklist?.length ? 'ready' : 'pending');
    return [
      { label: 'Proposal', value: selectedReview ? 'loaded' : 'idle' },
      { label: 'Review', value: reviewState },
      { label: 'Apply', value: applyState },
      { label: 'Verify', value: verifyState },
    ];
  }, [selectedReview, selectedRun, selectedRunArtifacts]);

  const selectedReviewApplyHistory = useMemo(
    () => recentApplyRuns.filter((run) => run.review_id === selectedReviewId),
    [recentApplyRuns, selectedReviewId],
  );

  const handleRefresh = () => {
    loadWorkbench(false);
  };

  const compactStateHygiene = async () => {
    setBusyKey('state-hygiene-compact');
    try {
      const response = await apiPost('/api/jarvis/state-hygiene/compact', {});
      const result = response.data?.state_hygiene || {};
      await loadWorkbench(false);
      toast.success(
        `Compacted state hygiene: ${result.memory?.archived_memories || 0} memories, `
        + `${result.reviews?.archived_reviews || 0} reviews, `
        + `${result.runs?.expired_runs || 0} runs.`,
      );
    } catch (error) {
      toast.error(`Could not compact state hygiene: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const snapshotSessionState = async () => {
    if (!activeSessionId) {
      toast.error('Open an active Jarvis session before capturing a state snapshot.');
      return;
    }
    setBusyKey('state-snapshot');
    try {
      const response = await apiPost(`/api/chat/sessions/${activeSessionId}/state/snapshot`, {
        reason: 'Workbench snapshot',
      });
      setActiveSession(response.data);
      setSelectedSnapshotId(response.data?.snapshot?.id || '');
      setStateDiff(null);
      await loadWorkbench(false);
      toast.success('Session snapshot captured');
    } catch (error) {
      toast.error(`Could not capture state snapshot: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const flushFallbackResidue = async () => {
    if (!activeSessionId) {
      toast.error('Open an active Jarvis session before flushing fallback residue.');
      return;
    }
    setBusyKey('state-flush-fallback');
    try {
      const response = await apiPost(`/api/chat/sessions/${activeSessionId}/state/flush-fallback`, {});
      setActiveSession(response.data);
      await loadWorkbench(false);
      toast.success('Fallback residue flushed');
    } catch (error) {
      toast.error(`Could not flush fallback residue: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const freezeSessionMode = async (mode = activeSession?.response_mode || 'operator', turns = 3) => {
    if (!activeSessionId) {
      toast.error('Open an active Jarvis session before freezing mode.');
      return;
    }
    setBusyKey('state-freeze-mode');
    try {
      const response = await apiPost(`/api/chat/sessions/${activeSessionId}/state/freeze-mode`, {
        mode,
        turns,
      });
      setActiveSession(response.data);
      await loadWorkbench(false);
      toast.success(`Mode frozen to ${mode} for ${turns} turn${turns === 1 ? '' : 's'}`);
    } catch (error) {
      toast.error(`Could not freeze session mode: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const hardResetSessionState = async () => {
    if (!activeSessionId) {
      toast.error('Open an active Jarvis session before resetting session state.');
      return;
    }
    setBusyKey('state-reset');
    try {
      const response = await apiPost(`/api/chat/sessions/${activeSessionId}/state/reset`, {});
      setActiveSession(response.data);
      await loadWorkbench(false);
      toast.success('Session state reset while mission context stayed intact');
    } catch (error) {
      toast.error(`Could not reset session state: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const updateAuthorityPreferences = async (payload, successMessage, busyToken = 'authority-control') => {
    if (!activeSessionId) {
      toast.error('Open an active Jarvis session before changing authority controls.');
      return null;
    }
    setBusyKey(busyToken);
    try {
      const response = await apiPost(`/api/chat/sessions/${activeSessionId}/authority/preferences`, payload);
      setActiveSession(response.data);
      await loadWorkbench(false);
      if (successMessage) {
        toast.success(successMessage);
      }
      return response.data;
    } catch (error) {
      toast.error(`Could not update authority controls: ${getApiErrorMessage(error)}`);
      return null;
    } finally {
      setBusyKey('');
    }
  };

  const applyAuthorityPreset = (presetId) => updateAuthorityPreferences(
    { preset: presetId },
    `${presetId.replace(/_/g, ' ')} preset applied`,
    `authority-preset:${presetId}`,
  );

  const pinPrimaryAuthority = (sourceType) => updateAuthorityPreferences(
    { action: 'pin_primary', source_type: sourceType },
    `${sourceType.replace(/_/g, ' ')} surfaced for operator priority`,
    `authority-pin:${sourceType}`,
  );

  const setAuthorityShadow = (sourceType) => updateAuthorityPreferences(
    { action: 'demote_shadow', source_type: sourceType },
    `${sourceType.replace(/_/g, ' ')} moved to shadow`,
    `authority-shadow:${sourceType}`,
  );

  const toggleAuthorityDisabled = (sourceType, disabled) => updateAuthorityPreferences(
    { action: disabled ? 'enable' : 'disable', source_type: sourceType },
    disabled
      ? `${sourceType.replace(/_/g, ' ')} re-enabled`
      : `${sourceType.replace(/_/g, ' ')} disabled`,
    `authority-toggle:${sourceType}`,
  );

  const lockTruthScope = (scope = truthScope, turns = 3) => updateAuthorityPreferences(
    { action: 'lock_truth_scope', truth_scope: scope, turns },
    `Truth scope locked to ${scope} for ${turns} turn${turns === 1 ? '' : 's'}`,
    'authority-lock-scope',
  );

  const unlockTruthScope = () => updateAuthorityPreferences(
    { action: 'unlock_truth_scope' },
    'Truth-scope lock removed',
    'authority-unlock-scope',
  );

  const compareSessionState = async (snapshotId = selectedSnapshotId, { quiet = false } = {}) => {
    if (!activeSessionId) {
      if (!quiet) {
        toast.error('Open an active Jarvis session before comparing state.');
      }
      return null;
    }
    setBusyKey('state-diff');
    try {
      const response = await apiGet(`/api/chat/sessions/${activeSessionId}/state/diff`, {
        params: snapshotId ? { snapshot_id: snapshotId } : {},
      });
      setStateDiff(response.data?.state_diff || null);
      if (snapshotId) {
        setSelectedSnapshotId(snapshotId);
      }
      if (!quiet) {
        toast.success(response.data?.state_diff?.summary || 'State diff loaded');
      }
      return response.data?.state_diff || null;
    } catch (error) {
      if (!quiet) {
        toast.error(`Could not compare state snapshots: ${getApiErrorMessage(error)}`);
      }
      return null;
    } finally {
      setBusyKey('');
    }
  };

  const toggleDeferredConflict = async (conflictId, deferred) => {
    if (!activeSessionId) {
      toast.error('Open an active Jarvis session before managing conflict inbox items.');
      return;
    }
    setBusyKey(`conflict:${conflictId}`);
    try {
      const response = await apiPost(`/api/chat/sessions/${activeSessionId}/knowledge/conflicts/${encodeURIComponent(conflictId)}/defer`, {
        deferred,
      });
      setActiveSession(response.data);
      await loadWorkbench(false);
      toast.success(deferred ? 'Conflict deferred' : 'Conflict reopened');
    } catch (error) {
      toast.error(`Could not update conflict inbox: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const archiveConflictMemory = async (memoryId) => {
    if (!memoryId) {
      toast.error('This conflict does not expose an archive candidate.');
      return;
    }
    setBusyKey(`conflict-archive:${memoryId}`);
    try {
      await apiPost(`/api/jarvis/memory/${memoryId}/archive`, {
        reason: 'Archived from the Knowledge Authority conflict inbox.',
      });
      await loadWorkbench(false);
      toast.success('Conflict archive applied');
    } catch (error) {
      toast.error(`Could not archive conflict candidate: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const focusMemoryRecord = (memoryId, mergeIds = []) => {
    setSelectedMemoryId(memoryId);
    setMergeSourceIds(mergeIds);
  };

  const updateMissionStatus = async (missionId, status) => {
    setBusyKey(`mission:${missionId}:${status}`);
    try {
      await apiPatch(`/api/jarvis/missions/${missionId}`, { status });
      await loadWorkbench(false);
    } catch (error) {
      toast.error(`Could not update mission: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const focusMission = async (missionId) => {
    setBusyKey(`mission-focus:${missionId}`);
    try {
      await apiPost(`/api/jarvis/missions/${missionId}/focus`, {});
      await loadWorkbench(false);
    } catch (error) {
      toast.error(`Could not focus mission: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const createMission = async (event) => {
    event.preventDefault();
    if (!missionDraft.title.trim() || !missionDraft.objective.trim()) {
      toast.error('Mission title and objective are required.');
      return;
    }
    setBusyKey('mission-create');
    try {
      await apiPost('/api/jarvis/missions', {
        title: missionDraft.title,
        objective: missionDraft.objective,
        next_step: missionDraft.next_step,
        status: 'queued',
      });
      setMissionDraft(createMissionDraft());
      await loadWorkbench(false);
      toast.success('Mission added to the board');
    } catch (error) {
      toast.error(`Could not create mission: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const createMemory = async (event) => {
    event.preventDefault();
    if (!memoryDraft.content.trim()) {
      toast.error('Memory content is required.');
      return;
    }
    setBusyKey('memory-create');
    try {
      await apiPost('/api/jarvis/memory', {
        content: memoryDraft.content,
        category: memoryDraft.category,
        priority: Number(memoryDraft.priority) || 50,
        why: memoryDraft.why,
      });
      setMemoryDraft(createMemoryDraft());
      await loadWorkbench(false);
      toast.success('Memory saved');
    } catch (error) {
      toast.error(`Could not create memory: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const saveMemory = async (event) => {
    event.preventDefault();
    if (!selectedMemoryId || !memoryEditor.content.trim()) {
      toast.error('Choose a memory and keep its content filled in.');
      return;
    }
    setBusyKey('memory-save');
    try {
      await apiPatch(`/api/jarvis/memory/${selectedMemoryId}`, {
        content: memoryEditor.content,
        category: memoryEditor.category,
        priority: Number(memoryEditor.priority) || 50,
        why: memoryEditor.why,
        note: 'Updated from the Jarvis Workbench.',
      });
      await loadWorkbench(false);
      await loadSelectedMemoryDetail(selectedMemoryId, { quiet: true });
      toast.success('Memory updated');
    } catch (error) {
      toast.error(`Could not save memory: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const archiveMemory = async () => {
    if (!selectedMemoryId) {
      return;
    }
    setBusyKey('memory-archive');
    try {
      await apiPost(`/api/jarvis/memory/${selectedMemoryId}/archive`, {
        reason: 'Archived from the Jarvis Workbench.',
      });
      await loadWorkbench(false);
      await loadSelectedMemoryDetail(selectedMemoryId, { quiet: true });
      toast.success('Memory archived');
    } catch (error) {
      toast.error(`Could not archive memory: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const mergeMemory = async () => {
    if (!selectedMemoryId || mergeSourceIds.length === 0) {
      toast.error('Pick at least one merge source.');
      return;
    }
    setBusyKey('memory-merge');
    try {
      await apiPost('/api/jarvis/memory/merge', {
        target_id: selectedMemoryId,
        source_ids: mergeSourceIds,
        why: memoryEditor.why,
        note: 'Merged from the Jarvis Workbench.',
      });
      await loadWorkbench(false);
      await loadSelectedMemoryDetail(selectedMemoryId, { quiet: true });
      toast.success('Memories merged into one canonical note');
    } catch (error) {
      toast.error(`Could not merge memories: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const decideReview = async (decision) => {
    if (!selectedReviewId) {
      return;
    }
    setBusyKey(`review:${decision}`);
    try {
      const response = await apiPost(`/api/jarvis/patch/reviews/${selectedReviewId}/decision`, {
        decision,
        note: `Workbench marked this review ${decision.replace('_', ' ')}.`,
      });
      setSelectedReview(response.data.review);
      await loadWorkbench(false);
      toast.success(`Review marked ${decision.replace('_', ' ')}`);
    } catch (error) {
      toast.error(`Could not update review: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const previewReview = async () => {
    if (!selectedReviewId) {
      return;
    }
    setBusyKey('review-preview');
    try {
      const response = await apiPost('/api/jarvis/patch/preview', { review_id: selectedReviewId });
      setPatchPreview(response.data.preview);
    } catch (error) {
      toast.error(`Could not preview review: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const applyReview = async () => {
    if (!selectedReviewId) {
      return;
    }
    setBusyKey('review-apply');
    try {
      const response = await apiPost(`/api/jarvis/patch/reviews/${selectedReviewId}/apply`, {});
      setPatchPreview(response.data.preview);
      setSelectedRun(response.data.run);
      setSelectedRunId(response.data.run?.id || '');
      await loadWorkbench(false);
      toast.success('Accepted patch applied');
    } catch (error) {
      if (error?.response?.status === 409 && error?.response?.data?.run) {
        const latestRun = error.response.data.run;
        setSelectedRun(latestRun);
        setSelectedRunId(latestRun.id || '');
        toast.success('This review already has a completed apply run. Opened the latest run instead.');
      } else {
      toast.error(`Could not apply patch review: ${getApiErrorMessage(error)}`);
      }
    } finally {
      setBusyKey('');
    }
  };

  const searchSymbols = async (event) => {
    event.preventDefault();
    if (!symbolQuery.trim()) {
      return;
    }
    setBusyKey('workspace-symbols');
    try {
      const response = await apiPost('/api/jarvis/workspace/symbols', {
        query: symbolQuery,
        limit: 10,
      });
      setSymbols(response.data.symbols || []);
      if ((response.data.symbols || [])[0]) {
        const first = response.data.symbols[0];
        const detail = await apiGet('/api/jarvis/workspace/symbol', {
          params: { symbol: first.qualname || first.name, path: first.path },
        });
        setSymbolDetail(detail.data.symbol || null);
      }
    } catch (error) {
      toast.error(`Could not search workspace symbols: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const openSymbol = async (symbol) => {
    setBusyKey('workspace-symbol-detail');
    try {
      const response = await apiGet('/api/jarvis/workspace/symbol', {
        params: { symbol: symbol.qualname || symbol.name, path: symbol.path },
      });
      setSymbolDetail(response.data.symbol || null);
    } catch (error) {
      toast.error(`Could not open symbol detail: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const mapWorkspace = async (event) => {
    event.preventDefault();
    setBusyKey('workspace-repo-map');
    try {
      const response = await apiPost('/api/jarvis/workspace/repo-map', {
        goal: repoGoal,
        focus_path: selectedReview?.patch_plan?.target_files?.[0],
        limit: 10,
      });
      setRepoMap(response.data);
    } catch (error) {
      toast.error(`Could not inspect the workspace lane: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  const toggleBreakGlass = async () => {
    const isActive = Boolean(governance.active_break_glass?.active);
    setBusyKey('break-glass');
    try {
      await apiPost('/api/jarvis/governance/break-glass', isActive
        ? {
            action: 'clear',
            actor_id: 'owner_local',
            actor_role: 'owner',
            reason: 'Workbench cleared break-glass.',
          }
        : {
            actor_id: 'owner_local',
            actor_role: 'owner',
            scope: 'high_sensitivity_access',
            duration_minutes: 10,
            reason: 'Workbench raised break-glass for operator review.',
          });
      await loadWorkbench(false);
      toast.success(isActive ? 'Break-glass cleared' : 'Break-glass activated');
    } catch (error) {
      toast.error(`Could not update break-glass: ${getApiErrorMessage(error)}`);
    } finally {
      setBusyKey('');
    }
  };

  if (loading && !snapshot) {
    return (
      <section className="workbench">
        <div className="page-intro">
          <h1>Jarvis Workbench</h1>
          <p>Loading the operator desk.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="workbench">
      <header className="workbench-hero">
        <div className="workbench-hero-copy">
          <div className={`status-pill ${health.ai_status === 'initialized' ? 'connected' : 'warning'}`}>
            <FiActivity />
            {health.ai_status === 'initialized' ? 'jarvis operator desk online' : 'runtime is warming up'}
          </div>
          <h1>Jarvis Workbench</h1>
          <p>
            Mission control, memory governance, patch review, run history, workspace intel,
            and governance now live in one calmer operator surface.
          </p>
          <div className="workbench-hero-actions">
            <Link to="/jarvis" className="workbench-button primary">
              Open Console
            </Link>
            <Link to="/memory" className="workbench-button ghost">
              Full Memory Bank
            </Link>
            <button
              type="button"
              className="workbench-button ghost"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <FiRefreshCw />
              {refreshing ? 'Refreshing' : 'Refresh'}
            </button>
          </div>
        </div>

        <div className="workbench-hero-side page-panel">
          <div className="workbench-health-row">
            <span>Ready reviews</span>
            <strong>{executionCockpit.ready_review_count || 0}</strong>
          </div>
          <div className="workbench-health-row">
            <span>Open runs</span>
            <strong>{executionCockpit.open_run_count || 0}</strong>
          </div>
          <div className="workbench-health-row">
            <span>Memory bank</span>
            <strong>{memoryBank.summary?.total || 0} records</strong>
          </div>
          <div className="workbench-health-row">
            <span>Focus mission</span>
            <strong>{missionBoard.focus_mission?.title || 'No focused mission yet'}</strong>
          </div>
          <div className="workbench-health-row">
            <span>Runtime modes</span>
            <strong>{health.requested_model_mode || 'auto'} / {health.active_model_mode || 'idle'}</strong>
          </div>
        </div>
      </header>

      <nav className="workbench-jump-row page-panel" aria-label="Workbench sections" data-testid="workbench-jump-nav">
        <a href="#workbench-authority-state" className="workbench-jump-link" data-testid="jump-authority-state">Authority &amp; State</a>
        <a href="#workbench-otem" className="workbench-jump-link" data-testid="jump-otem">OTEM</a>
        <a href="#workbench-forge" className="workbench-jump-link" data-testid="jump-forge">Forge</a>
        <a href="#workbench-execution" className="workbench-jump-link" data-testid="jump-execution">Execution</a>
        <a href="#workbench-missions" className="workbench-jump-link" data-testid="jump-missions">Missions</a>
        <a href="#workbench-memory" className="workbench-jump-link" data-testid="jump-memory">Memory</a>
        <a href="#workbench-workspace" className="workbench-jump-link" data-testid="jump-workspace">Workspace</a>
        <a href="#workbench-governance" className="workbench-jump-link" data-testid="jump-governance">Governance</a>
        <Link to="/jarvis" className="workbench-jump-link" data-testid="jump-console">Console</Link>
      </nav>

      <section id="workbench-authority-state" className="workbench-section page-panel" data-testid="workbench-authority-state">
        <div className="workbench-section-head">
          <div>
            <span>Authority &amp; State</span>
            <h2>Make truth order, selector decisions, and hygiene visible</h2>
          </div>
          <div className="workbench-action-row compact">
            <button
              type="button"
              className={`workbench-button ghost ${truthScope === 'live' ? 'is-active' : ''}`}
              onClick={() => setTruthScope('live')}
              data-testid="truth-scope-live"
            >
              Live truth
            </button>
            <button
              type="button"
              className={`workbench-button ghost ${truthScope === 'all' ? 'is-active' : ''}`}
              onClick={() => setTruthScope('all')}
              data-testid="truth-scope-all"
            >
              All records
            </button>
            <button
              type="button"
              className="workbench-button ghost"
              onClick={compactStateHygiene}
              disabled={busyKey === 'state-hygiene-compact'}
              data-testid="state-hygiene-compact-button"
            >
              <FiArchive />
              Compact residue
            </button>
          </div>
        </div>

        <div className="workbench-authority-grid">
          <div className="workbench-authority-column" data-testid="workbench-knowledge">
            <div className="workbench-checklist">
              <h4>Truth-scope summary</h4>
              <div className="workbench-inline-grid">
                <div className="workbench-mini-panel">
                  <span>Mode</span>
                  <strong>{authorityMode}</strong>
                </div>
                <div className="workbench-mini-panel">
                  <span>Scope</span>
                  <strong>{truthScope}</strong>
                </div>
                <div className="workbench-mini-panel">
                  <span>Contract</span>
                  <strong>{clipText(authorityContract, 86)}</strong>
                </div>
              </div>
              <div className="workbench-inline-grid">
                <div className="workbench-mini-panel">
                  <span>Surface priority</span>
                  <strong>{authoritySurfacePriority.label || authorityPreferences.primary_source || 'shared precedence'}</strong>
                </div>
                <div className="workbench-mini-panel">
                  <span>Truth lock</span>
                  <strong>{truthScopeLock ? `${truthScopeLock.scope} (${truthScopeLock.remaining_turns} turns)` : 'none'}</strong>
                </div>
                <div className="workbench-mini-panel">
                  <span>Conflicts</span>
                  <strong>{knowledgeAuthority.summary?.active_conflict_count ?? knowledgeConflictInbox.length} active</strong>
                </div>
              </div>
              <div className="workbench-chip-row">
                {(knowledgeAuthority.authority_order || []).slice(0, 5).map((entry) => (
                  <span key={`${entry.source_type}:${entry.truth_status}`} className="workbench-chip">
                    {entry.label}
                  </span>
                ))}
              </div>
              <p className="workbench-muted">
                Surface priority changes operator visibility only. Jarvis routing, voice, and final authority still come from the turn contract.
              </p>
              <div className="workbench-action-row compact">
                {authorityPresets.map((preset) => (
                  <button
                    key={preset.id}
                    type="button"
                    className={`workbench-button ghost ${authorityPreferences.preset === preset.id ? 'is-active' : ''}`}
                    onClick={() => applyAuthorityPreset(preset.id)}
                    disabled={!activeSessionId || busyKey === `authority-preset:${preset.id}`}
                    data-testid={`authority-preset-${preset.id}`}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
              <div className="workbench-action-row compact">
                <button
                  type="button"
                  className="workbench-button ghost"
                  onClick={() => lockTruthScope(truthScope, 3)}
                  disabled={!activeSessionId || busyKey === 'authority-lock-scope'}
                  data-testid="authority-lock-truth-scope"
                >
                  Lock {truthScope} for 3 turns
                </button>
                <button
                  type="button"
                  className="workbench-button ghost"
                  onClick={unlockTruthScope}
                  disabled={!activeSessionId || !truthScopeLock || busyKey === 'authority-unlock-scope'}
                  data-testid="authority-unlock-truth-scope"
                >
                  Unlock truth scope
                </button>
              </div>
            </div>

            <div className="workbench-checklist">
              <h4>Active authorities</h4>
              <div className="workbench-history-list">
                {authorityRows.map((authority) => (
                  <div key={authority.source_type || authority.name} className="workbench-history-item workbench-authority-item">
                    <div>
                      <strong>{authority.name}</strong>
                      <p>{authority.type} · {authority.version}</p>
                        <div className="workbench-chip-row">
                        <span className={`status-pill ${toneForState(authority.status)}`}>
                          {authority.status}
                        </span>
                        <span className="status-pill ghost">{authority.scope}</span>
                        {authority.surface_priority ? (
                          <span className="status-pill connected">surface</span>
                        ) : null}
                      </div>
                    </div>
                    <div className="workbench-action-row compact workbench-inline-actions">
                      <button
                        type="button"
                        className="workbench-button ghost"
                        onClick={() => pinPrimaryAuthority(authority.source_type)}
                        disabled={!activeSessionId || !authority.source_type || authority.surface_priority || busyKey === `authority-pin:${authority.source_type}`}
                        data-testid={`authority-pin-${authority.source_type}`}
                      >
                        Surface priority
                      </button>
                      <button
                        type="button"
                        className="workbench-button ghost"
                        onClick={() => setAuthorityShadow(authority.source_type)}
                        disabled={!activeSessionId || !authority.source_type || authority.status === 'shadow' || busyKey === `authority-shadow:${authority.source_type}`}
                        data-testid={`authority-shadow-${authority.source_type}`}
                      >
                        Demote to shadow
                      </button>
                      <button
                        type="button"
                        className="workbench-button ghost"
                        onClick={() => toggleAuthorityDisabled(authority.source_type, authority.status === 'disabled')}
                        disabled={!activeSessionId || !authority.source_type || busyKey === `authority-toggle:${authority.source_type}`}
                        data-testid={`authority-toggle-${authority.source_type}`}
                      >
                        {authority.status === 'disabled' ? 'Enable' : 'Disable'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="workbench-checklist">
              <h4>Per-turn authority trace</h4>
              <p className="workbench-muted">
                {activeSessionId
                  ? `Active session ${activeSessionId} is using the same precedence snapshot the backend resolves.`
                  : 'No active Jarvis session is selected in this browser yet.'}
              </p>
              <div className="workbench-chip-row">
                {(knowledgeAuthority.authority_order || []).slice(0, 3).map((entry, index) => (
                  <span key={`${entry.source_type}:${entry.truth_status}:trace`} className="workbench-chip">
                    #{index + 1} {entry.label}
                  </span>
                ))}
              </div>
              <ul>
                <li>Memory evidence: {activeSessionTrace?.memory_count || 0}</li>
                <li>Workspace evidence: {activeSessionTrace?.workspace_hits || 0}</li>
                <li>Live research sources: {activeSessionTrace?.research_sources || 0}</li>
                <li>Resolved contract: {(activeSessionTrace?.contract || 'not recorded').replace(/_/g, ' ')}</li>
                <li>Sovereign writer: {activeSovereigntyContract.state_writer || 'jarvis_sovereign_core'}</li>
                <li>Surface priority guard: {authoritySovereigntyGuard.surface_priority_non_authoritative ? 'presentation only' : 'not recorded'}</li>
              </ul>
              {authorityWarnings.length ? (
                <div className="workbench-notice warning">
                  <strong>Authority warnings</strong>
                  <ul>
                    {authorityWarnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="workbench-muted">No authority drift warnings are recorded on the latest visible turn.</p>
              )}
            </div>

            <div className="workbench-checklist" data-testid="knowledge-conflict-inbox">
              <div className="workbench-subhead compact">
                <h4>Knowledge conflict inbox</h4>
                <p>{knowledgeConflictInbox.length} visible</p>
              </div>
              {knowledgeConflictInbox.length ? (
                <div className="workbench-history-list">
                  {knowledgeConflictInbox.map((conflict) => (
                    <div key={conflict.id} className="workbench-history-item workbench-conflict-item" data-testid={`knowledge-conflict-${conflict.id}`}>
                      <div>
                        <strong>{conflict.title}</strong>
                        <p>{conflict.summary}</p>
                        <div className="workbench-chip-row">
                          <span className={`status-pill ${toneForDecision(conflict.status)}`}>{conflict.status}</span>
                          <span className={`status-pill ${toneForState(conflict.severity)}`}>{conflict.severity}</span>
                          <span className="status-pill ghost">{conflict.source_type}</span>
                        </div>
                      </div>
                      <div className="workbench-action-row compact workbench-inline-actions">
                        <button
                          type="button"
                          className="workbench-button ghost"
                          onClick={() => focusMemoryRecord(conflict.target_memory_id, conflict.memory_ids || [])}
                          disabled={!conflict.actions?.focus_memory}
                          data-testid={`knowledge-conflict-focus-${conflict.id}`}
                        >
                          Focus
                        </button>
                        <button
                          type="button"
                          className="workbench-button ghost"
                          onClick={() => archiveConflictMemory(conflict.archive_candidate_id)}
                          disabled={!conflict.actions?.archive_candidate || busyKey === `conflict-archive:${conflict.archive_candidate_id}`}
                          data-testid={`knowledge-conflict-archive-${conflict.id}`}
                        >
                          Archive candidate
                        </button>
                        <button
                          type="button"
                          className="workbench-button ghost"
                          onClick={() => toggleDeferredConflict(conflict.id, conflict.status !== 'deferred')}
                          disabled={!activeSessionId || !conflict.actions?.defer || busyKey === `conflict:${conflict.id}`}
                          data-testid={`knowledge-conflict-defer-${conflict.id}`}
                        >
                          {conflict.status === 'deferred' ? 'Reopen' : 'Defer'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="workbench-muted">No active knowledge conflicts are visible in the current authority stack.</p>
              )}
            </div>
          </div>

          <div className="workbench-authority-column" data-testid="workbench-state-hygiene">
            <div className="workbench-checklist">
              <h4>Live session state snapshot</h4>
              <div className="workbench-inline-grid">
                <div className="workbench-mini-panel">
                  <span>Session</span>
                  <strong>{activeSessionId || 'No active session'}</strong>
                </div>
                <div className="workbench-mini-panel">
                  <span>Turn</span>
                  <strong>{activeSession?.turn_count || 0}</strong>
                </div>
                <div className="workbench-mini-panel">
                  <span>Resolved mode</span>
                  <strong>{activeSessionModeGuidance?.effective_mode || activeSession?.response_mode || 'fast'}</strong>
                </div>
              </div>
              <div className="workbench-chip-row">
                <span className={`status-pill ${toneForState(activeSessionModeGuidance?.effective_mode || activeSession?.response_mode)}`}>
                  Mode · {activeSessionModeGuidance?.effective_mode || activeSession?.response_mode || 'fast'}
                </span>
                <span className={`status-pill ${activeSessionProviderNotice?.status === 'fallback' ? 'warning' : 'connected'}`}>
                  Provider · {activeSession?.model_route?.provider_label || activeSession?.model_route?.provider || activeSession?.preferred_provider || 'local'}
                </span>
                <span className={`status-pill ${fallbackState.tone}`}>
                  Fallback · {fallbackState.label}
                </span>
                <span className={`status-pill ${memoryState.tone}`}>
                  Memory · {memoryState.label}
                </span>
              </div>
              <ul>
                <li>Contract label: {activeTurnContract.contract_label || 'mode_guidance'}</li>
                <li>Resolved voice: {activeTurnContract.resolved_voice || activeSessionModeGuidance?.resolved_voice || 'jarvis'}</li>
                <li>Thread contract mode: {activeThreadContract.mode || 'standard'}</li>
                <li>Drift state: {activeDriftState.status || 'aligned'}</li>
                <li>Mode freeze: {activeModeFreeze ? `${activeModeFreeze.mode} for ${activeModeFreeze.remaining_turns} turn(s)` : 'none'}</li>
              </ul>
            </div>

            <div className="workbench-checklist">
              <div className="workbench-subhead compact">
                <h4>Memory merge inspector</h4>
                {memoryGovernance.merge_suggestions?.[0] ? (
                  <button
                    type="button"
                    className="workbench-button ghost"
                    onClick={() => focusMemoryRecord(
                      memoryGovernance.merge_suggestions[0].target_id,
                      memoryGovernance.merge_suggestions[0].source_ids || [],
                    )}
                    data-testid="memory-next-merge-candidate"
                  >
                    Show candidates
                  </button>
                ) : null}
              </div>
              {recentMergeEvents.length ? (
                <div className="workbench-history-list">
                  {recentMergeEvents.map((event) => (
                    <button
                      key={event.id}
                      type="button"
                      className="workbench-history-item action"
                      onClick={() => focusMemoryRecord(event.memoryId)}
                      data-testid={`memory-merge-event-${event.memoryId}`}
                    >
                      <div>
                        <strong>{event.label}</strong>
                        <p>{event.action} · {event.reason}</p>
                      </div>
                      <small>{event.source} · {formatStamp(event.timestamp)}</small>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="workbench-muted">No recent merge events are visible in the current truth scope.</p>
              )}
            </div>

            <div className="workbench-checklist" data-testid="selector-decision-trace">
              <h4>Selector decision trace</h4>
              <ul>
                <li>Operator text: {clipText(latestUserTurn?.content || 'No recent user turn in the active session.', 120)}</li>
                <li>Requested mode: {activeSession?.requested_response_mode || 'not recorded'}</li>
                <li>Selector trigger: {activeSessionModeGuidance?.selector_trigger || 'none'}</li>
                <li>Selector reason: {activeSessionModeGuidance?.selector_reason || 'operator-task default'}</li>
                <li>Anti-debug phrases: {antiDebugSignals.length ? antiDebugSignals.join(', ') : 'none'}</li>
                <li>Mode hints: {explicitModeSignals.length ? explicitModeSignals.join(', ') : 'none'}</li>
                <li>Resolved scope: {activeSessionModeGuidance?.resolved_scope || 'operator_task'}</li>
                <li>Resolved voice: {activeSessionModeGuidance?.resolved_voice || 'jarvis'}</li>
              </ul>
              <div className="workbench-chip-row">
                <span className={`status-pill ${toneForDecision(providerMindStatus)}`}>ProviderMind · {providerMindStatus}</span>
                <span className={`status-pill ${toneForDecision(memoryObedience)}`}>Memory · {memoryObedience}</span>
                <span className={`status-pill ${toneForDecision(activeSessionProviderNotice?.status === 'fallback' ? 'followed' : 'not invoked')}`}>
                  Fallback · {activeSessionProviderNotice?.status === 'fallback' ? 'followed' : 'not invoked'}
                </span>
                <span className={`status-pill ${toneForState(activeDriftState.status || 'aligned')}`}>Anti-drift · {activeDriftState.status || 'aligned'}</span>
              </div>
            </div>

            <div className="workbench-checklist">
              <h4>Hygiene posture</h4>
              <div className="workbench-inline-grid">
                <div className="workbench-mini-panel">
                  <span>Memories</span>
                  <strong>{hygieneSnapshot.memory?.visible ?? memoryBank.summary?.active ?? 0} visible / {hygieneSnapshot.memory?.total ?? memoryBank.summary?.total ?? 0} total</strong>
                </div>
                <div className="workbench-mini-panel">
                  <span>Reviews</span>
                  <strong>{hygieneSnapshot.reviews?.visible ?? reviews.length} visible / {hygieneSnapshot.reviews?.total ?? reviews.length} total</strong>
                </div>
                <div className="workbench-mini-panel">
                  <span>Runs</span>
                  <strong>{hygieneSnapshot.runs?.visible ?? runs.length} visible / {hygieneSnapshot.runs?.total ?? runs.length} total</strong>
                </div>
              </div>
              <div className="workbench-chip-row">
                <span className={`status-pill ${toneForBadge(hygieneSnapshot.memory?.state_hygiene?.badge?.tone)}`}>
                  Live {hygieneSnapshot.memory?.state_hygiene?.live ?? hygieneSnapshot.memory?.live ?? 0}
                </span>
                <span className="status-pill warning">Demo {hygieneSnapshot.memory?.state_hygiene?.demo ?? hygieneSnapshot.memory?.demo ?? 0}</span>
                <span className="status-pill warning">Smoke {hygieneSnapshot.memory?.state_hygiene?.smoke ?? hygieneSnapshot.memory?.smoke ?? 0}</span>
                <span className="status-pill ghost">Archived {hygieneSnapshot.memory?.state_hygiene?.archived ?? hygieneSnapshot.memory?.archived ?? 0}</span>
              </div>
            </div>

            <div className="workbench-checklist" data-testid="state-diff-panel">
              <div className="workbench-subhead compact">
                <h4>State diff</h4>
                <button
                  type="button"
                  className="workbench-button ghost"
                  onClick={() => compareSessionState(sessionSnapshots[sessionSnapshots.length - 1]?.id)}
                  disabled={!activeSessionId || !sessionSnapshots.length || busyKey === 'state-diff'}
                  data-testid="state-diff-latest-button"
                >
                  Compare latest snapshot
                </button>
              </div>
              {stateDiff ? (
                <>
                  <div className={`workbench-notice compact ${stateDiff.changed ? 'warning' : 'connected'}`}>
                    <strong>{stateDiff.summary}</strong>
                    <p>
                      Baseline: {stateDiff.baseline?.reason || 'Current session state'}
                      {stateDiff.baseline?.captured_at ? ` · ${formatStamp(stateDiff.baseline.captured_at)}` : ''}
                    </p>
                  </div>
                  {stateDiff.changes?.length ? (
                    <div className="workbench-history-list">
                      {stateDiff.changes.map((change) => (
                        <div key={change.field} className="workbench-history-item">
                          <div>
                            <strong>{change.label}</strong>
                            <p>{change.field}</p>
                          </div>
                          <small>
                            {String(change.before ?? 'none')} → {String(change.after ?? 'none')}
                          </small>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </>
              ) : (
                <p className="workbench-muted">Capture a snapshot, then compare it against the current session state.</p>
              )}
              {sessionSnapshots.length ? (
                <div className="workbench-history-list">
                  {sessionSnapshots.slice().reverse().slice(0, 4).map((snapshot) => (
                    <button
                      key={snapshot.id}
                      type="button"
                      className={`workbench-history-item action ${selectedSnapshotId === snapshot.id ? 'selected' : ''}`}
                      onClick={() => compareSessionState(snapshot.id)}
                      data-testid={`state-snapshot-${snapshot.id}`}
                    >
                      <div>
                        <strong>{snapshot.reason || 'Snapshot'}</strong>
                        <p>{snapshot.turn_contract?.contract_label || snapshot.mode_guidance?.effective_mode || 'operator_task'}</p>
                      </div>
                      <small>{formatStamp(snapshot.captured_at)}</small>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            <div className="workbench-checklist" data-testid="state-hygiene-actions">
              <h4>Hygiene actions</h4>
              <div className="workbench-action-row compact">
                <button
                  type="button"
                  className="workbench-button ghost"
                  onClick={snapshotSessionState}
                  disabled={!activeSessionId || busyKey === 'state-snapshot'}
                  data-testid="state-snapshot-button"
                >
                  Snapshot state
                </button>
                <button
                  type="button"
                  className="workbench-button ghost"
                  onClick={flushFallbackResidue}
                  disabled={!activeSessionId || busyKey === 'state-flush-fallback'}
                  data-testid="state-flush-fallback-button"
                >
                  Flush fallback residue
                </button>
                <button
                  type="button"
                  className="workbench-button ghost"
                  onClick={() => freezeSessionMode(activeSessionModeGuidance?.effective_mode || activeSession?.response_mode || 'operator', 3)}
                  disabled={!activeSessionId || busyKey === 'state-freeze-mode'}
                  data-testid="state-freeze-mode-button"
                >
                  Freeze mode for 3 turns
                </button>
                <button
                  type="button"
                  className="workbench-button ghost"
                  onClick={hardResetSessionState}
                  disabled={!activeSessionId || busyKey === 'state-reset'}
                  data-testid="state-reset-button"
                >
                  Hard reset session state
                </button>
              </div>
              {activeModeFreeze ? (
                <div className="workbench-notice warning compact">
                  <strong>Mode freeze is active</strong>
                  <p>{activeModeFreeze.mode} is locked for {activeModeFreeze.remaining_turns} more turn(s).</p>
                </div>
              ) : (
                <p className="workbench-muted">No mode freeze is active on the current session.</p>
              )}
            </div>
          </div>
        </div>
      </section>

      <section id="workbench-otem" className="workbench-section page-panel" data-testid="workbench-otem">
        <div className="workbench-section-head">
          <div>
            <span>OTEM</span>
            <h2>Read-only task reasoning through v5</h2>
          </div>
          <div className={`status-pill ${activeOtemState ? toneForState(activeOtemState.status) : 'ghost'}`}>
            {activeOtemState?.status || 'idle'}
          </div>
        </div>

        <div className="workbench-split">
          <div className="workbench-checklist">
            <div className="workbench-subhead">
              <h3>Current task thread</h3>
              <p>{activeOtemState ? 'Session-scoped only' : 'No active OTEM task in the selected Jarvis session'}</p>
            </div>
            {activeOtemState ? (
              <>
                {activeOtemRejected ? (
                  <div className="workbench-notice error" data-testid="otem-rejection">
                    <strong>OTEM rejected this task before planning.</strong>
                    <p>{activeOtemState.rejection_reason || 'The OTEM deterministic gate blocked this task.'}</p>
                    {activeOtemState.allowed_alternative ? (
                      <p>
                        Allowed alternative: {activeOtemState.allowed_alternative}
                      </p>
                    ) : null}
                  </div>
                ) : null}
                <div className="workbench-inline-grid">
                  <div className="workbench-mini-panel">
                    <span>Task</span>
                    <strong>{clipText(activeOtemState.restated_task || activeOtemState.task, 96)}</strong>
                  </div>
                  <div className="workbench-mini-panel">
                    <span>Operation</span>
                    <strong>{String(activeOtemState.operation || activeOtemState.session_context?.operation || 'new_task').replace(/_/g, ' ')}</strong>
                  </div>
                  <div className="workbench-mini-panel">
                    <span>Focus</span>
                    <strong>
                      {activeOtemState.session_context?.focus_step
                        ? `Step ${activeOtemState.session_context.focus_step.index}`
                        : 'Whole plan'}
                    </strong>
                  </div>
                </div>
                <p className="workbench-muted">{activeOtemState.session_context?.note || 'OTEM is carrying the active task plan inside this session only.'}</p>
                <div className="workbench-history-list">
                  {activeOtemPlan.length ? activeOtemPlan.map((step) => (
                    <div key={`otem-step-${step.index}`} className="workbench-history-item" data-testid={`otem-step-${step.index}`}>
                      <div>
                        <strong>{step.index}. {step.title}</strong>
                        <p>{step.description}</p>
                      </div>
                      <small>{step.status}</small>
                    </div>
                  )) : (
                    <div className="workbench-history-item" data-testid="otem-no-plan">
                      <div>
                        <strong>No plan was generated</strong>
                        <p>This preserves the OTEM reasoning-only contract for rejected tasks.</p>
                      </div>
                      <small>{activeOtemState.status || 'idle'}</small>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <p className="workbench-muted">
                Run OTEM from Jarvis or the OTEM endpoint to open a session-scoped task thread here.
              </p>
            )}
            <div className="workbench-chip-row">
              {(otemCatalog.execution_boundaries || []).map((item) => (
                <span key={item} className="workbench-chip">{item}</span>
              ))}
            </div>
          </div>

          <div className="workbench-checklist">
            <div className="workbench-subhead">
              <h3>Execution-aware proposals</h3>
              <p>{(otemCatalog.workflow_catalog || []).length} workflow template(s) · {(otemCatalog.tool_registry || []).length} tool(s)</p>
            </div>
            {activeOtemWorkflowHandoff ? (
              <div className="workbench-notice warning" data-testid="otem-workflow-handoff">
                <strong>{activeOtemWorkflowHandoff.template_name || activeOtemWorkflowHandoff.workflow_template_id}</strong>
                <p>{activeOtemWorkflowHandoff.rationale}</p>
              </div>
            ) : (
              <p className="workbench-muted">No workflow handoff is active on the latest OTEM task.</p>
            )}
            <div className="workbench-history-list">
              {activeOtemRecommendations.length ? activeOtemRecommendations.map((recommendation) => (
                <div key={`${recommendation.kind}:${recommendation.workflow_template_id || recommendation.run_id || recommendation.label}`} className="workbench-history-item">
                  <div>
                    <strong>{recommendation.label}</strong>
                    <p>{recommendation.rationale}</p>
                  </div>
                  <small>{recommendation.kind}</small>
                </div>
              )) : (
                <div className="workbench-history-item">
                  <div>
                    <strong>No execution recommendation</strong>
                    <p>OTEM did not find a stronger workflow, approval, or resume proposal for the active task.</p>
                  </div>
                  <small>read-only</small>
                </div>
              )}
            </div>
            <div className="workbench-history-list">
              {activeOtemToolSuggestions.length ? activeOtemToolSuggestions.map((suggestion) => (
                <div key={suggestion.tool_id} className="workbench-history-item" data-testid={`otem-tool-${suggestion.tool_id}`}>
                  <div>
                    <strong>{suggestion.label}</strong>
                    <p>{suggestion.reason}</p>
                  </div>
                  <small>proposal only</small>
                </div>
              )) : (
                <div className="workbench-history-item">
                  <div>
                    <strong>No tool proposal</strong>
                    <p>OTEM stayed tool-cold on the latest task.</p>
                  </div>
                  <small>v5</small>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section id="workbench-forge" className="workbench-section page-panel" data-testid="workbench-forge">
        <div className="workbench-section-head">
          <div>
            <span>Forge</span>
            <h2>Isolated contractor and evaluator boundaries</h2>
          </div>
          <div className="status-pill connected">
            review gated
          </div>
        </div>

        <div className="workbench-split">
          <div className="workbench-checklist">
            <div className="workbench-subhead">
              <h3>Forge Contractor</h3>
              <p>Bounded code contractor lane under Jarvis authority</p>
            </div>
            <ul>
              <li>Route: {forge.contractor?.route || '/api/jarvis/forge/code'}</li>
              <li>Base URL: {forge.contractor?.base_url || 'not configured'}</li>
              <li>Boundary: {forge.contractor?.boundary || 'review gated contractor lane'}</li>
            </ul>
            <div className="workbench-chip-row">
              {(forge.contractor?.kinds || []).map((kind) => (
                <span key={kind} className="workbench-chip">{kind}</span>
              ))}
            </div>
            {forge.contractor?.latest ? (
              <div className="workbench-history-item" data-testid="forge-contractor-latest">
                <div>
                  <strong>{forge.contractor.latest.task || 'Latest contractor request'}</strong>
                  <p>{forge.contractor.latest.kind} · {forge.contractor.latest.result?.summary || 'No result summary yet.'}</p>
                </div>
                <small>{forge.contractor.latest.updated_at ? formatStamp(forge.contractor.latest.updated_at) : 'session'}</small>
              </div>
            ) : (
              <p className="workbench-muted">No Forge contractor request is attached to the active session yet.</p>
            )}
          </div>

          <div className="workbench-checklist">
            <div className="workbench-subhead">
              <h3>ForgeEval</h3>
              <p>Read-only evaluator lane for bounded scoring and checks</p>
            </div>
            <ul>
              <li>Route: {forge.evaluator?.route || '/api/jarvis/forge/evaluate'}</li>
              <li>Base URL: {forge.evaluator?.base_url || 'not configured'}</li>
              <li>Boundary: {forge.evaluator?.boundary || 'isolated evaluator lane'}</li>
            </ul>
            <div className="workbench-chip-row">
              {(forge.evaluator?.modes || []).map((mode) => (
                <span key={mode} className="workbench-chip">{mode}</span>
              ))}
            </div>
            {forge.evaluator?.latest ? (
              <div className="workbench-history-item" data-testid="forge-evaluator-latest">
                <div>
                  <strong>{forge.evaluator.latest.mode || 'Latest evaluation'}</strong>
                  <p>{forge.evaluator.latest.result?.summary || 'No evaluator summary yet.'}</p>
                </div>
                <small>{forge.evaluator.latest.updated_at ? formatStamp(forge.evaluator.latest.updated_at) : 'session'}</small>
              </div>
            ) : (
              <p className="workbench-muted">No ForgeEval result is attached to the active session yet.</p>
            )}
          </div>
        </div>
      </section>

      <div className="workbench-grid">
        <div className="workbench-column workbench-column-primary">
          <section id="workbench-execution" className="workbench-section page-panel" data-testid="workbench-execution">
            <div className="workbench-section-head">
              <div>
                <span>Execution Cockpit</span>
                <h2>Proposal to review, apply, and verify</h2>
              </div>
              <div className={`status-pill ${toneForState(selectedReviewApplyGate.ready ? 'ready' : selectedReview?.current_decision?.state)}`}>
                <FiGitPullRequest />
                {selectedReviewApplyGate.ready ? 'apply gate open' : (selectedReview?.current_decision?.state || 'proposal')}
              </div>
            </div>

            <div className="workbench-flow">
              {executionSteps.map((step) => (
                <div key={step.label} className={`workbench-flow-step ${toneForState(step.value)}`}>
                  <span>{step.label}</span>
                  <strong>{String(step.value || 'idle').replace(/_/g, ' ')}</strong>
                </div>
              ))}
            </div>

            <div className="workbench-split">
              <div className="workbench-list-shell">
                <div className="workbench-subhead">
                  <h3>Patch Reviews</h3>
                  <p>{reviews.length} review record(s)</p>
                </div>
                <div className="workbench-list">
                  {reviews.length === 0 ? (
                    <div className="workbench-empty">
                      <p>No patch reviews yet. Create one from Jarvis or the API, then govern it here.</p>
                    </div>
                  ) : reviews.map((review) => (
                    <button
                      key={review.id}
                      type="button"
                      className={`workbench-list-item ${selectedReviewId === review.id ? 'selected' : ''}`}
                      onClick={() => setSelectedReviewId(review.id)}
                      data-testid={`review-item-${review.id}`}
                    >
                      <div className="workbench-list-title">
                        <strong>{clipText(review.goal || review.id, 88)}</strong>
                        <span className={`status-pill ${toneForState(review.current_decision?.state)}`}>
                          {review.current_decision?.state || review.status}
                        </span>
                      </div>
                      <p>{(review.target_files || []).length} target file(s) · {review.hunk_count || 0} hunk(s)</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="workbench-detail-shell">
                {!selectedReview ? (
                  <div className="workbench-empty">
                    <p>Choose a patch review to open the execution cockpit.</p>
                  </div>
                ) : (
                  <>
                    <div className="workbench-subhead">
                      <h3>{selectedReview.goal || selectedReview.id}</h3>
                      <p>{selectedReview.patch_plan?.summary || 'Review-first patch proposal'}</p>
                    </div>

                    <div className="workbench-inline-grid">
                      <div className="workbench-mini-panel">
                        <span>Target files</span>
                        <strong>{(selectedReview.patch_plan?.target_files || []).length}</strong>
                      </div>
                      <div className="workbench-mini-panel">
                        <span>Review state</span>
                        <strong>{selectedReview.current_decision?.state || selectedReview.status}</strong>
                      </div>
                      <div className="workbench-mini-panel">
                        <span>Apply gate</span>
                        <strong>{selectedReviewApplyGate.ready ? 'Ready' : 'Blocked'}</strong>
                      </div>
                    </div>

                    <div className="workbench-chip-row">
                      {(selectedReview.patch_plan?.target_files || []).map((path) => (
                        <span key={path} className="workbench-chip">{path}</span>
                      ))}
                    </div>

                    {executionStatusNotice ? (
                      <div className={`workbench-notice ${executionStatusNotice.tone}`} data-testid="execution-status-notice">
                        <strong>{executionStatusNotice.title}</strong>
                        <p>{executionStatusNotice.body}</p>
                      </div>
                    ) : null}

                    <div className="workbench-action-row">
                      <button type="button" className="workbench-button ghost" onClick={previewReview} disabled={busyKey === 'review-preview'} data-testid="review-preview-button">
                        <FiSearch />
                        Preview
                      </button>
                      <button type="button" className="workbench-button ghost" onClick={() => decideReview('accepted')} disabled={busyKey === 'review:accepted'} data-testid="review-accept-button">
                        <FiCheckCircle />
                        Accept
                      </button>
                      <button type="button" className="workbench-button ghost" onClick={() => decideReview('needs_revision')} disabled={busyKey === 'review:needs_revision'} data-testid="review-needs-revision-button">
                        <FiTarget />
                        Needs revision
                      </button>
                      <button type="button" className="workbench-button ghost" onClick={() => decideReview('rejected')} disabled={busyKey === 'review:rejected'} data-testid="review-reject-button">
                        <FiArchive />
                        Reject
                      </button>
                      <button
                        type="button"
                        className="workbench-button primary"
                        onClick={applyReview}
                        disabled={!selectedReviewApplyGate.ready || busyKey === 'review-apply'}
                        data-testid="review-apply-button"
                      >
                        <FiPlay />
                        Apply
                      </button>
                    </div>

                    {patchPreview ? (
                      <div className="workbench-preview" data-testid="review-preview-result">
                        <div className="workbench-subhead compact">
                          <h4>Workspace Preview</h4>
                          <p>{patchPreview.summary}</p>
                        </div>
                        <div className="workbench-chip-row">
                          {patchPreview.files?.map((file) => (
                            <span key={file.path} className={`workbench-chip ${file.status}`}>
                              {file.path} · {file.status}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    <div className="workbench-checklist">
                      <h4>Verify after apply</h4>
                      {(selectedReview.patch_plan?.verification_checklist || []).length === 0 ? (
                        <p className="workbench-muted">No focused verification checklist is attached to this review yet.</p>
                      ) : (
                        <ul>
                          {(selectedReview.patch_plan?.verification_checklist || []).map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    <div className="workbench-checklist">
                      <h4>Apply history</h4>
                      {selectedReviewApplyHistory.length === 0 ? (
                        <p className="workbench-muted">No guarded apply run has been recorded for this review yet.</p>
                      ) : (
                        <div className="workbench-history-list">
                          {selectedReviewApplyHistory.map((run) => (
                            <button
                              key={run.id}
                              type="button"
                              className="workbench-history-item action"
                              onClick={() => setSelectedRunId(run.id)}
                              data-testid={`review-apply-run-${run.id}`}
                            >
                              <div>
                                <strong>{run.title || run.id}</strong>
                                <p>{run.summary || 'Completed apply history entry.'}</p>
                              </div>
                              <small>{formatStamp(run.updated_at)}</small>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="workbench-run-shell">
              <div className="workbench-subhead">
                <h3>Run Ledger</h3>
                <p>Recent execution history and rollback notes.</p>
              </div>
              <div className="workbench-split">
                <div className="workbench-list-shell">
                  <div className="workbench-list">
                    {runs.length === 0 ? (
                      <div className="workbench-empty">
                        <p>No recorded runs yet.</p>
                      </div>
                    ) : runs.map((run) => (
                      <button
                        key={run.id}
                        type="button"
                        className={`workbench-list-item ${selectedRunId === run.id ? 'selected' : ''}`}
                        onClick={() => setSelectedRunId(run.id)}
                        data-testid={`run-item-${run.id}`}
                      >
                        <div className="workbench-list-title">
                          <strong>{clipText(run.title, 88)}</strong>
                          <span className={`status-pill ${toneForState(run.status)}`}>{run.status}</span>
                        </div>
                        <p>{run.kind} · {run.history_count || 0} step(s) · {formatStamp(run.updated_at)}</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="workbench-detail-shell">
                  {!selectedRun ? (
                    <div className="workbench-empty">
                      <p>Select a run to inspect steps, artifacts, and rollback notes.</p>
                    </div>
                  ) : (
                    <>
                      <div className="workbench-subhead compact">
                        <h4>{selectedRun.title}</h4>
                        <p>{selectedRun.summary || 'Run history detail'}</p>
                      </div>

                      <div className="workbench-step-list" data-testid="run-step-list">
                        {(selectedRun.steps || []).map((step) => (
                          <div key={step.id} className="workbench-step">
                            <div>
                              <strong>{step.title}</strong>
                              <p>{step.summary}</p>
                            </div>
                            <span className={`status-pill ${toneForState(step.status)}`}>{step.status}</span>
                          </div>
                        ))}
                      </div>

                      {selectedRunArtifacts.preview ? (
                        <div className="workbench-checklist" data-testid="run-verification-lane">
                          <h4>Apply Preview</h4>
                          <p className="workbench-muted">{selectedRunArtifacts.preview.summary}</p>
                        </div>
                      ) : null}

                      {selectedRunArtifacts.verificationPlan ? (
                        <div className="workbench-checklist" data-testid="run-rollback-notes">
                          <h4>Verification Lane</h4>
                          <p className="workbench-muted">{selectedRunArtifacts.verificationPlan.summary}</p>
                          {(selectedRunArtifacts.verificationPlan.verification_checklist || []).length ? (
                            <ul>
                              {(selectedRunArtifacts.verificationPlan.verification_checklist || []).map((item) => (
                                <li key={item}>{item}</li>
                              ))}
                            </ul>
                          ) : null}
                          {(selectedRunArtifacts.verificationPlan.recommended_tests || []).length ? (
                            <ul>
                              {(selectedRunArtifacts.verificationPlan.recommended_tests || []).map((item) => (
                                <li key={item}>{item}</li>
                              ))}
                            </ul>
                          ) : null}
                        </div>
                      ) : null}

                      {selectedRunArtifacts.patchApply?.rollback_notes?.length ? (
                        <div className="workbench-checklist">
                          <h4>Rollback Notes</h4>
                          <ul>
                            {selectedRunArtifacts.patchApply.rollback_notes.map((note) => (
                              <li key={note}>{note}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </>
                  )}
                </div>
              </div>
            </div>
          </section>

          <section id="workbench-missions" className="workbench-section page-panel" data-testid="workbench-missions">
            <div className="workbench-section-head">
              <div>
                <span>Mission Board</span>
                <h2>Keep the current objective visible</h2>
              </div>
              <div className="status-pill connected">
                <FiFlag />
                {missionBoard.missions?.length || 0} mission(s)
              </div>
            </div>

            <div className="workbench-missions">
              <div className="workbench-list">
                {(missionBoard.missions || []).length === 0 ? (
                  <div className="workbench-empty">
                    <p>No missions are on deck right now.</p>
                  </div>
                ) : (missionBoard.missions || []).map((mission) => (
                  <div key={mission.id} className="workbench-list-item static" data-testid={`mission-item-${mission.id}`}>
                    <div className="workbench-list-title">
                      <strong>{mission.title}</strong>
                      <span className={`status-pill ${toneForState(mission.status)}`}>{mission.status}</span>
                    </div>
                    <p>{clipText(mission.objective, 160)}</p>
                    <small>Next: {mission.next_step || 'Not set'}</small>
                    {mission.status === 'blocked' && mission.blocker ? (
                      <div className="workbench-notice error compact">
                        <p>{mission.blocker}</p>
                      </div>
                    ) : null}
                    <div className="workbench-action-row compact">
                      <button type="button" className="workbench-button ghost" onClick={() => focusMission(mission.id)} disabled={busyKey === `mission-focus:${mission.id}`} data-testid={`mission-focus-${mission.id}`}>
                        Focus
                      </button>
                      <button type="button" className="workbench-button ghost" onClick={() => updateMissionStatus(mission.id, 'active')} disabled={busyKey === `mission:${mission.id}:active`} data-testid={`mission-active-${mission.id}`}>
                        Active
                      </button>
                      <button type="button" className="workbench-button ghost" onClick={() => updateMissionStatus(mission.id, 'blocked')} disabled={busyKey === `mission:${mission.id}:blocked`} data-testid={`mission-blocked-${mission.id}`}>
                        Blocked
                      </button>
                      <button type="button" className="workbench-button ghost" onClick={() => updateMissionStatus(mission.id, 'completed')} disabled={busyKey === `mission:${mission.id}:completed`} data-testid={`mission-completed-${mission.id}`}>
                        Done
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <form className="workbench-form" onSubmit={createMission}>
                <div className="workbench-subhead compact">
                  <h4>Queue a mission</h4>
                  <p>Add the next concrete objective without leaving the desk.</p>
                </div>
                <label>
                  <span>Title</span>
                  <input
                    type="text"
                    value={missionDraft.title}
                    onChange={(event) => setMissionDraft((current) => ({ ...current, title: event.target.value }))}
                    placeholder="Stabilize the workbench runtime lane"
                  />
                </label>
                <label>
                  <span>Objective</span>
                  <textarea
                    value={missionDraft.objective}
                    onChange={(event) => setMissionDraft((current) => ({ ...current, objective: event.target.value }))}
                    placeholder="Describe the concrete outcome you need."
                  />
                </label>
                <label>
                  <span>Next step</span>
                  <input
                    type="text"
                    value={missionDraft.next_step}
                    onChange={(event) => setMissionDraft((current) => ({ ...current, next_step: event.target.value }))}
                    placeholder="Run a live browser smoke check"
                  />
                </label>
                <button type="submit" className="workbench-button primary" disabled={busyKey === 'mission-create'}>
                  <FiPlus />
                  Add mission
                </button>
              </form>
            </div>
          </section>
        </div>

        <div className="workbench-column workbench-column-secondary">
          <section id="workbench-memory" className="workbench-section page-panel" data-testid="workbench-memory">
            <div className="workbench-section-head">
              <div>
                <span>Memory Governance</span>
                <h2>Edit, merge, archive, and explain long-term memory</h2>
              </div>
              <Link to="/memory" className="workbench-inline-link">
                Open full bank <FiArrowRight />
              </Link>
            </div>

            <div className="workbench-inline-grid">
              <div className="workbench-mini-panel">
                <span>Active</span>
                <strong>{memoryBank.summary?.active || 0}</strong>
              </div>
              <div className="workbench-mini-panel">
                <span>Archived</span>
                <strong>{memoryBank.summary?.archived || 0}</strong>
              </div>
              <div className="workbench-mini-panel">
                <span>Overrides</span>
                <strong>{memoryBank.summary?.overrides || 0}</strong>
              </div>
            </div>

            <div className="workbench-insight-grid">
              <div className="workbench-checklist">
                <h4>Merge suggestions</h4>
                {memoryGovernance.merge_suggestions?.length ? (
                  <div className="workbench-history-list">
                    {memoryGovernance.merge_suggestions.map((item) => (
                      <button
                        key={`${item.target_id}:${(item.source_ids || []).join(',')}`}
                        type="button"
                        className="workbench-history-item action"
                        onClick={() => focusMemoryRecord(item.target_id, item.source_ids || [])}
                        data-testid={`memory-merge-suggestion-${item.target_id}`}
                      >
                        <div>
                          <strong>{item.target_excerpt}</strong>
                          <p>{item.reason}</p>
                        </div>
                        <small>{(item.source_ids || []).length} source</small>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="workbench-muted">No strong duplicate candidates are surfacing right now.</p>
                )}
              </div>

              <div className="workbench-checklist">
                <h4>Why gaps</h4>
                {memoryGovernance.why_gaps?.length ? (
                  <div className="workbench-history-list">
                    {memoryGovernance.why_gaps.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        className="workbench-history-item action"
                        onClick={() => focusMemoryRecord(item.id)}
                        data-testid={`memory-why-gap-${item.id}`}
                      >
                        <div>
                          <strong>{clipText(item.content, 86)}</strong>
                          <p>{item.prompt}</p>
                        </div>
                        <small>{item.category}</small>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="workbench-muted">Every active memory currently has a recorded rationale.</p>
                )}
              </div>
            </div>

            <div className="workbench-insight-grid">
              <div className="workbench-checklist">
                <h4>Conflict watch</h4>
                {memoryGovernance.conflicts?.length ? (
                  <div className="workbench-history-list">
                    {memoryGovernance.conflicts.map((item) => (
                      <button
                        key={item.memory_ids.join(':')}
                        type="button"
                        className="workbench-history-item action"
                        onClick={() => focusMemoryRecord(item.memory_ids[0])}
                        data-testid={`memory-conflict-${item.memory_ids[0]}`}
                      >
                        <div>
                          <strong>{item.category} memory tension</strong>
                          <p>{item.reason}</p>
                        </div>
                        <small>{(item.shared_terms || []).join(', ')}</small>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="workbench-muted">No active memory conflicts are flagged right now.</p>
                )}
              </div>

              <div className="workbench-checklist">
                <h4>Archive review</h4>
                {memoryGovernance.archive_review?.length ? (
                  <div className="workbench-history-list">
                    {memoryGovernance.archive_review.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        className="workbench-history-item action"
                        onClick={() => focusMemoryRecord(item.id)}
                        data-testid={`memory-archive-review-${item.id}`}
                      >
                        <div>
                          <strong>{clipText(item.content, 86)}</strong>
                          <p>{item.archived_reason || 'Archived memory record.'}</p>
                        </div>
                        <small>{formatStamp(item.archived_at || item.updated_at)}</small>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="workbench-muted">No archived memories need review right now.</p>
                )}
              </div>
            </div>

            <div className="workbench-split memory">
              <div className="workbench-list-shell">
                <div className="workbench-list">
                  {(memoryBank.memories || []).length === 0 ? (
                    <div className="workbench-empty">
                      <p>No memory records exist yet.</p>
                    </div>
                  ) : (memoryBank.memories || []).map((memory) => (
                    <button
                      key={memory.id}
                      type="button"
                      className={`workbench-list-item ${selectedMemoryId === memory.id ? 'selected' : ''}`}
                      onClick={() => setSelectedMemoryId(memory.id)}
                      data-testid={`memory-item-${memory.id}`}
                    >
                      <div className="workbench-list-title">
                        <strong>{clipText(memory.content, 88)}</strong>
                        <span className={`status-pill ${toneForState(memory.active ? 'active' : 'archived')}`}>
                          {memory.active ? memory.category : 'archived'}
                        </span>
                      </div>
                      <p>{memory.why ? clipText(memory.why, 120) : 'No rationale recorded yet.'}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="workbench-detail-shell">
                {!selectedMemory ? (
                  <div className="workbench-empty">
                    <p>Choose a memory to edit its content, rationale, and rewrite history.</p>
                  </div>
                ) : (
                  <>
                    <form className="workbench-form compact" onSubmit={saveMemory} data-testid="memory-editor-form">
                      <div className="workbench-subhead compact">
                        <h4>{selectedMemory.category} memory</h4>
                        <p>{selectedMemory.active ? 'Active memory' : 'Archived memory'} · updated {formatStamp(selectedMemory.updated_at)}</p>
                      </div>
                      <label>
                        <span>Memory text</span>
                        <textarea
                          value={memoryEditor.content}
                          onChange={(event) => setMemoryEditor((current) => ({ ...current, content: event.target.value }))}
                          data-testid="memory-editor-content"
                        />
                      </label>
                      <div className="workbench-inline-grid">
                        <label>
                          <span>Category</span>
                          <input
                            type="text"
                            value={memoryEditor.category}
                            onChange={(event) => setMemoryEditor((current) => ({ ...current, category: event.target.value }))}
                            data-testid="memory-editor-category"
                          />
                        </label>
                        <label>
                          <span>Priority</span>
                          <input
                            type="number"
                            value={memoryEditor.priority}
                            onChange={(event) => setMemoryEditor((current) => ({ ...current, priority: event.target.value }))}
                            data-testid="memory-editor-priority"
                          />
                        </label>
                      </div>
                      <label>
                        <span>Why this memory exists</span>
                        <textarea
                          value={memoryEditor.why}
                          onChange={(event) => setMemoryEditor((current) => ({ ...current, why: event.target.value }))}
                          data-testid="memory-editor-why"
                        />
                      </label>
                      <div className="workbench-action-row compact">
                        <button type="submit" className="workbench-button primary" disabled={busyKey === 'memory-save'} data-testid="memory-save-button">
                          Save rewrite
                        </button>
                        <button type="button" className="workbench-button ghost" onClick={archiveMemory} disabled={busyKey === 'memory-archive'} data-testid="memory-archive-button">
                          Archive
                        </button>
                      </div>
                    </form>

                    {memoryStatusNotice ? (
                      <div className={`workbench-notice ${memoryStatusNotice.tone}`} data-testid="memory-status-notice">
                        <strong>{memoryStatusNotice.title}</strong>
                        <p>{memoryStatusNotice.body}</p>
                      </div>
                    ) : null}

                    <div className="workbench-checklist">
                      <h4>Merge other memories into this note</h4>
                      {availableMergeSources.length === 0 ? (
                        <p className="workbench-muted">No other memories are available to merge.</p>
                      ) : (
                        <div className="workbench-checkboxes">
                          {availableMergeSources.map((memory) => (
                            <label key={memory.id} className="workbench-checkbox">
                              <input
                                type="checkbox"
                                checked={mergeSourceIds.includes(memory.id)}
                                onChange={(event) => {
                                  setMergeSourceIds((current) => (
                                    event.target.checked
                                      ? [...current, memory.id]
                                      : current.filter((item) => item !== memory.id)
                                  ));
                                }}
                                data-testid={`memory-merge-source-${memory.id}`}
                              />
                              <span>{clipText(memory.content, 86)}</span>
                            </label>
                          ))}
                        </div>
                      )}
                      <button type="button" className="workbench-button ghost" onClick={mergeMemory} disabled={busyKey === 'memory-merge'} data-testid="memory-merge-button">
                        Merge into this memory
                      </button>
                    </div>

                    <div className="workbench-history" data-testid="memory-history">
                      <h4>Rewrite history</h4>
                      <div className="workbench-history-list">
                        {(selectedMemory.history || []).slice().reverse().map((entry) => (
                          <div key={entry.id} className="workbench-history-item">
                            <div>
                              <strong>{entry.type.replace(/_/g, ' ')}</strong>
                              <p>{entry.note || entry.why || 'No note recorded.'}</p>
                            </div>
                            <small>{formatStamp(entry.at)}</small>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>

            <form className="workbench-form compact workbench-form-divider" onSubmit={createMemory} data-testid="memory-create-form">
              <div className="workbench-subhead compact">
                <h4>Capture a new memory</h4>
                <p>Write the durable truth, then explain why it belongs in long-term memory.</p>
              </div>
              <label>
                <span>Memory text</span>
                <textarea
                  value={memoryDraft.content}
                  onChange={(event) => setMemoryDraft((current) => ({ ...current, content: event.target.value }))}
                  data-testid="memory-create-content"
                />
              </label>
              <div className="workbench-inline-grid">
                <label>
                  <span>Category</span>
                  <input
                    type="text"
                    value={memoryDraft.category}
                    onChange={(event) => setMemoryDraft((current) => ({ ...current, category: event.target.value }))}
                    data-testid="memory-create-category"
                  />
                </label>
                <label>
                  <span>Priority</span>
                  <input
                    type="number"
                    value={memoryDraft.priority}
                    onChange={(event) => setMemoryDraft((current) => ({ ...current, priority: event.target.value }))}
                    data-testid="memory-create-priority"
                  />
                </label>
              </div>
              <label>
                <span>Why this memory exists</span>
                <textarea
                  value={memoryDraft.why}
                  onChange={(event) => setMemoryDraft((current) => ({ ...current, why: event.target.value }))}
                  data-testid="memory-create-why"
                />
              </label>
              <button type="submit" className="workbench-button primary" disabled={busyKey === 'memory-create'} data-testid="memory-create-button">
                <FiBookOpen />
                Save memory
              </button>
            </form>
          </section>

          <section id="workbench-workspace" className="workbench-section page-panel" data-testid="workbench-workspace">
            <div className="workbench-section-head">
              <div>
                <span>Workspace Lane</span>
                <h2>Finish the bounded evolving_ai inspection path</h2>
              </div>
              <div className="status-pill connected">
                <FiCompass />
                {workspaceLane.profile?.scope_prefix || 'workspace'}
              </div>
            </div>

            <div className="workbench-checklist">
              <h4>Profile</h4>
              <ul>
                <li>Languages: {(workspaceLane.profile?.languages || []).join(', ') || 'Unknown'}</li>
                <li>Frameworks: {(workspaceLane.profile?.frameworks || []).join(', ') || 'Unknown'}</li>
                <li>Tests: {(workspaceLane.profile?.test_commands || []).join(', ') || 'Unknown'}</li>
              </ul>
            </div>

            <form className="workbench-form compact" onSubmit={searchSymbols}>
              <label>
                <span>Search symbols</span>
                <input
                  type="text"
                  value={symbolQuery}
                  onChange={(event) => setSymbolQuery(event.target.value)}
                  placeholder="pending_action, action_lifecycle, build_patch_plan"
                />
              </label>
              <button type="submit" className="workbench-button ghost" disabled={busyKey === 'workspace-symbols'}>
                <FiSearch />
                Search symbols
              </button>
            </form>

            {symbols.length > 0 ? (
              <div className="workbench-list">
                {symbols.map((symbol) => (
                  <button
                    key={`${symbol.path}:${symbol.qualname}`}
                    type="button"
                    className={`workbench-list-item ${symbolDetail?.qualname === symbol.qualname && symbolDetail?.path === symbol.path ? 'selected' : ''}`}
                    onClick={() => openSymbol(symbol)}
                  >
                    <div className="workbench-list-title">
                      <strong>{symbol.qualname}</strong>
                      <span className="status-pill warning">{symbol.kind}</span>
                    </div>
                    <p>{symbol.path}</p>
                  </button>
                ))}
              </div>
            ) : null}

            {symbolDetail ? (
              <div className="workbench-code">
                <div className="workbench-subhead compact">
                  <h4>{symbolDetail.qualname}</h4>
                  <p>{symbolDetail.path}</p>
                </div>
                <pre>{symbolDetail.content}</pre>
              </div>
            ) : null}

            <form className="workbench-form compact workbench-form-divider" onSubmit={mapWorkspace}>
              <label>
                <span>Repo map goal</span>
                <input
                  type="text"
                  value={repoGoal}
                  onChange={(event) => setRepoGoal(event.target.value)}
                />
              </label>
              <button type="submit" className="workbench-button ghost" disabled={busyKey === 'workspace-repo-map'}>
                <FiLayers />
                Map workspace lane
              </button>
            </form>

            {repoMap ? (
              <div className="workbench-checklist">
                <h4>Repo map</h4>
                <p className="workbench-muted">{repoMap.summary}</p>
                <ul>
                  {(repoMap.related_paths || []).map((path) => (
                    <li key={path}>{path}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>

          <section id="workbench-governance" className="workbench-section page-panel" data-testid="workbench-governance">
            <div className="workbench-section-head">
              <div>
                <span>Governance</span>
                <h2>Break-glass and live policy posture</h2>
              </div>
              <button type="button" className="workbench-button ghost" onClick={toggleBreakGlass} disabled={busyKey === 'break-glass'} data-testid="governance-break-glass-button">
                <FiShield />
                {governance.active_break_glass?.active ? 'Clear break-glass' : 'Raise break-glass'}
              </button>
            </div>

            <div className={`workbench-notice ${governance.active_break_glass?.active ? 'warning' : 'connected'}`} data-testid="governance-break-glass-notice">
              <strong>{governance.active_break_glass?.active ? 'Break-glass is active' : 'Governance is nominal'}</strong>
              <p>
                {governance.active_break_glass?.active
                  ? `${governance.active_break_glass.scope || 'scope'} until ${formatStamp(governance.active_break_glass.expires_at)}`
                  : 'No emergency override is currently open.'}
              </p>
            </div>

            <div className="workbench-checklist" data-testid="governance-policy-requests">
              <h4>Open policy requests</h4>
              {(governance.open_policy_requests || []).length === 0 ? (
                <p className="workbench-muted">No staged or blocked policy requests right now.</p>
              ) : (
                <ul>
                  {(governance.open_policy_requests || []).map((request) => (
                    <li key={request.id}>
                      {request.title} · {request.status}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="workbench-checklist" data-testid="governance-events">
              <h4>Recent governance events</h4>
              {(governance.recent_events || []).length === 0 ? (
                <p className="workbench-muted">No recent governance events.</p>
              ) : (
                <ul>
                  {(governance.recent_events || []).slice().reverse().map((event) => (
                    <li key={event.id || `${event.event_type}-${event.created_at}`}>
                      {event.event_type} · {formatStamp(event.created_at)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          <section className="workbench-section page-panel">
            <div className="workbench-section-head">
              <div>
                <span>Creative Runtimes</span>
                <h2>Installed V9 and V10 runtime glance</h2>
              </div>
              <div className="status-pill connected">
                <FiZap />
                bounded runtimes
              </div>
            </div>

            <div className="workbench-inline-grid">
              <div className="workbench-mini-panel">
                <span>V9</span>
                <strong>{snapshot?.v9_runtime?.core || 'v9'}</strong>
                <small>{snapshot?.v9_runtime?.event_count || 0} event(s)</small>
              </div>
              <div className="workbench-mini-panel">
                <span>V10</span>
                <strong>{snapshot?.v10_runtime?.core || 'v10'}</strong>
                <small>{snapshot?.v10_runtime?.event_count || 0} event(s)</small>
              </div>
            </div>
          </section>
        </div>
      </div>
    </section>
  );
}

export default Dashboard;
