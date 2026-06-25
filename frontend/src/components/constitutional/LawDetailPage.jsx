import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { evaluateLaw, fetchTraceLaw, replayLawEvidence } from '../../lib/constitutionalApi';
import { getApiErrorMessage } from '../../lib/api';
import { ComprehensionFitness } from './ComprehensionFitness';
import { CrossLedgerTracePanel } from './CrossLedgerTracePanel';
import { EvidenceFitness } from './EvidenceFitness';
import { GITStrip } from './GITStrip';
import { MeaningFitness } from './MeaningFitness';
import { PITStrip } from './PITStrip';
import { SITStrip } from './SITStrip';
import { EvidenceGraph } from './EvidenceGraph';
import { LedgerTail } from './LedgerTail';
import { StatusPill } from './StatusPill';

export function LawDetailPage({
  law,
  loading,
  busy,
  stewardMode,
  onRefresh,
  onOpenEvidence,
  startEvaluateLaw,
  finishEvaluateLaw,
}) {
  const [statusUpdated, setStatusUpdated] = useState(false);
  const [trace, setTrace] = useState(null);
  const [traceLoading, setTraceLoading] = useState(false);
  const strip = law?.cit_strip;
  const meaningStrip = law?.meaning_strip;
  const eitStrip = law?.eit_strip;
  const sitStrip = law?.sit_strip;
  const gitStrip = law?.git_strip;
  const pitStrip = law?.pit_strip;
  const fitness = law?.fitness?.current ?? 0;

  const handleTrace = async () => {
    if (!law?.law_id) return;
    setTraceLoading(true);
    try {
      const payload = await fetchTraceLaw(law.law_id);
      setTrace(payload);
      toast.success(
        `Cross-ledger trace: ${payload.nodes?.length || 0} nodes, ${payload.edges?.length || 0} edges`,
      );
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Trace failed.'));
    } finally {
      setTraceLoading(false);
    }
  };

  const handleReplay = async () => {
    if (!law?.law_id) return;
    startEvaluateLaw?.();
    try {
      const result = await replayLawEvidence(law.law_id);
      if (result.passed) {
        toast.success(`EIT-2 replay converged for ${law.law_id}`);
      } else {
        toast.error(result.reason || 'EIT-2 replay did not converge.');
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Replay failed.'));
    } finally {
      finishEvaluateLaw?.();
    }
  };

  const handleEvaluate = async () => {
    if (!law?.law_id) return;
    startEvaluateLaw?.();
    try {
      const result = await evaluateLaw(law.law_id);
      toast.success(`Evaluated ${law.law_id} → evidence ${result.evidence_id}`);
      setStatusUpdated(true);
      window.setTimeout(() => setStatusUpdated(false), 600);
      await onRefresh?.();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Law evaluation failed.'));
    } finally {
      finishEvaluateLaw?.();
    }
  };

  if (loading) {
    return <div className="constitutional-panel">Loading law…</div>;
  }

  if (!law) {
    return <div className="constitutional-panel">Law not found.</div>;
  }

  return (
    <div>
      <div className="constitutional-panel">
        <div className="law-card-header">
          <h2>{law.law_id}</h2>
          <StatusPill status={law.status} updated={statusUpdated} />
        </div>
        <p className="constitutional-muted">{law.spec_ref}</p>
        <div className="law-card-metrics">
          <span>F={Number(fitness).toFixed(3)}</span>
          {strip?.chi != null ? <span>Χ={Number(strip.chi).toFixed(3)}</span> : null}
          {meaningStrip?.mu != null ? <span>Μ={Number(meaningStrip.mu).toFixed(3)}</span> : null}
          {eitStrip?.omega != null ? <span>Ω={Number(eitStrip.omega).toFixed(3)}</span> : null}
          {sitStrip?.sigma != null ? <span>Σ={Number(sitStrip.sigma).toFixed(3)}</span> : null}
          {gitStrip?.lambda != null ? <span>Λ={Number(gitStrip.lambda).toFixed(3)}</span> : null}
          {pitStrip?.phi != null ? <span>Φ={Number(pitStrip.phi).toFixed(3)}</span> : null}
        </div>
        <div className="constitutional-actions">
          <button
            type="button"
            className="constitutional-btn constitutional-btn-primary"
            disabled={busy}
            onClick={handleEvaluate}
          >
            Evaluate Law
          </button>
          {law.latest_evidence_id ? (
            <button
              type="button"
              className="constitutional-btn constitutional-btn-secondary"
              onClick={() => onOpenEvidence?.(law.latest_evidence_id)}
            >
              View Evidence
            </button>
          ) : null}
        </div>
      </div>

      {strip ? (
        <ComprehensionFitness
          explain={strip.explain}
          summarize={strip.summarize}
          whyExists={strip.why_exists}
          whatBreaksIfRemoved={strip.what_breaks_if_removed}
          constitutionalRole={strip.constitutional_role}
          chi={strip.chi}
          traceLinks={strip.trace_links}
          stewardMode={stewardMode}
          onTrace={handleTrace}
          onReplay={handleReplay}
        />
      ) : null}

      {eitStrip ? (
        <EvidenceFitness
          omega={eitStrip.omega}
          components={eitStrip.components}
          convergence={eitStrip.convergence}
          lineageSummary={eitStrip.lineage_summary}
          traceLinks={eitStrip.trace_links}
          stewardMode={stewardMode}
          onTrace={handleTrace}
          onReplay={handleReplay}
        />
      ) : null}

      {sitStrip ? (
        <SITStrip
          sigma={sitStrip.sigma}
          structureSummary={sitStrip.structure_summary}
          recoveryHint={sitStrip.recovery_hint}
          operatorIndependence={sitStrip.operator_independence}
          stewardMode={stewardMode}
        />
      ) : null}

      {gitStrip ? (
        <GITStrip
          lambdaValue={gitStrip.lambda}
          generativeLaw={gitStrip.generative_law}
          crossOperatorNote={gitStrip.cross_operator_note}
          recoverySummary={gitStrip.recovery_summary}
          stewardMode={stewardMode}
        />
      ) : null}

      {meaningStrip ? (
        <MeaningFitness
          mu={meaningStrip.mu}
          purpose={meaningStrip.purpose}
          canonicalMeaning={meaningStrip.canonical_meaning}
          intentNote={meaningStrip.intent_note}
          stewardMode={stewardMode}
        />
      ) : null}

      {pitStrip ? (
        <PITStrip
          phi={pitStrip.phi}
          fitnessCurrent={pitStrip.fitness_current}
          selectionNote={pitStrip.selection_note}
          evidenceCoupling={pitStrip.evidence_coupling}
          consensusNote={pitStrip.consensus_note}
          stewardMode={stewardMode}
        />
      ) : null}

      {trace || traceLoading ? (
        <CrossLedgerTracePanel
          trace={trace}
          loading={traceLoading}
          stewardMode={stewardMode}
          onNodeClick={(node) => {
            if (node.layer === 'evidence' || node.layer === 'evidence_ref') {
              onOpenEvidence?.(node.id);
            }
          }}
        />
      ) : null}

      {!stewardMode ? <LedgerTail title="Law Ledger Entries" entries={law.ledger_tail || []} /> : null}
    </div>
  );
}

export function EvidenceDetailPanel({ evidence, loading, stewardMode }) {
  if (loading) {
    return <div className="constitutional-panel">Loading evidence lineage…</div>;
  }

  if (!evidence?.found) {
    return <div className="constitutional-panel">Evidence not found.</div>;
  }

  const eitStrip = evidence.eit_strip;

  return (
    <div>
      {eitStrip ? (
        <EvidenceFitness
          omega={eitStrip.omega}
          components={eitStrip.components}
          convergence={eitStrip.convergence}
          lineageSummary={eitStrip.lineage_summary}
          traceLinks={eitStrip.trace_links}
          stewardMode={stewardMode}
        />
      ) : null}
      <div className="constitutional-panel">
        <h3>Evidence Lineage — {evidence.evidence_id}</h3>
        {!stewardMode ? (
          <EvidenceGraph nodes={evidence.nodes || []} edges={evidence.edges || []} />
        ) : (
          <p className="constitutional-muted">
            Steward view: {evidence.nodes?.length || 0} nodes, {evidence.edges?.length || 0} dependency edges.
          </p>
        )}
      </div>
    </div>
  );
}
