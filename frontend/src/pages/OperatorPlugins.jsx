import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import './WorkflowApprovals.css';

function OperatorPlugins() {
  const [tab, setTab] = useState('libraries');
  const [libraries, setLibraries] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [organs, setOrgans] = useState([]);
  const [plugins, setPlugins] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chainId, setChainId] = useState('research_brief');

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [libRes, wfRes, organRes, plugRes] = await Promise.all([
        apiGet('/api/operator/plugins/libraries'),
        apiGet('/api/operator/plugins/workflows'),
        apiGet('/api/operator/organs'),
        apiGet('/api/operator/plugins'),
      ]);
      setLibraries(libRes.data?.libraries || []);
      setWorkflows(wfRes.data?.workflows || []);
      setOrgans(organRes.data?.organs || []);
      setPlugins(plugRes.data?.plugins || null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not load operator plugins.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const togglePlug = async (plugId, enabled) => {
    try {
      await apiPost(`/api/operator/plugins/${encodeURIComponent(plugId)}/enabled`, { enabled });
      await refresh();
      toast.success(enabled ? 'Plug enabled' : 'Plug disabled');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not toggle plug.'));
    }
  };

  const runChain = async () => {
    try {
      const res = await apiPost(`/api/operator/workflows/${encodeURIComponent(chainId)}/execute`, {
        operator_approved: true,
        dry_run: true,
        args: {},
      });
      toast.success(`Chain run: ${res.data?.run?.run_id || 'ok'}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Chain execution failed.'));
    }
  };

  return (
    <div className="workflow-page">
      <div className="page-intro">
        <h1>Operator Plugins</h1>
        <p>Libraries, workflow bundles, organs, and governed chain execution.</p>
      </div>
      <div className="workflow-page-actions">
        <Link className="workflow-page-link" to="/operator">Console</Link>
        <Link className="workflow-page-link" to="/operator/brain">Brain Sessions</Link>
        <Link className="workflow-page-link" to="/operator/ledger">Decision Ledger</Link>
        <button type="button" className="workflow-secondary-btn" onClick={refresh}>Refresh</button>
      </div>
      <div className="workflow-page-actions">
        {['libraries', 'workflows', 'organs', 'chain'].map((t) => (
          <button key={t} type="button" className={`workflow-secondary-btn ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="workflow-card workflow-empty-card">Loading...</div>
      ) : (
        <>
          {tab === 'libraries' ? (
            <div className="workflow-approval-list">
              {libraries.map((lib) => (
                <article key={lib.identity?.library_id} className="workflow-card page-panel">
                  <strong>{lib.identity?.display_name}</strong>
                  <div className="workflow-step-type">{lib.identity?.library_class}</div>
                </article>
              ))}
            </div>
          ) : null}
          {tab === 'workflows' ? (
            <div className="workflow-approval-list">
              {workflows.map((wf) => (
                <article key={wf.workflow_id} className="workflow-card page-panel">
                  <strong>{wf.display_name}</strong>
                  <div className="workflow-step-type">{wf.workflow_id} · {wf.category}</div>
                </article>
              ))}
            </div>
          ) : null}
          {tab === 'organs' ? (
            <div className="workflow-approval-list">
              {organs.map((organ) => (
                <article key={organ.identity?.family_id} className="workflow-card page-panel">
                  <strong>{organ.identity?.display_name}</strong>
                  <div className="workflow-step-type">{organ.identity?.family_id}</div>
                </article>
              ))}
            </div>
          ) : null}
          {tab === 'chain' ? (
            <div className="workflow-card page-panel">
              <label>
                Workflow id
                <input value={chainId} onChange={(e) => setChainId(e.target.value)} style={{ marginLeft: '0.5rem' }} />
              </label>
              <button type="button" className="workflow-secondary-btn" onClick={runChain} style={{ marginLeft: '0.5rem' }}>
                Run chain (dry-run)
              </button>
            </div>
          ) : null}
          {plugins?.plugs?.length ? (
            <div className="workflow-approval-list" style={{ marginTop: '1rem' }}>
              <strong>Plug registry ({plugins.plug_count} · {plugins.enabled_count} enabled)</strong>
              {plugins.plugs.slice(0, 20).map((plug) => (
                <article key={plug.plug_id} className="workflow-card page-panel">
                  <div className="workflow-approval-header">
                    <div>
                      <strong>{plug.plug_id}</strong>
                      <div className="workflow-step-type">{plug.plug_class} · {plug.authority_level}</div>
                    </div>
                    <button
                      type="button"
                      className="workflow-secondary-btn"
                      onClick={() => togglePlug(plug.plug_id, !plug.enabled)}
                    >
                      {plug.enabled ? 'Disable' : 'Enable'}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

export default OperatorPlugins;
