import React from 'react';
import { COMPOSE_MODE_LABELS } from '../lib/composeReceipt';
import './ComposeReceiptPanel.css';

function runtimeChip(runtimeId) {
  return runtimeId.replace('cognitive.', '').replace('jarvis.', 'jarvis·');
}

export default function ComposeReceiptPanel({
  receipt,
  superNovaSummary = null,
  title = 'Turn process',
  compact = false,
}) {
  if (!receipt) {
    return null;
  }

  const modeLabel = COMPOSE_MODE_LABELS[receipt.composeMode] || receipt.composeModeLabel || receipt.composeMode;

  return (
    <section
      className={`compose-receipt${compact ? ' compose-receipt--compact' : ''}`}
      aria-label={title}
      data-testid="compose-receipt-panel"
    >
      <div className="compose-receipt__header">
        <p className="compose-receipt__kicker">{title}</p>
        <span className={`compose-receipt__status compose-receipt__status--${receipt.status}`}>
          {receipt.status}
        </span>
      </div>

      <div className="compose-receipt__grid">
        <div className="compose-receipt__fact">
          <span>Mode</span>
          <strong>{modeLabel}</strong>
        </div>
        <div className="compose-receipt__fact">
          <span>ARIS</span>
          <strong>{receipt.arisStatus || '—'}</strong>
        </div>
        {receipt.novaFaceId ? (
          <div className="compose-receipt__fact">
            <span>Face</span>
            <strong>{receipt.novaFaceId}</strong>
          </div>
        ) : null}
        {receipt.composeMs != null ? (
          <div className="compose-receipt__fact">
            <span>Compose</span>
            <strong>{receipt.composeMs} ms</strong>
          </div>
        ) : null}
        {receipt.hasCoherenceProjection ? (
          <div className="compose-receipt__fact">
            <span>Renderer</span>
            <strong>CPL bound</strong>
          </div>
        ) : null}
        {receipt.spineDoctrine ? (
          <div className="compose-receipt__fact">
            <span>Doctrine</span>
            <strong>{receipt.spineDoctrine}</strong>
          </div>
        ) : null}
      </div>

      {receipt.activeRuntimes?.length ? (
        <div className="compose-receipt__runtimes" aria-label="Active cognitive runtimes">
          {receipt.activeRuntimes.map((runtimeId) => (
            <span key={runtimeId} className="compose-receipt__chip">{runtimeChip(runtimeId)}</span>
          ))}
        </div>
      ) : (
        <p className="compose-receipt__empty">Cortex lobes idle — Spine + ARIS + Jarvis authority only.</p>
      )}

      {superNovaSummary ? (
        <div className="compose-receipt__super" data-testid="super-nova-compose-summary">
          <p className="compose-receipt__super-title">Super Nova gate</p>
          <div className="compose-receipt__grid">
            <div className="compose-receipt__fact">
              <span>Activation</span>
              <strong>{superNovaSummary.activationState}</strong>
            </div>
            <div className="compose-receipt__fact">
              <span>Phase gate</span>
              <strong>{superNovaSummary.phaseDecision}</strong>
            </div>
            <div className="compose-receipt__fact">
              <span>Token</span>
              <strong>{superNovaSummary.tokenPresent ? 'live' : 'missing'}</strong>
            </div>
            {superNovaSummary.lastAdmission ? (
              <div className="compose-receipt__fact">
                <span>Admission</span>
                <strong>{superNovaSummary.lastAdmission}</strong>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {receipt.reasonCodes?.length ? (
        <div className="compose-receipt__reasons">
          {receipt.reasonCodes.map((code) => (
            <span key={code} className="compose-receipt__reason">{code}</span>
          ))}
        </div>
      ) : null}
    </section>
  );
}
