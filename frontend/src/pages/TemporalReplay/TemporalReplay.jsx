import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { FiArrowLeft, FiDownload, FiRefreshCw } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { apiGet, apiPost, getApiErrorMessage } from '../../lib/api';
import '../OperatorConsole.css';
import './TemporalReplay.css';

const SUBJECT_TYPES = [
  'mission',
  'session',
  'workflow_run',
  'ugr_trace',
  'slingshot_case',
  'jarvis_run',
  'platform_job',
];

const KIND_LABELS = {
  cognitive_step: 'Cognitive',
  otem_gate: 'OTEM',
  nova_coherence: 'Nova / Coherence',
  intent_agency: 'Intent Agency',
  ledger_transition: 'Ledger',
  deliberation: 'UGR Deliberation',
  lineage_node: 'Lineage',
  law_event: 'Law',
  mission_receipt: 'Receipt',
  slingshot_receipt: 'Slingshot',
  capability_audit: 'Capability',
  platform_job: 'Platform Job',
  jarvis_run_step: 'Jarvis Run',
};

function claimTone(label) {
  const v = String(label || '').toLowerCase();
  if (v === 'proven') return 'proven';
  if (v === 'rejected') return 'drift';
  return '';
}

function groupEventsByKind(events) {
  const groups = {};
  events.forEach((ev) => {
    const kind = ev.kind || 'other';
    if (!groups[kind]) groups[kind] = [];
    groups[kind].push(ev);
  });
  return groups;
}

function CognitiveTraceTree({ events, summaries, selectedId, onSelect }) {
  if (!events?.length) {
    return <p className="session-empty">No events in timeline.</p>;
  }

  const groups = groupEventsByKind(events);

  return (
    <div className="temporal-replay-tree">
      {Object.entries(groups).map(([kind, groupEvents]) => (
          <details key={kind} open>
            <summary>
              <strong>{KIND_LABELS[kind] || kind}</strong>
              <span className="temporal-replay-chip">{groupEvents.length}</span>
            </summary>
            {groupEvents.map((ev) => {
        const summary = summaries?.find((s) => s.event_id === ev.event_id)
          || {
            kind: ev.kind,
            summary: ev.summary,
            hard_fail: ev.invariant_flags?.hard_fail,
          };
        const id = ev.event_id || `${ev.kind}-${ev.sequence}`;
        return (
          <details key={id} open={selectedId === id}>
            <summary
              role="button"
              tabIndex={0}
              onClick={(e) => {
                e.preventDefault();
                onSelect(ev);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  onSelect(ev);
                }
              }}
            >
              <strong>{summary.kind || ev.kind}</strong>
              {' — '}
              {summary.summary || ev.summary || 'event'}
              {summary.hard_fail ? ' [invariant]' : ''}
            </summary>
            {summary?.jump_target ? (
              <div className="temporal-replay-meta">
                <span>Subsystem: {summary.jump_target.display_name || summary.subsystem_id}</span>
                {summary.emitter_module ? <code>{summary.emitter_module}</code> : null}
                {summary.genome_ref ? <code>{summary.genome_ref}</code> : null}
              </div>
            ) : null}
            <pre className="temporal-replay-pre">{JSON.stringify(ev, null, 2)}</pre>
          </details>
        );
            })}
          </details>
      ))}
    </div>
  );
}

function TimelineScrubber({ summaries, selectedId, onSelect }) {
  if (!summaries?.length) {
    return null;
  }
  return (
    <div className="temporal-replay-scrubber" role="listbox" aria-label="Replay timeline">
      {summaries.map((s) => (
        <button
          key={s.event_id}
          type="button"
          className={`temporal-replay-tick ${selectedId === s.event_id ? 'active' : ''} ${s.hard_fail ? 'hard-fail' : ''}`}
          onClick={() => onSelect(s)}
        >
          <span>{s.kind}</span>
          <br />
          <small>{(s.timestamp_utc || '').slice(11, 19)}</small>
        </button>
      ))}
    </div>
  );
}

export default function TemporalReplayPage() {
  const { subjectType: routeType, subjectId: routeId } = useParams();
  const [subjectType, setSubjectType] = useState(routeType || 'mission');
  const [subjectId, setSubjectId] = useState(routeId || '');
  const [tenantId, setTenantId] = useState('');
  const [forkAt, setForkAt] = useState('');
  const [loading, setLoading] = useState(false);
  const [timeline, setTimeline] = useState(null);
  const [statePayload, setStatePayload] = useState(null);
  const [verifyPayload, setVerifyPayload] = useState(null);
  const [forwardPayload, setForwardPayload] = useState(null);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [compareLeft, setCompareLeft] = useState('');
  const [compareRight, setCompareRight] = useState('');
  const [comparePayload, setComparePayload] = useState(null);
  const [liveFork, setLiveFork] = useState(false);
  const [diffPayload, setDiffPayload] = useState(null);
  const [replayTarget, setReplayTarget] = useState('cloud_invariants');

  const replay = timeline?.replay || timeline;
  const summaries = replay?.summaries || [];
  const events = replay?.events || [];
  const lawPin = statePayload?.replay?.law_pin || statePayload?.law_pin;
  const invariantViolations = statePayload?.replay?.invariant_violations
    || statePayload?.invariant_violations
    || [];
  const selectedIndex = useMemo(
    () => summaries.findIndex((s) => s.event_id === selectedSummary?.event_id),
    [summaries, selectedSummary],
  );

  const selectedEvent = useMemo(() => {
    if (!selectedSummary?.event_id) return null;
    return events.find((e) => e.event_id === selectedSummary.event_id) || null;
  }, [events, selectedSummary]);

  const loadTimeline = useCallback(async (rebuild = false) => {
    const sid = subjectId.trim();
    if (!sid) {
      toast.error('Enter a subject id.');
      return;
    }
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (tenantId.trim()) q.set('tenant_id', tenantId.trim());
      if (rebuild) q.set('rebuild', '1');
      const path = `/api/operator/replay/${encodeURIComponent(subjectType)}/${encodeURIComponent(sid)}/timeline?${q}`;
      const res = await apiGet(path);
      setTimeline(res.data);
      const sum = res.data?.replay?.summaries || [];
      if (sum.length) {
        setSelectedSummary(sum[sum.length - 1]);
        setForkAt(sum[sum.length - 1].timestamp_utc || '');
      }
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Could not load timeline.'));
      setTimeline(null);
    } finally {
      setLoading(false);
    }
  }, [subjectType, subjectId, tenantId]);

  const loadState = useCallback(async (at) => {
    const sid = subjectId.trim();
    if (!sid) return;
    try {
      const q = new URLSearchParams();
      if (at) q.set('at', at);
      if (tenantId.trim()) q.set('tenant_id', tenantId.trim());
      const res = await apiGet(
        `/api/operator/replay/${encodeURIComponent(subjectType)}/${encodeURIComponent(sid)}/state?${q}`,
      );
      setStatePayload(res.data);
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Could not load state.'));
    }
  }, [subjectType, subjectId, tenantId]);

  const runVerify = useCallback(async () => {
    const sid = subjectId.trim();
    if (!sid) return;
    try {
      const res = await apiPost(
        `/api/operator/replay/${encodeURIComponent(subjectType)}/${encodeURIComponent(sid)}/verify`,
        { at: forkAt || undefined, tenant_id: tenantId.trim() || undefined },
      );
      setVerifyPayload(res.data);
      toast.success('Verification complete.');
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Verification failed.'));
    }
  }, [subjectType, subjectId, forkAt, tenantId]);

  const runForward = useCallback(async () => {
    const sid = subjectId.trim();
    if (!sid || !forkAt) {
      toast.error('Set fork time from timeline scrubber.');
      return;
    }
    try {
      const res = await apiPost(
        `/api/operator/replay/${encodeURIComponent(subjectType)}/${encodeURIComponent(sid)}/forward`,
        {
          fork_at: forkAt,
          mode: liveFork ? 'live_fork' : 'dry_run',
          steps: 1,
          target: 'cloud_invariants',
          tenant_id: tenantId.trim() || undefined,
        },
      );
      setForwardPayload(res.data);
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Forward replay failed.'));
    }
  }, [subjectType, subjectId, forkAt, tenantId, liveFork]);

  const runDiff = useCallback(async () => {
    const sid = subjectId.trim();
    if (!sid || !forkAt) {
      toast.error('Select a fork point on the timeline first.');
      return;
    }
    try {
      const q = new URLSearchParams({ fork_at: forkAt, target: replayTarget });
      if (tenantId.trim()) q.set('tenant_id', tenantId.trim());
      const res = await apiGet(
        `/api/operator/replay/${encodeURIComponent(subjectType)}/${encodeURIComponent(sid)}/diff?${q}`,
      );
      setDiffPayload(res.data);
      setForwardPayload(res.data);
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Reasoning diff failed.'));
    }
  }, [subjectType, subjectId, forkAt, tenantId, replayTarget]);

  const exportBundle = useCallback(async () => {
    const sid = subjectId.trim();
    if (!sid) return;
    try {
      const q = new URLSearchParams();
      if (forkAt) q.set('fork_at', forkAt);
      if (tenantId.trim()) q.set('tenant_id', tenantId.trim());
      const res = await apiGet(
        `/api/operator/replay/${encodeURIComponent(subjectType)}/${encodeURIComponent(sid)}/bundle?${q}`,
      );
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `replay-bundle-${subjectType}-${sid}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Bundle downloaded.');
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Export failed.'));
    }
  }, [subjectType, subjectId, forkAt, tenantId]);

  const runCompare = useCallback(async () => {
    if (!compareLeft.trim() || !compareRight.trim()) {
      toast.error('Enter both compare subject ids.');
      return;
    }
    try {
      const res = await apiPost('/api/operator/replay/compare', {
        left: { subject_type: subjectType, subject_id: compareLeft.trim() },
        right: { subject_type: subjectType, subject_id: compareRight.trim() },
        align_by: 'sequence',
      });
      setComparePayload(res.data);
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Compare failed.'));
    }
  }, [subjectType, compareLeft, compareRight]);

  useEffect(() => {
    if (routeType && routeId) {
      setSubjectType(routeType);
      setSubjectId(routeId);
    }
  }, [routeType, routeId]);

  useEffect(() => {
    if (routeType && routeId) {
      loadTimeline();
    }
  }, [routeType, routeId, loadTimeline]);

  useEffect(() => {
    if (forkAt && subjectId.trim()) {
      loadState(forkAt);
    }
  }, [forkAt, subjectId, loadState]);

  const onScrubSelect = useCallback((s) => {
    setSelectedSummary(s);
    setForkAt(s.timestamp_utc || '');
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if (!summaries.length || e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }
      if (e.key === 'ArrowLeft' && selectedIndex > 0) {
        onScrubSelect(summaries[selectedIndex - 1]);
      }
      if (e.key === 'ArrowRight' && selectedIndex >= 0 && selectedIndex < summaries.length - 1) {
        onScrubSelect(summaries[selectedIndex + 1]);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [summaries, selectedIndex, onScrubSelect]);

  const onTreeSelect = (ev) => {
    const sum = summaries.find((x) => x.event_id === ev.event_id) || {
      event_id: ev.event_id,
      timestamp_utc: ev.timestamp_utc,
      kind: ev.kind,
    };
    onScrubSelect(sum);
  };

  const verifyReplay = verifyPayload?.replay || verifyPayload;

  return (
    <section className="temporal-replay-page workbench" data-testid="temporal-replay-page">
      <header className="temporal-replay-header workbench-hero">
        <Link to="/operator" className="workbench-button ghost">
          <FiArrowLeft /> Operator
        </Link>
        <p className="eyebrow">Temporal Replay Machine</p>
        <h1>AAIS Flight Recorder</h1>
        <p>
          Law-pinned, receipt-verified replay. Dry-run forward replay is default; live fork requires explicit opt-in.
        </p>
      </header>

      <div className="temporal-replay-controls page-panel">
        <label>
          Subject type
          <select value={subjectType} onChange={(e) => setSubjectType(e.target.value)}>
            {SUBJECT_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>
        <label>
          Subject id
          <input
            value={subjectId}
            onChange={(e) => setSubjectId(e.target.value)}
            placeholder="mission-uuid"
          />
        </label>
        <label>
          Tenant (optional)
          <input value={tenantId} onChange={(e) => setTenantId(e.target.value)} placeholder="default" />
        </label>
        <label>
          Fork at (ISO)
          <input value={forkAt} onChange={(e) => setForkAt(e.target.value)} placeholder="2026-06-04T14:32:00+00:00" />
        </label>
        <button type="button" className="workbench-button primary" onClick={() => loadTimeline(true)} disabled={loading}>
          <FiRefreshCw /> Load timeline
        </button>
      </div>

      {lawPin ? (
        <div className="temporal-replay-meta page-panel" style={{ marginBottom: '1rem' }}>
          <span className="temporal-replay-chip">law {lawPin.law_id}</span>
          <span className="temporal-replay-chip">v {lawPin.invariant_version || lawPin.law_version}</span>
          <span className="temporal-replay-chip">tenant {lawPin.tenant_id}</span>
          {lawPin.boundary_digest ? (
            <span className="temporal-replay-chip">boundary {lawPin.boundary_digest.slice(0, 12)}…</span>
          ) : null}
        </div>
      ) : null}

      <div className="temporal-replay-grid">
        <div className="temporal-replay-panel">
          <h3>Timeline</h3>
          <p className="temporal-replay-meta">Arrow keys ← → scrub when focus is not in an input.</p>
          <TimelineScrubber
            summaries={summaries}
            selectedId={selectedSummary?.event_id}
            onSelect={onScrubSelect}
          />
          <p className="temporal-replay-meta">
            {replay?.event_count ?? 0} events
            {(replay?.coverage_notes || []).map((n) => (
              <span key={n} className="temporal-replay-chip">{n}</span>
            ))}
          </p>
        </div>

        <div className="temporal-replay-panel">
          <h3>Cognitive trace</h3>
          <CognitiveTraceTree
            events={events}
            summaries={summaries}
            selectedId={selectedSummary?.event_id}
            onSelect={onTreeSelect}
          />
        </div>

        {invariantViolations.length > 0 ? (
          <div className="temporal-replay-panel temporal-replay-invariant-overlay">
            <h3>Invariant overlay</h3>
            <ul>
              {invariantViolations.map((v) => (
                <li key={v.event_id}>
                  <strong>{v.kind}</strong> @ {v.timestamp_utc}
                  {(v.codes || []).length ? ` — ${v.codes.join(', ')}` : ''}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="temporal-replay-panel">
          <h3>State @ T</h3>
          <pre className="temporal-replay-pre">
            {JSON.stringify(statePayload?.replay || statePayload, null, 2)}
          </pre>
        </div>

        <div className="temporal-replay-panel">
          <h3>Verify & forward</h3>
          <div className="temporal-replay-actions">
            <label>
              Replay target
              <select value={replayTarget} onChange={(e) => setReplayTarget(e.target.value)}>
                <option value="cloud_invariants">cloud_invariants</option>
                <option value="cognitive_bridge">cognitive_bridge</option>
                <option value="otem">otem</option>
                <option value="mission_step">mission_step</option>
              </select>
            </label>
            <button type="button" onClick={runVerify}>Verify receipts</button>
            <button type="button" onClick={runDiff}>Reasoning diff</button>
            <button type="button" onClick={runForward}>Forward (dry-run)</button>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <input type="checkbox" checked={liveFork} onChange={(e) => setLiveFork(e.target.checked)} />
              Live fork (allowlisted only)
            </label>
            <button type="button" onClick={exportBundle}>
              <FiDownload /> Export bundle
            </button>
          </div>
          {verifyReplay ? (
            <div>
              <p className={`temporal-replay-chip ${claimTone(verifyReplay?.claim_label)}`}>
                verify: {verifyReplay?.claim_label || String(verifyReplay?.ok)}
              </p>
              <ul className="temporal-replay-verify-checks">
                {(verifyReplay.checks || []).map((c) => (
                  <li key={c.name}>
                    {c.name}: {c.ok ? 'ok' : c.detail}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {diffPayload?.replay ? (
            <div className="temporal-replay-diff-panel">
              <strong>Reasoning delta: {diffPayload.replay.replay_delta}</strong>
              <pre className="temporal-replay-pre">{JSON.stringify(diffPayload.replay, null, 2)}</pre>
            </div>
          ) : null}
          {forwardPayload && !diffPayload ? (
            <pre className="temporal-replay-pre">{JSON.stringify(forwardPayload?.replay || forwardPayload, null, 2)}</pre>
          ) : null}
        </div>
      </div>

      <div className="temporal-replay-panel" style={{ marginTop: '1rem' }}>
        <h3>Cross-run compare</h3>
        <div className="temporal-replay-compare temporal-replay-controls">
          <label>
            Left id
            <input value={compareLeft} onChange={(e) => setCompareLeft(e.target.value)} />
          </label>
          <label>
            Right id
            <input value={compareRight} onChange={(e) => setCompareRight(e.target.value)} />
          </label>
          <button type="button" onClick={runCompare}>Compare</button>
        </div>
        {comparePayload ? (
          <pre className="temporal-replay-pre">{JSON.stringify(comparePayload?.replay || comparePayload, null, 2)}</pre>
        ) : null}
      </div>
    </section>
  );
}
