import { apiGet, apiPost } from './api';

export async function fetchCockpitSummary() {
  const response = await apiGet('/api/cockpit/summary');
  return response.data;
}

export async function fetchComprehensionHealth() {
  const response = await apiGet('/api/cockpit/comprehension');
  return response.data;
}

export async function fetchLaws() {
  const response = await apiGet('/api/laws');
  return response.data?.laws || [];
}

export async function fetchLaw(lawId) {
  const response = await apiGet(`/api/laws/${encodeURIComponent(lawId)}`);
  return response.data;
}

export async function fetchEvidence(evidenceId) {
  const response = await apiGet(`/api/evidence/${encodeURIComponent(evidenceId)}`);
  return response.data;
}

export async function fetchCitStrip(objectType, objectId) {
  const response = await apiGet(
    `/api/cockpit/cit/${encodeURIComponent(objectType)}/${encodeURIComponent(objectId)}`,
  );
  return response.data;
}

export async function fetchStewardExplain(objectType, objectId) {
  const response = await apiGet(
    `/api/cockpit/explain/${encodeURIComponent(objectType)}/${encodeURIComponent(objectId)}`,
  );
  return response.data;
}

export async function fetchComprehensionFitnessLaw(lawId) {
  const response = await apiGet(
    `/api/fitness/comprehension/law/${encodeURIComponent(lawId)}`,
  );
  return response.data;
}

export async function fetchMeaningFitnessLaw(lawId) {
  const response = await apiGet(`/api/fitness/meaning/law/${encodeURIComponent(lawId)}`);
  return response.data;
}

export async function fetchEvidenceFitnessLaw(lawId) {
  const response = await apiGet(`/api/fitness/evidence/law/${encodeURIComponent(lawId)}`);
  return response.data;
}

export async function fetchAttentionAllocationFitness() {
  const response = await apiGet('/api/fitness/attention');
  return response.data;
}

/** @deprecated Use fetchComprehensionFitnessLaw */
export async function fetchCitLaw(lawId) {
  return fetchComprehensionFitnessLaw(lawId);
}

/** @deprecated Use fetchMeaningFitnessLaw */
export async function fetchMitLaw(lawId) {
  return fetchMeaningFitnessLaw(lawId);
}

/** @deprecated Use fetchEvidenceFitnessLaw */
export async function fetchEitLaw(lawId) {
  return fetchEvidenceFitnessLaw(lawId);
}

export async function fetchTraceLaw(lawId) {
  const response = await apiGet(`/api/trace/law/${encodeURIComponent(lawId)}`);
  return response.data;
}

export async function replayLawEvidence(lawId, body = {}) {
  const response = await apiPost(`/api/replay/law/${encodeURIComponent(lawId)}`, body);
  return response.data;
}

export async function evaluateLaw(lawId, body = {}) {
  const response = await apiPost(`/api/laws/${encodeURIComponent(lawId)}/evaluate`, body);
  return response.data;
}

export async function runEpoch(body = {}) {
  const response = await apiPost('/api/epoch/run', body);
  return response.data;
}

export async function fetchDecisions() {
  const response = await apiGet('/api/decisions');
  return response.data?.decisions || [];
}

export async function fetchDecision(decisionId) {
  const response = await apiGet(`/api/decisions/${encodeURIComponent(decisionId)}`);
  return response.data;
}

export async function fetchExplainLaw(lawId) {
  const response = await apiGet(`/api/explain/law/${encodeURIComponent(lawId)}`);
  return response.data;
}

export async function fetchOutcomeVariance(outcomeId) {
  const response = await apiGet(`/api/fitness/outcome/${encodeURIComponent(outcomeId)}`);
  return response.data;
}

export async function fetchOutcomeVarianceForDecision(decisionId) {
  const response = await apiGet(
    `/api/fitness/outcome/decision/${encodeURIComponent(decisionId)}`,
  );
  return response.data;
}
/** @deprecated Use fetchOutcomeVariance */
export async function fetchOutcome(outcomeId) {
  return fetchOutcomeVariance(outcomeId);
}

/** @deprecated Use fetchOutcomeVarianceForDecision */
export async function fetchOutcomeForDecision(decisionId) {
  return fetchOutcomeVarianceForDecision(decisionId);
}

export async function fetchPods() {
  const response = await apiGet('/api/pods');
  return response.data;
}

export async function fetchPod(podId) {
  const response = await apiGet(`/api/pods/${encodeURIComponent(podId)}`);
  return response.data;
}

export function mapLawCard(law) {
  const fitness = law?.fitness || {};
  return {
    lawId: law.law_id,
    status: law.status,
    fitness: fitness.current ?? 0,
    chi: law.chi ?? null,
    domains: law.domains || [],
    specRef: law.spec_ref,
  };
}
