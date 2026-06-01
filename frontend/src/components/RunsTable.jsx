import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiGet } from '../lib/api';

function statusClass(status) {
  if (status === 'completed') return 'connected';
  if (status === 'queued') return 'warning';
  if (status === 'running') return 'warning';
  if (status === 'recovering') return 'warning';
  if (status === 'awaiting_approval') return 'warning';
  if (status === 'stale') return 'error';
  if (status === 'failed') return 'error';
  return '';
}

function RunsTable({ initialRuns }) {
  const [runs, setRuns] = useState(initialRuns || []);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    let mounted = true;

    const refresh = async () => {
      try {
        setIsRefreshing(true);
        const response = await apiGet('/workflows/runs', {
          headers: { 'Cache-Control': 'no-store' },
        });
        if (mounted && Array.isArray(response.data.runs)) {
          setRuns(response.data.runs);
        }
      } finally {
        if (mounted) {
          setIsRefreshing(false);
        }
      }
    };

    refresh();
    const interval = window.setInterval(refresh, 4000);

    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  if (runs.length === 0) {
    return (
      <div className="workflow-card workflow-empty-card">
        No workflow runs yet. Run a workflow from the builder to see results here.
      </div>
    );
  }

  return (
    <div className="workflow-runs-table-wrapper">
      <div className="workflow-runs-table-meta">
        <p>Auto-refreshes every 4 seconds</p>
        <span className={`status-pill ${isRefreshing ? 'warning' : 'connected'}`}>
          {isRefreshing ? 'Refreshing' : 'Live'}
        </span>
      </div>

      <div className="workflow-table-shell page-panel">
        <table className="workflow-table">
          <thead>
            <tr>
              <th>Workflow</th>
              <th>Status</th>
              <th>Created</th>
              <th>View</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id}>
                <td>{run.workflow?.name || 'Untitled Workflow'}</td>
                <td>
                  <span className={`status-pill ${statusClass(run.status)}`}>{run.status}</span>
                </td>
                <td>{new Date(run.created_at).toLocaleString()}</td>
                <td>
                  <Link to={`/workflows/runs/${run.id}`}>Open</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default RunsTable;
