import React, { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import {
  FiActivity,
  FiBox,
  FiCheck,
  FiChevronRight,
  FiCode,
  FiGitBranch,
  FiGrid,
  FiLayers,
  FiPause,
  FiPlay,
  FiRefreshCw,
  FiRepeat,
  FiRotateCcw,
  FiShield,
  FiSkipBack,
  FiSkipForward,
  FiZap,
} from 'react-icons/fi';
import LineagePanel from '../components/continuity/LineagePanel';
import ReceiptsPanel from '../components/continuity/ReceiptsPanel';
import Timeline from '../components/continuity/Timeline';
import FileControls from '../components/file/FileControls';
import FileEditor from '../components/file/FileEditor';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import './NovaCodingAgent.css';

const railStages = [
  { label: 'EVENT', icon: FiGitBranch },
  { label: 'LINEAGE', icon: FiLayers },
  { label: 'METRICS', icon: FiActivity },
  { label: 'WAVE', icon: FiZap },
  { label: 'RECEIPT', icon: FiBox },
  { label: 'SPECIMEN', icon: FiGrid },
];

const corridorPanels = [
  {
    title: 'Intent',
    rows: ['Apply patch to engine.py', 'Insert verification before changes.'],
    footer: 'Confidence 0.93',
  },
  {
    title: 'Plan',
    rows: ['Analyze file', 'Map lineage', 'Create patch', 'Run checks', 'Apply decision'],
  },
  {
    title: 'Trace',
    rows: ['File.Loaded', 'Patch.Plan', 'Governance.Check', 'Patch.Review', 'Apply.Decision'],
  },
  {
    title: 'Calls',
    rows: ['ckce1.check_patch', 'lineage.verify_intent', 'create_backup', 'apply_changes'],
  },
  {
    title: 'Receipts',
    rows: ['Generated: 2', 'Valid: 2', 'Pending: 0'],
    footer: 'View all',
  },
];

function upsertNewest(events, nextEvent) {
  if (!nextEvent?.id) {
    return events;
  }
  return [nextEvent, ...events.filter((event) => event.id !== nextEvent.id)];
}

function eventTime(event, fallback = '10:42:21') {
  const raw = event?.createdAt || event?.created_at || event?.timestamp;
  if (!raw) {
    return fallback;
  }
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return String(raw).slice(-8) || fallback;
  }
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function truncateHash(value) {
  return String(value || '7c91...aa11').replace(/-/g, '').slice(0, 4) + '...' + String(value || 'aa11').slice(-4);
}

function deriveHealth(events, receipts) {
  const hasFile = events.some((event) => event.name === 'File.Opened' || event.name === 'File.Saved');
  const validReceipts = receipts.filter((receipt) => receipt.status === 'PASS').length;
  const base = hasFile ? 0.91 : 0.87;
  return {
    score: Math.min(0.97, base + Math.min(validReceipts, 3) * 0.01),
    events: Math.max(events.length, 4),
    receipts: Math.max(receipts.length, 2),
  };
}

function ActionButton({ children, intent = 'default', icon: Icon, onClick }) {
  return (
    <button className={`nova-action nova-action--${intent}`} type="button" onClick={onClick}>
      {Icon ? <Icon aria-hidden="true" /> : null}
      <span>{children}</span>
    </button>
  );
}

function WaveSignature() {
  return (
    <div className="studio-card wave-card">
      <div className="studio-card__header">
        <h2>WAVE SIGNATURE <span>(Live)</span></h2>
      </div>
      <div className="wave-plot" aria-label="Wave signature chart">
        <svg viewBox="0 0 520 170" role="img" aria-label="Expected, current, and corrected wave signatures">
          <defs>
            <linearGradient id="waveGlow" x1="0" x2="1">
              <stop offset="0%" stopColor="#29d3ff" />
              <stop offset="50%" stopColor="#9d6bff" />
              <stop offset="100%" stopColor="#5cffbc" />
            </linearGradient>
          </defs>
          {[35, 70, 105, 140].map((y) => (
            <line key={y} x1="0" y1={y} x2="400" y2={y} className="wave-grid-line" />
          ))}
          <path className="wave-path wave-path--expected" d="M0 86 C20 12 42 12 62 86 S104 160 124 86 S166 12 186 86 S228 160 248 86 S290 12 310 86 S352 160 372 86 S414 12 434 86" />
          <path className="wave-path wave-path--current" d="M0 104 C22 22 42 28 62 92 S104 145 124 73 S166 35 186 104 S228 142 248 74 S290 20 310 95 S352 153 372 82 S414 42 434 100" />
          <path className="wave-path wave-path--corrected" d="M0 90 C24 60 42 63 62 89 S104 118 124 86 S166 58 186 88 S228 115 248 86 S290 58 310 88 S352 116 372 87 S414 60 434 89" />
        </svg>
        <div className="wave-readout">
          <span>Drift</span>
          <strong>0.07</strong>
          <small>Low</small>
          <span>Status</span>
          <strong className="amber">Correcting</strong>
        </div>
      </div>
    </div>
  );
}

export default function NovaCodingAgent() {
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [lineage, setLineage] = useState([]);
  const [receipts, setReceipts] = useState([]);
  const [filePath, setFilePath] = useState('src/continuity/engine.py');
  const [fileContent, setFileContent] = useState('');
  const [manualEventName, setManualEventName] = useState('Manual.Plan');
  const [receiptStatus, setReceiptStatus] = useState('PASS');
  const [receiptDetails, setReceiptDetails] = useState('');
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [busyAction, setBusyAction] = useState('');
  const [actionNotice, setActionNotice] = useState('Awaiting operator decision');

  const selectedEventId = selectedEvent?.id || '';
  const health = useMemo(() => deriveHealth(events, receipts), [events, receipts]);
  const liveEvents = events.length ? events : [
    { id: 'seed-plan', name: 'Manual.Plan', payload: { source: 'operator' } },
    { id: 'seed-loaded', name: 'File.Loaded', payload: { path: 'src/continuity/engine.py' } },
    { id: 'seed-review', name: 'Patch.Review', payload: { status: 'pending' } },
  ];

  async function loadTimeline() {
    setLoadingTimeline(true);
    try {
      const response = await apiGet('/api/continuity/events');
      setEvents(response.data?.events || []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to load continuity timeline'));
    } finally {
      setLoadingTimeline(false);
    }
  }

  useEffect(() => {
    loadTimeline();
  }, []);

  async function selectEvent(event) {
    setSelectedEvent(event);
    setLineage([]);
    setReceipts([]);
    try {
      const [lineageResponse, receiptsResponse] = await Promise.all([
        apiGet(`/api/continuity/lineage/${event.id}`),
        apiGet('/api/continuity/receipts', { params: { eventId: event.id } }),
      ]);
      setLineage(lineageResponse.data?.lineage || []);
      setReceipts(receiptsResponse.data?.receipts || []);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to load selected event'));
    }
  }

  async function createManualEvent() {
    const name = manualEventName.trim();
    if (!name) {
      return;
    }
    setBusyAction('event');
    try {
      const response = await apiPost('/api/continuity/events', {
        name,
        payload: { source: 'nova-studio-cockpit' },
      });
      setEvents((current) => upsertNewest(current, response.data?.event));
      toast.success('Event anchored');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to create event'));
    } finally {
      setBusyAction('');
    }
  }

  async function openFile() {
    const path = filePath.trim();
    if (!path) {
      return;
    }
    setBusyAction('open');
    try {
      const response = await apiPost('/api/continuity/file/open', { path });
      setFileContent(response.data?.content || '');
      setFilePath(response.data?.path || path);
      setEvents((current) => upsertNewest(current, response.data?.event));
      setActionNotice('File continuity opened and emitted');
      toast.success('File opened into continuity');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to open file'));
    } finally {
      setBusyAction('');
    }
  }

  async function saveFile() {
    const path = filePath.trim();
    if (!path) {
      return;
    }
    setBusyAction('save');
    try {
      const response = await apiPost('/api/continuity/file/save', {
        path,
        content: fileContent,
      });
      setFilePath(response.data?.path || path);
      setEvents((current) => upsertNewest(current, response.data?.event));
      setActionNotice('Patch accepted into file continuity');
      toast.success('File saved into continuity');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to save file'));
    } finally {
      setBusyAction('');
    }
  }

  async function issueReceipt() {
    if (!selectedEventId) {
      return;
    }
    setBusyAction('receipt');
    try {
      const response = await apiPost('/api/continuity/receipts', {
        eventId: selectedEventId,
        status: receiptStatus,
        details: receiptDetails,
      });
      const receipt = response.data?.receipt;
      setReceipts((current) => (receipt ? [receipt, ...current] : current));
      setReceiptDetails('');
      setActionNotice('Receipt linked to selected event');
      toast.success('Receipt issued');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to issue receipt'));
    } finally {
      setBusyAction('');
    }
  }

  function announceAction(label) {
    setActionNotice(label);
    toast.success(label);
  }

  return (
    <section className="nova-coding-agent nova-studio">
      <header className="studio-topbar">
        <div className="studio-brand">
          <div className="studio-mark"><FiActivity aria-hidden="true" /></div>
          <div>
            <h1>NOVA STUDIO</h1>
            <p>Full Operational Cockpit</p>
          </div>
        </div>
        <div className="studio-meta">
          <span>Project: <strong>project-infinity</strong></span>
          <span>Branch: <strong className="green">feature/continuity-patch-plan</strong></span>
          <span>Nova Status: <strong className="amber">Executing</strong></span>
          <button className="studio-health-pill" type="button" onClick={loadTimeline}>
            Continuity Health: {health.score.toFixed(2)} (Healthy)
          </button>
        </div>
        <div className="studio-top-actions">
          <FiShield aria-label="Governance shield" />
          <FiRefreshCw aria-label="Refresh cockpit" onClick={loadTimeline} />
        </div>
      </header>

      <main className="studio-layout">
        <aside className="studio-left">
          <Timeline
            events={liveEvents}
            loadingTimeline={loadingTimeline}
            manualEventName={manualEventName}
            onManualEventNameChange={setManualEventName}
            onCreateEvent={createManualEvent}
            onSelectEvent={selectEvent}
            selectedEventId={selectedEventId}
            busyAction={busyAction}
          />

          <div className="studio-card lineage-graph">
            <div className="studio-card__header">
              <h2>LINEAGE GRAPH</h2>
              <span>Live</span>
            </div>
            <div className="lineage-map" aria-label="Lineage graph">
              {liveEvents.slice(0, 6).map((event, index) => (
                <button
                  className={`lineage-node lineage-node--${index % 4}`}
                  key={event.id}
                  style={{ '--x': `${12 + (index % 3) * 32}%`, '--y': `${16 + Math.floor(index / 3) * 38}%` }}
                  type="button"
                  onClick={() => selectEvent(event)}
                >
                  <span>{event.name}</span>
                  <small>{eventTime(event)}</small>
                </button>
              ))}
            </div>
            <LineagePanel selectedEvent={selectedEvent} lineage={lineage} />
          </div>

          <div className="studio-card health-card">
            <div className="studio-card__header">
              <h2>CONTINUITY HEALTH</h2>
            </div>
            <div className="health-body">
              <div className="health-ring">
                <strong>{health.score.toFixed(2)}</strong>
                <span>Healthy</span>
              </div>
              <div className="health-stats">
                <p><span>Coherence</span><strong>91%</strong></p>
                <p><span>Drift</span><strong className="amber">Low</strong></p>
                <p><span>Replay</span><strong>Stable</strong></p>
                <p><span>CKCE-1</span><strong className="amber">Enforced</strong></p>
              </div>
            </div>
            <div className="layer-strip">
              <span>Event Layer</span>
              <FiChevronRight />
              <span>Lineage Layer</span>
              <FiChevronRight />
              <span>Receipt Layer</span>
              <FiChevronRight />
              <span>Wave Layer</span>
            </div>
          </div>
        </aside>

        <section className="substrate-rail" aria-label="Four-layer substrate rail">
          {railStages.map(({ label, icon: Icon }) => (
            <div className="rail-node" key={label}>
              <Icon aria-hidden="true" />
              <span>{label}</span>
            </div>
          ))}
        </section>

        <section className="studio-center">
          <div className="studio-card code-workspace">
            <div className="studio-card__header code-header">
              <h2>CODE EDITOR</h2>
              <span>{filePath || 'src/continuity/engine.py'}</span>
              <small>Python 3.11</small>
            </div>
            <FileControls
              filePath={filePath}
              onFilePathChange={setFilePath}
              onOpen={openFile}
              onSave={saveFile}
              busyAction={busyAction}
            />
            <div className="editor-shell">
              <div className="line-numbers" aria-hidden="true">{Array.from({ length: 16 }, (_, index) => <span key={index}>{118 + index}</span>)}</div>
              <FileEditor fileContent={fileContent} onFileContentChange={setFileContent} />
            </div>
          </div>

          <div className="studio-card patch-preview">
            <div className="studio-card__header">
              <h2>PATCH PREVIEW <span>(Nova Proposal)</span></h2>
              <span>Unified Diff 1 / 3</span>
            </div>
            <pre>{`@@ -124,6 +124,10 @@ def apply_patch(plan: PatchPlan) -> PatchResult:
 # Nova: validate patch intent against lineage before applying
 lineage_ok = lineage.verify_intent(plan.intent, plan.target_file)
 if not lineage_ok:
     raise GovernanceError("lineage intent verification failed", plan.intent)`}</pre>
          </div>

          <div className="studio-card corridor-card">
            <div className="studio-card__header">
              <h2>NOVA REASONING CORRIDOR</h2>
              <span>{actionNotice}</span>
            </div>
            <div className="corridor-grid">
              {corridorPanels.map((panel) => (
                <article className="corridor-panel" key={panel.title}>
                  <h3>{panel.title}</h3>
                  {panel.rows.map((row, index) => (
                    <p key={row}><span>{row}</span>{index < 3 ? <FiCheck /> : <FiPause />}</p>
                  ))}
                  {panel.footer ? <strong>{panel.footer}</strong> : null}
                </article>
              ))}
            </div>
            <div className="action-console">
              <ActionButton icon={FiGitBranch} onClick={() => announceAction('Fix proposal queued')}>Propose Fix</ActionButton>
              <ActionButton icon={FiCode} onClick={() => announceAction('Test generation queued')}>Generate Tests</ActionButton>
              <ActionButton icon={FiShield} onClick={() => announceAction('Proof panel opened')}>Show Proof</ActionButton>
              <ActionButton icon={FiPlay} onClick={() => announceAction('Replay run requested')}>Run Replay</ActionButton>
              <ActionButton intent="accept" icon={FiCheck} onClick={() => announceAction('Patch accepted')}>Accept Patch</ActionButton>
              <ActionButton intent="danger" icon={FiRotateCcw} onClick={() => announceAction('Patch reverted')}>Revert</ActionButton>
            </div>
          </div>
        </section>

        <aside className="studio-right">
          <div className="studio-card ckce-card">
            <div className="studio-card__header">
              <h2>CKCE-1 ENFORCEMENT</h2>
              <span>Enforced</span>
            </div>
            <div className="ckce-stats">
              <p><strong>18 / 18</strong><span>Invariants</span></p>
              <p><strong>42</strong><span>Checks Run</span></p>
              <p><strong>0</strong><span>Violations</span></p>
              <p><strong className="amber">Strict</strong><span>Policy Mode</span></p>
            </div>
            <div className="enforced-callout">
              <FiShield aria-hidden="true" />
              <div>
                <strong>CKCE-1 ENFORCED</strong>
                <p>Step blocked: direct patch apply without lineage intent verification. Nova inserted required check.</p>
              </div>
            </div>
          </div>

          <WaveSignature />

          <div className="studio-card receipts-card">
            <div className="studio-card__header">
              <h2>CONTINUITY RECEIPTS</h2>
              <span>Live</span>
            </div>
            <ReceiptsPanel
              selectedEventId={selectedEventId}
              receipts={receipts.length ? receipts : liveEvents.slice(0, 4).map((event) => ({
                id: `receipt-${event.id}`,
                eventId: event.id,
                status: 'PASS',
                details: `${event.name} receipt`,
              }))}
              receiptStatus={receiptStatus}
              receiptDetails={receiptDetails}
              onReceiptStatusChange={setReceiptStatus}
              onReceiptDetailsChange={setReceiptDetails}
              onIssueReceipt={issueReceipt}
              busyAction={busyAction}
            />
          </div>

          <div className="studio-card specimen-card">
            <div className="studio-card__header">
              <h2>SPECIMEN EXPORT</h2>
              <span>Live</span>
            </div>
            <div className="specimen-grid">
              <article><span>Specimen #SC-9821</span><small>Patch intent verify</small></article>
              <article><span>Specimen #SC-9820</span><small>Rollback path test</small></article>
              <button type="button">Capture New Specimen</button>
            </div>
            <div className="specimen-actions">
              <button type="button">Export All</button>
              <button type="button">Compare</button>
              <button type="button">Package</button>
            </div>
          </div>
        </aside>
      </main>

      <footer className="studio-footer">
        <div className="studio-card event-log-card">
          <div className="studio-card__header">
            <h2>LIVE EVENT LOG</h2>
          </div>
          {liveEvents.slice(0, 4).map((event, index) => (
            <p key={event.id}><span className={`dot dot--${index}`}></span>{eventTime(event)} <strong>{event.name}</strong> {event.payload?.path || event.payload?.source || 'continuity event'}</p>
          ))}
        </div>
        <div className="studio-card replay-card">
          <div className="studio-card__header">
            <h2>REPLAY CONTROLS</h2>
            <span>Live</span>
          </div>
          <div className="replay-buttons">
            <button type="button"><FiSkipBack /></button>
            <button type="button"><FiPlay /></button>
            <button type="button"><FiSkipForward /></button>
            <button type="button"><FiRepeat /></button>
          </div>
          <div className="replay-track"><span></span><span></span><span></span><span></span><span></span></div>
        </div>
        <div className="studio-card summary-card">
          <div className="studio-card__header">
            <h2>SESSION SUMMARY</h2>
          </div>
          <div className="summary-grid">
            <p><span>Events</span><strong>{health.events}</strong></p>
            <p><span>Checks</span><strong>42</strong></p>
            <p><span>Receipts</span><strong>{health.receipts}</strong></p>
            <p><span>Specimens</span><strong>2</strong></p>
            <p><span>Coherence</span><strong>91%</strong></p>
            <p><span>Mode</span><strong className="amber">Strict</strong></p>
          </div>
        </div>
      </footer>
    </section>
  );
}
