import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, getApiErrorMessage } from '../../lib/api';
import './TemporalReplay.css';

const SUBJECT_TYPES = ['mission', 'session', 'operator_session', 'workflow_run'];
const KIND_LABELS = { operator_decision: 'Decision Ledger', ledger_transition: 'Ledger' };

export default function TemporalReplayPage() {
  const { subjectType: routeType, subjectId: routeId } = useParams();
  const [subjectType, setSubjectType] = useState(routeType || 'operator_session');
  const [subjectId, setSubjectId] = useState(routeId || 'global');
  const [timeline, setTimeline] = useState(null);
  const [ledgerDigest, setLedgerDigest] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scrubIndex, setScrubIndex] = useState(0);

  const loadTimeline = useCallback(async () => {
    const sid = subjectId.trim();
    if (!sid) return;
    setLoading(true);
    try {
      const res = await apiGet(`/api/operator/replay/${encodeURIComponent(subjectType)}/${encodeURIComponent(sid)}/timeline?rebuild=1`);
      setTimeline(res.data);
      setScrubIndex(0);
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Could not load timeline.'));
      setTimeline(null);
    } finally {
      setLoading(false);
    }
  }, [subjectType, subjectId]);

  const loadLedgerDigest = useCallback(async () => {
    const sid = subjectId.trim();
    if (!sid || !['session', 'operator_session'].includes(subjectType)) {
      setLedgerDigest(null);
      return;
    }
    try {
      const res = await apiGet(`/api/operator/ledger/digest?session_id=${encodeURIComponent(sid)}`);
      setLedgerDigest(res.data?.digest || null);
    } catch {
      setLedgerDigest(null);
    }
  }, [subjectType, subjectId]);

  useEffect(() => {
    if (routeType && routeId) {
      setSubjectType(routeType);
      setSubjectId(routeId);
    }
  }, [routeType, routeId]);

  useEffect(() => {
    if (subjectId.trim()) {
      loadTimeline();
      loadLedgerDigest();
    }
  }, [subjectId, subjectType, loadTimeline, loadLedgerDigest]);

  const events = useMemo(
    () => timeline?.replay?.events || timeline?.events || [],
    [timeline],
  );
  const activeEvent = useMemo(() => events[scrubIndex] || null, [events, scrubIndex]);

  return (
    <section className="temporal-replay-page" data-testid="temporal-replay-page">
      <header className="temporal-replay-header">
        <h1>Temporal Replay</h1>
        <Link to="/operator/ledger">Operator Ledger</Link>
      </header>
      <div className="temporal-replay-controls page-panel">
        <select value={subjectType} onChange={(e) => setSubjectType(e.target.value)}>
          {SUBJECT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <input value={subjectId} onChange={(e) => setSubjectId(e.target.value)} placeholder="subject id" />
        <button type="button" onClick={loadTimeline} disabled={loading}>Load timeline</button>
      </div>
      {ledgerDigest ? (
        <div className="page-panel" data-testid="operator-ledger-replay-digest">
          <span className="temporal-replay-chip">entries {ledgerDigest.entry_count}</span>
          {ledgerDigest.pending_count > 0 ? <span className="temporal-replay-chip">pending {ledgerDigest.pending_count}</span> : null}
          {ledgerDigest.cannot_undo_count > 0 ? <span className="temporal-replay-chip">cannot undo {ledgerDigest.cannot_undo_count}</span> : null}
          <Link to={`/operator/ledger?session_id=${encodeURIComponent(subjectId.trim())}`}>Operator Ledger</Link>
        </div>
      ) : null}
      {events.length > 0 ? (
        <div className="temporal-replay-scrubber page-panel" data-testid="temporal-replay-scrubber">
          <label>
            Scrubber ({scrubIndex + 1}/{events.length})
            <input
              type="range"
              min={0}
              max={Math.max(0, events.length - 1)}
              value={scrubIndex}
              onChange={(e) => setScrubIndex(Number(e.target.value))}
            />
          </label>
        </div>
      ) : null}
      <div className="temporal-replay-panel">
        <h3>Timeline ({events.length} events)</h3>
        {activeEvent ? (
          <article className="temporal-replay-detail" data-testid="temporal-replay-active-event">
            <strong>{KIND_LABELS[activeEvent.kind] || activeEvent.kind}</strong> — {activeEvent.summary}
            <div className="workflow-step-type">seq {activeEvent.sequence} · {activeEvent.timestamp_utc || '—'}</div>
            {activeEvent.kind === 'operator_decision' ? (
              <div><Link to={`/operator/ledger?session_id=${encodeURIComponent(subjectId.trim())}`}>Open in Operator Ledger</Link></div>
            ) : null}
          </article>
        ) : <p>No events.</p>}
        {events.map((ev, idx) => (
          <div
            key={ev.event_id || `${ev.kind}-${ev.sequence}`}
            className={`temporal-replay-event ${idx === scrubIndex ? 'is-active' : ''}`}
            onClick={() => setScrubIndex(idx)}
            onKeyDown={(e) => e.key === 'Enter' && setScrubIndex(idx)}
            role="button"
            tabIndex={0}
          >
            <strong>{KIND_LABELS[ev.kind] || ev.kind}</strong> — {ev.summary}
          </div>
        ))}
      </div>
    </section>
  );
}
