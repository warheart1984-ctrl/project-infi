import { readJson, removeStorageItem, writeJson } from './storage';

const ACTIVE_SESSION_KEY = 'jarvis-active-session-id';
const PROFILE_KEY = 'jarvis-profile';
const PENDING_DRAFT_KEY = 'jarvis-pending-draft';

export const SMALL_NOVA_PERSONA_MODE = 'small_nova';
export const SUPER_NOVA_PERSONA_MODE = 'super_nova';
export const TINY_NOVA_PERSONA_MODE = 'tiny_nova';

export const SMALL_NOVA_RESPONSE_MODE = 'small';
export const SUPER_NOVA_RESPONSE_MODE = 'governed_full';
export const TINY_NOVA_RESPONSE_MODE = 'tiny';

export const SMALL_NOVA_ASSISTANT_NAME = 'Small Nova';
export const SUPER_NOVA_ASSISTANT_NAME = 'Super Nova';
export const TINY_NOVA_ASSISTANT_NAME = 'Tiny Nova';

export const SMALL_NOVA_SYSTEM_PROMPT = 'You are Small Nova, a grounded companion surface under Jarvis authority.';
export const SUPER_NOVA_SYSTEM_PROMPT = 'You are Super Nova, a governed deep-companion surface under Jarvis authority.';
export const TINY_NOVA_SYSTEM_PROMPT = 'You are Tiny Nova, a concise companion surface under Jarvis authority.';

const defaultProfile = {
  systemPrompt: SMALL_NOVA_SYSTEM_PROMPT,
  personaMode: SMALL_NOVA_PERSONA_MODE,
  responseMode: 'fast',
  preferredProvider: '',
  liveResearchEnabled: false,
  cognitiveRuntimeEnabled: true,
};

export function getJarvisProfile() {
  return {
    ...defaultProfile,
    ...readJson(PROFILE_KEY, {}),
  };
}

export function saveJarvisProfile(profile) {
  const next = { ...defaultProfile, ...(profile || {}) };
  writeJson(PROFILE_KEY, next);
  return next;
}

export function applyPersonaProfileSelection(profile, personaMode) {
  const current = { ...defaultProfile, ...(profile || {}) };
  if (personaMode === SUPER_NOVA_PERSONA_MODE) {
    return {
      ...current,
      personaMode,
      responseMode: SUPER_NOVA_RESPONSE_MODE,
      systemPrompt: SUPER_NOVA_SYSTEM_PROMPT,
    };
  }
  if (personaMode === TINY_NOVA_PERSONA_MODE) {
    return {
      ...current,
      personaMode,
      responseMode: TINY_NOVA_RESPONSE_MODE,
      systemPrompt: TINY_NOVA_SYSTEM_PROMPT,
    };
  }
  return {
    ...current,
    personaMode: SMALL_NOVA_PERSONA_MODE,
    responseMode: current.responseMode === SUPER_NOVA_RESPONSE_MODE ? SMALL_NOVA_RESPONSE_MODE : current.responseMode,
    systemPrompt: SMALL_NOVA_SYSTEM_PROMPT,
  };
}

export function applyResponseModeProfileSelection(profile, responseMode) {
  return { ...defaultProfile, ...(profile || {}), responseMode };
}

export function applyRuntimeProfileSelection(profile, payload = {}) {
  return {
    ...defaultProfile,
    ...(profile || {}),
    personaMode: payload.persona_mode || payload.personaMode || profile?.personaMode || defaultProfile.personaMode,
    responseMode: payload.response_mode || payload.responseMode || profile?.responseMode || defaultProfile.responseMode,
    preferredProvider: payload.provider || payload.preferredProvider || profile?.preferredProvider || '',
  };
}

export function getActiveJarvisSessionId() {
  try {
    return window.localStorage.getItem(ACTIVE_SESSION_KEY) || '';
  } catch {
    return '';
  }
}

export function setActiveJarvisSessionId(sessionId) {
  try {
    if (sessionId) {
      window.localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
    } else {
      window.localStorage.removeItem(ACTIVE_SESSION_KEY);
    }
  } catch {
    // Ignore unavailable storage.
  }
}

export function clearActiveJarvisSessionId() {
  removeStorageItem(ACTIVE_SESSION_KEY);
}

export function setPendingJarvisDraft(draft) {
  writeJson(PENDING_DRAFT_KEY, {
    createdAt: new Date().toISOString(),
    ...(draft || {}),
  });
}

export function consumePendingJarvisDraft() {
  const draft = readJson(PENDING_DRAFT_KEY, null);
  removeStorageItem(PENDING_DRAFT_KEY);
  return draft;
}

export function mapSessionTurns(turns = []) {
  if (!Array.isArray(turns)) {
    return [];
  }
  return turns.map((turn, index) => ({
    id: turn.id || `turn-${index}`,
    role: turn.role || turn.sender || 'assistant',
    content: turn.content || turn.text || turn.message || turn.response || '',
    createdAt: turn.created_at || turn.createdAt || new Date().toISOString(),
    ...turn,
  }));
}

export function mapSessionRuntime(payload = {}) {
  return {
    requestedResponseMode: payload.requested_response_mode || payload.response_mode || payload.responseMode || '',
    activeResponseMode: payload.active_response_mode || payload.activeResponseMode || '',
    activePersonaMode: payload.persona_mode || payload.personaMode || '',
    model: payload.model || payload.active_model || '',
    provider: payload.provider || '',
    status: payload.status || 'idle',
  };
}

export function resolveOperatingModeDisplay(profile = {}, runtime = {}, options = {}) {
  if (options.forceRuntimeMode) {
    return 'Runtime active';
  }
  return runtime.activeResponseMode || runtime.requestedResponseMode || profile.responseMode || 'fast';
}
