import React, { useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import {
  FiArrowRight,
  FiCheckCircle,
  FiClock,
  FiCompass,
  FiEye,
  FiFileText,
  FiRefreshCw,
  FiShield,
  FiTarget,
} from 'react-icons/fi';
import { Link, useNavigate } from 'react-router-dom';
import { apiPost, getApiErrorMessage } from '../lib/api';
import { getActiveJarvisSessionId, setPendingJarvisDraft } from '../lib/jarvis';
import './RepoManager.css';

const HISTORY_LIMIT = 8;

function createDraft(overrides = {}) {
  return {
    objective: '',
    targetScope: '',
    allowedFilesText: '',
    excludedFilesText: '',
    changeIntent: 'review_only',
    maxChangeBudget: 'one narrow seam',
    validationTarget: 'route contract parity',
    operationMode: 'inspect_only',
    maxFilesToInspect: '6',
    maxDirectoryDepth: '3',
    filePathAllowlistText: '',
    explicitDenylistText: '',
    noExecutionWithoutHandoff: true,
    ...overrides,
  };
}

function splitScopeList(value) {
  if (Array.isArray(value)) {
    const seen = new Set();
    return value
      .map((item) => String(item || '').trim())
      .filter((item) => {
        if (!item || seen.has(item)) {
          return false;
        }
        seen.add(item);
        return true;
      })
      .slice(0, 12);
  }
  const seen = new Set();
  return String(value || '')
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter((item) => {
      if (!item || seen.has(item)) {
        return false;
      }
      seen.add(item);
      return true;
    })
    .slice(0, 12);
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

function clipText(value, limit = 180) {
  const cleaned = String(value || '').replace(/\s+/g, ' ').trim();
  if (cleaned.length <= limit) {
    return cleaned;
  }
  return `${cleaned.slice(0, limit - 3).trimEnd()}...`;
}

function describeFocusReason(file, entry) {
  const requestedAllowed = splitScopeList(entry?.request?.focus_files || []);
  const allowlist = splitScopeList(entry?.request?.file_path_allowlist || []);
  if (requestedAllowed.includes(file)) {
    return 'Explicitly allowed by operator scope.';
  }
  if (allowlist.some((rule) => String(file || '').startsWith(String(rule || '').replace('*', '')))) {
    return 'Included because it matched the hard allowlist.';
  }
  return 'Included as bounded workspace evidence for this slice.';
}

function extractRepoManagerPayload(responsePayload) {
  return (
    responsePayload?.result?.result?.repo_manager
    || responsePayload?.result?.repo_manager
    || null
  );
}

function toneForConfidence(value) {
  const normalized = String(value || '').trim().toLowerCase();
  if (normalized === 'high') {
    return 'connected';
  }
  if (normalized === 'medium') {
    return 'warning';
  }
  return 'ghost';
}

function RepoManager() {
  const navigate = useNavigate();
  const [draft, setDraft] = useState(() => createDraft({
    objective: 'Inspect the current backend/operator seam and propose the smallest safe next change.',
    targetScope: 'backend operator seam',
    filePathAllowlistText: 'src/*',
  }));
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([]);
  const [selectedEntryId, setSelectedEntryId] = useState('');

  const activeSessionId = getActiveJarvisSessionId();

  const selectedEntry = useMemo(
    () => history.find((entry) => entry.id === selectedEntryId) || history[0] || null,
    [history, selectedEntryId],
  );

  const selectedPayload = useMemo(
    () => extractRepoManagerPayload(selectedEntry?.response),
    [selectedEntry],
  );

  const handleDraftChange = (key) => (event) => {
    const nextValue = event?.target?.value ?? '';
    setDraft((current) => ({
      ...current,
      [key]: nextValue,
    }));
  };

  const applyEntryToDraft = (entry) => {
    if (!entry) {
      return;
    }
    const request = entry.request || {};
    setDraft(createDraft({
      objective: request.task || '',
      targetScope: request.target_scope || '',
      allowedFilesText: (request.focus_files || []).join('\n'),
      excludedFilesText: (request.excluded_files || []).join('\n'),
      changeIntent: request.change_intent || 'review_only',
      maxChangeBudget: request.max_change_budget || 'one narrow seam',
      validationTarget: request.validation_target || '',
      operationMode: request.operation_mode || 'inspect_only',
      maxFilesToInspect: request.max_files_to_inspect ? String(request.max_files_to_inspect) : '6',
      maxDirectoryDepth: request.max_directory_depth ? String(request.max_directory_depth) : '3',
      filePathAllowlistText: (request.file_path_allowlist || []).join('\n'),
      explicitDenylistText: (request.explicit_denylist || []).join('\n'),
      noExecutionWithoutHandoff: request.no_execution_without_handoff !== false,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const task = draft.objective.trim();
    if (!task || busy) {
      return;
    }

    const payload = {
      task,
      session_id: activeSessionId || undefined,
      target_scope: draft.targetScope.trim() || undefined,
      focus_files: splitScopeList(draft.allowedFilesText),
      excluded_files: splitScopeList(draft.excludedFilesText),
      change_intent: draft.changeIntent,
      max_change_budget: draft.maxChangeBudget.trim() || undefined,
      validation_target: draft.validationTarget.trim() || undefined,
      operation_mode: draft.operationMode,
      max_files_to_inspect: draft.maxFilesToInspect ? Number(draft.maxFilesToInspect) : undefined,
      max_directory_depth: draft.maxDirectoryDepth ? Number(draft.maxDirectoryDepth) : undefined,
      file_path_allowlist: splitScopeList(draft.filePathAllowlistText),
      explicit_denylist: splitScopeList(draft.explicitDenylistText),
      no_execution_without_handoff: Boolean(draft.noExecutionWithoutHandoff),
    };

    setBusy(true);
    try {
      const response = await apiPost('/api/jarvis/forge/repo-manager', payload);
      const entry = {
        id: response.data.task_id || `repo-manager-${Date.now()}`,
        createdAt: new Date().toISOString(),
        request: payload,
        response: response.data,
      };
      setHistory((current) => {
        const next = [entry, ...current.filter((item) => item.id !== entry.id)];
        return next.slice(0, HISTORY_LIMIT);
      });
      setSelectedEntryId(entry.id);
      toast.success('Repo manager is ready with a bounded read-first pass.');
    } catch (error) {
      toast.error(`Repo manager could not inspect that slice: ${getApiErrorMessage(error)}`);
    } finally {
      setBusy(false);
    }
  };

  const rerunSelected = async () => {
    if (!selectedEntry || busy) {
      return;
    }
    applyEntryToDraft(selectedEntry);
    const syntheticEvent = { preventDefault() {} };
    await handleSubmit(syntheticEvent);
  };

  const buildBoundedPlanText = (entry, payload) => {
    if (!entry || !payload) {
      return '';
    }
    const lines = [
      `Repo summary: ${payload.repo_summary}`,
      `Target scope: ${payload.target_scope}`,
      `Focus files: ${(payload.focus_files || []).join(', ') || 'None'}`,
      'Risks:',
      ...(payload.risks || []).map((risk) => `- ${risk.file}: ${risk.issue} | Evidence: ${risk.evidence}`),
      'Smallest safe plan:',
      ...(payload.plan || []).map((step, index) => (
        `${index + 1}. ${step.step}${step.file ? ` [${step.file}]` : ''} | Purpose: ${step.purpose} | Validation: ${step.validation}`
      )),
      `Execution ready: ${payload.execution_ready ? 'yes' : 'no'}`,
    ];
    return lines.join('\n');
  };

  const handleCopyBoundedPlan = async () => {
    if (!selectedEntry || !selectedPayload) {
      return;
    }
    const text = buildBoundedPlanText(selectedEntry, selectedPayload);
    try {
      await navigator.clipboard.writeText(text);
      toast.success('Bounded plan copied');
    } catch (error) {
      toast.error('Could not copy the bounded plan');
    }
  };

  const handleSendSummaryToJarvis = () => {
    if (!selectedEntry || !selectedPayload) {
      return;
    }
    setPendingJarvisDraft({
      text: `Use this repo-manager summary in operator mode.\n\n${buildBoundedPlanText(selectedEntry, selectedPayload)}`,
      source: 'repo_manager_summary',
    });
    navigate('/jarvis');
  };

  const handleDraftForgeHandoff = () => {
    if (!selectedEntry || !selectedPayload) {
      return;
    }
    setPendingJarvisDraft({
      text: `Review this bounded repo-manager plan for a Forge handoff. Do not execute automatically.\n\n${buildBoundedPlanText(selectedEntry, selectedPayload)}`,
      source: 'repo_manager_handoff',
    });
    navigate('/jarvis');
  };

  const structuredExport = useMemo(() => {
    if (!selectedEntry || !selectedPayload) {
      return '';
    }
    return [
      'repo_manager_handoff:',
      `  objective: ${selectedEntry.request?.task || ''}`,
      `  target_scope: ${selectedPayload.target_scope || ''}`,
      `  operation_mode: ${selectedEntry.request?.operation_mode || 'inspect_only'}`,
      `  change_intent: ${selectedEntry.request?.change_intent || 'review_only'}`,
      `  max_change_budget: ${selectedEntry.request?.max_change_budget || ''}`,
      `  validation_target: ${selectedEntry.request?.validation_target || ''}`,
      `  no_execution_without_handoff: ${selectedEntry.request?.no_execution_without_handoff !== false}`,
      '  focus_files:',
      ...(selectedPayload.focus_files || []).map((file) => `    - ${file}`),
      '  risks:',
      ...(selectedPayload.risks || []).map((risk) => `    - file: ${risk.file} | issue: ${risk.issue} | evidence: ${risk.evidence} | confidence: ${risk.confidence}`),
      '  plan:',
      ...(selectedPayload.plan || []).map((step, index) => (
        `    - ${index + 1}. ${step.step}${step.file ? ` | file: ${step.file}` : ''} | purpose: ${step.purpose} | expected_effect: ${step.expected_effect} | validation: ${step.validation}${step.rollback_note ? ` | rollback: ${step.rollback_note}` : ''}`
      )),
      '  validations:',
      ...(selectedPayload.validations || []).map((item) => `    - ${item}`),
    ].join('\n');
  }, [selectedEntry, selectedPayload]);

  return (
    <section className="repo-manager-page">
      <div className="repo-manager-hero repo-manager-card">
        <div>
          <span className="repo-manager-kicker">Forge Companion</span>
          <h1>Repo Manager</h1>
          <p>
            A bounded repo-first contractor surface for Forge. It inspects, narrows, warns, and
            hands off the smallest safe plan without editing by default.
          </p>
          <p className="repo-manager-boundary-copy">
            Repo Manager inspects and proposes. Forge executes only after explicit handoff.
          </p>
        </div>
        <div className="repo-manager-hero-meta">
          <div className="repo-manager-chip repo-manager-chip--connected">
            <FiShield />
            <span>Inspect-only</span>
          </div>
          <div className="repo-manager-chip">
            <FiTarget />
            <span>{activeSessionId ? 'Session attached' : 'Independent run'}</span>
          </div>
          <div className="repo-manager-chip">
            <FiCompass />
            <span>No direct edits unless execution handoff is explicit</span>
          </div>
        </div>
      </div>

      <div className="repo-manager-trust-grid">
        <article className="repo-manager-card repo-manager-trust-card">
          <span>Allowed</span>
          <strong>What this lane can do</strong>
          <ul>
            <li>Inspect a bounded repo slice</li>
            <li>Narrow focus files</li>
            <li>Surface evidence-backed risks</li>
            <li>Propose the smallest safe plan</li>
            <li>Define validations and prepare handoff</li>
          </ul>
        </article>
        <article className="repo-manager-card repo-manager-trust-card">
          <span>Not Allowed</span>
          <strong>What it cannot do</strong>
          <ul>
            <li>Edit files directly</li>
            <li>Run execution steps on its own</li>
            <li>Expand scope beyond the selected slice</li>
            <li>Become a generic repo chatbot</li>
          </ul>
        </article>
        <article className="repo-manager-card repo-manager-trust-card">
          <span>Trust Basis</span>
          <strong>Why the result is inspectable</strong>
          <ul>
            <li>Explicit scope and file caps</li>
            <li>Explicit evidence for every risk</li>
            <li>Explicit validation target</li>
            <li>Explicit handoff boundary</li>
          </ul>
        </article>
      </div>

      <div className="repo-manager-layout">
        <aside className="repo-manager-sidebar">
          <form className="repo-manager-card repo-manager-form" onSubmit={handleSubmit}>
            <div className="repo-manager-section-header">
              <div>
                <span>Request</span>
                <h2>Ask Repo Manager</h2>
              </div>
              <button
                type="submit"
                className="repo-manager-primary-button"
                disabled={busy || !draft.objective.trim()}
              >
                {busy ? <FiRefreshCw className="spin" /> : <FiArrowRight />}
                <span>{busy ? 'Inspecting...' : 'Run inspection'}</span>
              </button>
            </div>

            <label className="repo-manager-field">
              <span>Objective</span>
              <textarea
                value={draft.objective}
                onChange={handleDraftChange('objective')}
                placeholder="Inspect the current repo slice and give me the smallest safe next move."
                rows={5}
                data-testid="repo-manager-objective"
              />
            </label>

            <div className="repo-manager-form-grid">
              <label className="repo-manager-field">
                <span>Repo slice / target path</span>
                <input
                  type="text"
                  value={draft.targetScope}
                  onChange={handleDraftChange('targetScope')}
                  placeholder="backend operator seam"
                  data-testid="repo-manager-target-scope"
                />
              </label>

              <label className="repo-manager-field">
                <span>Change intent</span>
                <select
                  value={draft.changeIntent}
                  onChange={handleDraftChange('changeIntent')}
                  data-testid="repo-manager-change-intent"
                >
                  <option value="review_only">Review only</option>
                  <option value="risk_audit">Risk audit</option>
                  <option value="execution_handoff">Execution handoff</option>
                  <option value="patch_ready">Patch ready</option>
                </select>
              </label>
            </div>

            <label className="repo-manager-field">
              <span>Max change budget</span>
              <input
                type="text"
                value={draft.maxChangeBudget}
                onChange={handleDraftChange('maxChangeBudget')}
                placeholder="one narrow seam"
                data-testid="repo-manager-change-budget"
              />
            </label>

            <div className="repo-manager-form-grid">
              <label className="repo-manager-field">
                <span>Validation target</span>
                <input
                  type="text"
                  value={draft.validationTarget}
                  onChange={handleDraftChange('validationTarget')}
                  placeholder="route payload parity"
                  data-testid="repo-manager-validation-target"
                />
              </label>

              <label className="repo-manager-field">
                <span>Mode</span>
                <select
                  value={draft.operationMode}
                  onChange={handleDraftChange('operationMode')}
                  data-testid="repo-manager-operation-mode"
                >
                  <option value="inspect_only">Inspect only</option>
                  <option value="read_only">Read only</option>
                </select>
              </label>
            </div>

            <div className="repo-manager-form-grid repo-manager-form-grid--stacked">
              <label className="repo-manager-field">
                <span>Allowed files</span>
                <textarea
                  value={draft.allowedFilesText}
                  onChange={handleDraftChange('allowedFilesText')}
                  placeholder={'src/api.py\nsrc/jarvis_operator.py'}
                  rows={5}
                  data-testid="repo-manager-allowed-files"
                />
              </label>

              <label className="repo-manager-field">
                <span>Excluded files</span>
                <textarea
                  value={draft.excludedFilesText}
                  onChange={handleDraftChange('excludedFilesText')}
                  placeholder={'frontend/src/App.jsx\nfrontend/src/components/Navbar.jsx'}
                  rows={5}
                  data-testid="repo-manager-excluded-files"
                />
              </label>
            </div>

            <div className="repo-manager-card repo-manager-scope-card">
              <div className="repo-manager-section-header">
                <div>
                  <span>Hard scope</span>
                  <h2>Safety seam</h2>
                </div>
              </div>

              <div className="repo-manager-form-grid">
                <label className="repo-manager-field">
                  <span>Max files to inspect</span>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={draft.maxFilesToInspect}
                    onChange={handleDraftChange('maxFilesToInspect')}
                    data-testid="repo-manager-max-files"
                  />
                </label>

                <label className="repo-manager-field">
                  <span>Max directories deep</span>
                  <input
                    type="number"
                    min="0"
                    max="12"
                    value={draft.maxDirectoryDepth}
                    onChange={handleDraftChange('maxDirectoryDepth')}
                    data-testid="repo-manager-max-depth"
                  />
                </label>
              </div>

              <div className="repo-manager-form-grid repo-manager-form-grid--stacked">
                <label className="repo-manager-field">
                  <span>File path allowlist</span>
                  <textarea
                    value={draft.filePathAllowlistText}
                    onChange={handleDraftChange('filePathAllowlistText')}
                    placeholder={'src/*\nforge/*'}
                    rows={4}
                    data-testid="repo-manager-allowlist"
                  />
                </label>

                <label className="repo-manager-field">
                  <span>Explicit denylist</span>
                  <textarea
                    value={draft.explicitDenylistText}
                    onChange={handleDraftChange('explicitDenylistText')}
                    placeholder={'frontend/*\n*.env'}
                    rows={4}
                    data-testid="repo-manager-denylist"
                  />
                </label>
              </div>

              <label className="repo-manager-toggle">
                <input
                  type="checkbox"
                  checked={draft.noExecutionWithoutHandoff}
                  onChange={(event) => setDraft((current) => ({
                    ...current,
                    noExecutionWithoutHandoff: event.target.checked,
                  }))}
                  data-testid="repo-manager-no-execution"
                />
                <span>No execution without handoff</span>
              </label>
            </div>

            <div className="repo-manager-boundary">
              <FiShield />
              <div>
                <strong>Boundary</strong>
                <span>
                  May summarize the repo slice, rank focus files, identify grounded risks, propose
                  the smallest safe change, and suggest validations. It does not edit by default.
                </span>
              </div>
            </div>

            <div className="repo-manager-card repo-manager-scope-preview">
              <div className="repo-manager-section-header">
                <div>
                  <span>Visible scope</span>
                  <h2>Current envelope</h2>
                </div>
              </div>
              <div className="repo-manager-scope-grid">
                <div className="repo-manager-context-card">
                  <span>Target path</span>
                  <strong>{draft.targetScope || 'Not set'}</strong>
                </div>
                <div className="repo-manager-context-card">
                  <span>Mode</span>
                  <strong>{draft.operationMode}</strong>
                </div>
                <div className="repo-manager-context-card">
                  <span>Allowed files</span>
                  <strong>{splitScopeList(draft.allowedFilesText).length || 0}</strong>
                  <p>{splitScopeList(draft.allowedFilesText).join(', ') || 'None specified'}</p>
                </div>
                <div className="repo-manager-context-card">
                  <span>Excluded files</span>
                  <strong>{splitScopeList(draft.excludedFilesText).length || 0}</strong>
                  <p>{splitScopeList(draft.excludedFilesText).join(', ') || 'None specified'}</p>
                </div>
                <div className="repo-manager-context-card">
                  <span>Max inspection depth</span>
                  <strong>{draft.maxDirectoryDepth || 'Not set'}</strong>
                </div>
                <div className="repo-manager-context-card">
                  <span>Max file count</span>
                  <strong>{draft.maxFilesToInspect || 'Not set'}</strong>
                </div>
              </div>
            </div>
          </form>

          <div className="repo-manager-card repo-manager-history">
            <div className="repo-manager-section-header">
              <div>
                <span>Recent passes</span>
                <h2>Request history</h2>
              </div>
            </div>

            {history.length ? (
              <div className="repo-manager-history-list">
                {history.map((entry) => {
                  const repoPayload = extractRepoManagerPayload(entry.response);
                  return (
                    <button
                      type="button"
                      key={entry.id}
                      className={`repo-manager-history-item ${selectedEntry?.id === entry.id ? 'selected' : ''}`}
                      onClick={() => setSelectedEntryId(entry.id)}
                      data-testid={`repo-manager-history-${entry.id}`}
                    >
                      <strong>{clipText(entry.request?.task, 86)}</strong>
                      <span>{repoPayload?.target_scope || entry.request?.target_scope || 'Repo slice'}</span>
                      <small>{formatStamp(entry.createdAt)}</small>
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="repo-manager-empty">
                Run one inspection and it will stay here as a bounded handoff record.
              </div>
            )}
          </div>
        </aside>

        <div className="repo-manager-results">
          <div className="repo-manager-card repo-manager-results-card">
            <div className="repo-manager-section-header">
              <div>
                <span>Result</span>
                <h2>Structured handoff</h2>
              </div>
              <div className="repo-manager-action-row">
                <button
                  type="button"
                  className="repo-manager-secondary-button"
                  onClick={() => applyEntryToDraft(selectedEntry)}
                  disabled={!selectedEntry}
                >
                  <FiFileText />
                  <span>Load into composer</span>
                </button>
                <button
                  type="button"
                  className="repo-manager-secondary-button"
                  onClick={rerunSelected}
                  disabled={!selectedEntry || busy}
                >
                  <FiRefreshCw />
                  <span>Rerun</span>
                </button>
              </div>
            </div>

            {selectedEntry && selectedPayload ? (
              <>
                <div className="repo-manager-summary-strip">
                  <div className="repo-manager-pill repo-manager-pill--connected">
                    <FiEye />
                    <span>{selectedEntry.request?.operation_mode || 'inspect_only'}</span>
                  </div>
                  <div className={`repo-manager-pill ${selectedPayload.execution_ready ? 'repo-manager-pill--warning' : ''}`}>
                    <FiCheckCircle />
                    <span>{selectedPayload.execution_ready ? 'Execution handoff ready' : 'Read-first recommendation'}</span>
                  </div>
                  <div className="repo-manager-pill">
                    <FiClock />
                    <span>{formatStamp(selectedEntry.createdAt)}</span>
                  </div>
                </div>

                <div className="repo-manager-summary-copy">
                  <p>{selectedPayload.repo_summary}</p>
                  <div className="repo-manager-inline-meta">
                    <span>
                      <FiTarget />
                      {selectedPayload.target_scope}
                    </span>
                    {selectedEntry.request?.max_change_budget ? (
                      <span>
                        <FiCompass />
                        Budget: {selectedEntry.request.max_change_budget}
                      </span>
                    ) : null}
                    {selectedEntry.request?.change_intent ? (
                      <span>
                        <FiShield />
                        Intent: {selectedEntry.request.change_intent}
                      </span>
                    ) : null}
                  </div>
                </div>

                <div className="repo-manager-section-block">
                  <h3>Scope envelope</h3>
                  <div className="repo-manager-scope-grid">
                    <div className="repo-manager-context-card">
                      <span>Target path</span>
                      <strong>{selectedPayload.target_scope || 'Not set'}</strong>
                    </div>
                    <div className="repo-manager-context-card">
                      <span>Mode</span>
                      <strong>{selectedEntry.request?.operation_mode || 'inspect_only'}</strong>
                    </div>
                    <div className="repo-manager-context-card">
                      <span>Allowed files</span>
                      <strong>{(selectedEntry.request?.focus_files || []).length}</strong>
                      <p>{(selectedEntry.request?.focus_files || []).join(', ') || 'None specified'}</p>
                    </div>
                    <div className="repo-manager-context-card">
                      <span>Excluded files</span>
                      <strong>{(selectedEntry.request?.excluded_files || []).length}</strong>
                      <p>{(selectedEntry.request?.excluded_files || []).join(', ') || 'None specified'}</p>
                    </div>
                    <div className="repo-manager-context-card">
                      <span>Max inspection depth</span>
                      <strong>{selectedEntry.request?.max_directory_depth ?? 'Not set'}</strong>
                    </div>
                    <div className="repo-manager-context-card">
                      <span>Max file count</span>
                      <strong>{selectedEntry.request?.max_files_to_inspect ?? 'Not set'}</strong>
                    </div>
                  </div>
                </div>

                <div className="repo-manager-section-block">
                  <h3>Focus files</h3>
                  <div className="repo-manager-risk-list">
                    {selectedPayload.focus_files.map((file) => (
                      <article className="repo-manager-context-card" key={file}>
                        <span>Why this file is listed</span>
                        <strong>{file}</strong>
                        <p>{describeFocusReason(file, selectedEntry)}</p>
                      </article>
                    ))}
                  </div>
                </div>

                <div className="repo-manager-section-block">
                  <h3>Risks</h3>
                  <div className="repo-manager-risk-list">
                    {selectedPayload.risks.map((risk, index) => (
                      <article className="repo-manager-risk-card" key={`${risk.file}-${index}`}>
                        <div className="repo-manager-risk-head">
                          <strong>{risk.issue}</strong>
                          <span className={`repo-manager-chip repo-manager-chip--${toneForConfidence(risk.confidence)}`}>
                            {risk.confidence}
                          </span>
                        </div>
                        <div className="repo-manager-risk-file">{risk.file}</div>
                        <p>{risk.evidence}</p>
                      </article>
                    ))}
                  </div>
                </div>

                <div className="repo-manager-section-block">
                  <h3>Smallest safe plan</h3>
                  <div className="repo-manager-plan-list">
                    {selectedPayload.plan.map((step, index) => (
                      <article className="repo-manager-plan-card" key={`${step.step}-${index}`}>
                        <div className="repo-manager-plan-index">{index + 1}</div>
                        <div className="repo-manager-plan-body">
                          <strong>{step.step}</strong>
                          {step.file ? <div className="repo-manager-risk-file">{step.file}</div> : null}
                          <p>{step.purpose}</p>
                          <div className="repo-manager-plan-meta">
                            <span><strong>Effect:</strong> {step.expected_effect}</span>
                            <span><strong>Validate:</strong> {step.validation}</span>
                            {step.rollback_note ? <span><strong>Rollback:</strong> {step.rollback_note}</span> : null}
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                </div>

                {selectedPayload.validations?.length ? (
                  <div className="repo-manager-section-block">
                    <h3>Validations</h3>
                    <ul className="repo-manager-validation-list">
                      {selectedPayload.validations.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div className="repo-manager-section-block">
                  <h3>Handoff ready</h3>
                  <div className="repo-manager-handoff-card">
                    <div className="repo-manager-inline-meta">
                        <span>
                          <FiShield />
                          {selectedPayload.execution_ready ? 'Execution handoff can be prepared.' : 'Still read-first and review-gated.'}
                      </span>
                      {selectedEntry.request?.validation_target ? (
                        <span>
                          <FiCheckCircle />
                          Validation target: {selectedEntry.request.validation_target}
                        </span>
                      ) : null}
                      {selectedEntry.request?.no_execution_without_handoff ? (
                        <span>
                          <FiCompass />
                          No execution without handoff
                        </span>
                      ) : null}
                    </div>
                    <div className="repo-manager-action-row">
                      <button
                        type="button"
                        className="repo-manager-secondary-button"
                        onClick={handleDraftForgeHandoff}
                      >
                        <FiArrowRight />
                        <span>Draft Forge handoff</span>
                      </button>
                      <button
                        type="button"
                        className="repo-manager-secondary-button"
                        onClick={handleSendSummaryToJarvis}
                      >
                        <FiFileText />
                        <span>Send summary to Jarvis</span>
                      </button>
                      <button
                        type="button"
                        className="repo-manager-secondary-button"
                        onClick={handleCopyBoundedPlan}
                      >
                        <FiCheckCircle />
                        <span>Copy bounded plan</span>
                      </button>
                    </div>
                    <pre className="repo-manager-export-preview">{structuredExport}</pre>
                  </div>
                </div>

                <div className="repo-manager-section-block">
                  <h3>Context used</h3>
                  <div className="repo-manager-context-grid">
                    <div className="repo-manager-context-card">
                      <span>Forge scope</span>
                      <strong>{selectedEntry.response?.forge_context?.target_scope || 'Not set'}</strong>
                      <p>
                        Focus files: {(selectedEntry.response?.forge_context?.focus_files || []).join(', ') || 'None'}
                      </p>
                      <p>
                        Allowlist: {(selectedEntry.response?.forge_context?.file_path_allowlist || []).join(', ') || 'None'}
                      </p>
                    </div>
                    <div className="repo-manager-context-card">
                      <span>Workspace context</span>
                      <strong>{selectedEntry.response?.workspace_context?.project_scope || 'Workspace slice'}</strong>
                      <p>
                        Attached files: {(selectedEntry.response?.workspace_context?.files || []).length}
                      </p>
                      <p>
                        Max depth: {selectedEntry.response?.forge_context?.max_directory_depth ?? 'Not set'}
                      </p>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="repo-manager-empty repo-manager-empty--large">
                <div>
                  <strong>No repo-manager turn yet.</strong>
                  <p>
                    Send a task on the left and Forge will return a bounded repo summary, grounded
                    risks, and a smallest-safe-change handoff plan.
                  </p>
                  <Link className="repo-manager-secondary-link" to="/jarvis">
                    Back to Jarvis Console
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

export default RepoManager;
