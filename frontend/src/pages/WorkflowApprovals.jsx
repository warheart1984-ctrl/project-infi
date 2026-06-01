import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Link, useNavigate } from 'react-router-dom';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import './WorkflowApprovals.css';

function WorkflowApprovals() {
  const navigate = useNavigate();
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState('');
  const [busyAction, setBusyAction] = useState('');

  useEffect(() => {
    let active = true;

    const refresh = async () => {
      try {
        const response = await apiGet('/workflows/approvals', {
          headers: { 'Cache-Control': 'no-store' },
        });
        if (active) {
          setApprovals(Array.isArray(response.data.approvals) ? response.data.approvals : []);
        }
      } catch {
        if (active) {
          setApprovals([]);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    refresh();
    const interval = window.setInterval(refresh, 4000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const handleAction = async (approvalId, action) => {
    try {
      setBusyId(approvalId);
      setBusyAction(action);
      const approval = approvals.find((item) => item.id === approvalId);
      await apiPost(`/workflows/approvals/${approvalId}`, { action });
      setApprovals((current) => current.filter((approval) => approval.id !== approvalId));
      toast.success(action === 'approve' ? 'Approval granted' : 'Approval rejected');
      if (approval?.workflow_run_id) {
        navigate(`/workflows/runs/${approval.workflow_run_id}`);
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Approval action failed'));
    } finally {
      setBusyId('');
      setBusyAction('');
    }
  };

  return (
    <div className="workflow-page">
      <div className="page-intro">
        <h1>Workflow Approvals</h1>
        <p>Review sensitive workflow steps before execution continues.</p>
      </div>

      <div className="workflow-page-actions">
        <Link className="workflow-page-link" to="/workflows/runs">
          View runs
        </Link>
        <Link className="workflow-page-link" to="/workflows">
          Back to Builder
        </Link>
      </div>

      {loading ? (
        <div className="workflow-card workflow-empty-card">Loading approvals...</div>
      ) : approvals.length === 0 ? (
        <div className="workflow-card workflow-empty-card">No pending approvals.</div>
      ) : (
        <div className="workflow-approval-list">
          {approvals.map((approval) => (
            <article key={approval.id} className="workflow-card page-panel workflow-approval-card">
              <div className="workflow-approval-header">
                <div>
                  <strong>{approval.workflow_run?.workflow?.name || 'Workflow'} → {approval.step_label}</strong>
                  <div className="workflow-step-type">{approval.step_type}</div>
                </div>

                <div className="workflow-approval-actions">
                  <button
                    className="workflow-primary-btn"
                    disabled={busyId === approval.id}
                    onClick={() => handleAction(approval.id, 'approve')}
                  >
                    {busyId === approval.id && busyAction === 'approve' ? 'Approving...' : 'Approve'}
                  </button>
                  <button
                    className="workflow-secondary-btn"
                    disabled={busyId === approval.id}
                    onClick={() => handleAction(approval.id, 'reject')}
                  >
                    {busyId === approval.id && busyAction === 'reject' ? 'Rejecting...' : 'Reject'}
                  </button>
                </div>
              </div>

              {approval.reason ? <div className="workflow-approval-reason">{approval.reason}</div> : null}

              <details>
                <summary>View payload</summary>
                <pre>{JSON.stringify(approval.payload, null, 2)}</pre>
              </details>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

export default WorkflowApprovals;
