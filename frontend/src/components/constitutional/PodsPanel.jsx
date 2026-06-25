import React, { useCallback, useEffect, useState } from 'react';
import { fetchPods } from '../../lib/constitutionalApi';
import { getApiErrorMessage } from '../../lib/api';
import { PodStrip } from './PodStrip';

export function PodsPanel() {
  const [pods, setPods] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadPods = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const payload = await fetchPods();
      setPods(payload.pods || []);
      setMeta({
        count: payload.count,
        ledgerPath: payload.ledger_path,
        registryVersion: payload.registry_version,
      });
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to load discovery pods.'));
      setPods([]);
      setMeta(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPods();
  }, [loadPods]);

  return (
    <section className="pods-panel">
      <header className="pods-panel-header">
        <h2>Discovery Pods</h2>
        <p className="constitutional-muted">
          Ledger-truth view of operator and tenant pods from DiscoveryPodLedger.
        </p>
        {meta ? (
          <p className="pods-meta">
            {meta.count} pods · registry v{meta.registryVersion || '—'} · {meta.ledgerPath}
          </p>
        ) : null}
      </header>

      {loading ? <p className="constitutional-muted">Loading pods…</p> : null}
      {error ? <p className="constitutional-warning">{error}</p> : null}

      <div className="pods-list">
        {pods.map((pod) => (
          <PodStrip
            key={pod.pod_id}
            podId={pod.pod_id}
            displayName={pod.display_name}
            provenCount={pod.proven_count}
            reputation={pod.total_reputation_awarded}
            discoveryCount={pod.discovery_count}
            arcTier={pod.arc_tier}
            rewardMultiplier={pod.pod_reward_multiplier}
          />
        ))}
      </div>
    </section>
  );
}
