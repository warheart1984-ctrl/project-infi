import React from 'react';
import { StatusPill } from './StatusPill';

export function LawCard({ law, onSelect }) {
  const fitness = law?.fitness?.current ?? law?.fitness ?? 0;
  const chi = law?.chi ?? law?.cit_strip?.chi;
  const mu = law?.mu ?? law?.meaning_strip?.mu;
  const omega = law?.omega ?? law?.eit_strip?.omega;
  const sigma = law?.sigma ?? law?.sit_strip?.sigma;
  const lambdaValue = law?.lambda ?? law?.git_strip?.lambda;
  const phi = law?.phi ?? law?.pit_strip?.phi;

  return (
    <button type="button" className="constitutional-panel law-card" onClick={() => onSelect?.(law.law_id)}>
      <div className="law-card-header">
        <strong>{law.law_id}</strong>
        <StatusPill status={law.status} />
      </div>
      <div className="constitutional-muted">{law.spec_ref}</div>
      <div className="law-card-metrics">
        <span>F={Number(fitness).toFixed(3)}</span>
        {chi != null ? <span>Χ={Number(chi).toFixed(3)}</span> : null}
        {mu != null ? <span>Μ={Number(mu).toFixed(3)}</span> : null}
        {omega != null ? <span>Ω={Number(omega).toFixed(3)}</span> : null}
        {sigma != null ? <span>Σ={Number(sigma).toFixed(3)}</span> : null}
        {lambdaValue != null ? <span>Λ={Number(lambdaValue).toFixed(3)}</span> : null}
        {phi != null ? <span>Φ={Number(phi).toFixed(3)}</span> : null}
      </div>
    </button>
  );
}
