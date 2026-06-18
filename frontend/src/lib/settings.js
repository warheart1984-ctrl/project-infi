import { getApiBaseUrl as getEnvApiBaseUrl } from './auth';
import { readJson, removeStorageItem, writeJson } from './storage';

const SETTINGS_KEY = 'aais-settings';

export const defaultSettings = {
  apiUrl: getEnvApiBaseUrl() || 'http://127.0.0.1:8000',
  defaultModel: 'AAIS local API',
  defaultMaxLength: 500,
  theme: 'system',
};

export function getSettings() {
  return {
    ...defaultSettings,
    ...readJson(SETTINGS_KEY, {}),
  };
}

export function saveSettings(settings) {
  const next = { ...defaultSettings, ...(settings || {}) };
  writeJson(SETTINGS_KEY, next);
  return next;
}

export function resetSettings() {
  removeStorageItem(SETTINGS_KEY);
  return defaultSettings;
}

export function getApiBaseUrl() {
  return getSettings().apiUrl || defaultSettings.apiUrl;
}

export function getApiBaseUrlCandidates(value) {
  const candidates = [
    value,
    getEnvApiBaseUrl(),
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    '',
  ]
    .map((item) => String(item || '').replace(/\/+$/, ''))
    .filter((item, index, all) => all.indexOf(item) === index);
  return candidates;
}
