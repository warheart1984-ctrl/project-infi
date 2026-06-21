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

export async function fetchCitLaw(lawId) {
  const response = await apiGet(`/api/cit/law/${encodeURIComponent(lawId)}`);
  return response.data;
}

export async function fetchMitLaw(lawId) {
  const response = await apiGet(`/api/mit/law/${encodeURIComponent(lawId)}`);
  return response.data;
}

export async function fetchExplainLaw(lawId) {
  const response = await apiGet(`/api/explain/law/${encodeURIComponent(lawId)}`);
  return response.data;
}

export async function fetchEitLaw(lawId) {
  const response = await apiGet(`/api/eit/law/${encodeURIComponent(lawId)}`);
  return response.data;
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
