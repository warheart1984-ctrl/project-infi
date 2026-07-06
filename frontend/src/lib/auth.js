const TRUE_VALUES = new Set(['1', 'true', 'yes', 'on']);

function readEnv(name, fallback = '') {
  return String(import.meta.env?.[name] ?? fallback).trim();
}

export function isTruthyEnvValue(value) {
  return TRUE_VALUES.has(String(value || '').trim().toLowerCase());
}

export function isAmplifyAuthEnabled() {
  return isTruthyEnvValue(readEnv('VITE_AMPLIFY_AUTH'));
}

export function getApiBaseUrl() {
  return readEnv('VITE_API_BASE_URL') || readEnv('REACT_APP_API_BASE_URL') || '';
}

export function getStaticBearerToken() {
  return readEnv('VITE_APP_BEARER_TOKEN') || readEnv('REACT_APP_BEARER_TOKEN') || '';
}
