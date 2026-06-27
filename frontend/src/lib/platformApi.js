const API_KEY_STORAGE = 'platform-api-key';

export function getPlatformApiBaseUrl() {
  return String(import.meta.env?.VITE_PLATFORM_API_BASE_URL || '/platform-api').replace(/\/+$/, '');
}

export function getPlatformApiKey() {
  try {
    return window.localStorage.getItem(API_KEY_STORAGE) || '';
  } catch {
    return '';
  }
}

export function setPlatformApiKey(value) {
  try {
    if (value) {
      window.localStorage.setItem(API_KEY_STORAGE, value);
    } else {
      window.localStorage.removeItem(API_KEY_STORAGE);
    }
  } catch {
    // Ignore unavailable storage.
  }
}

async function platformFetch(path, options = {}) {
  const response = await fetch(`${getPlatformApiBaseUrl()}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(getPlatformApiKey() ? { 'X-Api-Key': getPlatformApiKey() } : {}),
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const message = data.detail || data.message || `Platform request failed with status ${response.status}`;
    throw new Error(message);
  }
  return data;
}

export function platformGet(path) {
  return platformFetch(path);
}

export function platformPost(path, payload) {
  return platformFetch(path, { method: 'POST', body: JSON.stringify(payload || {}) });
}

export function platformPut(path, payload) {
  return platformFetch(path, { method: 'PUT', body: JSON.stringify(payload || {}) });
}
