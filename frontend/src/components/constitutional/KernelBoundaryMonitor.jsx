import React, { useEffect, useState } from 'react';

export function KernelBoundaryMonitorPanel() {
  const [history, setHistory] = useState([]);
  const [lastSignals, setLastSignals] = useState(null);

  useEffect(() => {
    const poll = () => {
      fetch('/api/kernel/boundary')
        .then((response) => response.json())
        .then((data) => {
          setHistory((prev) => [
            ...prev.slice(-99),
            { t: Date.now(), insufficiency: Number(data.insufficiency || 0) },
          ]);
          setLastSignals(data.signals || null);
        })
        .catch(() => {});
    };
    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, []);

  const last = history[history.length - 1];

  return (
    <section className="constitutional-panel kernel-boundary-monitor">
      <header>
        <h3>Kernel boundary (CRK-T1 / T2)</h3>
        <p className="constitutional-muted">Insufficiency over time — amendment pressure.</p>
      </header>
      <div className="kbm-current">
        <span className="kbm-label">Current insufficiency</span>
        <span className="kbm-value">{last ? last.insufficiency.toFixed(2) : '—'}</span>
      </div>
      {lastSignals ? (
        <p className="constitutional-muted kbm-signals">
          Signals: {lastSignals.map((value) => Number(value).toFixed(2)).join(' · ')}
        </p>
      ) : null}
      <div className="kbm-chart" aria-hidden="true">
        {history.map((point) => (
          <div
            key={point.t}
            className="kbm-bar"
            style={{ height: `${Math.min(1, point.insufficiency) * 100}%` }}
            title={point.insufficiency.toFixed(2)}
          />
        ))}
      </div>
    </section>
  );
}
