export function buildSeedWorkflowFromOnboarding(onboardingState = {}) {
  if (!onboardingState?.onboarding_done && !onboardingState?.goal) {
    return null;
  }
  const goal = onboardingState.goal || 'New governed workflow';
  return {
    name: goal,
    nodes: [
      { id: 'trigger', type: 'input', position: { x: 0, y: 80 }, data: { label: 'Manual trigger' } },
      { id: 'plan', type: 'default', position: { x: 260, y: 80 }, data: { label: 'Plan next step' } },
    ],
    edges: [{ id: 'trigger-plan', source: 'trigger', target: 'plan' }],
  };
}

export function rankTemplatesForOnboarding(templates = [], onboardingState = {}) {
  const goal = String(onboardingState?.goal || '').toLowerCase();
  return [...templates].sort((a, b) => scoreTemplate(b, goal) - scoreTemplate(a, goal));
}

export function getTopRecommendations(templates = [], onboardingState = {}, limit = 3) {
  return rankTemplatesForOnboarding(templates, onboardingState).slice(0, limit);
}

function scoreTemplate(template, goal) {
  const haystack = `${template?.name || ''} ${template?.description || ''} ${template?.category || ''}`.toLowerCase();
  if (!goal) {
    return 0;
  }
  return goal.split(/\s+/).filter((word) => word.length > 3 && haystack.includes(word)).length;
}
