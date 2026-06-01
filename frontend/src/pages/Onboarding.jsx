import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import './Onboarding.css';

function Onboarding() {
  const navigate = useNavigate();
  const [goal, setGoal] = useState('');
  const [tools, setTools] = useState([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    apiGet('/onboarding')
      .then((response) => {
        if (!active) return;
        const data = response.data || {};
        if (data.onboarding_done) {
          navigate('/workflows/templates', { replace: true });
          return;
        }
        setGoal(data.goal || '');
        setTools(Array.isArray(data.tools) ? data.tools : []);
      })
      .catch(() => {
        // Let onboarding work even if the initial fetch fails.
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [navigate]);

  const toggleTool = (tool) => {
    setTools((current) =>
      current.includes(tool) ? current.filter((item) => item !== tool) : [...current, tool],
    );
  };

  const complete = async () => {
    try {
      setBusy(true);
      await apiPost('/onboarding/complete', {
        goal,
        tools,
      });
      toast.success('Onboarding saved');
      navigate('/workflows/templates');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not save onboarding'));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div className="workflow-page"><div className="workflow-card workflow-empty-card">Loading onboarding...</div></div>;
  }

  return (
    <div className="onboarding-page">
      <section className="onboarding-shell page-panel">
        <div className="onboarding-copy">
          <span className="status-pill connected">Guided setup</span>
          <h1>Tell AAIS what you want to automate.</h1>
          <p>
            We’ll use this to point you toward the strongest templates and keep the workflow builder focused from the
            start.
          </p>
        </div>

        <div className="onboarding-form">
          <div className="workflow-section">
            <label className="workflow-label">What do you want to automate?</label>
            <input
              type="text"
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
              placeholder="Summarize important emails and send alerts..."
            />
          </div>

          <div className="workflow-section">
            <div className="workflow-label">Which tools matter most?</div>
            <div className="onboarding-tool-grid">
              {['email', 'slack', 'api', 'schedules'].map((tool) => (
                <button
                  key={tool}
                  type="button"
                  className={`workflow-filter-chip ${tools.includes(tool) ? 'active' : ''}`}
                  onClick={() => toggleTool(tool)}
                >
                  {tool}
                </button>
              ))}
            </div>
          </div>

          <button className="workflow-primary-btn" onClick={complete} disabled={busy}>
            {busy ? 'Saving...' : 'Continue to Templates'}
          </button>
        </div>
      </section>
    </div>
  );
}

export default Onboarding;
