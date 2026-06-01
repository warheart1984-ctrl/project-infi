import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import RunsTable from '../components/RunsTable';
import { apiGet, getApiErrorMessage } from '../lib/api';
import './WorkflowRuns.css';

function WorkflowRuns() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    apiGet('/workflows/runs')
      .then((response) => {
        if (active) {
          setRuns(Array.isArray(response.data.runs) ? response.data.runs : []);
        }
      })
      .catch((err) => {
        if (active) {
          setError(getApiErrorMessage(err, 'Could not load workflow runs.'));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="workflow-page">
      <div className="page-intro">
        <h1>Workflow Runs</h1>
        <p>Inspect queued, running, blocked, and completed workflow executions from one place.</p>
      </div>

      <div className="workflow-page-actions">
        <Link className="workflow-page-link" to="/workflows">
          Back to Builder
        </Link>
        <Link className="workflow-page-link" to="/workflows/approvals">
          Review Approvals
        </Link>
      </div>

      {loading ? (
        <div className="workflow-card workflow-empty-card">Loading workflow runs...</div>
      ) : error ? (
        <div className="workflow-card workflow-error-card">{error}</div>
      ) : (
        <RunsTable initialRuns={runs} />
      )}
    </div>
  );
}

export default WorkflowRuns;
