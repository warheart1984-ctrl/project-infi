import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { platformPost } from '../lib/platformApi';
import './PlatformConsole.css';

export default function PlatformAssistant() {
  const [orgId, setOrgId] = useState(localStorage.getItem('platform_org_id') || '');
  const [jobId, setJobId] = useState('');
  const [question, setQuestion] = useState('What should I review first?');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function onQuery(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await platformPost('/v1/assistant/query', {
        org_id: orgId,
        job_id: jobId,
        question,
      });
      setResult(data);
    } catch (err) {
      setError(err.message || 'Query failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="platform-console page-shell">
      <header className="platform-console__header">
        <h1>Platform Assistant</h1>
        <p className="platform-console__subtitle">Read-only advisor (MA-13). No job execution or policy mutation.</p>
        <nav className="platform-console__nav">
          <Link to="/platform">Console</Link>
          <Link to="/platform/workflows">Workflows</Link>
        </nav>
      </header>
      <form className="platform-console__form" onSubmit={onQuery}>
        <label>
          Org ID
          <input value={orgId} onChange={(e) => setOrgId(e.target.value)} required />
        </label>
        <label>
          Job ID (optional)
          <input value={jobId} onChange={(e) => setJobId(e.target.value)} />
        </label>
        <label>
          Question
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={3} />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Querying…' : 'Ask'}
        </button>
      </form>
      {error && <p className="platform-console__error">{error}</p>}
      {result && (
        <section className="platform-console__panel">
          <p>
            <strong>Summary:</strong> {result.summary}
          </p>
          <p>
            <strong>Claim:</strong> {result.claim_label}
          </p>
          {result.recommendations?.length > 0 && (
            <>
              <h3>Recommendations</h3>
              <ul>
                {result.recommendations.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </>
          )}
          {result.anomalies?.length > 0 && (
            <>
              <h3>Anomalies</h3>
              <ul>
                {result.anomalies.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </div>
  );
}
