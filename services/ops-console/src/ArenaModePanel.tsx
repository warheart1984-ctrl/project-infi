import { useMemo, useState } from 'react';

import type {
  ArenaBattleScar,
  ArenaLifecyclePhase,
  ArenaReadinessCertificate,
  ArenaScorecard,
  ArenaSnapshot,
  ArenaTrace,
  TournamentMatch,
} from './arenaMode.js';

type ArenaTab = 'challenge' | 'scorecard' | 'lifecycle' | 'certificate' | 'map' | 'talents' | 'tournament' | 'replay';

const TAB_LABELS: Array<{ id: ArenaTab; label: string }> = [
  { id: 'challenge', label: 'Challenge' },
  { id: 'scorecard', label: 'Scorecard' },
  { id: 'lifecycle', label: 'Lifecycle' },
  { id: 'certificate', label: 'Certificate' },
  { id: 'map', label: 'Map' },
  { id: 'talents', label: 'Talents' },
  { id: 'tournament', label: 'Tournament' },
  { id: 'replay', label: 'Replay Timeline' },
];

const TERRAIN_PALETTE: Record<string, { background: string; color: string; border: string }> = {
  'Trust Bastion': { background: '#e8fff4', color: '#0f766e', border: '#9ae6b4' },
  'Evidence Floodplain': { background: '#fff4e8', color: '#9a3412', border: '#fdba74' },
  'Disputed Edge': { background: '#fdf2f8', color: '#be185d', border: '#f9a8d4' },
  'Invariant Ridge': { background: '#eef2ff', color: '#4338ca', border: '#c7d2fe' },
  'Relay Spine': { background: '#f0f9ff', color: '#0369a1', border: '#bae6fd' },
};

const FACTION_PALETTE: Record<string, { background: string; color: string; border: string }> = {
  Protoss: { background: '#eef2ff', color: '#3730a3', border: '#c7d2fe' },
  Zerg: { background: '#ecfdf5', color: '#047857', border: '#a7f3d0' },
  Terran: { background: '#fff7ed', color: '#9a3412', border: '#fed7aa' },
};

const STATUS_PALETTE: Record<string, { background: string; color: string; border: string }> = {
  PASS: { background: '#ecfdf5', color: '#047857', border: '#a7f3d0' },
  WARN: { background: '#fffbeb', color: '#b45309', border: '#fcd34d' },
  FAIL: { background: '#fef2f2', color: '#b91c1c', border: '#fecaca' },
  INFO: { background: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' },
};

export function ArenaModePanel({ arena }: { arena: ArenaSnapshot }) {
  const [activeTab, setActiveTab] = useState<ArenaTab>('challenge');
  const firstReplayMatch = useMemo(() => findFirstReplayMatch(arena.tournament.rounds), [arena.tournament.rounds]);
  const [selectedMatchId, setSelectedMatchId] = useState<string | null>(firstReplayMatch?.matchId ?? null);
  const [selectedChallengeRunId, setSelectedChallengeRunId] = useState<string | null>(arena.challengeRuns[0]?.runId ?? null);

  const selectedMatch = selectedMatchId ? findMatch(arena.tournament.rounds, selectedMatchId) : firstReplayMatch;
  const selectedTrace = selectedMatch?.matchId ? arena.traces[selectedMatch.matchId] : undefined;
  const selectedReport = selectedMatch?.matchId ? arena.replayReports[selectedMatch.matchId] : undefined;
  const selectedChallengeRun = selectedChallengeRunId
    ? arena.challengeRuns.find((run) => run.runId === selectedChallengeRunId) ?? arena.challengeRuns[0]
    : arena.challengeRuns[0];
  const selectedChallengePack = selectedChallengeRun
    ? arena.challengePacks.find((pack) => pack.scenarioIds.includes(selectedChallengeRun.scenarioId)) ?? arena.challengePacks[0]
    : arena.challengePacks[0];

  const openReplay = (match: TournamentMatch) => {
    if (!match.traceId) {
      return;
    }
    setSelectedMatchId(match.matchId);
    setActiveTab('replay');
  };

  const downloadTrace = (trace: ArenaTrace | undefined) => {
    if (!trace) {
      return;
    }
    const blob = new Blob([JSON.stringify(trace, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${trace.traceId}.cnode-trace`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section id="arena" style={sectionStyle}>
      <div style={headerRowStyle}>
        <div>
          <h2 style={{ margin: 0 }}>Arena Mode</h2>
          <p style={{ margin: '6px 0 0', color: '#5f6b7a' }}>
            Constitutional proving ground for runtime, agent, governance, replay, and certification flows.
          </p>
        </div>
        <div style={summaryPillStyle}>{arena.title}</div>
      </div>

      <div style={metricGridStyle}>
        <Metric label="Arena" value={arena.arenaId} />
        <Metric label="Map" value={`${arena.map.width} x ${arena.map.height}`} />
        <Metric label="Agents" value={String(arena.agents.length)} />
        <Metric label="Challenges" value={String(arena.challengeRuns.length)} />
        <Metric label="Proof level" value={arena.scorecard.proofLevel} />
        <Metric label="Readiness" value={arena.scorecard.readinessLevel} />
      </div>

      <div style={tabRowStyle}>
        {TAB_LABELS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            style={{
              ...tabButtonStyle,
              ...(activeTab === tab.id ? tabButtonActiveStyle : null),
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'challenge' ? (
        <div style={twoColumnStyle}>
          <Panel title="Challenge Packs">
            <div style={cardStackStyle}>
              {arena.challengePacks.map((pack) => (
                <button
                  key={pack.packId}
                  type="button"
                  onClick={() => {
                    const nextRun = arena.challengeRuns.find((run) => pack.scenarioIds.includes(run.scenarioId));
                    if (nextRun) {
                      setSelectedChallengeRunId(nextRun.runId);
                    }
                  }}
                  style={{
                    ...listButtonStyle,
                    ...(selectedChallengePack?.packId === pack.packId ? listButtonActiveStyle : null),
                  }}
                >
                  <div style={rowSpreadStyle}>
                    <strong>{pack.name}</strong>
                    <span style={badgeStyle}>pack</span>
                  </div>
                  <div style={copyStyle}>{pack.description}</div>
                  <div style={mutedLineStyle}>{pack.scenarioIds.length} challenge scenarios</div>
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="Challenge Runs">
            <div style={cardStackStyle}>
              {arena.challengeRuns.map((run) => (
                <button
                  key={run.runId}
                  type="button"
                  onClick={() => setSelectedChallengeRunId(run.runId)}
                  style={{
                    ...listButtonStyle,
                    ...(selectedChallengeRun?.runId === run.runId ? listButtonActiveStyle : null),
                  }}
                >
                  <div style={rowSpreadStyle}>
                    <strong>{run.scenarioName}</strong>
                    <span style={{ ...badgeStyle, ...statusPalette(run.status) }}>{run.status}</span>
                  </div>
                  <div style={mutedLineStyle}>{run.focus} focus, {run.severity} severity</div>
                  <div style={metricChipsStyle}>
                    <span>Proof {run.proofLevel}</span>
                    <span>Maturity {run.constitutionalMaturity.toFixed(1)}</span>
                    <span>Replay {run.replaySuccess ? 'yes' : 'no'}</span>
                    <span>Pass {run.challengePassRate.toFixed(1)}%</span>
                  </div>
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="Challenge Detail">
            {selectedChallengeRun ? (
              <div style={{ display: 'grid', gap: 12 }}>
                <div style={metricGridStyle}>
                  <Metric label="Scenario" value={selectedChallengeRun.scenarioName} />
                  <Metric label="Status" value={selectedChallengeRun.status} />
                  <Metric label="Proof level" value={selectedChallengeRun.proofLevel} />
                  <Metric label="Maturity" value={selectedChallengeRun.constitutionalMaturity.toFixed(1)} />
                  <Metric label="Replay" value={selectedChallengeRun.replaySuccess ? 'verified' : 'diverged'} />
                  <Metric label="Pass rate" value={`${selectedChallengeRun.challengePassRate.toFixed(1)}%`} />
                </div>
                <Panel title="Replay Timeline">
                  <div style={timelineWrapStyle}>
                    {selectedChallengeRun.timeline.map((entry) => (
                      <div key={`${selectedChallengeRun.runId}-${entry.stage}`} style={timelineEntryStyle}>
                        <div style={rowSpreadStyle}>
                          <strong>{entry.stage}</strong>
                          <span style={{ ...badgeStyle, ...statusPalette(entry.status) }}>{entry.status}</span>
                        </div>
                        <div style={copyStyle}>{entry.detail}</div>
                      </div>
                    ))}
                  </div>
                </Panel>
                <Panel title="Resource Pressure">
                  <div style={resourceGridStyle}>
                    <Metric label="CPU" value={`${selectedChallengeRun.resourceUsage.cpu}%`} />
                    <Metric label="Memory" value={`${selectedChallengeRun.resourceUsage.memory}%`} />
                    <Metric label="Network" value={`${selectedChallengeRun.resourceUsage.network}%`} />
                    <Metric label="Latency" value={`${selectedChallengeRun.resourceUsage.latency}ms`} />
                    <Metric label="Throughput" value={String(selectedChallengeRun.resourceUsage.throughput)} />
                    <Metric label="Recovery" value={`${selectedChallengeRun.failureRecovery.toFixed(1)}%`} />
                  </div>
                </Panel>
                <Panel title="Battle Scars">
                  {selectedChallengeRun.battleScars.length > 0 ? (
                    <ul style={{ marginBottom: 0 }}>
                      {selectedChallengeRun.battleScars.map((scar) => (
                        <li key={scar}>{scar}</li>
                      ))}
                    </ul>
                  ) : (
                    <p style={copyStyle}>No immediate scars were recorded for this challenge.</p>
                  )}
                </Panel>
                <Panel title="Proof Receipt">
                  <p style={copyStyle}><strong>Receipt:</strong> {selectedChallengeRun.proofReceiptId}</p>
                  <p style={copyStyle}><strong>Evidence:</strong> {selectedChallengeRun.evidenceReceipts.join(', ')}</p>
                  <p style={copyStyle}><strong>Final outcome:</strong> {selectedChallengeRun.finalOutcome}</p>
                </Panel>
              </div>
            ) : (
              <p style={copyStyle}>Select a challenge run to inspect the timeline and proof receipts.</p>
            )}
          </Panel>
        </div>
      ) : null}

      {activeTab === 'scorecard' ? (
        <div style={twoColumnStyle}>
          <Panel title="Arena Scorecard">
            <div style={metricGridStyle}>
              <Metric label="Proof level" value={arena.scorecard.proofLevel} />
              <Metric label="Maturity" value={`${arena.scorecard.constitutionalMaturity.toFixed(1)}%`} />
              <Metric label="Replay success" value={`${arena.scorecard.replaySuccess.toFixed(1)}%`} />
              <Metric label="Determinism" value={`${arena.scorecard.determinism.toFixed(1)}%`} />
              <Metric label="Compliance" value={`${arena.scorecard.governanceCompliance.toFixed(1)}%`} />
              <Metric label="Performance" value={`${arena.scorecard.performance.toFixed(1)}%`} />
              <Metric label="Efficiency" value={`${arena.scorecard.resourceEfficiency.toFixed(1)}%`} />
              <Metric label="Recovery" value={`${arena.scorecard.failureRecovery.toFixed(1)}%`} />
              <Metric label="Challenge pass" value={`${arena.scorecard.challengePassRate.toFixed(1)}%`} />
              <Metric label="Readiness" value={arena.scorecard.readinessLevel} />
            </div>
            <p style={copyStyle}>
              Arena Mode automatically grades each run so the proving ground can gate promotion into higher maturity stages.
            </p>
          </Panel>

          <Panel title="Challenge Packs">
            <div style={cardStackStyle}>
              {arena.challengePacks.map((pack) => (
                <div key={pack.packId} style={detailCardStyle}>
                  <div style={rowSpreadStyle}>
                    <strong>{pack.name}</strong>
                    <span style={badgeStyle}>{pack.scenarioIds.length} scenarios</span>
                  </div>
                  <div style={copyStyle}>{pack.description}</div>
                  <ul style={{ marginBottom: 0 }}>
                    {pack.scenarioIds.map((scenarioId) => (
                      <li key={scenarioId}>{scenarioId}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === 'lifecycle' ? (
        <div style={twoColumnStyle}>
          <Panel title="Constitutional Engineering Lifecycle">
            <div style={lifecycleGridStyle}>
              {arena.lifecycle.map((phase) => (
                <div key={phase.stage} style={phaseCardStyle}>
                  <div style={rowSpreadStyle}>
                    <strong>{phase.stage}</strong>
                    <span style={{ ...badgeStyle, ...statusPalette(lifecycleStatusToPalette(phase.status)) }}>{phase.status}</span>
                  </div>
                  <div style={copyStyle}>{phase.description}</div>
                  <ul style={{ marginBottom: 0 }}>
                    {phase.artifacts.map((artifact) => (
                      <li key={artifact}>{artifact}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Digital Thread">
            <div style={cardStackStyle}>
              {arena.digitalThread.map((item) => (
                <div key={item} style={threadLineStyle}>
                  {item}
                </div>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === 'certificate' ? (
        <div style={twoColumnStyle}>
          <Panel title="Constitutional Readiness Certificate">
            <CertificateCard certificate={arena.certificate} scorecard={arena.scorecard} />
          </Panel>

          <Panel title="Battle Scars">
            <div style={cardStackStyle}>
              {arena.battleScars.map((scar) => (
                <ScarCard key={scar.scarId} scar={scar} />
              ))}
              {arena.battleScars.length === 0 ? <p style={copyStyle}>No scars have been recorded yet.</p> : null}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === 'map' ? (
        <div style={twoColumnStyle}>
          <Panel title="Density Profile">
            <p style={copyStyle}><strong>{arena.densityProfile.name}</strong></p>
            <p style={copyStyle}>
              Center bias: {arena.densityProfile.centerBias?.join(', ') ?? 'none'}
            </p>
            <p style={copyStyle}>
              Edge bias: {arena.densityProfile.edgeBias?.join(', ') ?? 'none'}
            </p>
            <ul style={{ marginBottom: 0 }}>
              {Object.entries(arena.densityProfile.terrainWeights).map(([terrain, weight]) => (
                <li key={terrain}>
                  {terrain}: {weight}
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="Terrain Summary">
            <div style={terrainSummaryWrapStyle}>
              {arena.map.terrainSummary.map((entry) => (
                <div key={entry.terrain} style={terrainSummaryPillStyle}>
                  <strong>{entry.terrain}</strong>
                  <span>{entry.count}</span>
                </div>
              ))}
            </div>
            <div style={mapGridStyle}>
              {arena.map.terrainGrid.map((row, rowIndex) => (
                <div key={rowIndex} style={mapRowStyle}>
                  {row.map((terrain, columnIndex) => {
                    const palette = TERRAIN_PALETTE[terrain] ?? {
                      background: '#f8fafc',
                      color: '#334155',
                      border: '#cbd5e1',
                    };
                    return (
                      <span
                        key={`${rowIndex}-${columnIndex}`}
                        title={terrain}
                        style={{
                          ...mapCellStyle,
                          background: palette.background,
                          color: palette.color,
                          borderColor: palette.border,
                        }}
                      >
                        {terrain.replace(/[^A-Z]/g, '').slice(0, 2) || '??'}
                      </span>
                    );
                  })}
                </div>
              ))}
            </div>
          </Panel>
        </div>
      ) : null}

      {activeTab === 'talents' ? (
        <div style={factionGridStyle}>
          {arena.factions.map((faction) => (
            <Panel key={faction.faction} title={`${faction.faction} Doctrine`}>
              <div style={factionHeaderStyle}>
                <span style={{ ...factionBadgeStyle, ...factionBadgePalette(faction.faction) }}>{faction.faction}</span>
                <span style={factionDoctrineStyle}>{faction.doctrine}</span>
              </div>
              <p style={copyStyle}>
                <strong>Ultimate:</strong> {faction.ultimate.name}
              </p>
              <p style={copyStyle}>{faction.ultimate.description}</p>
              <ul style={{ marginBottom: 0 }}>
                {faction.roster.map((agentName) => {
                  const agent = arena.agents.find((entry) => entry.name === agentName);
                  return (
                    <li key={agentName}>
                      {agentName}
                      {agent ? ` - ready tick ${agent.ultimateReadyTick}` : ''}
                    </li>
                  );
                })}
              </ul>
            </Panel>
          ))}
          <Panel title="Talent Synergies">
            {arena.agents.map((agent) => (
              <div key={agent.agentId} style={talentCardStyle}>
                <div style={factionHeaderStyle}>
                  <strong>{agent.name}</strong>
                  <span style={{ ...factionBadgeStyle, ...factionBadgePalette(agent.faction) }}>{agent.faction}</span>
                </div>
                <div style={modifierGridStyle}>
                  <div><strong>Constraint</strong>: {agent.baseStats.constraintDensity}</div>
                  <div><strong>Evidence</strong>: {agent.baseStats.evidenceWeight}</div>
                  <div><strong>CIEMS</strong>: {agent.baseStats.ciemsProgress}</div>
                  <div><strong>Risk</strong>: {agent.baseStats.riskTolerance}</div>
                </div>
                <div style={modifierGridStyle}>
                  <div><strong>Ultimate</strong>: {agent.ultimate.name}</div>
                  <div><strong>Ready tick</strong>: {agent.ultimateReadyTick}</div>
                </div>
                <div style={modifierGridStyle}>
                  {Object.keys(agent.synergyMods).length > 0 ? (
                    Object.entries(agent.synergyMods).map(([key, value]) => (
                      <div key={key}><strong>{key}</strong>: {String(value)}</div>
                    ))
                  ) : (
                    <div>No synergy modifiers active.</div>
                  )}
                </div>
              </div>
            ))}
          </Panel>
        </div>
      ) : null}

      {activeTab === 'tournament' ? (
        <div style={{ display: 'grid', gap: 16 }}>
          {arena.tournament.rounds.map((round, roundIndex) => (
            <Panel key={`round-${roundIndex}`} title={`Round ${roundIndex + 1}`}>
              <div style={matchListStyle}>
                {round.map((match) => (
                  <div key={match.matchId} style={matchCardStyle}>
                    <div style={factionHeaderStyle}>
                      <strong>{match.matchId}</strong>
                      <span style={matchWinnerStyle}>{match.winner ?? 'pending'}</span>
                    </div>
                    <div style={copyStyle}>{match.agents.join(' vs ')}</div>
                    <div style={copyStyle}>{match.summary}</div>
                    <div style={matchActionsStyle}>
                      <button type="button" onClick={() => openReplay(match)} style={primaryButtonStyle}>
                        Open Replay Analyzer
                      </button>
                      <button
                        type="button"
                        onClick={() => downloadTrace(match.traceId ? arena.traces[match.matchId] : undefined)}
                        style={secondaryButtonStyle}
                        disabled={!match.traceId}
                      >
                        Download .cnode-trace
                      </button>
                    </div>
                    <div style={tracePathStyle}>
                      Trace path: {match.tracePath ?? 'bye'}
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          ))}
        </div>
      ) : null}

      {activeTab === 'replay' ? (
        <div style={twoColumnStyle}>
          <Panel title="Replay Analyzer">
            {selectedReport ? (
              <div style={{ display: 'grid', gap: 12 }}>
                <div style={metricGridStyle}>
                  <Metric label="Trace" value={selectedReport.traceId} />
                  <Metric label="Integrity" value={`${Math.round(selectedReport.integrityScore * 100)}%`} />
                  <Metric label="Events" value={String(selectedReport.eventCount)} />
                  <Metric label="Replayable" value={selectedReport.replayable ? 'yes' : 'no'} />
                </div>
                <Panel title="Replay Timeline">
                  <div style={timelineWrapStyle}>
                    {selectedReport.timeline.map((entry) => (
                      <div key={`${selectedReport.traceId}-${entry.stage}`} style={timelineEntryStyle}>
                        <div style={rowSpreadStyle}>
                          <strong>{entry.stage}</strong>
                          <span style={{ ...badgeStyle, ...statusPalette(entry.status) }}>{entry.status}</span>
                        </div>
                        <div style={copyStyle}>{entry.detail}</div>
                      </div>
                    ))}
                  </div>
                </Panel>
                <Panel title="Resource Usage">
                  <div style={resourceGridStyle}>
                    <Metric label="CPU" value={`${selectedReport.resourceUsage.cpu}%`} />
                    <Metric label="Memory" value={`${selectedReport.resourceUsage.memory}%`} />
                    <Metric label="Network" value={`${selectedReport.resourceUsage.network}%`} />
                    <Metric label="Latency" value={`${selectedReport.resourceUsage.latency}ms`} />
                    <Metric label="Throughput" value={String(selectedReport.resourceUsage.throughput)} />
                  </div>
                </Panel>
                <p style={copyStyle}><strong>Open path:</strong> {selectedReport.openReplayPath}</p>
                <p style={copyStyle}><strong>Match:</strong> {selectedReport.matchId}</p>
                {selectedReport.warnings.length > 0 ? (
                  <Panel title="Warnings">
                    <ul style={{ marginBottom: 0 }}>
                      {selectedReport.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                    </ul>
                  </Panel>
                ) : (
                  <Panel title="Warnings">
                    <p style={copyStyle}>No replay warnings.</p>
                  </Panel>
                )}
                <Panel title="Notes">
                  {selectedReport.notes.length > 0 ? (
                    <ul style={{ marginBottom: 0 }}>
                      {selectedReport.notes.map((note) => <li key={note}>{note}</li>)}
                    </ul>
                  ) : (
                    <p style={copyStyle}>No replay notes.</p>
                  )}
                </Panel>
                <button
                  type="button"
                  onClick={() => downloadTrace(selectedTrace)}
                  style={primaryButtonStyle}
                  disabled={!selectedTrace}
                >
                  Open selected replay
                </button>
              </div>
            ) : (
              <p style={copyStyle}>Select a match in the Tournament tab to inspect its .cnode-trace replay.</p>
            )}
          </Panel>

          <Panel title="Trace Events">
            {selectedTrace ? (
              <div style={{ display: 'grid', gap: 8 }}>
                {selectedTrace.events.map((event) => (
                  <div key={`${event.kind}-${event.tick}-${event.actor ?? 'arena'}`} style={eventCardStyle}>
                    <div style={factionHeaderStyle}>
                      <strong>Tick {event.tick}</strong>
                      <span>{event.kind}</span>
                    </div>
                    {event.actor ? <div style={copyStyle}>Actor: {event.actor}</div> : null}
                    <pre style={preStyle}>{JSON.stringify(event.payload, null, 2)}</pre>
                  </div>
                ))}
              </div>
            ) : (
              <p style={copyStyle}>No replay trace selected.</p>
            )}
          </Panel>
        </div>
      ) : null}
    </section>
  );
}

function findFirstReplayMatch(rounds: TournamentMatch[][]): TournamentMatch | undefined {
  for (const round of rounds) {
    for (const match of round) {
      if (match.traceId) {
        return match;
      }
    }
  }
  return undefined;
}

function findMatch(rounds: TournamentMatch[][], matchId: string): TournamentMatch | undefined {
  for (const round of rounds) {
    for (const match of round) {
      if (match.matchId === matchId) {
        return match;
      }
    }
  }
  return undefined;
}

function statusPalette(status: string): React.CSSProperties {
  return STATUS_PALETTE[status] ?? { background: '#f8fafc', color: '#334155', border: '#cbd5e1' };
}

function factionBadgePalette(faction: string): React.CSSProperties {
  return FACTION_PALETTE[faction] ?? { background: '#f8fafc', color: '#334155', border: '#cbd5e1' };
}

function lifecycleStatusToPalette(status: ArenaLifecyclePhase['status']): 'PASS' | 'WARN' | 'INFO' {
  if (status === 'complete') {
    return 'PASS';
  }
  if (status === 'in-progress') {
    return 'WARN';
  }
  return 'INFO';
}

function CertificateCard({ certificate, scorecard }: { certificate: ArenaReadinessCertificate; scorecard: ArenaScorecard }) {
  return (
    <div style={detailCardStyle}>
      <div style={rowSpreadStyle}>
        <strong>{certificate.certificateId}</strong>
        <span style={{ ...badgeStyle, ...statusPalette(scorecard.readinessLevel === 'production-ready' ? 'PASS' : scorecard.readinessLevel === 'candidate' ? 'WARN' : 'INFO') }}>
          {scorecard.readinessLevel}
        </span>
      </div>
      <p style={copyStyle}><strong>Proof surface:</strong> {certificate.proofSurface}</p>
      <p style={copyStyle}><strong>Challenge results:</strong> {certificate.challengeResults}</p>
      <p style={copyStyle}><strong>Replay verification:</strong> {certificate.replayVerification}</p>
      <p style={copyStyle}><strong>Conformance status:</strong> {certificate.conformanceStatus}</p>
      <p style={copyStyle}><strong>Maturity:</strong> {certificate.constitutionalMaturity.toFixed(1)}%</p>
      <p style={copyStyle}><strong>Readiness level:</strong> {certificate.readinessLevel}</p>
      <p style={copyStyle}><strong>Issued at:</strong> {certificate.issuedAt}</p>
      <div>
        <strong>Evidence receipts</strong>
        <ul style={{ marginBottom: 0 }}>
          {certificate.evidenceReceipts.map((receipt) => (
            <li key={receipt}>{receipt}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ScarCard({ scar }: { scar: ArenaBattleScar }) {
  return (
    <div style={detailCardStyle}>
      <div style={rowSpreadStyle}>
        <strong>{scar.title}</strong>
        <span style={{ ...badgeStyle, ...statusPalette(scar.severity === 'high' ? 'FAIL' : scar.severity === 'medium' ? 'WARN' : 'INFO') }}>
          {scar.type.replace(/_/g, ' ')}
        </span>
      </div>
      <div style={copyStyle}>{scar.detail}</div>
      <div style={mutedLineStyle}>Scenario: {scar.scenarioId}</div>
    </div>
  );
}

const sectionStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #dfe3e8',
  borderRadius: 8,
  padding: 16,
  marginBottom: 16,
};

const headerRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  gap: 16,
  alignItems: 'start',
  marginBottom: 16,
};

const summaryPillStyle: React.CSSProperties = {
  border: '1px solid #c8d4e3',
  borderRadius: 999,
  padding: '6px 12px',
  background: '#eef4ff',
  color: '#23405f',
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
};

const metricGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
  marginBottom: 16,
};

const tabRowStyle: React.CSSProperties = {
  display: 'flex',
  gap: 8,
  flexWrap: 'wrap',
  marginBottom: 16,
};

const tabButtonStyle: React.CSSProperties = {
  border: '1px solid #cbd5e1',
  background: '#fff',
  color: '#23405f',
  borderRadius: 999,
  padding: '8px 12px',
  cursor: 'pointer',
  fontWeight: 700,
};

const tabButtonActiveStyle: React.CSSProperties = {
  background: '#23405f',
  color: '#fff',
  borderColor: '#23405f',
};

const twoColumnStyle: React.CSSProperties = {
  display: 'grid',
  gap: 16,
  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
};

const panelStyle: React.CSSProperties = {
  border: '1px solid #e3e7ed',
  borderRadius: 8,
  padding: 12,
  background: '#fff',
};

const copyStyle: React.CSSProperties = {
  margin: 0,
  color: '#334155',
  lineHeight: 1.55,
};

const terrainSummaryWrapStyle: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 8,
  marginBottom: 12,
};

const terrainSummaryPillStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 999,
  padding: '6px 10px',
  background: '#f8fbff',
  display: 'flex',
  gap: 6,
  alignItems: 'center',
};

const mapGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 6,
};

const mapRowStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(42px, 1fr))',
  gap: 6,
  gridAutoFlow: 'column',
};

const mapCellStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: 34,
  border: '1px solid',
  borderRadius: 8,
  fontSize: 10,
  fontWeight: 800,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  padding: '0 4px',
};

const factionGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 16,
  gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
};

const factionHeaderStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: 8,
  flexWrap: 'wrap',
  marginBottom: 8,
};

const factionBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  borderRadius: 999,
  padding: '4px 10px',
  fontSize: 11,
  fontWeight: 800,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  border: '1px solid',
};

const factionDoctrineStyle: React.CSSProperties = {
  color: '#5f6b7a',
  fontSize: 13,
  flex: 1,
};

const talentCardStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 12,
  padding: 12,
  background: '#f8fbff',
  display: 'grid',
  gap: 8,
};

const modifierGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 6,
  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
};

const matchListStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
};

const matchCardStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 12,
  padding: 12,
  background: '#fdfefe',
  display: 'grid',
  gap: 8,
};

const matchWinnerStyle: React.CSSProperties = {
  borderRadius: 999,
  padding: '4px 10px',
  background: '#ecfdf5',
  color: '#047857',
  fontWeight: 800,
  textTransform: 'uppercase',
  fontSize: 11,
  letterSpacing: '0.06em',
};

const matchActionsStyle: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 8,
};

const primaryButtonStyle: React.CSSProperties = {
  border: '1px solid #23405f',
  borderRadius: 10,
  padding: '8px 12px',
  background: '#23405f',
  color: '#fff',
  fontWeight: 700,
  cursor: 'pointer',
};

const secondaryButtonStyle: React.CSSProperties = {
  border: '1px solid #cbd5e1',
  borderRadius: 10,
  padding: '8px 12px',
  background: '#fff',
  color: '#23405f',
  fontWeight: 700,
  cursor: 'pointer',
};

const tracePathStyle: React.CSSProperties = {
  color: '#64748b',
  fontSize: 12,
};

const eventCardStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 12,
  padding: 12,
  background: '#fff',
  display: 'grid',
  gap: 8,
};

const preStyle: React.CSSProperties = {
  margin: 0,
  padding: 12,
  background: '#f8fbff',
  borderRadius: 10,
  overflow: 'auto',
  fontSize: 12,
  lineHeight: 1.45,
};

const cardStackStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
};

const detailCardStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 12,
  padding: 12,
  background: '#f8fbff',
  display: 'grid',
  gap: 8,
};

const listButtonStyle: React.CSSProperties = {
  textAlign: 'left',
  border: '1px solid #d9e0ea',
  borderRadius: 12,
  padding: 12,
  background: '#fff',
  color: '#1f2937',
  display: 'grid',
  gap: 8,
  cursor: 'pointer',
};

const listButtonActiveStyle: React.CSSProperties = {
  borderColor: '#23405f',
  boxShadow: '0 0 0 1px #23405f inset',
};

const rowSpreadStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  gap: 12,
  alignItems: 'center',
  flexWrap: 'wrap',
};

const badgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  borderRadius: 999,
  padding: '4px 10px',
  border: '1px solid #cbd5e1',
  background: '#f8fbff',
  color: '#23405f',
  fontSize: 11,
  fontWeight: 800,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
};

const mutedLineStyle: React.CSSProperties = {
  color: '#64748b',
  fontSize: 12,
};

const metricChipsStyle: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 8,
  color: '#475569',
  fontSize: 12,
};

const timelineWrapStyle: React.CSSProperties = {
  display: 'grid',
  gap: 10,
};

const timelineEntryStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 12,
  padding: 12,
  background: '#f8fbff',
  display: 'grid',
  gap: 8,
};

const resourceGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
};

const lifecycleGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
};

const phaseCardStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 12,
  padding: 12,
  background: '#f8fbff',
  display: 'grid',
  gap: 8,
};

const threadLineStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 12,
  padding: 10,
  background: '#fff',
};

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={panelStyle}>
      <h3 style={{ margin: '0 0 12px', fontSize: 16 }}>{title}</h3>
      {children}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={metricCardStyle}>
      <div style={metricLabelStyle}>{label}</div>
      <div style={metricValueStyle}>{value}</div>
    </div>
  );
}

const metricCardStyle: React.CSSProperties = {
  border: '1px solid #d9e0ea',
  borderRadius: 12,
  padding: 12,
  background: '#f8fbff',
  display: 'grid',
  gap: 4,
};

const metricLabelStyle: React.CSSProperties = {
  color: '#64748b',
  fontSize: 12,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
};

const metricValueStyle: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 800,
  color: '#1f2937',
  wordBreak: 'break-word',
};
