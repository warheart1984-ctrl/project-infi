import axios from 'axios';
import { ensureAmplifySession } from './amplifyAuth';
import { getApiBaseUrl, getStaticBearerToken } from './auth';

const client = axios.create({
  baseURL: getApiBaseUrl(),
});

async function buildHeaders(headers = {}) {
  const token = getStaticBearerToken() || (await ensureAmplifySession());
  return {
    ...headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function isFormData(payload) {
  return typeof FormData !== 'undefined' && payload instanceof FormData;
}

function normalizeRequestConfig(config = {}) {
  const { headers, ...rest } = config || {};
  return { headers: headers || {}, rest };
}

export async function apiGet(path, config = {}) {
  const { headers, rest } = normalizeRequestConfig(config);
  return client.get(path, {
    ...rest,
    headers: await buildHeaders(headers),
  });
}

export async function apiDelete(path, config = {}) {
  const { headers, rest } = normalizeRequestConfig(config);
  return client.delete(path, {
    ...rest,
    headers: await buildHeaders(headers),
  });
}

export async function apiPost(path, payload, config = {}) {
  const { headers, rest } = normalizeRequestConfig(config);
  return client.post(path, payload, {
    ...rest,
    headers: await buildHeaders({
      ...headers,
      ...(isFormData(payload) ? {} : { 'Content-Type': 'application/json' }),
    }),
  });
}

export async function apiPatch(path, payload, config = {}) {
  const { headers, rest } = normalizeRequestConfig(config);
  return client.patch(path, payload, {
    ...rest,
    headers: await buildHeaders({
      ...headers,
      ...(isFormData(payload) ? {} : { 'Content-Type': 'application/json' }),
    }),
  });
}

export async function apiPut(path, payload, config = {}) {
  const { headers, rest } = normalizeRequestConfig(config);
  return client.put(path, payload, {
    ...rest,
    headers: await buildHeaders({
      ...headers,
      ...(isFormData(payload) ? {} : { 'Content-Type': 'application/json' }),
    }),
  });
}

export async function apiPostStream(path, payload, options = {}) {
  const headers = await buildHeaders({ 'Content-Type': 'application/json', ...(options.headers || {}) });
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload || {}),
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  function flushEvent(rawEvent) {
    const dataLines = rawEvent
      .split(/\r?\n/)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trim());

    if (!dataLines.length) {
      return;
    }

    const data = dataLines.join('\n');
    if (data === '[DONE]') {
      return;
    }

    try {
      options.onEvent?.(JSON.parse(data));
    } catch (error) {
      options.onEvent?.({ event: 'error', error: error.message || String(error) });
    }
  }

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

    const events = buffer.split(/\r?\n\r?\n/);
    buffer = events.pop() || '';
    events.forEach(flushEvent);

    if (done) {
      if (buffer.trim()) {
        flushEvent(buffer);
      }
      return;
    }
  }
}

export function getApiErrorMessage(error, fallback = 'Request failed') {
  const detail = error?.response?.data?.detail || error?.response?.data?.message;
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail) && detail.length) {
    return detail.map((item) => item?.msg || item?.message || String(item)).join(', ');
  }
  return error?.message || fallback;
}
