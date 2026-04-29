import React, { startTransition, useCallback, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import {
  FiArrowRight,
  FiCompass,
  FiFileText,
  FiLink2,
  FiPaperclip,
  FiRefreshCw,
  FiSend,
  FiStar,
} from 'react-icons/fi';
import { Link } from 'react-router-dom';
import { apiGet, apiPost, apiPostStream, getApiErrorMessage } from '../lib/api';
import {
  applyPersonaProfileSelection,
  clearActiveJarvisSessionId,
  consumePendingJarvisDraft,
  getActiveJarvisSessionId,
  getJarvisProfile,
  mapSessionTurns,
  saveJarvisProfile,
  SMALL_NOVA_ASSISTANT_NAME,
  setActiveJarvisSessionId,
  SMALL_NOVA_PERSONA_MODE,
  SMALL_NOVA_RESPONSE_MODE,
  SMALL_NOVA_SYSTEM_PROMPT,
  SUPER_NOVA_ASSISTANT_NAME,
  SUPER_NOVA_PERSONA_MODE,
  SUPER_NOVA_RESPONSE_MODE,
  SUPER_NOVA_SYSTEM_PROMPT,
  TINY_NOVA_ASSISTANT_NAME,
  TINY_NOVA_PERSONA_MODE,
  TINY_NOVA_RESPONSE_MODE,
  TINY_NOVA_SYSTEM_PROMPT,
} from '../lib/jarvis';
import {
  buildDefaultNovaArchiveTitle,
  clearActiveNovaSessionArchive,
  consumePendingNovaSessionArchive,
  getActiveNovaSessionArchive,
  listNovaSessionArchives,
  openNovaSessionArchive,
  saveNovaSessionArchive,
  setActiveNovaSessionArchive,
  toLoadedSessionArchivePayload,
} from '../lib/novaSessionArchive';
import './NovaLandingPage.css';

const DEFAULT_COMPANION_PERSONA = SMALL_NOVA_PERSONA_MODE;
const COMPANION_PERSONA_MODES = [
  SMALL_NOVA_PERSONA_MODE,
  SUPER_NOVA_PERSONA_MODE,
  TINY_NOVA_PERSONA_MODE,
];

const COMPANION_SURFACES = {
  [SMALL_NOVA_PERSONA_MODE]: {
    personaMode: SMALL_NOVA_PERSONA_MODE,
    responseMode: SMALL_NOVA_RESPONSE_MODE,
    systemPrompt: SMALL_NOVA_SYSTEM_PROMPT,
    assistantName: SMALL_NOVA_ASSISTANT_NAME,
    blurb: 'Grounded, steadier, and a little deeper.',
    heroLead: 'Small Nova is the installed companion lane: a steadier chat, a visible intake lane, and a quieter first step into the system while Jarvis keeps authority.',
    greeting: 'I’m Small Nova. Bring me the question, the note, or the document you want to work through.',
    starterPrompts: [
      'Help me sort the next step I should take today.',
      'Read this idea with me and tell me what feels true.',
      'Ground this answer in the documents I already uploaded.',
    ],
    intakeSuccess: 'is now in Small Nova\'s intake.',
    intakeHeading: 'Bring source material in without leaving Small Nova.',
    promptPlaceholder: 'Bring Small Nova the question, the draft, or the feeling you want help sorting.',
    chatModeLabel: 'Small Nova chat',
    heading: 'Ask Small Nova directly.',
    siteSignal: 'Small Nova is live on the companion surface.',
    siteIntakeContext: 'Small Nova site intake',
    pastedNoteContext: 'Small Nova pasted note intake',
    pastedNoteSource: 'Small Nova pasted note',
    urlIntakeContext: 'Small Nova URL intake',
    offlineDetail: 'Start the backend to chat with Small Nova.',
    checkingDetail: 'Small Nova is checking the local runtime.',
    readyLabel: 'Small Nova ready',
  },
  [SUPER_NOVA_PERSONA_MODE]: {
    personaMode: SUPER_NOVA_PERSONA_MODE,
    responseMode: SUPER_NOVA_RESPONSE_MODE,
    systemPrompt: SUPER_NOVA_SYSTEM_PROMPT,
    assistantName: SUPER_NOVA_ASSISTANT_NAME,
    blurb: 'Deeper continuity, structured reflection, and explicit governed activation.',
    heroLead: 'Super Nova is the governed deep-companion lane: broader continuity, calmer multi-thread organization, and explicit activation before live use while Jarvis keeps authority.',
    greeting: 'I’m Super Nova. Activate me when you want deeper continuity and a more structured companion conversation.',
    starterPrompts: [
      'Help me hold the full shape of this problem without losing the next step.',
      'Organize these threads and show me what matters most first.',
      'Stay grounded and help me continue this with deeper continuity.',
    ],
    intakeSuccess: 'is now in Super Nova\'s intake.',
    intakeHeading: 'Bring source material in without leaving Super Nova.',
    promptPlaceholder: 'Activate Super Nova, then bring the deeper thread, draft, or question you want to work through.',
    chatModeLabel: 'Super Nova chat',
    heading: 'Ask Super Nova directly.',
    siteSignal: 'Super Nova is available behind an explicit governed activation gate.',
    siteIntakeContext: 'Super Nova site intake',
    pastedNoteContext: 'Super Nova pasted note intake',
    pastedNoteSource: 'Super Nova pasted note',
    urlIntakeContext: 'Super Nova URL intake',
    offlineDetail: 'Start the backend to activate and chat with Super Nova.',
    checkingDetail: 'Super Nova is checking the local runtime and activation gate.',
    readyLabel: 'Super Nova available',
  },
  [TINY_NOVA_PERSONA_MODE]: {
    personaMode: TINY_NOVA_PERSONA_MODE,
    responseMode: TINY_NOVA_RESPONSE_MODE,
    systemPrompt: TINY_NOVA_SYSTEM_PROMPT,
    assistantName: TINY_NOVA_ASSISTANT_NAME,
    blurb: 'Lighter, briefer, and one-thought-at-a-time.',
    heroLead: 'Tiny Nova is the lighter companion lane: a quieter chat, a visible intake lane, and one gentle thought at a time while Jarvis keeps authority.',
    greeting: 'I’m Tiny Nova. Bring me the question, the note, or the document you want to work through.',
    starterPrompts: [
      'Help me find one gentle next step.',
      'Read this note with me and tell me what stands out first.',
      'Stay with this feeling for one quiet thought.',
    ],
    intakeSuccess: 'is now in Tiny Nova\'s intake.',
    intakeHeading: 'Bring source material in without leaving Tiny Nova.',
    promptPlaceholder: 'Bring Tiny Nova the question, the draft, or the feeling you want help sorting.',
    chatModeLabel: 'Tiny Nova chat',
    heading: 'Ask Tiny Nova directly.',
    siteSignal: 'Tiny Nova is live on the companion surface.',
    siteIntakeContext: 'Tiny Nova site intake',
    pastedNoteContext: 'Tiny Nova pasted note intake',
    pastedNoteSource: 'Tiny Nova pasted note',
    urlIntakeContext: 'Tiny Nova URL intake',
    offlineDetail: 'Start the backend to chat with Tiny Nova.',
    checkingDetail: 'Tiny Nova is checking the local runtime.',
    readyLabel: 'Tiny Nova ready',
  },
};

const baseSurfaceCategories = [
  {
    id: 'nova',
    label: 'Nova',
    summary: 'Chat, intake, and orientation',
    items: [
      { label: 'Open Chat', href: '#chat', detail: 'Return to companion conversation.' },
      { label: 'Document Intake', href: '#intake', detail: 'Upload PDF, text, or URL context.' },
    ],
  },
  {
    id: 'console',
    label: 'Console',
    summary: 'Jarvis operator spine',
    items: [
      { label: 'Operator Console', to: '/jarvis', detail: 'Open the command cockpit.' },
      { label: 'Tool Layer', to: '/jarvis#jarvis-tool-layer', detail: 'Jump to tools, workspace, and execution rails.' },
    ],
  },
  {
    id: 'memory',
    label: 'Memory',
    summary: 'Continuity and history',
    items: [
      { label: 'Memory Bank', to: '/memory', detail: 'Durable notes, overrides, and continuity edits.' },
      { label: 'Memory Log', to: '/history', detail: 'Review prior sessions and saved activity.' },
    ],
  },
  {
    id: 'tools',
    label: 'Tools',
    summary: 'Analysis and generation',
    items: [
      { label: 'Prompt Lab', to: '/prompt-lab', detail: 'Draft and refine prompt-driven output.' },
      { label: 'Image Analyzer', to: '/image-analyzer', detail: 'Inspect images and extracted signal.' },
      { label: 'Audio Processor', to: '/audio-processor', detail: 'Process voice and audio inputs.' },
      { label: 'Batch Tools', to: '/batch-processor', detail: 'Run grouped jobs and repeated tasks.' },
    ],
  },
  {
    id: 'workflows',
    label: 'Workflows',
    summary: 'Automation and approvals',
    items: [
      { label: 'Workflow Builder', to: '/workflows', detail: 'Create and edit automation flows.' },
      { label: 'Runs', to: '/workflows/runs', detail: 'Inspect execution history.' },
      { label: 'Approvals', to: '/workflows/approvals', detail: 'Review pending decisions.' },
      { label: 'Templates', to: '/workflows/templates', detail: 'Start from reusable patterns.' },
    ],
  },
  {
    id: 'system',
    label: 'System',
    summary: 'Settings and operational state',
    items: [
      { label: 'Settings', to: '/settings', detail: 'Adjust client and runtime behavior.' },
      { label: 'Operator Cockpit', to: '/jarvis', detail: 'Review routing, guardrails, and live state.' },
      { label: 'Onboarding', to: '/onboarding', detail: 'Walk the available platform surfaces.' },
    ],
  },
];

function getCompanionSurface(personaMode) {
  return COMPANION_SURFACES[personaMode] || COMPANION_SURFACES[DEFAULT_COMPANION_PERSONA];
}

function resolveCompanionPersona(profile) {
  const requestedPersona = profile?.personaMode;
  if (COMPANION_PERSONA_MODES.includes(requestedPersona)) {
    return requestedPersona;
  }
  return DEFAULT_COMPANION_PERSONA;
}

function loadInitialCompanionPersona() {
  try {
    return resolveCompanionPersona(getJarvisProfile());
  } catch (error) {
    return DEFAULT_COMPANION_PERSONA;
  }
}

function buildSurfaceCategories(surface) {
  return baseSurfaceCategories.map((category) => {
    if (category.id !== 'nova') {
      return category;
    }
    return {
      ...category,
      label: surface.assistantName,
      items: [
        { label: 'Open Chat', href: '#chat', detail: `Return to ${surface.assistantName} conversation.` },
        { label: 'Document Intake', href: '#intake', detail: 'Upload PDF, text, or URL context.' },
      ],
    };
  });
}

function buildCalmSignals(surface) {
  return [
    surface.siteSignal,
    'Jarvis still holds routing, state, and execution authority.',
    'One quiet place to talk, think, and orient.',
    'Document intake that stays visible and inspectable.',
    'Console, Memory Bank, and operator categories stay reachable.',
  ];
}

function buildClientId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function buildDefaultMessages(surface = getCompanionSurface(DEFAULT_COMPANION_PERSONA)) {
  return [
    {
      id: buildClientId('assistant'),
      role: 'assistant',
      content: surface.greeting,
      timestamp: new Date().toISOString(),
      mode: 'chat',
      sources: [],
      streaming: false,
    },
  ];
}

function slugifyDocumentId(value) {
  return String(value || 'nova_document')
    .replace(/\.[^/.]+$/, '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 48) || 'nova_document';
}

function formatDocumentRole(role) {
  return String(role || 'context')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function normalizeDocuments(response) {
  return [...(response?.data?.documents || [])].reverse();
}

function summarizeHealth(response) {
  const aiStatus = response?.data?.ai_status || 'offline';
  const modelMode = response?.data?.active_model_mode || 'unknown';

  if (aiStatus === 'initialized') {
    return {
      tone: 'connected',
      label: 'Backend online',
      detail: `Model mode: ${modelMode}`,
    };
  }

  return {
    tone: 'warning',
    label: 'Backend warming',
    detail: `AI status: ${aiStatus}`,
  };
}

function isSuperNovaPersona(personaMode) {
  return personaMode === SUPER_NOVA_PERSONA_MODE;
}

function summarizeSuperNovaActivation(superNovaState) {
  const activation = superNovaState?.activation || {};
  const continuity = superNovaState?.continuity || {};
  const currentState = activation.current_state || 'dormant';
  const failureReasons = continuity.failure_reasons || activation.last_failure_reasons || [];

  if (currentState === 'activation_ready' && activation.activation_token_present) {
    return {
      tone: 'connected',
      label: 'Activation ready',
      detail: continuity.status === 'verified'
        ? 'Token live and continuity verified.'
        : 'Token live, but continuity still needs review.',
      currentState,
      failureReasons,
    };
  }

  if (currentState === 'paused') {
    return {
      tone: 'warning',
      label: 'Paused',
      detail: 'Super Nova is paused by operator control.',
      currentState,
      failureReasons,
    };
  }

  if (currentState === 'stopped') {
    return {
      tone: 'error',
      label: 'Stopped',
      detail: 'The live token was revoked. Activate again to continue.',
      currentState,
      failureReasons,
    };
  }

  return {
    tone: failureReasons.length ? 'warning' : 'warning',
    label: 'Needs activation',
    detail: failureReasons.length
      ? `Blocked until activation passes: ${failureReasons.join(', ')}`
      : 'Explicit activation is required before Super Nova can answer live.',
    currentState,
    failureReasons,
  };
}

function NovaLandingPage() {
  const [companionPersona, setCompanionPersona] = useState(loadInitialCompanionPersona);
  const surface = getCompanionSurface(companionPersona);
  const [messages, setMessages] = useState(() => buildDefaultMessages(getCompanionSurface(loadInitialCompanionPersona())));
  const [draft, setDraft] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [activeMode, setActiveMode] = useState('chat');
  const [documents, setDocuments] = useState([]);
  const [backendStatus, setBackendStatus] = useState({
    tone: 'warning',
    label: 'Checking backend',
    detail: getCompanionSurface(loadInitialCompanionPersona()).checkingDetail,
  });
  const [sending, setSending] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [fileUploading, setFileUploading] = useState(false);
  const [textUploading, setTextUploading] = useState(false);
  const [urlUploading, setUrlUploading] = useState(false);
  const [textIntake, setTextIntake] = useState('');
  const [urlIntake, setUrlIntake] = useState('');
  const [superNovaState, setSuperNovaState] = useState(null);
  const [superNovaBusy, setSuperNovaBusy] = useState(false);
  const [archiveEntries, setArchiveEntries] = useState([]);
  const [archiveSaving, setArchiveSaving] = useState(false);
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [archivePanelOpen, setArchivePanelOpen] = useState(false);
  const [archiveTitle, setArchiveTitle] = useState('');
  const [archiveTags, setArchiveTags] = useState('');
  const [archivePassphraseEnabled, setArchivePassphraseEnabled] = useState(false);
  const [archivePassphrase, setArchivePassphrase] = useState('');
  const [loadedArchive, setLoadedArchive] = useState(() => getActiveNovaSessionArchive());
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const streamAbortRef = useRef(null);
  const surfaceCategories = buildSurfaceCategories(surface);
  const calmSignals = buildCalmSignals(surface);
  const superNovaSurface = isSuperNovaPersona(companionPersona);
  const superNovaActivation = superNovaState?.activation || {};
  const superNovaContinuity = superNovaState?.continuity || {};
  const superNovaStatus = summarizeSuperNovaActivation(superNovaState);
  const superNovaReady = !superNovaSurface || (
    superNovaActivation.current_state === 'activation_ready'
    && Boolean(superNovaActivation.activation_token_present)
  );

  const persistCompanionProfile = useCallback((personaMode) => {
    const nextProfile = applyPersonaProfileSelection(getJarvisProfile(), personaMode);
    saveJarvisProfile(nextProfile);
  }, []);

  const syncSuperNovaState = useCallback((payload, personaMode = companionPersona) => {
    if (isSuperNovaPersona(personaMode)) {
      setSuperNovaState(payload?.super_nova || null);
      return;
    }
    setSuperNovaState(null);
  }, [companionPersona]);

  const patchMessage = (messageId, patch) => {
    setMessages((current) => current.map((message) => (
      message.id === messageId ? { ...message, ...patch } : message
    )));
  };

  const refreshDocuments = async () => {
    const response = await apiGet('/api/documents');
    startTransition(() => {
      setDocuments(normalizeDocuments(response));
    });
    return response;
  };

  const refreshArchiveEntries = useCallback(async () => {
    const entries = await listNovaSessionArchives();
    startTransition(() => {
      setArchiveEntries(entries);
    });
    return entries;
  }, []);

  const refreshSuperNovaStatus = useCallback(async (targetSessionId = sessionId, targetPersona = companionPersona) => {
    if (!targetSessionId || !isSuperNovaPersona(targetPersona)) {
      setSuperNovaState(null);
      return null;
    }

    const response = await apiGet(`/api/chat/sessions/${targetSessionId}/super-nova/status`);
    startTransition(() => {
      setSuperNovaState(response.data?.super_nova || null);
    });
    return response.data?.super_nova || null;
  }, [companionPersona, sessionId]);

  const applyLoadedArchive = (nextArchive) => {
    const normalizedArchive = nextArchive || null;
    setLoadedArchive(normalizedArchive);
    if (normalizedArchive) {
      setActiveNovaSessionArchive(normalizedArchive);
      return;
    }
    clearActiveNovaSessionArchive();
  };

  const refreshSurface = useCallback(async () => {
    setRefreshing(true);
    try {
      const [healthResult, documentsResult, archiveResult] = await Promise.allSettled([
        apiGet('/health'),
        apiGet('/api/documents'),
        refreshArchiveEntries(),
      ]);

      if (healthResult.status === 'fulfilled') {
        setBackendStatus(summarizeHealth(healthResult.value));
      } else {
        setBackendStatus({
          tone: 'error',
          label: 'Backend offline',
          detail: surface.offlineDetail,
        });
      }

      if (documentsResult.status === 'fulfilled') {
        startTransition(() => {
          setDocuments(normalizeDocuments(documentsResult.value));
        });
      }

      if (archiveResult.status === 'fulfilled') {
        startTransition(() => {
          setArchiveEntries(archiveResult.value);
        });
      }
      if (sessionId && isSuperNovaPersona(companionPersona)) {
        try {
          await refreshSuperNovaStatus(sessionId, companionPersona);
        } catch (error) {
          setSuperNovaState(null);
        }
      }
    } finally {
      setRefreshing(false);
    }
  }, [companionPersona, refreshArchiveEntries, refreshSuperNovaStatus, sessionId, surface.offlineDetail]);

  const hydrateNovaSession = useCallback(async (targetPersona = companionPersona) => {
    const targetSurface = getCompanionSurface(targetPersona);
    const storedSessionId = getActiveJarvisSessionId();

    if (storedSessionId) {
      try {
        const response = await apiGet(`/api/chat/sessions/${storedSessionId}`);
        if (response.data?.persona_mode === targetSurface.personaMode) {
          setSessionId(storedSessionId);
          syncSuperNovaState(response.data, targetSurface.personaMode);
          startTransition(() => {
            setMessages(mapSessionTurns(response.data.turns).length
              ? mapSessionTurns(response.data.turns)
              : buildDefaultMessages(targetSurface));
          });
          if (isSuperNovaPersona(targetSurface.personaMode) && !response.data?.super_nova) {
            await refreshSuperNovaStatus(storedSessionId, targetSurface.personaMode);
          }
          return storedSessionId;
        }
      } catch (error) {
        clearActiveJarvisSessionId();
      }
    }

    persistCompanionProfile(targetSurface.personaMode);
    const response = await apiPost('/api/chat/sessions', {
      system_prompt: targetSurface.systemPrompt,
      persona_mode: targetSurface.personaMode,
      response_mode: targetSurface.responseMode,
    });

    setActiveJarvisSessionId(response.data.session_id);
    setSessionId(response.data.session_id);
    syncSuperNovaState(response.data, targetSurface.personaMode);
    startTransition(() => {
      setMessages(mapSessionTurns(response.data.turns).length
        ? mapSessionTurns(response.data.turns)
        : buildDefaultMessages(targetSurface));
    });
    if (isSuperNovaPersona(targetSurface.personaMode) && !response.data?.super_nova) {
      await refreshSuperNovaStatus(response.data.session_id, targetSurface.personaMode);
    }
    return response.data.session_id;
  }, [companionPersona, persistCompanionProfile, refreshSuperNovaStatus, syncSuperNovaState]);

  const ensureNovaSession = useCallback(async () => {
    if (sessionId) {
      return sessionId;
    }

    return hydrateNovaSession();
  }, [hydrateNovaSession, sessionId]);

  useEffect(() => {
    let active = true;
    persistCompanionProfile(companionPersona);

    const bootstrap = async () => {
      await refreshSurface();

      try {
        const nextSessionId = await hydrateNovaSession(companionPersona);
        if (!active) {
          return;
        }

        const pendingDraft = consumePendingJarvisDraft();
        if (pendingDraft?.text) {
          setDraft((current) => {
            const existing = String(current || '').trim();
            return existing ? `${existing}\n\n${pendingDraft.text}` : pendingDraft.text;
          });
        }

        if (nextSessionId) {
          setBackendStatus((current) => (
            current.tone === 'error'
              ? current
              : { ...current, label: surface.readyLabel, detail: current.detail }
          ));
        }

        const pendingArchive = consumePendingNovaSessionArchive() || getActiveNovaSessionArchive();
        if (pendingArchive) {
          applyLoadedArchive(pendingArchive);
        }
      } catch (error) {
        if (!active) {
          return;
        }

        setBackendStatus({
          tone: 'error',
          label: 'Backend offline',
          detail: surface.offlineDetail,
        });
      }
    };

    bootstrap();

    return () => {
      active = false;
      streamAbortRef.current?.abort?.();
      streamAbortRef.current = null;
    };
  }, [
    companionPersona,
    hydrateNovaSession,
    persistCompanionProfile,
    refreshSurface,
    surface.offlineDetail,
    surface.readyLabel,
  ]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (mode = activeMode) => {
    const text = draft.trim();
    if (!text || sending) {
      return;
    }

    if (superNovaSurface && !superNovaReady) {
      toast.error('Activate Super Nova before sending a live turn.');
      return;
    }

    if (mode === 'documents' && documents.length === 0) {
      toast.error(`Upload a document first so ${surface.assistantName} has something to ground against.`);
      return;
    }

    const userMessage = {
      id: buildClientId('user'),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
      mode,
      sources: [],
      streaming: false,
    };
    const assistantMessageId = buildClientId('assistant');

    setDraft('');
    setSending(true);
    setMessages((current) => [
      ...current,
      userMessage,
      {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        mode,
        sources: [],
        streaming: true,
      },
    ]);

    try {
      if (mode === 'documents') {
        const response = await apiPost('/api/documents/ask', {
          query: text,
          top_k: 5,
          max_length: 512,
        });

        patchMessage(assistantMessageId, {
          content: response.data?.answer || 'No document answer was returned.',
          sources: response.data?.sources || [],
          streaming: false,
        });
      } else {
        const activeSessionId = await ensureNovaSession();
        const abortController = new AbortController();
        streamAbortRef.current = abortController;
        let finalPayload = null;
        let streamError = null;

        await apiPostStream(
          `/api/chat/sessions/${activeSessionId}/stream`,
          {
            message: text,
            persona_mode: surface.personaMode,
            response_mode: surface.responseMode,
            loaded_session_archive: loadedArchive
              ? toLoadedSessionArchivePayload(loadedArchive)
              : null,
          },
          {
            signal: abortController.signal,
            onEvent: (payload) => {
              if (payload.event === 'token') {
                patchMessage(assistantMessageId, {
                  content: payload.text_so_far || '',
                  streaming: !payload.finished,
                });
                return;
              }

              if (payload.event === 'final') {
                finalPayload = payload;
                patchMessage(assistantMessageId, {
                  content: payload.response || '',
                  streaming: false,
                });
                syncSuperNovaState(payload, surface.personaMode);
                return;
              }

              if (payload.event === 'error') {
                streamError = new Error(payload.error || 'Streaming failed');
              }
            },
          },
        );

        if (streamError) {
          throw streamError;
        }

        if (finalPayload?.response) {
          patchMessage(assistantMessageId, {
            content: finalPayload.response,
            streaming: false,
          });
        }

        if (finalPayload?.loaded_session_archive) {
          applyLoadedArchive({
            ...loadedArchive,
            ...finalPayload.loaded_session_archive,
          });
        }
        if (finalPayload?.super_nova) {
          setSuperNovaState(finalPayload.super_nova);
        }
      }

      setBackendStatus((current) => (
        current.tone === 'error'
          ? current
          : { ...current, tone: 'connected', label: 'Backend online' }
      ));
    } catch (error) {
      patchMessage(assistantMessageId, {
        content: getApiErrorMessage(error, `${surface.assistantName} could not answer right now.`),
        error: true,
        streaming: false,
      });
      if (error?.response?.data?.super_nova) {
        setSuperNovaState(error.response.data.super_nova);
      }
      setBackendStatus({
        tone: 'error',
        label: 'Backend offline',
        detail: surface.offlineDetail,
      });
      toast.error(getApiErrorMessage(error, `${surface.assistantName} could not answer right now.`));
    } finally {
      streamAbortRef.current = null;
      setSending(false);
    }
  };

  const handleCompanionSwitch = async (targetPersona) => {
    if (targetPersona === companionPersona || sending) {
      return;
    }
    const targetSurface = getCompanionSurface(targetPersona);
    streamAbortRef.current?.abort?.();
    streamAbortRef.current = null;
    setSending(false);
    setDraft('');
    setSessionId('');
    setActiveMode('chat');
    setSuperNovaState(null);
    setMessages(buildDefaultMessages(targetSurface));
    setBackendStatus((current) => ({
      ...current,
      label: 'Checking backend',
      detail: targetSurface.checkingDetail,
    }));
    clearActiveJarvisSessionId();
    persistCompanionProfile(targetPersona);
    setCompanionPersona(targetPersona);
  };

  const runSuperNovaControl = async (path, successMessage) => {
    const activeSessionId = await ensureNovaSession();
    setSuperNovaBusy(true);
    try {
      const response = await apiPost(`/api/chat/sessions/${activeSessionId}${path}`, {});
      syncSuperNovaState(response.data, SUPER_NOVA_PERSONA_MODE);
      if (successMessage) {
        toast.success(successMessage);
      }
    } catch (error) {
      if (error?.response?.data) {
        syncSuperNovaState(error.response.data, SUPER_NOVA_PERSONA_MODE);
      }
      toast.error(getApiErrorMessage(error, 'Super Nova control request failed.'));
    } finally {
      setSuperNovaBusy(false);
    }
  };

  const handleActivateSuperNova = async () => {
    await runSuperNovaControl('/super-nova/activate', 'Super Nova activated.');
  };

  const handlePauseSuperNova = async () => {
    await runSuperNovaControl('/super-nova/pause', 'Super Nova paused.');
  };

  const handleResumeSuperNova = async () => {
    await runSuperNovaControl('/super-nova/resume', 'Super Nova resumed.');
  };

  const handleStopSuperNova = async () => {
    await runSuperNovaControl('/super-nova/stop', 'Super Nova stopped.');
  };

  const handleFileIntake = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setFileUploading(true);

    try {
      const normalizedName = slugifyDocumentId(file.name);
      const isPdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name);
      const isText = file.type.startsWith('text/') || /\.(md|txt)$/i.test(file.name);

      if (isPdf) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('doc_id', normalizedName);
        formData.append('role', 'input_artifact');
        formData.append('operator_context', surface.siteIntakeContext);
        formData.append('metadata', JSON.stringify({ source: file.name }));
        await apiPost('/api/documents/upload/pdf', formData);
      } else if (isText) {
        const text = await file.text();
        await apiPost('/api/documents/upload/text', {
          text,
          doc_id: normalizedName,
          role: 'input_artifact',
          operator_context: surface.siteIntakeContext,
          metadata: { source: file.name },
        });
      } else {
        throw new Error('Upload a PDF, TXT, or MD file for intake.');
      }

      await refreshDocuments();
      setActiveMode('documents');
      toast.success(`${file.name} ${surface.intakeSuccess}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Document intake failed.'));
    } finally {
      event.target.value = '';
      setFileUploading(false);
    }
  };

  const handleTextIntake = async () => {
    const text = textIntake.trim();
    if (!text) {
      toast.error('Paste a note before sending it to intake.');
      return;
    }

    setTextUploading(true);
    try {
      await apiPost('/api/documents/upload/text', {
        text,
        doc_id: slugifyDocumentId(`nova_note_${Date.now()}`),
        role: 'input_artifact',
        operator_context: surface.pastedNoteContext,
        metadata: { source: surface.pastedNoteSource },
      });
      setTextIntake('');
      setActiveMode('documents');
      await refreshDocuments();
      toast.success('Pasted note added to intake.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Text intake failed.'));
    } finally {
      setTextUploading(false);
    }
  };

  const handleUrlIntake = async () => {
    const url = urlIntake.trim();
    if (!url) {
      toast.error('Add a URL before sending it to intake.');
      return;
    }

    setUrlUploading(true);
    try {
      await apiPost('/api/documents/upload/url', {
        url,
        doc_id: slugifyDocumentId(url),
        role: 'input_artifact',
        operator_context: surface.urlIntakeContext,
        metadata: { source: url },
      });
      setUrlIntake('');
      setActiveMode('documents');
      await refreshDocuments();
      toast.success('URL content added to intake.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'URL intake failed.'));
    } finally {
      setUrlUploading(false);
    }
  };

  const openArchiveSavePanel = () => {
    setArchiveTitle((current) => current || buildDefaultNovaArchiveTitle(surface.assistantName));
    setArchivePanelOpen(true);
  };

  const closeArchiveSavePanel = () => {
    setArchivePanelOpen(false);
    setArchivePassphrase('');
    setArchivePassphraseEnabled(false);
  };

  const handleSaveSessionArchive = async () => {
    const storableMessages = messages.filter((message) => String(message?.content || '').trim());
    if (!storableMessages.length) {
      toast.error('There is no session content to save yet.');
      return;
    }

    if (archivePassphraseEnabled && !archivePassphrase.trim()) {
      toast.error('Add a passphrase or switch back to device-local encryption.');
      return;
    }

    setArchiveSaving(true);
    try {
      await saveNovaSessionArchive({
        title: archiveTitle.trim() || buildDefaultNovaArchiveTitle(surface.assistantName),
        tags: archiveTags,
        messages: storableMessages,
        sessionId,
        assistantName: surface.assistantName,
        personaMode: surface.personaMode,
        responseMode: surface.responseMode,
        passphrase: archivePassphraseEnabled ? archivePassphrase : '',
      });
      await refreshArchiveEntries();
      closeArchiveSavePanel();
      setArchiveTitle('');
      setArchiveTags('');
      toast.success('Session saved to the local Nova archive.');
    } catch (error) {
      toast.error(error.message || 'Nova could not save this local session archive.');
    } finally {
      setArchiveSaving(false);
    }
  };

  const handleQuickArchiveLoad = async (archiveId) => {
    setArchiveLoading(true);
    try {
      const activeArchive = await openNovaSessionArchive(archiveId);
      applyLoadedArchive(activeArchive);
      toast.success('Session archive loaded as document context.');
    } catch (error) {
      toast.error(error.message || 'Nova could not open that local session archive.');
    } finally {
      setArchiveLoading(false);
    }
  };

  const handleClearLoadedArchive = () => {
    applyLoadedArchive(null);
    toast.success('Loaded session archive cleared.');
  };

  return (
    <div className="nova-site">
      <section className="nova-hero" id="top">
        <div className="nova-hero__veil" aria-hidden="true" />
        <div className="nova-hero__grid" aria-hidden="true" />
        <div className="nova-hero__content">
          <div className="nova-hero__copy">
            <p className="nova-eyebrow">{surface.assistantName}</p>
            <h1>One calm companion surface to talk and take in documents.</h1>
            <p className="nova-lead">{surface.heroLead}</p>
            <div className="nova-companion-switch" aria-label="Companion tier">
              {COMPANION_PERSONA_MODES.map((personaMode) => {
                const option = getCompanionSurface(personaMode);
                const active = personaMode === companionPersona;
                return (
                  <button
                    key={personaMode}
                    type="button"
                    className={`nova-companion-chip ${active ? 'active' : ''}`}
                    onClick={() => handleCompanionSwitch(personaMode)}
                    disabled={sending}
                    aria-pressed={active}
                  >
                    <strong>{option.assistantName}</strong>
                    <span>{option.blurb}</span>
                  </button>
                );
              })}
            </div>
            <div className="nova-actions">
              <a className="nova-button nova-button--primary" href="#chat">
                Open Chat
                <FiArrowRight />
              </a>
              <a className="nova-button nova-button--ghost" href="#intake">
                Document Intake
              </a>
              <Link className="nova-button nova-button--ghost" to="/jarvis">
                Console
              </Link>
              <Link className="nova-button nova-button--ghost" to="/memory">
                Memory Bank
              </Link>
              <Link className="nova-button nova-button--ghost" to="/history">
                Session Archive
              </Link>
            </div>
            <section className="nova-category-deck page-panel" id="categories" aria-label="System categories">
              <div className="nova-category-deck__header">
                <div>
                  <p className="nova-kicker">System Categories</p>
                  <h2>Architecture navigation stays near the banner.</h2>
                </div>
                <span className="status-pill connected">jarvis authority preserved</span>
              </div>

              <div className="nova-category-grid">
                {surfaceCategories.map((category) => (
                  <details key={category.id} className="nova-category-menu">
                    <summary className="nova-category-summary">
                      <span>{category.label}</span>
                      <strong>{category.summary}</strong>
                    </summary>
                    <div className="nova-category-menu__content">
                      {category.items.map((item) => (
                        item.to ? (
                          <Link key={item.label} className="nova-category-link" to={item.to}>
                            <strong>{item.label}</strong>
                            <span>{item.detail}</span>
                          </Link>
                        ) : (
                          <a key={item.label} className="nova-category-link" href={item.href}>
                            <strong>{item.label}</strong>
                            <span>{item.detail}</span>
                          </a>
                        )
                      ))}
                    </div>
                  </details>
                ))}
              </div>
            </section>
            <div className="nova-status-row">
              <span className={`status-pill ${backendStatus.tone}`}>{backendStatus.label}</span>
              <span className="nova-status-detail">{backendStatus.detail}</span>
            </div>
            <ul className="nova-signals" aria-label="Nova signals">
              {calmSignals.map((signal) => (
                <li key={signal}>{signal}</li>
              ))}
            </ul>
          </div>

          <section className="nova-live-panel page-panel" id="chat">
            <div className="nova-live-panel__header">
              <div>
                <p className="nova-kicker">Live Conversation</p>
                <h2>{surface.heading}</h2>
              </div>
              <button
                type="button"
                className="nova-inline-action"
                onClick={() => fileInputRef.current?.click()}
                disabled={fileUploading || textUploading || urlUploading}
              >
                <FiPaperclip />
                Document Intake
              </button>
            </div>

            <section className="nova-archive-panel" aria-label="Session archive">
              <div className="nova-archive-panel__intro">
                <p className="nova-kicker">Session Archive</p>
                <h3>Save locally, then load later as a document.</h3>
                <p>
                  Opt-in only. Stored on this device. Loaded archives are explicit reference
                  context, not Nova memory.
                </p>
              </div>
              <div className="nova-archive-panel__actions">
                <button
                  type="button"
                  className="nova-button nova-button--ghost"
                  onClick={openArchiveSavePanel}
                  disabled={sending || archiveSaving}
                >
                  Save Session
                </button>
                <Link className="nova-button nova-button--ghost" to="/history">
                  Open Archive
                </Link>
              </div>
            </section>

            {superNovaSurface ? (
              <section className="nova-super-panel" aria-label="Super Nova controls">
                <div className="nova-super-panel__intro">
                  <p className="nova-kicker">Super Nova Control</p>
                  <h3>Explicit activation, visible state, and governed continuity.</h3>
                  <p>
                    Super Nova stays under Jarvis authority. She must be activated before live use,
                    and the watchdog can pause or revoke the lane if continuity drifts.
                  </p>
                </div>
                <div className="nova-super-panel__status">
                  <span className={`status-pill ${superNovaStatus.tone}`}>{superNovaStatus.label}</span>
                  <span className="nova-status-detail">{superNovaStatus.detail}</span>
                </div>
                <div className="nova-super-panel__facts">
                  <span>State: {superNovaActivation.current_state || 'dormant'}</span>
                  <span>Continuity: {superNovaContinuity.status || 'not_checked'}</span>
                  <span>Trace events: {(superNovaState?.trace || []).length}</span>
                  <span>Immune coupling: {superNovaState?.immune_coupling || 'blocked'}</span>
                </div>
                {superNovaStatus.failureReasons.length ? (
                  <div className="nova-super-panel__reasons">
                    {superNovaStatus.failureReasons.map((reason) => (
                      <span key={reason} className="nova-super-reason">{reason}</span>
                    ))}
                  </div>
                ) : null}
                <div className="nova-super-panel__actions">
                  <button
                    type="button"
                    className="nova-button nova-button--primary"
                    onClick={handleActivateSuperNova}
                    disabled={superNovaBusy || sending || superNovaReady}
                  >
                    {superNovaBusy && !superNovaReady ? 'Activating…' : 'Activate'}
                  </button>
                  <button
                    type="button"
                    className="nova-button nova-button--ghost"
                    onClick={handlePauseSuperNova}
                    disabled={superNovaBusy || !superNovaReady || superNovaActivation.current_state === 'paused'}
                  >
                    Pause
                  </button>
                  <button
                    type="button"
                    className="nova-button nova-button--ghost"
                    onClick={handleResumeSuperNova}
                    disabled={superNovaBusy || superNovaActivation.current_state !== 'paused'}
                  >
                    Resume
                  </button>
                  <button
                    type="button"
                    className="nova-button nova-button--ghost"
                    onClick={handleStopSuperNova}
                    disabled={superNovaBusy || !superNovaActivation.current_state || superNovaActivation.current_state === 'stopped'}
                  >
                    Stop
                  </button>
                </div>
              </section>
            ) : null}

            {loadedArchive ? (
              <section className="nova-loaded-archive" aria-label="Loaded session archive">
                <div>
                  <strong>{loadedArchive.title}</strong>
                  <p>
                    Loaded as document context from this device. Nova should treat it as a saved
                    session you opened, not as memory.
                  </p>
                </div>
                <div className="nova-loaded-archive__actions">
                  <span className="status-pill connected">
                    {loadedArchive.requiresPassphrase ? 'passphrase archive' : 'device-local archive'}
                  </span>
                  <button
                    type="button"
                    className="nova-inline-action"
                    onClick={handleClearLoadedArchive}
                  >
                    Clear
                  </button>
                </div>
              </section>
            ) : null}

            {archivePanelOpen ? (
              <section className="nova-archive-form">
                <label className="nova-field">
                  <span>Session title</span>
                  <input
                    type="text"
                    value={archiveTitle}
                    onChange={(event) => setArchiveTitle(event.target.value)}
                    placeholder={buildDefaultNovaArchiveTitle(surface.assistantName)}
                  />
                </label>

                <label className="nova-field">
                  <span>Tags</span>
                  <input
                    type="text"
                    value={archiveTags}
                    onChange={(event) => setArchiveTags(event.target.value)}
                    placeholder="idea, planning, check-in"
                  />
                </label>

                <label className="nova-toggle-field">
                  <input
                    type="checkbox"
                    checked={archivePassphraseEnabled}
                    onChange={(event) => setArchivePassphraseEnabled(event.target.checked)}
                  />
                  <span>Protect this archive with a passphrase</span>
                </label>

                {archivePassphraseEnabled ? (
                  <label className="nova-field">
                    <span>Passphrase</span>
                    <input
                      type="password"
                      value={archivePassphrase}
                      onChange={(event) => setArchivePassphrase(event.target.value)}
                      placeholder="Enter a passphrase for this archive"
                    />
                  </label>
                ) : null}

                <div className="nova-archive-form__actions">
                  <button
                    type="button"
                    className="nova-button nova-button--ghost"
                    onClick={closeArchiveSavePanel}
                    disabled={archiveSaving}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="nova-button nova-button--primary"
                    onClick={handleSaveSessionArchive}
                    disabled={archiveSaving}
                  >
                    {archiveSaving ? 'Saving…' : 'Save Local Archive'}
                  </button>
                </div>
              </section>
            ) : null}

            <section className="nova-archive-recent" aria-label="Recent saved sessions">
              <div className="nova-archive-recent__head">
                <strong>Recent session archives</strong>
                <span>{archiveEntries.length} saved locally</span>
              </div>

              {archiveEntries.length === 0 ? (
                <p className="nova-empty-copy">
                  No session archive has been saved yet. Use Save Session when you want a local,
                  non-memory record you can reopen later.
                </p>
              ) : (
                <div className="nova-archive-recent__list">
                  {archiveEntries.slice(0, 3).map((entry) => (
                    <article key={entry.id} className="nova-archive-row">
                      <div>
                        <strong>{entry.title}</strong>
                        <p>
                          {entry.assistantName} • {entry.messageCount} messages •{' '}
                          {entry.requiresPassphrase ? 'passphrase' : 'device-local'}
                        </p>
                      </div>
                      {entry.requiresPassphrase ? (
                        <Link className="nova-inline-action" to="/history">
                          Open in Archive
                        </Link>
                      ) : (
                        <button
                          type="button"
                          className="nova-inline-action"
                          onClick={() => handleQuickArchiveLoad(entry.id)}
                          disabled={archiveLoading}
                        >
                          {archiveLoading ? 'Opening…' : 'Load'}
                        </button>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </section>

            <div className="nova-message-feed">
              {messages.map((message) => (
                <article
                  key={message.id}
                  className={`nova-message ${message.role} ${message.error ? 'is-error' : ''}`}
                >
                  <div className="nova-message__meta">
                    <span>{message.role === 'assistant' ? surface.assistantName : 'You'}</span>
                    <span>{message.mode === 'documents' ? 'grounded in intake' : 'chat'}</span>
                  </div>
                  <p>{message.content || (message.streaming ? '...' : '')}</p>
                  {message.sources?.length > 0 && (
                    <div className="nova-source-list">
                      {message.sources.slice(0, 3).map((source) => (
                        <div key={`${message.id}-${source.doc_id}-${source.score}`} className="nova-source-pill">
                          <strong>{source.doc_id}</strong>
                          <span>{source.excerpt}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </article>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <div className="nova-prompt-grid">
              {surface.starterPrompts.map((prompt) => (
                <button
                  type="button"
                  key={prompt}
                  className="nova-prompt-chip"
                  onClick={() => setDraft(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>

            <div className="nova-compose">
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder={surface.promptPlaceholder}
                rows="4"
              />

              <div className="nova-compose__footer">
                <div className="nova-mode-row" aria-label="Conversation mode">
                  <button
                    type="button"
                    className={`nova-mode-chip ${activeMode === 'chat' ? 'active' : ''}`}
                    onClick={() => setActiveMode('chat')}
                  >
                    {surface.chatModeLabel}
                  </button>
                  <button
                    type="button"
                    className={`nova-mode-chip ${activeMode === 'documents' ? 'active' : ''}`}
                    onClick={() => setActiveMode('documents')}
                    disabled={documents.length === 0}
                  >
                    Ask intake
                  </button>
                </div>

                <div className="nova-compose__actions">
                  <button
                    type="button"
                    className="nova-button nova-button--ghost"
                    onClick={refreshSurface}
                    disabled={refreshing}
                  >
                    <FiRefreshCw className={refreshing ? 'is-spinning' : ''} />
                    Refresh
                  </button>
                  <button
                    type="button"
                    className="nova-button nova-button--primary"
                    onClick={() => handleSend()}
                    disabled={sending || !draft.trim() || (superNovaSurface && !superNovaReady)}
                  >
                    <FiSend />
                    {superNovaSurface && !superNovaReady
                      ? 'Activate First'
                      : activeMode === 'documents'
                        ? 'Ask Intake'
                        : 'Send'}
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </section>

      <section className="nova-intake" id="intake">
        <div className="nova-intake__intro">
          <p className="nova-kicker">Document Lane</p>
          <h2>{surface.intakeHeading}</h2>
          <p>
            PDF, text, and URL intake are live here. Once something is ingested, you can switch
            the chat into document-grounded answers with one tap.
          </p>
        </div>

        <div className="nova-intake__grid">
          <div className="nova-intake-card page-panel">
            <div className="nova-card-head">
              <div>
                <span>Upload or Paste</span>
                <h3>New intake</h3>
              </div>
              <FiCompass />
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md,text/plain,application/pdf"
              className="nova-hidden-input"
              onChange={handleFileIntake}
            />

            <button
              type="button"
              className="nova-upload-button"
              onClick={() => fileInputRef.current?.click()}
              disabled={fileUploading}
            >
              <FiPaperclip />
              {fileUploading ? 'Uploading…' : 'Choose PDF or text file'}
            </button>

            <label className="nova-field">
              <span>Paste text</span>
              <textarea
                value={textIntake}
                onChange={(event) => setTextIntake(event.target.value)}
                placeholder="Paste notes, excerpts, or raw thinking here."
                rows="6"
              />
            </label>

            <button
              type="button"
              className="nova-button nova-button--ghost nova-inline-submit"
              onClick={handleTextIntake}
              disabled={textUploading || !textIntake.trim()}
            >
              <FiFileText />
              {textUploading ? 'Ingesting…' : 'Ingest text'}
            </button>

            <label className="nova-field">
              <span>Remote URL</span>
              <input
                type="text"
                value={urlIntake}
                onChange={(event) => setUrlIntake(event.target.value)}
                placeholder="https://example.com/reference"
              />
            </label>

            <button
              type="button"
              className="nova-button nova-button--ghost nova-inline-submit"
              onClick={handleUrlIntake}
              disabled={urlUploading || !urlIntake.trim()}
            >
              <FiLink2 />
              {urlUploading ? 'Ingesting…' : 'Ingest URL'}
            </button>
          </div>

          <div className="nova-intake-card page-panel">
            <div className="nova-card-head">
              <div>
                <span>Current Intake</span>
                <h3>{documents.length} document{documents.length === 1 ? '' : 's'}</h3>
              </div>
              <FiStar />
            </div>

            {documents.length === 0 ? (
              <p className="nova-empty-copy">
                Nothing has been ingested yet. Start with a PDF, a pasted note, or a URL.
              </p>
            ) : (
              <div className="nova-document-list">
                {documents.map((document) => (
                  <article key={document.doc_id} className="nova-document-row">
                    <div>
                      <strong>{document.metadata?.source || document.doc_id}</strong>
                      <p>{formatDocumentRole(document.metadata?.document_role)} • {document.chunk_count} chunks</p>
                    </div>
                    <span className="nova-document-id">{document.doc_id}</span>
                  </article>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

export default NovaLandingPage;
