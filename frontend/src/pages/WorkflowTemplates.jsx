import React, { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { Link, useNavigate } from 'react-router-dom';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import { getTopRecommendations, rankTemplatesForOnboarding } from '../lib/workflowOnboarding';
import './WorkflowTemplates.css';

function normalizeTemplate(template) {
  if (!template || typeof template !== 'object') {
    return null;
  }

  const id = `${template.id || ''}`.trim();
  const name = `${template.name || ''}`.trim();
  if (!id || !name) {
    return null;
  }

  return {
    id,
    name,
    description: `${template.description || 'No description available.'}`.trim(),
    category: `${template.category || 'productivity'}`.trim(),
    difficulty: `${template.difficulty || 'easy'}`.trim(),
    integrations: Array.isArray(template.integrations) ? template.integrations.filter(Boolean) : [],
  };
}

function WorkflowTemplates() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [category, setCategory] = useState('all');
  const [busyId, setBusyId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [onboardingState, setOnboardingState] = useState(null);

  useEffect(() => {
    let active = true;

    Promise.allSettled([apiGet('/workflows/templates'), apiGet('/onboarding')])
      .then(([templatesResult, onboardingResult]) => {
        if (!active) {
          return;
        }

        if (templatesResult.status !== 'fulfilled') {
          const message = getApiErrorMessage(templatesResult.reason, 'Could not load templates');
          setError(message);
          toast.error(message);
          return;
        }

        const normalizedTemplates = (Array.isArray(templatesResult.value.data.templates) ? templatesResult.value.data.templates : [])
          .map(normalizeTemplate)
          .filter(Boolean);
        const nextOnboardingState =
          onboardingResult.status === 'fulfilled' ? onboardingResult.value.data || null : null;

        setOnboardingState(nextOnboardingState);
        setTemplates(rankTemplatesForOnboarding(normalizedTemplates, nextOnboardingState));
        setError(
          normalizedTemplates.length === 0 ? 'No valid workflow templates are available right now.' : '',
        );
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

  const filtered = useMemo(() => {
    if (category === 'all') {
      return templates;
    }
    return templates.filter((template) => template.category === category);
  }, [category, templates]);
  const recommendedTemplates = useMemo(
    () => getTopRecommendations(templates, onboardingState),
    [onboardingState, templates],
  );

  const handleUseTemplate = async (templateId) => {
    try {
      setBusyId(templateId);
      const response = await apiPost(`/workflows/templates/${templateId}/use`, {});
      const workflowId = response.data.workflow?.id;
      if (!workflowId) {
        throw new Error('Template was created but no workflow id was returned.');
      }
      toast.success('Template added to your workflow library');
      navigate(`/workflows?workflowId=${workflowId}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not use template'));
    } finally {
      setBusyId('');
    }
  };

  return (
    <div className="workflow-page">
      <div className="page-intro">
        <h1>Workflow Templates</h1>
        <p>Start from a proven workflow instead of a blank canvas.</p>
      </div>

      <div className="workflow-page-actions">
        <Link className="workflow-page-link" to="/workflows">
          Open Builder
        </Link>
        <Link className="workflow-page-link" to="/onboarding">
          Revisit onboarding
        </Link>
      </div>

      {recommendedTemplates.length > 0 ? (
        <section className="workflow-card page-panel">
          <h2>Recommended for your onboarding goal</h2>
          <p>
            AAIS used your goal and preferred tools to surface the strongest starting points first.
          </p>
          <div className="workflow-template-tags">
            {recommendedTemplates.map((template) => (
              <span key={template.id} className="accent">
                {template.name}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      <div className="workflow-template-filter-row">
        {['all', 'email', 'slack', 'api', 'productivity'].map((item) => (
          <button
            key={item}
            className={`workflow-filter-chip ${category === item ? 'active' : ''}`}
            onClick={() => setCategory(item)}
          >
            {item}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="workflow-card workflow-empty-card">Loading templates...</div>
      ) : error ? (
        <div className="workflow-card workflow-error-card">{error}</div>
      ) : filtered.length === 0 ? (
        <div className="workflow-card workflow-empty-card">No templates match this filter yet.</div>
      ) : (
        <div className="workflow-template-grid">
          {filtered.map((template) => (
            <article key={template.id} className="workflow-card page-panel workflow-template-card">
              <div>
                <h2>{template.name}</h2>
                <p>{template.description}</p>
              </div>

              <div className="workflow-template-tags">
                <span>{template.category}</span>
                <span>{template.difficulty}</span>
                {template.recommended ? <span className="accent">recommended</span> : null}
                {(template.integrations || []).map((integration) => (
                  <span key={integration} className="accent">{integration}</span>
                ))}
              </div>

              {template.recommendationReasons?.length ? (
                <p className="workflow-muted-copy">{template.recommendationReasons[0]}</p>
              ) : null}

              <button
                className="workflow-primary-btn"
                onClick={() => handleUseTemplate(template.id)}
                disabled={busyId === template.id}
              >
                {busyId === template.id ? 'Creating...' : 'Use Template'}
              </button>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

export default WorkflowTemplates;
