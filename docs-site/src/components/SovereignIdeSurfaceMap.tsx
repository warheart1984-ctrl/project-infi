import React, { useEffect, useRef, useState } from 'react';

const DEFAULT_ULX_SOURCE = `@constitution {
    @article sovereignty {
        always: true;
        never: false;
    }
}

module constitutional_governance [sovereign] {
    fn validate_constitution() -> bool {
        return true;
    }
}
`;

const surfaces = [
  {
    key: 'timeline',
    title: 'Temporal Replay Timeline',
    subtitle: 'Epoch playback',
    backend: 'Sovereign Ledger Explorer v2',
    frontend: 'TimelineCanvas, EventNodes, ContinuitySyncIndicator',
    route: 'GET /api/timeline?epoch=<int>',
    tone: 'cyan',
  },
  {
    key: 'shader',
    title: 'Quantum Glyph Shader Engine',
    subtitle: 'Harmonic visual grammar',
    backend: 'Harmonic Engine constants',
    frontend: 'DynamicPulse, RotationalHarmony, GLSL shaders',
    route: 'POST /api/shader/update',
    tone: 'violet',
  },
  {
    key: 'monitor',
    title: 'Federated AI Organism Monitor',
    subtitle: 'Node vitality',
    backend: 'Telemetry Analyzer + AAES-OS metrics',
    frontend: 'MetricsPanel, Chart.js graphs, organism map',
    route: 'GET /api/organism/state',
    tone: 'emerald',
  },
  {
    key: 'consensus',
    title: 'Governance Consensus Map',
    subtitle: 'Promotion quorum',
    backend: 'Promotion v2.0 Protocol',
    frontend: 'Radial consensus graph, filters, outcomes',
    route: 'GET /api/consensus/votes',
    tone: 'amber',
  },
  {
    key: 'ledger',
    title: 'Sovereign Ledger Explorer v2',
    subtitle: 'Immutable proof blocks',
    backend: 'Proof Block Generator + Ledger Controller',
    frontend: '3D blockchain viewer, proof overlays',
    route: 'GET /api/ledger/blocks',
    tone: 'rose',
  },
  {
    key: 'mandala',
    title: 'Neural Mandala Composer',
    subtitle: 'Resonance synthesis',
    backend: 'Harmonic Engine pulse data',
    frontend: 'WebAudio + shader-driven mandala',
    route: 'POST /api/audio/pulse',
    tone: 'gold',
  },
  {
    key: 'ulx',
    title: 'ULX Workbench',
    subtitle: 'Compile, run, trace',
    backend: 'ULX core + governance bridge',
    frontend: 'ULX command cards and trace ledger',
    route: 'POST /api/ulx/compile',
    tone: 'cyan',
  },
] as const;

const controls = [
  'Focus timeline',
  'Focus shader',
  'Focus monitor',
  'Focus consensus',
  'Focus ledger',
  'Focus mandala',
  'Focus ULX',
  'Sync runtime refreshes node status and evidence',
];

const heroStatus = [
  { label: 'Node status', value: 'governed' },
  { label: 'Surfaces', value: '7 live views' },
  { label: 'Launcher', value: 'sovereign-ide' },
];

type SurfaceKey = (typeof surfaces)[number]['key'];
type LiveEndpointMap = Record<string, unknown>;

type UlxAction = 'compile' | 'run' | 'trace';

type UlxOutcome = {
  action: UlxAction;
  accepted: boolean;
  elapsedMs: number;
  sourceHash: string;
  traceId?: string;
  summary: string;
  error?: string;
};

type UlxSelection = {
  start: number;
  end: number;
  text: string;
};

type UlxEvidenceReceipt = {
  receiptId: string;
  replayId: string;
  sourceHash: string;
  selectionHash: string;
  verificationStatus: string;
  evidenceStatus: string;
  issuedAt: string;
  replayable: boolean;
  proof: Record<string, unknown>;
};

type UlxSnapshot = {
  surface?: Record<string, unknown>;
  origin: string;
  revision: number;
  updatedAt: string;
  source: string;
  sourceHash: string;
  selection: UlxSelection;
  selectionText: string;
  evidenceReceipt?: UlxEvidenceReceipt | null;
  receiptId?: string;
  replayId?: string;
  verificationStatus?: string;
};

type LiveRuntimeState = {
  apiBaseUrl: string;
  connected: boolean;
  error: string | null;
  health: Record<string, unknown> | null;
  endpoints: LiveEndpointMap;
};

const defaultLiveRuntimeState: LiveRuntimeState = {
  apiBaseUrl: resolveApiBaseUrl(),
  connected: false,
  error: null,
  health: null,
  endpoints: {},
};

function resolveApiBaseUrl() {
  if (typeof window !== 'undefined') {
    const globalWindow = window as Window & {
      __SOVEREIGN_IDE_API_BASE_URL__?: string;
    };
    if (globalWindow.__SOVEREIGN_IDE_API_BASE_URL__) {
      return globalWindow.__SOVEREIGN_IDE_API_BASE_URL__;
    }

    const meta = document.querySelector('meta[name="sovereign-ide-api-base-url"]') as HTMLMetaElement | null;
    if (meta?.content) {
      return meta.content;
    }
  }

  if (typeof process !== 'undefined' && process.env?.SOVEREIGN_IDE_API_BASE_URL) {
    return process.env.SOVEREIGN_IDE_API_BASE_URL;
  }

  return 'http://127.0.0.1:8787';
}

function renderSurfaceVisual(
  surface: (typeof surfaces)[number],
  live: LiveRuntimeState,
  ulxUi: {
    source: string;
    busy: UlxAction | null;
    outcome: UlxOutcome | null;
    error: string | null;
    selection: UlxSelection;
    snapshot: UlxSnapshot | null;
    sourceRef: React.RefObject<HTMLTextAreaElement | null>;
    setSource: (value: string) => void;
    runAction: (action: UlxAction) => void;
    syncSelection: () => void;
    syncSnapshot: (origin?: string) => void;
  } | null,
) {
  switch (surface.key) {
    case 'timeline': {
      const timeline = live.endpoints.timeline as Record<string, unknown> | undefined;
      const liveReplay = typeof timeline?.replay_mode === 'string' ? timeline.replay_mode : 'governed';
      const liveContinuity = typeof timeline?.continuity_sync === 'string' ? timeline.continuity_sync : 'pending';
      return (
        <div className="sovereign-ide-doc__visual sovereign-ide-doc__visual--timeline">
          <div className="sovereign-ide-doc__rail">
            {['Epoch 014', 'Epoch 015', 'Epoch 016', 'Epoch 017'].map((label, index) => (
              <span key={label} className={`sovereign-ide-doc__rail-segment sovereign-ide-doc__rail-segment--${index + 1}`}>
                {label}
              </span>
            ))}
          </div>
          <div className="sovereign-ide-doc__meter-group">
            <div className="sovereign-ide-doc__meter sovereign-ide-doc__meter--small">
              <span>Replay</span>
              <strong>{String(liveReplay)}</strong>
            </div>
            <div className="sovereign-ide-doc__meter sovereign-ide-doc__meter--wide">
              <span>Continuity</span>
              <strong>{String(liveContinuity)}</strong>
            </div>
          </div>
        </div>
      );
    }
    case 'shader': {
      const shader = live.endpoints.shader as Record<string, unknown> | undefined;
      const params = (shader?.parameters as Record<string, unknown> | undefined) ?? {};
      const glow = shader?.render_state as Record<string, unknown> | undefined;
      return (
        <div className="sovereign-ide-doc__visual sovereign-ide-doc__visual--shader">
          <div className="sovereign-ide-doc__shader-preview">
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="sovereign-ide-doc__chip-row">
            <span>Density: {String(params.density ?? 'medium')}</span>
            <span>Rotation: {String(params.rotation ?? 'stable')}</span>
            <span>Glow: {String(glow?.glow_intensity ?? 'low')}</span>
          </div>
        </div>
      );
    }
    case 'monitor': {
      const organism = live.endpoints.organism as Record<string, unknown> | undefined;
      const telemetry = (organism?.telemetry as Record<string, unknown> | undefined) ?? {};
      const lineage = (organism?.lineage as Record<string, unknown> | undefined) ?? {};
      return (
        <div className="sovereign-ide-doc__visual sovereign-ide-doc__visual--monitor">
          <div className="sovereign-ide-doc__stat-grid">
            <div>
              <span>Codex base</span>
              <strong>{String(organism?.codex_base ?? 'sovereign')}</strong>
            </div>
            <div>
              <span>Federation</span>
              <strong>{String(telemetry.status ?? 'bootstrapped')}</strong>
            </div>
            <div>
              <span>Telemetry</span>
              <strong>{String(telemetry.mode ?? 'summary')}</strong>
            </div>
            <div>
              <span>Vitality</span>
              <strong>{String(organism?.node_vitality ?? '88%')}</strong>
            </div>
          </div>
          <div className="sovereign-ide-doc__progress">
            <div className="sovereign-ide-doc__progress-fill sovereign-ide-doc__progress-fill--emerald" />
          </div>
          <div className="sovereign-ide-doc__chip-row sovereign-ide-doc__chip-row--wrap">
            <span>Specs: {String((lineage.spec_families as unknown[] | undefined)?.length ?? 0)}</span>
            <span>Conformance: {String((lineage.conformance_families as unknown[] | undefined)?.length ?? 0)}</span>
          </div>
        </div>
      );
    }
    case 'consensus': {
      const consensus = live.endpoints.consensus as Record<string, unknown> | undefined;
      const votes = (consensus?.votes as Record<string, unknown> | undefined) ?? {};
      return (
        <div className="sovereign-ide-doc__visual sovereign-ide-doc__visual--consensus">
          <div className="sovereign-ide-doc__ring">
            <span>Quorum</span>
            <strong>{String(consensus?.quorum ?? 'reached')}</strong>
          </div>
          <div className="sovereign-ide-doc__vote-stack">
            <div className="sovereign-ide-doc__vote-row"><span>Favor</span><strong>{String(votes.favor ?? 14)}</strong></div>
            <div className="sovereign-ide-doc__vote-row"><span>Pending</span><strong>{String(votes.pending ?? 3)}</strong></div>
          </div>
        </div>
      );
    }
    case 'ledger': {
      const ledger = live.endpoints.ledger as Record<string, unknown> | undefined;
      const blocks = Array.isArray(ledger?.proof_blocks) ? ledger.proof_blocks as Array<Record<string, unknown>> : [];
      const visibleBlocks = blocks.length ? blocks : [
        { label: 'Receipt 031' },
        { label: 'Receipt 032' },
        { label: 'Receipt 033' },
      ];
      return (
        <div className="sovereign-ide-doc__visual sovereign-ide-doc__visual--ledger">
          {visibleBlocks.slice(0, 3).map((block, index) => (
            <div key={String(block.label ?? index)} className="sovereign-ide-doc__receipt">
              <span>{String(block.label ?? `Receipt 03${index + 1}`)}</span>
              <strong>Visible proof chain</strong>
            </div>
          ))}
        </div>
      );
    }
    case 'mandala': {
      const pulse = live.endpoints.audio as Record<string, unknown> | undefined;
      const soundscape = (pulse?.soundscape as Record<string, unknown> | undefined) ?? {};
      return (
        <div className="sovereign-ide-doc__visual sovereign-ide-doc__visual--mandala">
          <div className="sovereign-ide-doc__orb">
            <span />
            <strong>Mandala</strong>
          </div>
          <div className="sovereign-ide-doc__chip-row sovereign-ide-doc__chip-row--wrap">
            <span>Waveform: {String(soundscape.waveform ?? 'sine')}</span>
            <span>Resonance: {String(soundscape.resonance ?? '0.72')}</span>
            <span>Pulse: {String(soundscape.pulse_frequency ?? '1.5')}</span>
          </div>
        </div>
      );
    }
    case 'ulx': {
      const ulx = live.endpoints.ulx as Record<string, unknown> | undefined;
      const bridge = (ulx?.bridge as Record<string, unknown> | undefined) ?? {};
      const compile = (bridge.compile as Record<string, unknown> | undefined) ?? {};
      const run = (bridge.run as Record<string, unknown> | undefined) ?? {};
      const trace = (bridge.trace as Record<string, unknown> | undefined) ?? {};
      const links = (trace.links as Record<string, unknown> | undefined) ?? {};
      const audit = (trace.audit as Record<string, unknown> | undefined) ?? {};
      const source = ulxUi?.source ?? DEFAULT_ULX_SOURCE;
      const selection = ulxUi?.selection ?? { start: 0, end: 0, text: '' };
      const snapshot = ulxUi?.snapshot ?? null;
      const receipt = snapshot?.evidenceReceipt ?? null;
      return (
        <div className="sovereign-ide-doc__visual sovereign-ide-doc__visual--ulx">
          <div className="sovereign-ide-doc__stat-grid">
            <div>
              <span>Source hash</span>
              <strong>{String(bridge.source_hash ?? 'pending')}</strong>
            </div>
            <div>
              <span>Commands</span>
              <strong>{Array.isArray(bridge.commands) ? bridge.commands.join(', ') : 'compile, run, trace'}</strong>
            </div>
            <div>
              <span>Compile</span>
              <strong>{String(compile.command ?? 'idle')}</strong>
            </div>
            <div>
              <span>Trace</span>
              <strong>{String(trace.traceId ?? 'pending')}</strong>
            </div>
          </div>
          <div className="sovereign-ide-doc__ulx-snapshot">
            <span>Shared snapshot</span>
            <strong>{snapshot ? `rev ${snapshot.revision} from ${snapshot.origin}` : 'pending'}</strong>
            <small>{snapshot ? `${snapshot.selectionText ? 'selection mirrored' : 'full draft mirrored'} | receipt ${snapshot.receiptId || receipt?.receiptId || 'pending'} | replay ${snapshot.replayId || receipt?.replayId || 'pending'} | status ${snapshot.verificationStatus || receipt?.verificationStatus || 'pending'}` : 'waiting for a live source snapshot'}</small>
          </div>
          <div className="sovereign-ide-doc__ulx-editor">
            <div className="sovereign-ide-doc__panel-label">ULX source editor</div>
            <textarea
              ref={ulxUi?.sourceRef ?? undefined}
              className="sovereign-ide-doc__ulx-textarea"
              value={source}
              spellCheck={false}
              aria-label="ULX source editor"
              onChange={(event) => ulxUi?.setSource(event.target.value)}
              onMouseUp={ulxUi?.syncSelection}
              onKeyUp={ulxUi?.syncSelection}
              onSelect={ulxUi?.syncSelection}
              onFocus={ulxUi?.syncSelection}
            />
            <div className="sovereign-ide-doc__ulx-note">
              Select text to compile, run, or trace just that fragment. If nothing is selected, the full draft is used.
            </div>
            <div className="sovereign-ide-doc__ulx-selection">
              <span>Selection range: {selection.end > selection.start ? `${selection.start}-${selection.end}` : 'none'}</span>
              <span>Selection text: {selection.text ? selection.text : 'full draft'}</span>
            </div>
            <div className="sovereign-ide-doc__ulx-actions">
              <button type="button" onClick={() => ulxUi?.runAction('compile')} disabled={ulxUi?.busy === 'compile'}>
                {ulxUi?.busy === 'compile' ? 'Compiling...' : 'Compile selected text'}
              </button>
              <button type="button" onClick={() => ulxUi?.runAction('run')} disabled={ulxUi?.busy === 'run'}>
                {ulxUi?.busy === 'run' ? 'Running...' : 'Run selected text'}
              </button>
              <button type="button" onClick={() => ulxUi?.runAction('trace')} disabled={ulxUi?.busy === 'trace'}>
                {ulxUi?.busy === 'trace' ? 'Tracing...' : 'Trace selected text'}
              </button>
            </div>
            {ulxUi?.outcome ? (
              <div className={`sovereign-ide-doc__ulx-outcome${ulxUi.outcome.error ? ' sovereign-ide-doc__ulx-outcome--error' : ''}`}>
                <strong>{ulxUi.outcome.action.toUpperCase()} {ulxUi.outcome.accepted ? 'accepted' : 'failed'}</strong>
                <span>{ulxUi.outcome.summary}</span>
                <span>Source hash: {ulxUi.outcome.sourceHash}</span>
                {ulxUi.outcome.traceId ? <span>Trace ID: {ulxUi.outcome.traceId}</span> : null}
                <span>Elapsed: {ulxUi.outcome.elapsedMs} ms</span>
              </div>
            ) : (
              <div className="sovereign-ide-doc__ulx-empty">No ULX action has been executed yet.</div>
            )}
            {ulxUi?.error ? <div className="sovereign-ide-doc__ulx-error">{ulxUi.error}</div> : null}
          </div>
          <div className="sovereign-ide-doc__chip-row sovereign-ide-doc__chip-row--wrap">
            <span>Run: {String(run.command ?? 'idle')}</span>
            <span>Links: {String(Array.isArray(links.forward) ? links.forward.length : 0)}</span>
            <span>Audit: {String(audit.chain_valid ? 'valid' : 'pending')}</span>
          </div>
        </div>
      );
    }
    default:
      return null;
  }
}

function endpointUrl(baseUrl: string, path: string) {
  return new URL(path, baseUrl).toString();
}

async function readJson(baseUrl: string, path: string, init?: RequestInit) {
  const response = await fetch(endpointUrl(baseUrl, path), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json();
}

export function SovereignIdeSurfaceMap() {
  const [live, setLive] = useState<LiveRuntimeState>(defaultLiveRuntimeState);
  const [ulxSource, setUlxSource] = useState(DEFAULT_ULX_SOURCE);
  const [ulxBusy, setUlxBusy] = useState<UlxAction | null>(null);
  const [ulxOutcome, setUlxOutcome] = useState<UlxOutcome | null>(null);
  const [ulxError, setUlxError] = useState<string | null>(null);
  const [ulxSelection, setUlxSelection] = useState<UlxSelection>({ start: 0, end: 0, text: '' });
  const [ulxSnapshot, setUlxSnapshot] = useState<UlxSnapshot | null>(null);
  const ulxSourceRef = useRef<HTMLTextAreaElement | null>(null);
  const ulxSnapshotRevisionRef = useRef(0);
  const ulxSnapshotTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const baseUrl = defaultLiveRuntimeState.apiBaseUrl;

    const hydrate = async () => {
      try {
        const health = await readJson(baseUrl, '/health', { signal: controller.signal });
        const [timeline, shader, organism, consensus, ledger, audio, ulx] = await Promise.all([
          readJson(baseUrl, '/api/timeline?epoch=17', { signal: controller.signal }),
          readJson(baseUrl, '/api/shader/update', {
            method: 'POST',
            body: JSON.stringify({ resonance: 0.78, pulse_frequency: 1.5 }),
            signal: controller.signal,
          }),
          readJson(baseUrl, '/api/organism/state', { signal: controller.signal }),
          readJson(baseUrl, '/api/consensus/votes', { signal: controller.signal }),
          readJson(baseUrl, '/api/ledger/blocks', { signal: controller.signal }),
          readJson(baseUrl, '/api/audio/pulse', {
            method: 'POST',
            body: JSON.stringify({ waveform: 'sine' }),
            signal: controller.signal,
          }),
          readJson(baseUrl, '/api/ulx/manifest', { signal: controller.signal }),
        ]);

        setLive({
          apiBaseUrl: baseUrl,
          connected: true,
          error: null,
          health,
          endpoints: { timeline, shader, organism, consensus, ledger, audio, ulx },
        });
        applyUlxSnapshot(ulx?.snapshot ?? ulx, { persist: false });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setLive((current) => ({
          ...current,
          apiBaseUrl: baseUrl,
          connected: false,
          error: error instanceof Error ? error.message : 'Unable to connect to the live Sovereign IDE API',
        }));
      }
    };

    void hydrate();

    return () => {
      controller.abort();
    };
  }, []);

  useEffect(() => {
    const baseUrl = live.apiBaseUrl || defaultLiveRuntimeState.apiBaseUrl;
    let cancelled = false;
    const pollSnapshot = async () => {
      try {
        const snapshot = await readJson(baseUrl, '/api/ulx/snapshot');
        if (!cancelled) {
          applyUlxSnapshot(snapshot, { persist: false });
        }
      } catch {
        // Keep the local draft available when the shared snapshot endpoint is unavailable.
      }
    };
    void pollSnapshot();
    ulxSnapshotTimerRef.current = window.setInterval(() => {
      void pollSnapshot();
    }, 1000);
    return () => {
      cancelled = true;
      if (ulxSnapshotTimerRef.current !== null) {
        window.clearInterval(ulxSnapshotTimerRef.current);
        ulxSnapshotTimerRef.current = null;
      }
    };
  }, [live.apiBaseUrl]);

  const readUlxSource = () => {
    const textarea = ulxSourceRef.current;
    const value = textarea?.value ?? ulxSource;
    if (!textarea || typeof textarea.selectionStart !== 'number' || typeof textarea.selectionEnd !== 'number') {
      return value.trim() || DEFAULT_ULX_SOURCE;
    }
    const selected = textarea.selectionEnd > textarea.selectionStart ? value.slice(textarea.selectionStart, textarea.selectionEnd) : '';
    return selected.trim() ? selected : value.trim() || DEFAULT_ULX_SOURCE;
  };

  const syncUlxSelection = () => {
    const textarea = ulxSourceRef.current;
    if (!textarea) {
      return;
    }
    const value = textarea.value ?? '';
    const start = typeof textarea.selectionStart === 'number' ? textarea.selectionStart : 0;
    const end = typeof textarea.selectionEnd === 'number' ? textarea.selectionEnd : 0;
    const text = end > start ? value.slice(start, end) : '';
    setUlxSelection({
      start,
      end,
      text,
    });
    void pushUlxSnapshot('docs-selection');
  };

  const normalizeUlxSelection = (value: unknown, fallbackSource: string): UlxSelection => {
    const selection = value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
    const start = Number.isFinite(Number(selection.start)) ? Math.max(0, Number(selection.start)) : 0;
    const end = Number.isFinite(Number(selection.end)) ? Math.max(0, Number(selection.end)) : 0;
    const text = String(selection.text ?? '');
    const source = String(fallbackSource ?? '');
    return {
      start,
      end: end < start ? start : end,
      text: text || (end > start ? source.slice(start, end) : ''),
    };
  };

  const normalizeUlxSnapshot = (value: unknown): UlxSnapshot | null => {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const snapshot = value as Record<string, unknown>;
    const source = String(snapshot.source ?? '');
    const selection = normalizeUlxSelection(snapshot.selection, source);
    const evidenceReceipt = snapshot.evidenceReceipt && typeof snapshot.evidenceReceipt === 'object'
      ? (snapshot.evidenceReceipt as Record<string, unknown>)
      : null;
    return {
      surface: snapshot.surface && typeof snapshot.surface === 'object' ? (snapshot.surface as Record<string, unknown>) : undefined,
      origin: String(snapshot.origin ?? 'unknown'),
      revision: Number.isFinite(Number(snapshot.revision)) ? Number(snapshot.revision) : 0,
      updatedAt: String(snapshot.updatedAt ?? ''),
      source,
      sourceHash: String(snapshot.sourceHash ?? ''),
      selection,
      selectionText: String(snapshot.selectionText ?? selection.text ?? ''),
      evidenceReceipt: evidenceReceipt
        ? {
            receiptId: String(evidenceReceipt.receiptId ?? snapshot.receiptId ?? ''),
            replayId: String(evidenceReceipt.replayId ?? snapshot.replayId ?? ''),
            sourceHash: String(evidenceReceipt.sourceHash ?? snapshot.sourceHash ?? source),
            selectionHash: String(evidenceReceipt.selectionHash ?? ''),
            verificationStatus: String(evidenceReceipt.verificationStatus ?? snapshot.verificationStatus ?? 'pending'),
            evidenceStatus: String(evidenceReceipt.evidenceStatus ?? 'linked'),
            issuedAt: String(evidenceReceipt.issuedAt ?? snapshot.updatedAt ?? ''),
            replayable: Boolean(evidenceReceipt.replayable ?? true),
            proof: (evidenceReceipt.proof as Record<string, unknown>) ?? {},
          }
        : null,
      receiptId: String(snapshot.receiptId ?? evidenceReceipt?.receiptId ?? ''),
      replayId: String(snapshot.replayId ?? evidenceReceipt?.replayId ?? ''),
      verificationStatus: String(snapshot.verificationStatus ?? evidenceReceipt?.verificationStatus ?? 'pending'),
    };
  };

  const applyUlxSnapshot = (value: unknown, options: { persist?: boolean } = {}) => {
    const snapshot = normalizeUlxSnapshot(value);
    if (!snapshot) {
      return null;
    }
    if (snapshot.revision < ulxSnapshotRevisionRef.current) {
      return snapshot;
    }
    ulxSnapshotRevisionRef.current = snapshot.revision;
    setUlxSnapshot(snapshot);
    setUlxSource(snapshot.source || DEFAULT_ULX_SOURCE);
    setUlxSelection(snapshot.selection);
    if (options.persist !== false) {
      const textarea = ulxSourceRef.current;
      if (textarea && document.activeElement !== textarea) {
        textarea.value = snapshot.source || DEFAULT_ULX_SOURCE;
      }
    }
    return snapshot;
  };

  const pushUlxSnapshot = async (origin: string) => {
    const baseUrl = live.apiBaseUrl || defaultLiveRuntimeState.apiBaseUrl;
    const textarea = ulxSourceRef.current;
    const source = textarea?.value ?? ulxSource;
    const selection = textarea
      ? {
          start: typeof textarea.selectionStart === 'number' ? textarea.selectionStart : ulxSelection.start,
          end: typeof textarea.selectionEnd === 'number' ? textarea.selectionEnd : ulxSelection.end,
          text: typeof textarea.selectionStart === 'number' && typeof textarea.selectionEnd === 'number' && textarea.selectionEnd > textarea.selectionStart
            ? source.slice(textarea.selectionStart, textarea.selectionEnd)
            : ulxSelection.text,
        }
      : ulxSelection;
    try {
      const snapshot = await readJson(baseUrl, '/api/ulx/snapshot', {
        method: 'POST',
        body: JSON.stringify({
          origin,
          source,
          selection,
          selectionText: selection.text,
        }),
      });
      applyUlxSnapshot(snapshot, { persist: false });
      return snapshot;
    } catch {
      return null;
    }
  };

  const summarizeUlxResult = (action: UlxAction, payload: Record<string, unknown>) => {
    if (action === 'compile') {
      const summary = payload.bytecode_summary as Record<string, unknown> | undefined;
      const functions = Array.isArray(summary?.functions) ? summary?.functions.join(', ') : 'none';
      return `Functions: ${functions}; constitution: ${summary?.has_constitution ? 'yes' : 'no'}`;
    }
    if (action === 'run') {
      return `Result: ${String(payload.result ?? 'pending')}`;
    }
    const links = (payload.links as { forward?: unknown[] } | undefined)?.forward;
    const audit = payload.audit as { chain_valid?: boolean } | undefined;
    return `Trace ID: ${String(payload.traceId ?? 'pending')}; links: ${Array.isArray(links) ? links.length : 0}; audit: ${audit?.chain_valid ? 'valid' : 'pending'}`;
  };

  const runUlxAction = async (action: UlxAction) => {
    const baseUrl = live.apiBaseUrl || defaultLiveRuntimeState.apiBaseUrl;
    const source = readUlxSource();
    setUlxBusy(action);
    setUlxError(null);
    const started = performance.now();
    try {
      await pushUlxSnapshot(`docs-${action}`);
      const result = await readJson(baseUrl, `/api/ulx/${action}`, {
        method: 'POST',
        body: JSON.stringify({ source }),
      });
      setUlxOutcome({
        action,
        accepted: result.accepted !== false,
        elapsedMs: Math.round(performance.now() - started),
        sourceHash: String(result.source_hash ?? 'pending'),
        traceId: typeof result.traceId === 'string' ? result.traceId : undefined,
        summary: summarizeUlxResult(action, result as Record<string, unknown>),
      });
      setUlxSource(source);
    } catch (error) {
      setUlxOutcome({
        action,
        accepted: false,
        elapsedMs: Math.round(performance.now() - started),
        sourceHash: 'pending',
        summary: 'ULX action failed',
        error: error instanceof Error ? error.message : String(error),
      });
      setUlxError(error instanceof Error ? error.message : String(error));
    } finally {
      setUlxBusy(null);
    }
  };

  const ulxUi = {
    source: ulxSource,
    busy: ulxBusy,
    outcome: ulxOutcome,
    error: ulxError,
    selection: ulxSelection,
    snapshot: ulxSnapshot,
    sourceRef: ulxSourceRef,
    setSource: (value: string) => {
      setUlxSource(value);
      void pushUlxSnapshot('docs-input');
    },
    runAction: runUlxAction,
    syncSelection: syncUlxSelection,
    syncSnapshot: pushUlxSnapshot,
  };

  const activeHeroStatus = [
    heroStatus[0],
    { label: 'Surfaces', value: live.connected ? '7 live views' : 'static fallback' },
    { label: 'Launcher', value: live.apiBaseUrl },
  ];

  const liveSummary = live.health as Record<string, unknown> | null;

  return (
    <section className="sovereign-ide-doc">
      <div className="sovereign-ide-doc__hero">
        <div className="sovereign-ide-doc__hero-copy">
          <div className="sovereign-ide-doc__eyebrow">Sovereign IDE</div>
          <h2 className="sovereign-ide-doc__title">Workspace shell for the seven governed surfaces</h2>
          <p className="sovereign-ide-doc__lead">
            This page now hydrates from the live `sovereign-ide` API server when it is available, so the docs cockpit
            and the desktop shell read from the same runtime contract.
          </p>
          <div className="sovereign-ide-doc__hero-status">
            {activeHeroStatus.map((item) => (
              <div key={item.label} className="sovereign-ide-doc__hero-status-item">
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
          <div className={`sovereign-ide-doc__live-badge${live.connected ? ' sovereign-ide-doc__live-badge--online' : ''}`}>
            <span>{live.connected ? 'Live API connected' : 'Live API offline'}</span>
            <strong>{live.apiBaseUrl}</strong>
          </div>
          {live.error ? <p className="sovereign-ide-doc__live-error">{live.error}</p> : null}
          {liveSummary ? (
            <dl className="sovereign-ide-doc__live-summary">
              <div>
                <dt>Boot</dt>
                <dd>{String(liveSummary.app_name ?? 'Sovereign IDE')}</dd>
              </div>
              <div>
                <dt>Launcher</dt>
                <dd>{String(liveSummary.launcher_command ?? 'sovereign-ide')}</dd>
              </div>
              <div>
                <dt>Surfaces</dt>
                <dd>{Array.isArray(liveSummary.surfaces) ? liveSummary.surfaces.length : 0}</dd>
              </div>
            </dl>
          ) : null}
        </div>
        <div className="sovereign-ide-doc__hero-controls">
          <span className="sovereign-ide-doc__hero-controls-item sovereign-ide-doc__hero-controls-item--active">
            Focus timeline
          </span>
          <span className="sovereign-ide-doc__hero-controls-item">Focus shader</span>
          <span className="sovereign-ide-doc__hero-controls-item">Focus monitor</span>
          <span className="sovereign-ide-doc__hero-controls-item">Focus consensus</span>
          <span className="sovereign-ide-doc__hero-controls-item">Focus ledger</span>
          <span className="sovereign-ide-doc__hero-controls-item sovereign-ide-doc__hero-controls-item--active">
            Focus ULX
          </span>
          <span className="sovereign-ide-doc__hero-controls-item sovereign-ide-doc__hero-controls-item--active">
            Sync runtime
          </span>
        </div>
      </div>

      <div className="sovereign-ide-doc__grid">
        {surfaces.map((surface, index) => (
          <article key={surface.key} className={`sovereign-ide-doc__card sovereign-ide-doc__card--${surface.tone}`}>
            <div className="sovereign-ide-doc__card-header">
              <div>
                <div className="sovereign-ide-doc__surface-type">{surface.subtitle}</div>
                <h3>{surface.title}</h3>
              </div>
              <div className="sovereign-ide-doc__surface-index">0{index + 1}</div>
            </div>
            {renderSurfaceVisual(surface, live, surface.key === 'ulx' ? ulxUi : null)}
            <dl className="sovereign-ide-doc__meta">
              <div>
                <dt>Backend</dt>
                <dd>{surface.backend}</dd>
              </div>
              <div>
                <dt>Frontend</dt>
                <dd>{surface.frontend}</dd>
              </div>
              <div>
                <dt>Route</dt>
                <dd>{surface.route}</dd>
              </div>
              <div>
                <dt>Live</dt>
                <dd>{live.connected ? 'Connected' : 'Static fallback'}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>

      <div className="sovereign-ide-doc__footer">
        <section className="sovereign-ide-doc__panel">
          <h3>Shared controls</h3>
          <ul>
            {controls.map((control) => (
              <li key={control}>{control}</li>
            ))}
          </ul>
        </section>
        <section className="sovereign-ide-doc__panel">
          <h3>Canonical contract</h3>
          <p>
            The docs page mirrors the live shell contract: node status, seven surface cards, API hooks, roadmap,
            launcher commands, source editor wiring, and environment requirements.
          </p>
        </section>
        <section className="sovereign-ide-doc__panel">
          <h3>Live surface</h3>
          <p>
            The visualizer hydrates from the running API server when `SOVEREIGN_IDE_API_BASE_URL` is set, or it falls
            back to `http://127.0.0.1:8787` for local development.
          </p>
        </section>
      </div>
    </section>
  );
}
