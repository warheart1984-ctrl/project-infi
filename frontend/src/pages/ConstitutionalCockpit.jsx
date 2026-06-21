import React, { useState } from 'react';
import { Link, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { runEpoch } from '../lib/constitutionalApi';
import { getApiErrorMessage } from '../lib/api';
import { useCockpit } from '../hooks/useCockpit';
import { useCockpitState } from '../hooks/useCockpitState';
import { useLaw } from '../hooks/useLaw';
import { useLaws } from '../hooks/useLaws';
import { useEvidence } from '../hooks/useEvidence';
import { Cockpit } from '../components/constitutional/Cockpit';
import { LawsPage } from '../components/constitutional/LawsPage';
import { EvidenceDetailPanel, LawDetailPage } from '../components/constitutional/LawDetailPage';
import '../styles/constitutional/tokens.css';
import '../styles/constitutional/layout.css';
import '../styles/constitutional/cockpit.css';

function LawDetailRoute({ stewardMode, cockpitState, onRefreshCockpit }) {
  const { lawId } = useParams();
  const navigate = useNavigate();
  const { law, loading, refresh } = useLaw(lawId);
  const evidenceId = law?.latest_evidence_id;
  const { data: evidence, loading: evidenceLoading, refresh: refreshEvidence } = useEvidence(evidenceId);

  return (
    <>
      <div className="constitutional-actions" style={{ marginBottom: 16 }}>
        <Link className="constitutional-btn constitutional-btn-secondary" to="/operator/constitutional/laws">
          ← All Laws
        </Link>
      </div>
      <LawDetailPage
        law={law}
        loading={loading}
        busy={cockpitState.busy}
        stewardMode={stewardMode}
        onRefresh={async () => {
          await refresh();
          await onRefreshCockpit();
        }}
        onOpenEvidence={(id) => navigate(`/operator/constitutional/evidence/${encodeURIComponent(id)}`)}
        startEvaluateLaw={cockpitState.startEvaluateLaw}
        finishEvaluateLaw={cockpitState.finishEvaluateLaw}
      />
      {evidenceId ? (
        <EvidenceDetailPanel evidence={evidence} loading={evidenceLoading} stewardMode={stewardMode} />
      ) : null}
    </>
  );
}

function EvidenceRoute({ stewardMode }) {
  const { evidenceId } = useParams();
  const { data, loading } = useEvidence(evidenceId);
  return (
    <div>
      <Link className="constitutional-btn constitutional-btn-secondary" to="/operator/constitutional">
        ← Cockpit
      </Link>
      <EvidenceDetailPanel evidence={data} loading={loading} stewardMode={stewardMode} />
    </div>
  );
}

export default function ConstitutionalCockpit() {
  const navigate = useNavigate();
  const { summary, loading, refresh, epochPulse } = useCockpit();
  const cockpitState = useCockpitState();
  const { laws, loading: lawsLoading, refresh: refreshLaws } = useLaws();

  const handleRunEpoch = async () => {
    cockpitState.startRunEpoch();
    try {
      const result = await runEpoch({ signer: 'operator' });
      if (result.status === 'blocked') {
        toast.error(result.reason || 'Epoch blocked by CIT.');
      } else {
        toast.success(`Epoch ${result.epoch} simulated for ${result.evaluated?.length || 0} laws.`);
      }
      await refresh();
      await refreshLaws();
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Epoch simulation failed.'));
    } finally {
      cockpitState.finishRunEpoch();
    }
  };

  return (
    <div className="constitutional-shell">
      {cockpitState.stewardMode ? (
        <div className="steward-banner">Steward Mode — summaries and causal chains optimized for human cognition.</div>
      ) : null}

      <Routes>
        <Route
          index
          element={(
            <>
              <Cockpit
                summary={summary}
                epochPulse={epochPulse}
                busy={cockpitState.busy || loading}
                stewardMode={cockpitState.stewardMode}
                onRunEpoch={handleRunEpoch}
                onToggleSteward={cockpitState.toggleStewardMode}
              />
              <div className="constitutional-actions" style={{ marginTop: 20 }}>
                <Link className="constitutional-btn constitutional-btn-primary" to="laws">
                  Open Law Registry
                </Link>
              </div>
            </>
          )}
        />
        <Route
          path="laws"
          element={(
            <LawsPage
              laws={laws}
              loading={lawsLoading}
              onSelectLaw={(lawId) => navigate(`/operator/constitutional/laws/${encodeURIComponent(lawId)}`)}
            />
          )}
        />
        <Route
          path="laws/:lawId"
          element={(
            <LawDetailRoute
              stewardMode={cockpitState.stewardMode}
              cockpitState={cockpitState}
              onRefreshCockpit={refresh}
            />
          )}
        />
        <Route path="evidence/:evidenceId" element={<EvidenceRoute stewardMode={cockpitState.stewardMode} />} />
      </Routes>
    </div>
  );
}
