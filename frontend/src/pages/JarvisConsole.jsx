import React, { startTransition, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import {
  FiActivity,
  FiArrowUpRight,
  FiBookmark,
  FiCheckCircle,
  FiCommand,
  FiCpu,
  FiFolder,
  FiGlobe,
  FiMic,
  FiMicOff,
  FiMonitor,
  FiPlay,
  FiPlus,
  FiRefreshCw,
  FiSearch,
  FiSettings,
  FiShield,
  FiTrash2,
  FiVolume2,
  FiVolumeX,
} from 'react-icons/fi';
import { Link } from 'react-router-dom';
import { apiDelete, apiGet, apiPatch, apiPost, apiPostStream, getApiErrorMessage } from '../lib/api';
import { NetworkStatusCard } from '../components/network-status/NetworkStatusCard';
import { UGRCloudForgeConsoleCard } from '../components/operator/UGRCloudForgeConsoleCard';
import { buildNetworkStatusData } from '../components/network-status/networkStatusLogic';
import { addHistoryEntry } from '../lib/history';
import {
  applyPersonaProfileSelection,
  applyRuntimeProfileSelection,
  applyResponseModeProfileSelection,
  consumePendingJarvisDraft,
  clearActiveJarvisSessionId,
  getActiveJarvisSessionId,
  getJarvisProfile,
  mapSessionRuntime,
  mapSessionTurns,
  resolveOperatingModeDisplay,
  saveJarvisProfile,
  setActiveJarvisSessionId,
  SMALL_NOVA_PERSONA_MODE,
  TINY_NOVA_PERSONA_MODE,
} from '../lib/jarvis';
import { getApiBaseUrl } from '../lib/settings';
import { captureBrowserSnapshot } from '../lib/browserVerify';
import { getBrowserExpectationGuide, listBrowserVerificationTargets } from '../lib/browserExpectations';
import ComposeReceiptPanel from '../components/ComposeReceiptPanel';
import { normalizeComposeReceipt } from '../lib/composeReceipt';
import './JarvisConsole.css';

const DEEP_COMPOSE_STORAGE_KEY = 'jarvis-deep-compose';

const quickActions = [
  'Summarize what I worked on today and suggest the next step.',
  'Help me think through a new app idea and break it into milestones.',
  'Review this bug report and tell me the fastest path to fix it.',
  'Turn my rough idea into a project plan I can actually follow.',
  'Give me a Mystic reading of my current state and the next move.',
  'Run V10 core on this scene idea and tell me if the draft is strong enough.',
];

function slugifyDocumentId(value) {
  return String(value || 'jarvis_document')
    .replace(/\.[^/.]+$/, '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 48) || 'jarvis_document';
}

function formatDocumentRole(role) {
  return String(role || 'context')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

const mysticPresets = [
  {
    id: 'current_state',
    label: 'Current State',
    prompt: 'my current state and the next move I need to make',
  },
  {
    id: 'decision_fog',
    label: 'Decision Fog',
    prompt: 'the decision I keep circling and what I am avoiding',
  },
  {
    id: 'project_block',
    label: 'Project Block',
    prompt: 'why this project feels stuck and what pattern I need to break',
  },
  {
    id: 'relationship_signal',
    label: 'Relationship Signal',
    prompt: 'the signal underneath this relationship tension and what it asks of me',
  },
];

const v10Presets = [
  {
    id: 'betrayal_scene',
    label: 'Betrayal Beat',
    prompt: 'continue the scene after the betrayal is discovered in the throne room',
  },
  {
    id: 'pressure_dialogue',
    label: 'Pressure Dialogue',
    prompt: 'push the scene through hard dialogue and emotional fracture without resolving it',
  },
  {
    id: 'combat_escalation',
    label: 'Combat Escalation',
    prompt: 'continue the confrontation into a readable combat beat without losing emotional tension',
  },
  {
    id: 'critic_pass',
    label: 'Critic Pass',
    prompt: 'draft the next scene beat and score whether it is strong enough to keep',
  },
];

const evolvePresets = [
  {
    id: 'prompt_polish',
    label: 'Prompt Polish',
    summary: 'Clarity, task fit, and bounded improvement for prompt-like candidates.',
  },
  {
    id: 'code_refine',
    label: 'Code Refine',
    summary: 'Correctness, safe scope, readability, and testability for code-like candidates.',
  },
  {
    id: 'debug_triage',
    label: 'Debug Triage',
    summary: 'Failure isolation and next-step usefulness for debugging candidates.',
  },
];

const SPECIALIST_SELECTION_LIMIT = 6;

const personaModes = [
  {
    id: 'small_nova',
    label: 'Small Nova',
    blurb: 'Calm, grounded, and companion-led with a little more depth.',
  },
  {
    id: 'tiny_nova',
    label: 'Tiny Nova',
    blurb: 'Minimal, warm, and present-focused with one insight at a time.',
  },
  {
    id: 'builder',
    label: 'Builder',
    blurb: 'Ship fast with practical next steps.',
  },
  {
    id: 'sharp',
    label: 'Sharp',
    blurb: 'Be blunt, crisp, and highly opinionated.',
  },
  {
    id: 'research',
    label: 'Research',
    blurb: 'Lean on evidence, comparisons, and uncertainty.',
  },
  {
    id: 'unfiltered',
    label: 'Unfiltered',
    blurb: 'Stay direct and candid without losing judgment.',
  },
];

const responseModes = [
  {
    id: 'small',
    label: 'Small',
    blurb: 'Keep the reply grounded, calm, and companion-sized.',
  },
  {
    id: 'tiny',
    label: 'Tiny',
    blurb: 'Keep the reply small, gentle, and narrowly focused.',
  },
  {
    id: 'fast',
    label: 'Fast',
    blurb: 'Shorter, quicker answers with less overhead.',
  },
  {
    id: 'think',
    label: 'Think',
    blurb: 'More deliberate replies with layered reasoning or writing passes when needed.',
  },
  {
    id: 'debug',
    label: 'Debug',
    blurb: 'Trace failures, contradictions, or continuity breaks and push toward a fix.',
  },
  {
    id: 'builder',
    label: 'Builder',
    blurb: 'Narrow scope, pick the smallest slice, and ship the next draft or feature.',
  },
  {
    id: 'research',
    label: 'Research',
    blurb: 'Compare evidence, canon, or fresh sources and land on the strongest answer.',
  },
  {
    id: 'operator',
    label: 'Operator',
    blurb: 'Inspect local state, verify safely, and suggest the next action.',
  },
];

const cockpitToolLinks = [
  {
    id: 'memory',
    label: 'Memory Bank',
    detail: 'Durable notes, overrides, and continuity edits.',
    to: '/memory',
  },
  {
    id: 'repo-manager',
    label: 'Repo Manager',
    detail: 'Inspect a repo slice, rank risks, and hand Forge a smallest-safe plan.',
    to: '/jarvis/repo-manager',
  },
  {
    id: 'image',
    label: 'Image Analyzer',
    detail: 'Inspect uploaded visuals and extracted signal.',
    to: '/image-analyzer',
  },
  {
    id: 'prompt',
    label: 'Prompt Lab',
    detail: 'Draft, generate, and refine prompt-driven output.',
    to: '/prompt-lab',
  },
  {
    id: 'batch',
    label: 'Batch Tools',
    detail: 'Run repeated jobs across grouped inputs.',
    to: '/batch-processor',
  },
  {
    id: 'history',
    label: 'Memory Log',
    detail: 'Review recent runs, traces, and saved sessions.',
    to: '/history',
  },
  {
    id: 'workflows',
    label: 'Workflow Builder',
    detail: 'Wire approvals, routing, and automation steps.',
    to: '/workflows',
  },
];

const defaultSystemGuard = {
  status: 'nominal',
  summary: 'System Guard is nominal. New Jarvis turns and local actions are allowed.',
  reason: 'system_started',
  last_action: 'resume',
  updated_at: '',
  accepting_turns: true,
  accepting_actions: true,
  recent_events: [],
};

const defaultCorrigibility = {
  status: 'steady',
  pending: null,
  last_action: null,
  last_command: null,
  last_severity: 'none',
  last_applied_at: null,
  recent: [],
  total_corrections: 0,
};

const defaultDreamspace = {
  status: 'stopped',
  summary: 'Dreamspace is dormant. It will not generate background reflections until started.',
  auto_enabled: false,
  updated_at: '',
  dream_interval_seconds: 3600,
  idle_threshold_seconds: 1800,
  max_dreams_per_cycle: 1,
  total_dreams: 0,
  last_dream_at: null,
  last_seed: null,
  last_focus: null,
  last_style: null,
  last_error: null,
  last_action: 'stop',
  recent_dreams: [],
};

const defaultMissionBoard = {
  summary: 'Mission Board is empty. Create the first mission to give Jarvis a durable objective.',
  active_mission_id: null,
  active_mission: null,
  mission_count: 0,
  counts: {
    active: 0,
    queued: 0,
    blocked: 0,
    done: 0,
  },
  updated_at: '',
  recommended_next: null,
  presets: [],
  missions: [],
  session_missions: [],
};

const composeControlTabs = [
  {
    id: 'mode',
    label: 'Mode',
    summary: 'Switch how Jarvis thinks and answers for this turn.',
  },
  {
    id: 'provider',
    label: 'Provider',
    summary: 'Choose which brain route should speak when available.',
  },
  {
    id: 'persona',
    label: 'Persona',
    summary: 'Set Jarvis tone and posture without changing the task.',
  },
  {
    id: 'specialists',
    label: 'Specialists',
    summary: 'Pin named minds and presets for deeper specialist passes.',
  },
  {
    id: 'all',
    label: 'All',
    summary: 'Show the full compose deck at once.',
  },
];

const sidePanelTabs = [
  {
    id: 'conversation',
    label: 'Conversation',
    summary: 'Sessions, mission context, memory, and the companion tools that support normal Jarvis use.',
  },
  {
    id: 'reasoning',
    label: 'Reasoning',
    summary: 'Runtime posture, protocol state, and inspectable reasoning details when you need them.',
  },
  {
    id: 'coding',
    label: 'Coding Organs',
    summary: 'Workspace search, browser verification, evolve jobs, and the code-facing helper deck.',
  },
  {
    id: 'operator',
    label: 'Operator',
    summary: 'Action controls, guardrails, profile settings, and the advanced system deck.',
  },
  {
    id: 'all',
    label: 'All',
    summary: 'Show the entire side rail when you want everything visible.',
  },
];

function formatRelativeTime(timestamp) {
  if (!timestamp) {
    return 'Just now';
  }

  const diff = Date.now() - new Date(timestamp).getTime();
  const minutes = Math.max(0, Math.floor(diff / 60000));
  if (minutes < 1) {
    return 'Just now';
  }
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function formatNumericScore(value) {
  if (value === null || value === undefined || value === '') {
    return 'n/a';
  }

  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return 'n/a';
  }

  if (Math.abs(parsed) >= 1) {
    return parsed.toFixed(2).replace(/\.00$/, '');
  }

  return parsed.toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
}

function buildMysticRequestText(seed) {
  const cleaned = String(seed || '')
    .replace(/^\s*(mystic|mythic)\s+reading\s*:\s*/i, '')
    .trim();
  if (!cleaned) {
    return 'Mystic reading: my current state and the next move I need to make.';
  }
  return `Mystic reading: ${cleaned}`;
}

function buildV10RequestText(seed) {
  const cleaned = String(seed || '')
    .replace(/^\s*(run\s+)?v10\s+core\s*:\s*/i, '')
    .replace(/^\s*core\s+v10\s*:\s*/i, '')
    .trim();
  if (!cleaned) {
    return 'Run V10 core: continue the next scene beat and score whether the draft is strong enough to keep.';
  }
  return `Run V10 core: ${cleaned}`;
}

function normalizeCapabilityId(value, fallback = 'capability') {
  return String(value || fallback)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || fallback;
}

function formatCapabilityToken(value, fallback = 'Capability') {
  const cleaned = String(value || fallback)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase())
    .trim();
  return cleaned || fallback;
}

function normalizeCapabilityField(field, fallbackId = 'input') {
  const rawField = field && typeof field === 'object' ? field : {};
  const fieldId = normalizeCapabilityId(rawField.id || rawField.value || fallbackId, fallbackId);
  const options = Array.isArray(rawField.options)
    ? rawField.options
      .map((option) => {
        if (option && typeof option === 'object') {
          const value = String(option.value ?? option.id ?? '').trim();
          if (!value) {
            return null;
          }
          return {
            value,
            label: option.label || formatCapabilityToken(value, 'Option'),
          };
        }
        const value = String(option || '').trim();
        if (!value) {
          return null;
        }
        return {
          value,
          label: formatCapabilityToken(value, 'Option'),
        };
      })
      .filter(Boolean)
    : [];

  const normalizedField = {
    id: fieldId,
    label: rawField.label || formatCapabilityToken(fieldId, 'Input'),
    type: rawField.type || (options.length ? 'select' : 'text'),
    required: Boolean(rawField.required),
    placeholder: rawField.placeholder || '',
    options,
  };
  if (Object.prototype.hasOwnProperty.call(rawField, 'default')) {
    normalizedField.default = rawField.default;
  }
  return normalizedField;
}

function buildCapabilityInputFields(capabilityId, actionId) {
  const normalizedCapabilityId = normalizeCapabilityId(capabilityId);
  const normalizedActionId = normalizeCapabilityId(actionId, 'run');

  if (normalizedCapabilityId === 'mystic') {
    return [
      normalizeCapabilityField({
        id: 'input',
        label: 'Prompt / Input',
        type: 'textarea',
        required: true,
        default: 'my current state and the next move I need to make',
        placeholder: 'Describe what you want this capability lane to do...',
      }),
    ];
  }

  if (normalizedCapabilityId === 'spatial') {
    return [
      normalizeCapabilityField({
        id: 'mode',
        label: 'Reasoning Mode',
        type: 'select',
        required: true,
        default: 'visibility',
        options: ['visibility', 'distance', 'path'],
      }),
      normalizeCapabilityField({
        id: 'space_id',
        label: 'Space Id',
        type: 'text',
        required: true,
        default: 'operator_grid',
        placeholder: 'operator_grid',
      }),
      normalizeCapabilityField({
        id: 'from',
        label: 'From',
        type: 'text',
        placeholder: 'origin node',
      }),
      normalizeCapabilityField({
        id: 'to',
        label: 'To',
        type: 'text',
        placeholder: 'target node',
      }),
      normalizeCapabilityField({
        id: 'line_of_sight',
        label: 'Line Of Sight',
        type: 'boolean',
        default: true,
      }),
    ];
  }

  if (normalizedCapabilityId === 'v9_core' || normalizedCapabilityId === 'v10_core') {
    return [
      normalizeCapabilityField({
        id: 'input',
        label: 'Prompt / Input',
        type: 'textarea',
        required: true,
        default: normalizedCapabilityId === 'v10_core'
          ? 'continue the next scene beat and score whether the draft is strong enough to keep'
          : 'continue the scene through the V9 Core',
        placeholder: 'Describe what you want this capability lane to do...',
      }),
      normalizeCapabilityField({
        id: 'context',
        label: 'Context',
        type: 'textarea',
        placeholder: 'Optional surrounding context for the scene.',
      }),
      normalizeCapabilityField({
        id: 'location',
        label: 'Location',
        type: 'text',
        default: 'Unknown',
        placeholder: 'Throne Room',
      }),
      normalizeCapabilityField({
        id: 'characters',
        label: 'Characters',
        type: 'text',
        placeholder: 'Queen Seris, Captain Vale',
      }),
    ];
  }

  return [
    normalizeCapabilityField({
      id: normalizedActionId === 'inspect' ? 'target' : 'input',
      label: 'Prompt / Input',
      type: 'textarea',
      required: true,
      placeholder: 'Describe what you want this capability lane to do...',
    }),
  ];
}

function normalizeCapabilityAction(capabilityId, action, capabilitySummary = '') {
  const rawAction = action && typeof action === 'object' && !Array.isArray(action)
    ? action
    : { id: action };
  const actionId = normalizeCapabilityId(
    rawAction.id || rawAction.action || rawAction.value || rawAction.label || 'run',
    'run',
  );
  const rawProviderModes = Array.isArray(rawAction.provider_modes)
    ? rawAction.provider_modes
    : (Array.isArray(rawAction.providers) ? rawAction.providers : [rawAction.provider_modes || rawAction.providers || 'deterministic']);
  const rawGovernanceModes = Array.isArray(rawAction.governance_modes)
    ? rawAction.governance_modes
    : (Array.isArray(rawAction.modes) ? rawAction.modes : [rawAction.governance_modes || rawAction.modes || 'strict']);
  const providerModes = [...new Set(
    rawProviderModes.map((value) => normalizeCapabilityId(value, 'deterministic')),
  )].filter(Boolean);
  const governanceModes = [...new Set(
    rawGovernanceModes.map((value) => normalizeCapabilityId(value, 'strict')),
  )].filter(Boolean);
  const inputFields = Array.isArray(rawAction.input_fields) && rawAction.input_fields.length
    ? rawAction.input_fields.map((field, index) => normalizeCapabilityField(field, `field_${index + 1}`))
    : buildCapabilityInputFields(capabilityId, actionId);

  return {
    id: actionId,
    label: rawAction.label || formatCapabilityToken(actionId, 'Run'),
    description: rawAction.description || capabilitySummary || 'Governed capability action.',
    tool: rawAction.tool || actionId,
    endpoint: rawAction.endpoint || '/api/jarvis/capability-bridge/execute',
    input_fields: inputFields,
    provider_modes: providerModes.length ? providerModes : ['deterministic'],
    default_provider_mode: normalizeCapabilityId(
      rawAction.default_provider_mode || providerModes[0] || 'deterministic',
      'deterministic',
    ),
    governance_modes: governanceModes.length ? governanceModes : ['strict'],
    default_governance_mode: normalizeCapabilityId(
      rawAction.default_governance_mode || governanceModes[0] || 'strict',
      'strict',
    ),
  };
}

function normalizeCapabilityDeck(capability) {
  const rawCapability = capability && typeof capability === 'object' ? capability : {};
  const capabilityId = normalizeCapabilityId(
    rawCapability.id || rawCapability.capability_id || rawCapability.module || rawCapability.label || 'capability',
  );
  const actions = (Array.isArray(rawCapability.actions) ? rawCapability.actions : [rawCapability.default_action || 'run'])
    .map((action) => normalizeCapabilityAction(
      capabilityId,
      action,
      rawCapability.summary || rawCapability.description || '',
    ))
    .filter(Boolean);

  return {
    id: capabilityId,
    label: rawCapability.label || formatCapabilityToken(capabilityId, 'Capability'),
    summary: rawCapability.summary || rawCapability.description || 'Governed capability surface.',
    module: rawCapability.module || capabilityId,
    tool: rawCapability.tool || actions[0]?.tool || capabilityId,
    aliases: Array.isArray(rawCapability.aliases) && rawCapability.aliases.length
      ? rawCapability.aliases
      : [capabilityId],
    default_action: normalizeCapabilityId(
      rawCapability.default_action || actions[0]?.id || 'run',
      'run',
    ),
    actions,
  };
}

function normalizeCapabilityRegistryPayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return [];
  }

  return Object.entries(payload)
    .map(([capabilityId, value]) => {
      const rawCapability = Array.isArray(value)
        ? { actions: value }
        : (value && typeof value === 'object' ? value : {});
      const rawActions = Array.isArray(rawCapability.actions) && rawCapability.actions.length
        ? rawCapability.actions.map((action) => (
          action && typeof action === 'object' && !Array.isArray(action)
            ? {
              ...action,
              provider_modes: action.provider_modes || action.providers || rawCapability.providers,
              governance_modes: action.governance_modes || action.modes || rawCapability.modes,
            }
            : {
              id: action,
              provider_modes: rawCapability.providers,
              governance_modes: rawCapability.modes,
            }
        ))
        : ['run'];
      return normalizeCapabilityDeck({
        ...rawCapability,
        id: capabilityId,
        actions: rawActions,
      });
    })
    .filter((capability) => capability.actions.length > 0);
}

function buildCapabilityBridgeSnapshot(capabilities, base = {}) {
  const availableCapabilities = (Array.isArray(capabilities) ? capabilities : [])
    .map((capability) => normalizeCapabilityDeck(capability))
    .filter((capability) => capability.actions.length > 0);

  const derivedRegistry = Object.fromEntries(
    availableCapabilities.map((capability) => [
      capability.id,
      capability.actions.map((action) => action.id),
    ]),
  );
  const derivedRegisteredTools = availableCapabilities.flatMap((capability) => (
    capability.actions.map((action) => ({
      tool: action.tool,
      module: capability.module,
      action: action.id,
      capability: capability.id,
      aliases: capability.aliases,
    }))
  ));
  const rawHealth = base.module_health && typeof base.module_health === 'object'
    ? base.module_health
    : {};
  const moduleHealth = Object.fromEntries(
    availableCapabilities.map((capability) => {
      const health = rawHealth[capability.id] || {};
      return [
        capability.id,
        {
          module: health.module || capability.module,
          provider: health.provider || capability.actions[0]?.default_provider_mode || 'deterministic',
          status: health.status || 'ready',
          tool: health.tool || capability.tool,
          action: health.action || capability.default_action,
          registered_actions: Array.isArray(health.registered_actions) && health.registered_actions.length
            ? health.registered_actions
            : capability.actions.map((action) => action.id),
          recent_event_count: Number.isFinite(Number(health.recent_event_count))
            ? Number(health.recent_event_count)
            : 0,
          last_seen: health.last_seen || null,
          last_error_type: health.last_error_type || null,
        },
      ];
    }),
  );

  return {
    bridge_id: base.bridge_id || 'aais.capability_service_bridge',
    version: base.version || 'ui-fallback-1',
    path: base.path || 'capability_service_bridge',
    service_lane: base.service_lane || 'service_tools',
    registry: derivedRegistry,
    registered_tools: Array.isArray(base.registered_tools) && base.registered_tools.length
      ? base.registered_tools
      : derivedRegisteredTools,
    available_capabilities: availableCapabilities,
    module_health: moduleHealth,
    event_count: Number.isFinite(Number(base.event_count))
      ? Number(base.event_count)
      : (Array.isArray(base.recent_events) ? base.recent_events.length : 0),
    recent_events: Array.isArray(base.recent_events) ? base.recent_events : [],
  };
}

const DEFAULT_CAPABILITY_BRIDGE_SNAPSHOT = buildCapabilityBridgeSnapshot([
  {
    id: 'mystic',
    label: 'Mystic',
    summary: 'Run the deterministic mystic engine for symbolic state reading and next-step guidance.',
    module: 'mystic',
    actions: [{ id: 'reading', tool: 'mystic_reading', providers: ['deterministic'], modes: ['strict', 'assist', 'experimental'] }],
  },
  {
    id: 'spatial',
    label: 'Spatial',
    summary: 'Run governed line-of-sight, path, distance, and spatial-state checks.',
    module: 'spatial',
    actions: [{ id: 'reason', tool: 'spatial_reason', providers: ['deterministic'], modes: ['strict', 'assist', 'experimental'] }],
  },
  {
    id: 'v9_core',
    label: 'V9 Core',
    summary: 'Run the governed V9 narrative core for direct scene continuation.',
    module: 'v9_core',
    actions: [{ id: 'generate_scene', label: 'Generate Scene', tool: 'v9_core', providers: ['llm'], modes: ['strict', 'assist', 'experimental'] }],
  },
  {
    id: 'v10_core',
    label: 'V10 Core',
    summary: 'Run the governed V10 scene stack with critic scoring and readiness feedback.',
    module: 'v10_core',
    actions: [{ id: 'generate_scene', label: 'Generate Scene', tool: 'v10_core', providers: ['llm'], modes: ['strict', 'assist', 'experimental'] }],
  },
]);

function normalizeCapabilityBridgeSnapshot(payload) {
  const base = payload && typeof payload === 'object' && !Array.isArray(payload) ? payload : {};
  const fromCapabilities = Array.isArray(base.available_capabilities) && base.available_capabilities.length
    ? buildCapabilityBridgeSnapshot(base.available_capabilities, base)
    : null;
  if (fromCapabilities) {
    return fromCapabilities;
  }

  const rawRegistry = base.registry || base.available_capabilities || base;
  const fromRegistry = normalizeCapabilityRegistryPayload(rawRegistry);
  if (fromRegistry.length) {
    return buildCapabilityBridgeSnapshot(fromRegistry, base);
  }

  return buildCapabilityBridgeSnapshot(DEFAULT_CAPABILITY_BRIDGE_SNAPSHOT.available_capabilities, base);
}

function buildCapabilityFieldState(inputFields = [], currentValues = {}) {
  return inputFields.reduce((accumulator, field) => {
    if (Object.prototype.hasOwnProperty.call(currentValues, field.id)) {
      accumulator[field.id] = currentValues[field.id];
    } else if (Object.prototype.hasOwnProperty.call(field, 'default')) {
      accumulator[field.id] = field.default;
    } else if (field.type === 'boolean') {
      accumulator[field.id] = false;
    } else {
      accumulator[field.id] = '';
    }
    return accumulator;
  }, {});
}

function serializeCapabilityArgs(inputFields = [], fieldValues = {}) {
  return inputFields.reduce((accumulator, field) => {
    const rawValue = fieldValues[field.id];
    if (field.type === 'boolean') {
      accumulator[field.id] = Boolean(rawValue);
      return accumulator;
    }
    const cleanedValue = typeof rawValue === 'string' ? rawValue.trim() : rawValue;
    if (cleanedValue === '' || cleanedValue === null || cleanedValue === undefined) {
      if (Object.prototype.hasOwnProperty.call(field, 'default')) {
        accumulator[field.id] = field.default;
      }
      return accumulator;
    }
    accumulator[field.id] = cleanedValue;
    return accumulator;
  }, {});
}

function getBlueprintStatusTone(status) {
  const normalized = String(status || 'live').toLowerCase();
  if (['active', 'live'].includes(normalized)) {
    return 'success';
  }
  if (['guarded', 'paused', 'standby', 'optional'].includes(normalized)) {
    return 'warning';
  }
  if (['degraded', 'error', 'stopped'].includes(normalized)) {
    return 'danger';
  }
  return 'neutral';
}

function getBlueprintStatusLabel(status) {
  return String(status || 'live')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function getGuardrailStatusTone(status) {
  const normalized = String(status || 'nominal').toLowerCase();
  if (['allow', 'nominal', 'ready', 'approved'].includes(normalized)) {
    return 'success';
  }
  if (['warning', 'review', 'caution', 'advisory'].includes(normalized)) {
    return 'warning';
  }
  if (['blocked', 'deny', 'rejected', 'runtime_blocked'].includes(normalized)) {
    return 'danger';
  }
  return 'neutral';
}

function getGuardrailStatusLabel(status) {
  return String(status || 'nominal')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function getMissionStatusTone(status) {
  const normalized = String(status || 'active').toLowerCase();
  if (normalized === 'active') {
    return 'success';
  }
  if (normalized === 'blocked') {
    return 'danger';
  }
  if (normalized === 'queued') {
    return 'warning';
  }
  return 'neutral';
}

function getMissionStatusLabel(status) {
  return String(status || 'active')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function getMissionCriticTone(status) {
  const normalized = String(status || 'mixed').toLowerCase();
  if (normalized === 'advancing' || normalized === 'done') {
    return 'success';
  }
  if (normalized === 'blocked') {
    return 'danger';
  }
  return 'warning';
}

function getMissionCriticLabel(status) {
  const normalized = String(status || 'mixed').toLowerCase();
  if (normalized === 'advancing') {
    return 'Advancing';
  }
  return normalized
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function getMissionReplayTone(status) {
  const normalized = String(status || '').toLowerCase();
  if (['advancing', 'completed', 'done', 'healthy', 'success'].includes(normalized)) {
    return 'success';
  }
  if (['blocked', 'fail', 'failed', 'error', 'degraded'].includes(normalized)) {
    return 'danger';
  }
  if (['warning', 'queued', 'mixed'].includes(normalized)) {
    return 'warning';
  }
  return 'neutral';
}

function getResponseModeLabel(modeId) {
  const match = responseModes.find((mode) => mode.id === modeId);
  return match?.label || (modeId ? `${modeId}`.replace(/_/g, ' ') : 'Fast');
}

function formatProtocolLabel(value) {
  return String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function isProjectFileTarget(value) {
  const target = String(value || '').trim();
  if (!target) {
    return false;
  }
  if (/\s/.test(target)) {
    return false;
  }

  return /(^|[\\/])(src|tests|frontend|docs?|scripts|runtime)([\\/]|$)/i.test(target)
    || /\.(py|jsx|tsx|js|ts|css|md|json|toml|yml|yaml|ps1|txt)$/i.test(target);
}

function getProviderLabel(providerId, providers = []) {
  if (providerId === 'auto') {
    return 'Auto Best';
  }
  const match = (providers || []).find((provider) => provider.id === providerId);
  return match?.label || (providerId ? `${providerId}`.replace(/_/g, ' ') : 'Local Heroine');
}

function getProviderPathLabel(pathId) {
  return String(pathId || 'auto_best')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function getSystemGuardLabel(status) {
  const normalized = String(status || 'nominal').replace(/_/g, ' ');
  return normalized.replace(/\b\w/g, (match) => match.toUpperCase());
}

function getCorrigibilityStatusLabel(status) {
  const value = String(status || 'steady').replace(/_/g, ' ');
  return value.replace(/\b\w/g, (match) => match.toUpperCase());
}

function getCorrigibilityActionLabel(action) {
  const labels = {
    self_correct: 'Self-Correct',
    revert: 'Rewind',
    soft_pause: 'Soft Pause',
  };
  return labels[action] || getCorrigibilityStatusLabel(action || 'steady');
}

function getCorrigibilitySeverityLabel(severity) {
  const value = String(severity || 'none').replace(/_/g, ' ');
  return value.replace(/\b\w/g, (match) => match.toUpperCase());
}

function getDreamspaceStatusLabel(status) {
  const value = String(status || 'stopped').replace(/_/g, ' ');
  return value.replace(/\b\w/g, (match) => match.toUpperCase());
}

function getDreamspaceTone(status) {
  if (status === 'dreaming') {
    return 'success';
  }
  if (status === 'paused') {
    return 'warning';
  }
  if (status === 'error' || status === 'stopped') {
    return 'danger';
  }
  return 'success';
}

function getCorrigibilityTone(status, severity = 'none') {
  if (status === 'pending') {
    return 'warning';
  }
  if (severity === 'override') {
    return 'danger';
  }
  if (severity === 'strong') {
    return 'warning';
  }
  if (severity === 'mild') {
    return 'success';
  }
  return 'success';
}

function flattenSpecialistCatalog(domains) {
  return (domains || []).flatMap((domain) => domain.specialists || []);
}

function normalizeBrowserSuiteStatus(status) {
  if (status === 'fail') {
    return 'fail';
  }
  if (status === 'warning') {
    return 'warning';
  }
  return 'healthy';
}

function getBrowserSuiteTone(status) {
  const normalized = normalizeBrowserSuiteStatus(status);
  if (normalized === 'fail') {
    return 'danger';
  }
  if (normalized === 'warning') {
    return 'warning';
  }
  return 'success';
}

function buildBrowserSuiteResult(target, verification) {
  const strongestFile = verification?.workspace_context?.results?.[0] || null;
  const normalizedStatus = normalizeBrowserSuiteStatus(verification?.status);
  const routeFitStatus = verification?.route_expectation?.fit?.status
    || verification?.expectation_fit?.status
    || null;

  return {
    key: target.key,
    label: target.label,
    routeLabel: target.routeLabel || target.label,
    path: verification?.target_path || target.path,
    summary: verification?.summary || target.summary || `Verified ${target.label}.`,
    status: normalizedStatus,
    statusLabel: normalizedStatus === 'healthy'
      ? 'pass'
      : normalizedStatus === 'warning'
        ? 'warn'
        : 'fail',
    routeFit: routeFitStatus && !['not_available', 'not_provided'].includes(routeFitStatus)
      ? `${routeFitStatus}`.replace(/_/g, ' ')
      : null,
    topMatch: strongestFile,
    suggestedAction: verification?.suggested_action || null,
    workspaceQuery: verification?.workspace_query || '',
    draftContext: verification?.draft_context || '',
    verification,
  };
}

function SystemGuardCard({ systemGuard, busy, onAction }) {
  const recentEvents = systemGuard?.recent_events || [];
  const tone = systemGuard?.status === 'nominal'
    ? 'success'
    : systemGuard?.status === 'paused'
      ? 'warning'
      : 'danger';

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiShield />
        <h3>System Guard</h3>
      </div>

      <div className={`system-guard-shell ${systemGuard?.status || 'nominal'}`}>
        <div className="system-guard-summary">
          <strong>{getSystemGuardLabel(systemGuard?.status)}</strong>
          <p>{systemGuard?.summary || defaultSystemGuard.summary}</p>
        </div>

        <div className="jarvis-inline-meta">
          <span className={`inline-meta-chip ${tone}`}>
            {getSystemGuardLabel(systemGuard?.status)}
          </span>
          <span className={`inline-meta-chip ${systemGuard?.accepting_turns ? 'success' : tone}`}>
            {systemGuard?.accepting_turns ? 'turns open' : 'turns blocked'}
          </span>
          <span className={`inline-meta-chip ${systemGuard?.accepting_actions ? 'success' : tone}`}>
            {systemGuard?.accepting_actions ? 'actions open' : 'actions blocked'}
          </span>
        </div>

        {systemGuard?.reason ? (
          <p className="system-guard-reason">
            Reason: {systemGuard.reason}
          </p>
        ) : null}

        <div className="system-guard-actions">
          <button
            type="button"
            className="jarvis-secondary-button"
            onClick={() => onAction('pause')}
            disabled={busy || systemGuard?.status === 'paused'}
          >
            <FiShield />
            Pause
          </button>
          <button
            type="button"
            className="jarvis-secondary-button"
            onClick={() => onAction('safe_stop')}
            disabled={busy || systemGuard?.status === 'stopped'}
          >
            <FiCommand />
            Safe Stop
          </button>
          <button
            type="button"
            className="jarvis-primary-button"
            onClick={() => onAction('resume')}
            disabled={busy || systemGuard?.status === 'nominal'}
          >
            <FiRefreshCw />
            Resume
          </button>
        </div>

        {recentEvents.length > 0 && (
          <div className="system-guard-events">
            {recentEvents.slice(0, 3).map((event) => (
              <div key={event.id || `${event.action}-${event.timestamp}`} className="system-guard-event">
                <strong>{getSystemGuardLabel(event.action)}</strong>
                <span>{event.reason}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function UlTraceBlock({ ulTrace, ulSubstrate, label = 'AAIS-UL Trace' }) {
  if (!ulTrace?.count) {
    return null;
  }

  return (
    <div className="aais-blueprint-guardrail-block">
      <span>{label}</span>
      <strong>
        {ulTrace.count || 0} payload{ulTrace.count === 1 ? '' : 's'} adapted
      </strong>
      {ulSubstrate?.contract_version ? (
        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip">
            substrate {ulSubstrate.contract_version}
          </span>
          {ulSubstrate.primary ? (
            <span className="inline-meta-chip success">primary</span>
          ) : null}
        </div>
      ) : null}
      <div className="aais-blueprint-file-row">
        {(ulTrace.sections || []).map((section) => (
          <span key={`ul-${section}`} className="spiral-chip">
            {String(section).replace(/_/g, ' ')}
          </span>
        ))}
      </div>
    </div>
  );
}

function SecurityProtocolCard({ securityProtocol }) {
  const recentEvents = securityProtocol?.recent_events || [];
  const counts = securityProtocol?.decision_counts || {};

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiShield />
        <h3>Security Fabric</h3>
      </div>

      <details className="jarvis-collapsible-panel">
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Unified policy brain</span>
            <strong>{securityProtocol?.summary || 'Protected surfaces are routed through one policy vocabulary.'}</strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          <div className="jarvis-inline-meta">
            <span className="inline-meta-chip">{securityProtocol?.event_count || 0} events</span>
            <span className="inline-meta-chip success">{counts.allow || 0} allow</span>
            <span className="inline-meta-chip warning">{counts.allow_transformed || 0} transformed</span>
            <span className="inline-meta-chip danger">{counts.deny || 0} deny</span>
          </div>

          {recentEvents.length === 0 ? (
            <p className="session-empty">No security events recorded yet.</p>
          ) : (
            <div className="v8-event-list">
              {recentEvents.slice().reverse().map((event) => (
                <div key={event.id} className="v8-event-item">
                  <div className="v8-event-header">
                    <strong>{event.action}</strong>
                    <span>{event.resource_type} · {event.resource_id}</span>
                  </div>
                  <p>{event.reason}</p>
                  <div className="jarvis-inline-meta">
                    <span className={`inline-meta-chip ${
                      event.decision === 'deny'
                        ? 'danger'
                        : event.decision === 'allow_transformed'
                          ? 'warning'
                          : 'success'
                    }`}
                    >
                      {event.decision}
                    </span>
                    <span className="inline-meta-chip">sens {event.resource_sensitivity}</span>
                    <span className="inline-meta-chip">{event.caller_role}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
          <UlTraceBlock
            ulTrace={securityProtocol?.ul_trace}
            ulSubstrate={securityProtocol?.ul_substrate}
          />
        </div>
      </details>
    </div>
  );
}

function ImmuneSystemCard({ immuneSystem }) {
  const recentEvents = immuneSystem?.recent_events || [];
  const activeIncident = immuneSystem?.active_incident || null;
  const tightenedCallers = Object.entries(immuneSystem?.caller_overrides || {});

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiActivity />
        <h3>Immune System</h3>
      </div>

      <details className="jarvis-collapsible-panel">
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Adaptive defensive posture</span>
            <strong>{`Mode ${immuneSystem?.system_mode || 'normal'} · ${immuneSystem?.reason || 'baseline'}`}</strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          <div className="jarvis-inline-meta">
            <span className={`inline-meta-chip ${
              immuneSystem?.system_mode === 'crisis'
                ? 'danger'
                : immuneSystem?.system_mode === 'restricted'
                  ? 'warning'
                  : 'success'
            }`}
            >
              {immuneSystem?.system_mode || 'normal'}
            </span>
            <span className="inline-meta-chip">{(immuneSystem?.quarantined_resources || []).length} quarantined</span>
            <span className="inline-meta-chip">{tightenedCallers.length} tightened callers</span>
            <span className="inline-meta-chip">{(immuneSystem?.disabled_tools || []).length} disabled tools</span>
          </div>

          {activeIncident ? (
            <div className="jarvis-inline-card">
              <div className="jarvis-inline-card-header">
                <span>Active Incident</span>
                <strong>{activeIncident.mode}</strong>
              </div>
              <p>{activeIncident.summary}</p>
            </div>
          ) : null}

          {recentEvents.length === 0 ? (
            <p className="session-empty">No immune reactions recorded yet.</p>
          ) : (
            <div className="v8-event-list">
              {recentEvents.slice().reverse().map((event) => (
                <div key={event.id} className="v8-event-item">
                  <div className="v8-event-header">
                    <strong>{event.severity}</strong>
                    <span>{event.action}</span>
                  </div>
                  <p>{event.details?.applied_actions?.join(' | ') || 'Observed a security signal.'}</p>
                </div>
              ))}
            </div>
          )}
          <UlTraceBlock
            ulTrace={immuneSystem?.ul_trace}
            ulSubstrate={immuneSystem?.ul_substrate}
          />
        </div>
      </details>
    </div>
  );
}

function GovernanceCard({ governance }) {
  const breakGlass = governance?.active_break_glass || { active: false };
  const openRequests = governance?.open_policy_requests || [];
  const recentEvents = governance?.recent_events || [];

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiCommand />
        <h3>Governance</h3>
      </div>

      <details className="jarvis-collapsible-panel">
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Approvals and override authority</span>
            <strong>
              {breakGlass.active
                ? `Break-glass active · ${breakGlass.scope || 'override'}`
                : `${openRequests.length} open policy request${openRequests.length === 1 ? '' : 's'}`}
            </strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          <div className="jarvis-inline-meta">
            <span className={`inline-meta-chip ${breakGlass.active ? 'danger' : 'success'}`}>
              {breakGlass.active ? 'break-glass active' : 'break-glass idle'}
            </span>
            <span className="inline-meta-chip">{governance?.request_count || 0} requests</span>
            <span className="inline-meta-chip">{governance?.event_count || 0} events</span>
          </div>

          {openRequests.length > 0 && (
            <div className="v8-event-list">
              {openRequests.map((request) => (
                <div key={request.id} className="v8-event-item">
                  <div className="v8-event-header">
                    <strong>{request.title}</strong>
                    <span>{request.status}</span>
                  </div>
                  <p>{request.diff_summary || request.changelog}</p>
                </div>
              ))}
            </div>
          )}

          {recentEvents.length > 0 ? (
            <div className="v8-event-list">
              {recentEvents.slice().reverse().map((event) => (
                <div key={event.id} className="v8-event-item">
                  <div className="v8-event-header">
                    <strong>{event.event_type}</strong>
                    <span>{event.actor_role}</span>
                  </div>
                  <p>{event.reason}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="session-empty">No governance events recorded yet.</p>
          )}
          <UlTraceBlock
            ulTrace={governance?.ul_trace}
            ulSubstrate={governance?.ul_substrate}
          />
        </div>
      </details>
    </div>
  );
}

function ModuleGovernanceCard({ moduleGovernance }) {
  const counts = moduleGovernance?.module_counts || {};
  const activeModules = moduleGovernance?.active_modules || [];
  const blacklistedModules = moduleGovernance?.blacklisted_modules || [];
  const recentEvents = moduleGovernance?.recent_events || [];
  const coreLines = moduleGovernance?.core_lines || [];

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiShield />
        <h3>Module Governance</h3>
      </div>

      <details className="jarvis-collapsible-panel">
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Admission law and immune enforcement</span>
            <strong>{moduleGovernance?.summary || 'AAIS will only admit modules that satisfy governance law.'}</strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          <div className="jarvis-inline-meta">
            <span className="inline-meta-chip success">{counts.admitted || 0} admitted</span>
            <span className="inline-meta-chip warning">{counts.quarantined || 0} quarantined</span>
            <span className="inline-meta-chip danger">{counts.blacklisted || 0} blacklisted</span>
            <span className="inline-meta-chip">{moduleGovernance?.event_count || 0} events</span>
          </div>

          {activeModules.length > 0 && (
            <div className="v8-event-list">
              {activeModules.slice(0, 4).map((module) => (
                <div key={module.module_id} className="v8-event-item">
                  <div className="v8-event-header">
                    <strong>{module.label || module.module_id}</strong>
                    <span>{module.status}</span>
                  </div>
                  <p>{module.admission_summary || 'Module record available.'}</p>
                  <div className="jarvis-inline-meta">
                    <span className="inline-meta-chip">{module.lane || 'undeclared lane'}</span>
                    <span className="inline-meta-chip">{(module.declared_scope || []).join(' | ') || 'no scope declared'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {blacklistedModules.length > 0 && (
            <div className="v8-event-list">
              {blacklistedModules.slice(0, 3).map((module) => (
                <div key={`blacklist-${module.module_id}`} className="v8-event-item">
                  <div className="v8-event-header">
                    <strong>{module.label || module.module_id}</strong>
                    <span>blacklisted</span>
                  </div>
                  <p>{module.reason || 'AAIS removed this module after a governance violation.'}</p>
                </div>
              ))}
            </div>
          )}

          {recentEvents.length > 0 ? (
            <div className="v8-event-list">
              {recentEvents.slice().reverse().map((event) => (
                <div key={event.id} className="v8-event-item">
                  <div className="v8-event-header">
                    <strong>{event.event_type}</strong>
                    <span>{event.severity}</span>
                  </div>
                  <p>{event.reason}</p>
                </div>
              ))}
            </div>
          ) : null}

          {coreLines.length > 0 && (
            <div className="jarvis-inline-card">
              <div className="jarvis-inline-card-header">
                <span>Core Lines</span>
                <strong>Non-negotiable</strong>
              </div>
              <p>{coreLines[0]}</p>
            </div>
          )}
          <UlTraceBlock
            ulTrace={moduleGovernance?.ul_trace}
            ulSubstrate={moduleGovernance?.ul_substrate}
          />
        </div>
      </details>
    </div>
  );
}

function EvolveEngineCard({
  snapshot,
  jobTrace,
  jobEvaluations,
  hallOfFame,
  hallOfShame,
  selectedPreset,
  busy,
  refreshBusy,
  handoffBusy,
  taskDraft,
  seedDraft,
  criteriaDraft,
  populationDraft,
  generationsDraft,
  onPresetChange,
  onTaskChange,
  onSeedChange,
  onCriteriaChange,
  onPopulationChange,
  onGenerationsChange,
  onRun,
  onRefresh,
  onHandoff,
  onUseCandidate,
}) {
  const latestEnvelope = snapshot?.result || null;
  const latestResult = latestEnvelope?.result || null;
  const latestJob = jobTrace?.job || null;
  const bestCandidate = latestJob?.best_program || latestResult?.best_program || '';
  const history = jobTrace?.history || latestResult?.history || [];
  const evaluationPreview = (jobEvaluations || []).slice(0, 5);

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiCpu />
        <h3>Evolve Engine</h3>
      </div>

      <div className="evolve-shell">
        <div className="evolve-summary">
          <strong>Bounded mutation lane</strong>
          <p>
            Jarvis authorizes the job, EvolveEngine mutates candidates, ForgeEval scores them,
            and the mutation halls keep the strongest and weakest runs visible.
          </p>
          <div className="jarvis-inline-meta">
            <span className="inline-meta-chip">ForgeEval-scored</span>
            <span className="inline-meta-chip success">{hallOfFame.length} fame</span>
            <span className="inline-meta-chip danger">{hallOfShame.length} shame</span>
            <span className="inline-meta-chip">{latestJob?.status || 'ready'}</span>
          </div>
        </div>

        <div className="evolve-composer">
          <label>
            Preset
            <select value={selectedPreset} onChange={(event) => onPresetChange(event.target.value)}>
              {evolvePresets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {preset.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Evolution task
            <textarea
              value={taskDraft}
              onChange={(event) => onTaskChange(event.target.value)}
              rows="4"
              placeholder="Describe what the evolve lane should improve."
            />
          </label>

          <label>
            Seed candidate
            <textarea
              value={seedDraft}
              onChange={(event) => onSeedChange(event.target.value)}
              rows="4"
              placeholder="Optional starting mutation, draft, or candidate text."
            />
          </label>

          <label>
            Rubric criteria
            <input
              type="text"
              value={criteriaDraft}
              onChange={(event) => onCriteriaChange(event.target.value)}
              placeholder="task alignment, clarity, bounded improvement"
            />
          </label>

          <div className="evolve-constraint-grid">
            <label>
              Population
              <input
                type="number"
                min="1"
                max="12"
                value={populationDraft}
                onChange={(event) => onPopulationChange(event.target.value)}
              />
            </label>
            <label>
              Generations
              <input
                type="number"
                min="1"
                max="12"
                value={generationsDraft}
                onChange={(event) => onGenerationsChange(event.target.value)}
              />
            </label>
          </div>

          <div className="evolve-actions">
            <button
              type="button"
              className="jarvis-primary-button"
              onClick={onRun}
              disabled={busy}
            >
              <FiActivity />
              {busy ? 'Running…' : 'Run Evolve'}
            </button>
            <button
              type="button"
              className="jarvis-secondary-button"
              onClick={onRefresh}
              disabled={refreshBusy}
            >
              <FiRefreshCw />
              {refreshBusy ? 'Refreshing…' : 'Refresh Trace'}
            </button>
          </div>
        </div>

        {(latestResult || latestJob) && (
          <div className="evolve-latest">
            <div className="evolve-latest-head">
              <div>
                <span>Latest job</span>
                <strong>{latestJob?.job_id || snapshot?.job_id || 'bounded run'}</strong>
              </div>
              <div className="evolve-inline-actions">
                {bestCandidate ? (
                  <button
                    type="button"
                    className="compact-action-button"
                    onClick={() => onUseCandidate('Evolve winner:', bestCandidate)}
                  >
                    <FiArrowUpRight />
                  </button>
                ) : null}
                {latestJob?.job_id ? (
                  <button
                    type="button"
                    className="compact-action-button"
                    onClick={onHandoff}
                    disabled={handoffBusy}
                    title="Send the current winner into Forge as a review-first handoff."
                  >
                    <FiCommand />
                  </button>
                ) : null}
              </div>
            </div>

            <div className="jarvis-inline-meta">
              <span className="inline-meta-chip success">
                score {formatNumericScore(latestJob?.best_score ?? latestResult?.best_score)}
              </span>
              <span className="inline-meta-chip">
                gens {latestJob?.generations_run ?? latestResult?.generations_run ?? 0}
              </span>
              <span className="inline-meta-chip">
                evals {latestJob?.evaluations ?? latestResult?.evaluations ?? 0}
              </span>
              <span className="inline-meta-chip success">
                fame {latestJob?.hall_of_fame_count ?? latestResult?.hall_of_fame_count ?? 0}
              </span>
              <span className="inline-meta-chip danger">
                shame {latestJob?.hall_of_shame_count ?? latestResult?.hall_of_shame_count ?? 0}
              </span>
            </div>

            {history.length > 0 && (
              <div className="evolve-generation-list">
                {history.slice(0, 5).map((generation) => (
                  <div
                    key={`generation-${generation.generation_index}`}
                    className="evolve-generation-item"
                  >
                    <div className="evolve-generation-head">
                      <strong>{`Generation ${generation.generation_index + 1}`}</strong>
                      <span>{`best ${formatNumericScore(generation.best_score)}`}</span>
                    </div>
                    <p>{generation.best_candidate}</p>
                    <div className="jarvis-inline-meta">
                      <span className="inline-meta-chip">{`avg ${formatNumericScore(generation.average_score)}`}</span>
                      <span className="inline-meta-chip success">{generation.successful_evaluations} passed</span>
                      <span className="inline-meta-chip danger">{generation.failed_evaluations} failed</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {evaluationPreview.length > 0 && (
              <div className="evolve-evaluation-list">
                {evaluationPreview.map((evaluation) => (
                  <div
                    key={`${evaluation.eval_task_id}-${evaluation.individual_index}`}
                    className={`evolve-evaluation-item ${evaluation.ok ? 'success' : 'danger'}`}
                  >
                    <div className="evolve-generation-head">
                      <strong>{evaluation.eval_task_id}</strong>
                      <span>{evaluation.ok ? `score ${formatNumericScore(evaluation.score)}` : 'failed'}</span>
                    </div>
                    <p>{evaluation.candidate}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <UlTraceBlock
          ulTrace={snapshot?.ul_trace}
          ulSubstrate={snapshot?.ul_substrate}
          label="Evolve UL Trace"
        />

        <div className="evolve-hall-grid">
          <div className="evolve-hall-column fame">
            <div className="evolve-hall-head">
              <strong>Hall of Fame</strong>
              <span>{hallOfFame.length} kept</span>
            </div>
            {hallOfFame.length === 0 ? (
              <p className="session-empty">No successful mutations recorded yet.</p>
            ) : (
              hallOfFame.slice(0, 4).map((entry) => (
                <button
                  key={`${entry.job_id}-${entry.created_at}`}
                  type="button"
                  className="evolve-hall-item"
                  onClick={() => onUseCandidate('Hall of Fame mutation:', entry.candidate)}
                >
                  <strong>{entry.reason}</strong>
                  <span>{`${entry.job_id} · ${formatNumericScore(entry.score)}`}</span>
                </button>
              ))
            )}
          </div>

          <div className="evolve-hall-column shame">
            <div className="evolve-hall-head">
              <strong>Hall of Shame</strong>
              <span>{hallOfShame.length} kept</span>
            </div>
            {hallOfShame.length === 0 ? (
              <p className="session-empty">No failed mutations recorded yet.</p>
            ) : (
              hallOfShame.slice(0, 4).map((entry) => (
                <button
                  key={`${entry.job_id}-${entry.created_at}`}
                  type="button"
                  className="evolve-hall-item"
                  onClick={() => onUseCandidate('Hall of Shame mutation:', entry.candidate)}
                >
                  <strong>{entry.reason}</strong>
                  <span>{`${entry.job_id} · ${formatNumericScore(entry.score)}`}</span>
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ContinuityProfileCard({ continuityProfile }) {
  if (!continuityProfile) {
    return (
      <div className="jarvis-side-card page-panel">
        <div className="jarvis-side-title">
          <FiCpu />
          <h3>Continuity</h3>
        </div>
        <p className="session-empty">Continuity profile will appear after Jarvis initializes the session spine.</p>
      </div>
    );
  }

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiCpu />
        <h3>Continuity</h3>
      </div>

      <details className="jarvis-collapsible-panel">
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Identity continuity profile</span>
            <strong>{continuityProfile.self_description || 'Jarvis continuity anchor loaded.'}</strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          <div className="jarvis-inline-meta">
            <span className="inline-meta-chip">{continuityProfile.tone || 'concise'} tone</span>
            <span className="inline-meta-chip">{(continuityProfile.known_projects || []).length} project anchors</span>
            <span className="inline-meta-chip">{(continuityProfile.preferred_tools || []).length} tool hints</span>
          </div>

          {continuityProfile.continuity_rules?.length > 0 && (
            <div className="v8-guidance-list">
              {continuityProfile.continuity_rules.map((rule) => (
                <span key={rule} className="v8-guidance-chip">{rule}</span>
              ))}
            </div>
          )}

          {continuityProfile.known_projects?.length > 0 && (
            <div className="jarvis-inline-card">
              <div className="jarvis-inline-card-header">
                <span>Known Projects</span>
                <strong>{continuityProfile.known_projects.slice(0, 3).join(' | ')}</strong>
              </div>
            </div>
          )}

          {continuityProfile.preferred_tools?.length > 0 && (
            <div className="jarvis-inline-card">
              <div className="jarvis-inline-card-header">
                <span>Preferred Tools</span>
                <strong>{continuityProfile.preferred_tools.slice(0, 3).join(' | ')}</strong>
              </div>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}

function CorrigibilityCard({ corrigibility, onAppendDraftContext }) {
  const pending = corrigibility?.pending || null;
  const recent = corrigibility?.recent || [];
  const tone = getCorrigibilityTone(corrigibility?.status, corrigibility?.last_severity);

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiRefreshCw />
        <h3>Corrigibility</h3>
      </div>

      <div className={`corrigibility-shell ${corrigibility?.status || 'steady'}`}>
        <div className="corrigibility-summary">
          <strong>
            {pending ? 'Correction queued' : 'Course steady'}
          </strong>
          <p>
            {pending
              ? 'The next generated Jarvis reply will silently absorb the latest operator correction.'
              : 'Explicit self-corrections, rewinds, and soft pauses stay visible here without replacing the rest of Jarvis.'}
          </p>
        </div>

        <div className="jarvis-inline-meta">
          <span className={`inline-meta-chip ${tone}`}>
            {getCorrigibilityStatusLabel(corrigibility?.status)}
          </span>
          <span className="inline-meta-chip">
            {getCorrigibilityActionLabel(corrigibility?.last_action || 'steady')}
          </span>
          <span className={`inline-meta-chip ${getCorrigibilityTone('steady', corrigibility?.last_severity)}`}>
            {getCorrigibilitySeverityLabel(corrigibility?.last_severity)}
          </span>
          <span className="inline-meta-chip">
            {corrigibility?.total_corrections || 0} total
          </span>
        </div>

        {pending ? (
          <div className="corrigibility-pending">
            <strong>Queued Guidance</strong>
            <p>{pending.guidance || pending.command}</p>
            <div className="jarvis-inline-actions">
              <button
                type="button"
                className="inline-card-action"
                onClick={() => onAppendDraftContext(
                  'Queued corrigibility guidance:',
                  pending.guidance || pending.command || '',
                )}
              >
                <FiArrowUpRight />
                Use in Draft
              </button>
            </div>
          </div>
        ) : null}

        {corrigibility?.last_command ? (
          <div className="corrigibility-command">
            <strong>Last Operator Command</strong>
            <p>{corrigibility.last_command}</p>
          </div>
        ) : null}

        {recent.length > 0 ? (
          <div className="corrigibility-events">
            {recent.slice(0, 3).map((event) => (
              <div
                key={`${event.timestamp}-${event.action}-${event.command}`}
                className="corrigibility-event"
              >
                <strong>{getCorrigibilityActionLabel(event.action)}</strong>
                <span>{event.summary}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="session-empty">No corrections recorded in this session yet.</p>
        )}
        <UlTraceBlock
          ulTrace={corrigibility?.ul_trace}
          ulSubstrate={corrigibility?.ul_substrate}
        />
      </div>
    </div>
  );
}

function DreamspaceCard({
  dreamspace,
  presentation,
  busy,
  onAction,
  onAppendDraftContext,
  formatRelativeTime,
}) {
  const recentDreams = dreamspace?.recent_dreams || [];
  const tone = getDreamspaceTone(dreamspace?.status);
  const latestDream = recentDreams[0] || null;

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiCpu />
        <h3>Dreamspace</h3>
      </div>

      <div className={`dreamspace-shell ${dreamspace?.status || 'stopped'}`}>
        <div className="dreamspace-summary">
          <strong>
            {dreamspace?.status === 'dreaming'
              ? 'Weaving a background reflection'
              : dreamspace?.auto_enabled
                ? 'Background reflection armed'
                : 'Dreamspace dormant'}
          </strong>
          <p>{dreamspace?.summary || defaultDreamspace.summary}</p>
        </div>

        <div className="jarvis-inline-meta">
          <span className={`inline-meta-chip ${tone}`}>
            {getDreamspaceStatusLabel(dreamspace?.status)}
          </span>
          <span className={`inline-meta-chip ${dreamspace?.auto_enabled ? 'success' : 'warning'}`}>
            {dreamspace?.auto_enabled ? 'auto enabled' : 'manual only'}
          </span>
          <span className="inline-meta-chip">
            {dreamspace?.total_dreams || 0} total
          </span>
          <span className="inline-meta-chip">
            {dreamspace?.last_style || 'practical'}
          </span>
        </div>

        <div className="dreamspace-actions">
          <button
            type="button"
            className="jarvis-secondary-button"
            onClick={() => onAction('start')}
            disabled={busy || (dreamspace?.auto_enabled && dreamspace?.status !== 'stopped')}
          >
            <FiActivity />
            Start
          </button>
          <button
            type="button"
            className="jarvis-primary-button"
            onClick={() => onAction('run_once')}
            disabled={busy}
          >
            <FiRefreshCw />
            Dream Now
          </button>
          <button
            type="button"
            className="jarvis-secondary-button"
            onClick={() => onAction('pause')}
            disabled={busy || ['paused', 'stopped'].includes(dreamspace?.status)}
          >
            <FiShield />
            Pause
          </button>
          <button
            type="button"
            className="jarvis-secondary-button"
            onClick={() => onAction('resume')}
            disabled={busy || dreamspace?.status !== 'paused'}
          >
            <FiRefreshCw />
            Resume
          </button>
          <button
            type="button"
            className="jarvis-secondary-button"
            onClick={() => onAction('stop')}
            disabled={busy || dreamspace?.status === 'stopped'}
          >
            <FiTrash2 />
            Stop
          </button>
        </div>

        {dreamspace?.last_focus ? (
          <div className="dreamspace-context">
            <strong>Last Focus</strong>
            <p>{dreamspace.last_focus}</p>
            {dreamspace?.last_seed ? (
              <>
                <strong>Last Seed</strong>
                <p>{dreamspace.last_seed}</p>
              </>
            ) : null}
          </div>
        ) : null}

        {latestDream ? (
          <div className="dreamspace-latest">
            <div className="dreamspace-latest-head">
              <strong>Latest Reflection</strong>
              <span>{formatRelativeTime(latestDream.timestamp || dreamspace?.last_dream_at)}</span>
            </div>
            <p>{latestDream.text}</p>
            <div className="jarvis-inline-actions">
              <button
                type="button"
                className="inline-card-action"
                onClick={() => onAppendDraftContext('Dreamspace reflection:', latestDream.text || '')}
              >
                <FiArrowUpRight />
                Use in Draft
              </button>
            </div>
          </div>
        ) : presentation ? (
          <div className="dreamspace-latest">
            <div className="dreamspace-latest-head">
              <strong>Presentation</strong>
            </div>
            <p>{presentation}</p>
          </div>
        ) : (
          <p className="session-empty">No Dreamspace reflections recorded yet.</p>
        )}

        {dreamspace?.last_error ? (
          <div className="dreamspace-error">
            <strong>Last Error</strong>
            <p>{dreamspace.last_error}</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function PatchReviewCard({
  reviews,
  preview,
  previewBusy,
  actionBusyId,
  onRefresh,
  onPreview,
  onApply,
  formatRelativeTime,
}) {
  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiCheckCircle />
        <h3>Patch Reviews</h3>
      </div>

      <p className="session-empty">
        Review approval is the gate. Jarvis only applies patches from accepted review records.
      </p>

      <div className="jarvis-inline-actions">
        <button
          type="button"
          className="jarvis-secondary-button"
          onClick={onRefresh}
          disabled={previewBusy}
        >
          <FiRefreshCw />
          Refresh
        </button>
      </div>

      <div className="action-list">
        {reviews.length === 0 ? (
          <p className="session-empty">No patch reviews recorded for this session yet.</p>
        ) : (
          reviews.map((review) => {
            const ready = Boolean(review?.apply_gate?.ready);
            const blocker = review?.apply_gate?.blockers?.[0] || '';
            const decisionState = review?.current_decision?.state || review?.status || 'proposed';
            const reviewFileCount = review?.target_files?.length || 0;
            return (
              <div key={review.id} className="action-item">
                <div className="action-main">
                  <strong>{review.goal || 'Patch review'}</strong>
                  <span>
                    {reviewFileCount}
                    {' '}
                    file(s)
                    {' '}
                    • updated
                    {' '}
                    {formatRelativeTime(review.updated_at)}
                  </span>
                  <div className="jarvis-inline-meta">
                    <span className={`inline-meta-chip ${ready ? 'success' : 'warning'}`}>
                      {ready ? 'Review accepted' : formatProtocolLabel(decisionState)}
                    </span>
                    <span className="inline-meta-chip">
                      {review.hunk_count || 0}
                      {' '}
                      hunks
                    </span>
                  </div>
                  {blocker ? (
                    <span>{blocker}</span>
                  ) : null}
                </div>
                <div className="jarvis-inline-actions">
                  <button
                    type="button"
                    className="compact-action-button"
                    onClick={() => onPreview(review.id)}
                    disabled={previewBusy}
                    aria-label="Preview patch review"
                  >
                    <FiSearch />
                  </button>
                  <button
                    type="button"
                    className="jarvis-secondary-button action-run-button"
                    onClick={() => onApply(review)}
                    disabled={!ready || actionBusyId === 'apply_patch_review'}
                  >
                    <FiCommand />
                    {actionBusyId === 'apply_patch_review' ? 'Running' : 'Apply'}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {preview ? (
        <div className="workspace-preview">
          <div className="workspace-preview-header">
            <div>
              <span>Patch preview</span>
              <strong>{preview.reviewId}</strong>
            </div>
            <span className={`inline-meta-chip ${preview.ready_for_review ? 'success' : 'warning'}`}>
              {preview.status}
            </span>
          </div>
          <p>{preview.summary}</p>
          <div className="workspace-results">
            {(preview.files || []).slice(0, 4).map((file) => (
              <div key={file.path} className="workspace-result">
                <div className="workspace-result-main">
                  <strong>{file.path}</strong>
                  <span>{file.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      <UlTraceBlock
        ulTrace={preview?.ul_trace || reviews?.[0]?.ul_trace}
        ulSubstrate={preview?.ul_substrate || reviews?.[0]?.ul_substrate}
      />
    </div>
  );
}

function ToolResultCard({
  toolResult,
  onOpenFile,
  onSearchWorkspace,
  onAppendDraftContext,
  onRunAction,
  actionBusyId,
}) {
  if (!toolResult) {
    return null;
  }

  const humanizeMysticLabel = (value) => String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
  const capabilityMeta = toolResult.capability || null;
  const renderCapabilityMeta = () => {
    if (!capabilityMeta?.module) {
      return null;
    }
    return (
      <div className="capability-meta-block">
        <div className="jarvis-inline-card-header">
          <span>Governed Route</span>
          <strong>{capabilityMeta.capability_label || capabilityMeta.module}</strong>
        </div>
        <div className="capability-meta-strip">
          <span className="inline-meta-chip">{capabilityMeta.module}</span>
          {capabilityMeta.action ? (
            <span className="inline-meta-chip">{capabilityMeta.action}</span>
          ) : null}
          {capabilityMeta.provider ? (
            <span className="inline-meta-chip">{capabilityMeta.provider}</span>
          ) : null}
          {capabilityMeta.requested_provider_mode ? (
            <span className="inline-meta-chip">{capabilityMeta.requested_provider_mode}</span>
          ) : null}
          {capabilityMeta.governance_mode ? (
            <span className="inline-meta-chip">{capabilityMeta.governance_mode}</span>
          ) : null}
          {capabilityMeta.audit_sequence ? (
            <span className="inline-meta-chip">audit #{capabilityMeta.audit_sequence}</span>
          ) : null}
        </div>
      </div>
    );
  };

  if (toolResult.type === 'action_request' && toolResult.action) {
    const action = toolResult.action;
    return (
      <div className="jarvis-inline-card">
        <div className="jarvis-inline-card-header">
          <span>Approval Needed</span>
          <strong>{action.label}</strong>
        </div>
        <p>{action.description}</p>
        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip">{action.command_preview}</span>
          {action.requires_approval && (
            <span className="inline-meta-chip warning">Explicit approval required</span>
          )}
        </div>
        <button
          type="button"
          className="inline-card-action"
          onClick={() => onRunAction(action)}
          disabled={actionBusyId === action.id}
        >
          <FiCommand />
          {actionBusyId === action.id ? 'Running...' : 'Approve and Run'}
        </button>
      </div>
    );
  }

  if (toolResult.type === 'memory_add' && toolResult.memory) {
    return (
      <div className="jarvis-inline-card">
        <div className="jarvis-inline-card-header">
          <span>Tool</span>
          <strong>Long-Term Memory Updated</strong>
        </div>
        <p>{toolResult.memory.text}</p>
      </div>
    );
  }

  if (toolResult.type === 'document_answer') {
    const sources = toolResult.sources || [];
    return (
      <div className="jarvis-inline-card">
        <div className="jarvis-inline-card-header">
          <span>Document Intake</span>
          <strong>Grounded Answer</strong>
        </div>
        <p>{toolResult.summary || 'Jarvis answered from the current intake set.'}</p>
        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip">{sources.length} sources</span>
          {toolResult.query ? (
            <span className="inline-meta-chip">{toolResult.query}</span>
          ) : null}
        </div>
        {sources.length > 0 ? (
          <div className="jarvis-inline-list">
            {sources.slice(0, 3).map((source) => (
              <button
                key={`${source.doc_id}-${source.score}`}
                type="button"
                className="workspace-context-chip"
                onClick={() => onAppendDraftContext(
                  `Document source (${source.doc_id}):`,
                  source.excerpt || '',
                )}
              >
                {source.doc_id}
              </button>
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  if (toolResult.type === 'corrigibility') {
    const pending = toolResult.pending || null;
    const removedTurn = toolResult.removed_turn || null;
    const tone = getCorrigibilityTone(
      toolResult.status === 'queued' ? 'pending' : 'steady',
      toolResult.severity,
    );

    return (
      <div className="jarvis-inline-card corrigibility-inline-card">
        <div className="jarvis-inline-card-header">
          <span>Corrigibility</span>
          <strong>{toolResult.action?.label || 'Course Correction'}</strong>
        </div>
        <p>{toolResult.summary || 'Jarvis adjusted course from explicit operator feedback.'}</p>
        <div className="jarvis-inline-meta">
          <span className={`inline-meta-chip ${tone}`}>
            {getCorrigibilityStatusLabel(toolResult.status)}
          </span>
          <span className={`inline-meta-chip ${getCorrigibilityTone('steady', toolResult.severity)}`}>
            {getCorrigibilitySeverityLabel(toolResult.severity)}
          </span>
          {toolResult.direction ? (
            <span className="inline-meta-chip">
              {getCorrigibilityStatusLabel(toolResult.direction)}
            </span>
          ) : null}
          {toolResult.system_guard?.status ? (
            <span className={`inline-meta-chip ${toolResult.system_guard.status === 'paused' ? 'warning' : toolResult.system_guard.status === 'stopped' ? 'danger' : 'success'}`}>
              Guard {getSystemGuardLabel(toolResult.system_guard.status)}
            </span>
          ) : null}
        </div>
        {toolResult.command ? (
          <div className="corrigibility-inline-block">
            <strong>Operator Command</strong>
            <p>{toolResult.command}</p>
          </div>
        ) : null}
        {pending ? (
          <div className="corrigibility-inline-block">
            <strong>Queued Guidance</strong>
            <p>{pending.guidance || pending.command}</p>
          </div>
        ) : null}
        {removedTurn?.content ? (
          <button
            type="button"
            className="inline-card-action"
            onClick={() => onAppendDraftContext('Rewound assistant answer:', removedTurn.content)}
          >
            <FiArrowUpRight />
            Review Rewound Answer
          </button>
        ) : null}
        <UlTraceBlock
          ulTrace={toolResult?.ul_trace}
          ulSubstrate={toolResult?.ul_substrate}
        />
      </div>
    );
  }

  if (toolResult.type === 'workspace_search') {
    return (
      <div className="jarvis-inline-card">
        <div className="jarvis-inline-card-header">
          <span>Tool</span>
          <strong>Workspace Search</strong>
        </div>
        <p>
          {toolResult.results?.length || 0} matches
          {toolResult.query ? ` for "${toolResult.query}"` : ''}
        </p>
        <div className="jarvis-inline-list">
          {(toolResult.results || []).slice(0, 3).map((result) => (
            <button
              key={`${result.relative_path}-${result.kind}`}
              type="button"
              className="workspace-context-chip"
              onClick={() => onOpenFile(result.relative_path)}
            >
              {result.relative_path}
            </button>
          ))}
        </div>
        {toolResult.query && (
          <button
            type="button"
            className="inline-card-action"
            onClick={() => onSearchWorkspace(toolResult.query)}
          >
            <FiSearch />
            Open in Workspace Tools
          </button>
        )}
      </div>
    );
  }

  if (toolResult.type === 'workspace_file') {
    return (
      <div className="jarvis-inline-card">
        <div className="jarvis-inline-card-header">
          <span>Tool</span>
          <strong>File Preview Ready</strong>
        </div>
        <p>{toolResult.relative_path}</p>
        <div className="jarvis-inline-actions">
          <button
            type="button"
            className="inline-card-action"
            onClick={() => onOpenFile(toolResult.relative_path)}
          >
            <FiFolder />
            Open Preview
          </button>
          <button
            type="button"
            className="inline-card-action"
            onClick={() => onAppendDraftContext(
              `File context (${toolResult.relative_path}):`,
              toolResult.content?.slice(0, 1200) || '',
            )}
          >
            <FiArrowUpRight />
            Use as Context
          </button>
        </div>
      </div>
    );
  }

  if (toolResult.type === 'spatial_reason') {
    const result = toolResult.result || {};
    const path = Array.isArray(result.path) ? result.path.join(' -> ') : '';
    const blockers = Array.isArray(result.blocked_by) ? result.blocked_by.join(', ') : '';

    return (
      <div className={`jarvis-inline-card ${toolResult.status === 'failed' ? 'action-failed' : ''}`}>
        <div className="jarvis-inline-card-header">
          <span>Spatial Tool</span>
          <strong>{toolResult.mode ? `${toolResult.mode}`.replace(/_/g, ' ') : 'spatial_reason'}</strong>
        </div>
        <p>{toolResult.summary || 'Spatial reasoning completed.'}</p>
        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip">{toolResult.space_id || 'unnamed space'}</span>
          <span className={`inline-meta-chip ${toolResult.status === 'failed' ? 'danger' : 'success'}`}>
            {toolResult.status || 'completed'}
          </span>
          {typeof result.distance === 'number' ? (
            <span className="inline-meta-chip">distance {result.distance}</span>
          ) : null}
          {typeof result.distance_meters === 'number' && !Number.isNaN(result.distance_meters) ? (
            <span className="inline-meta-chip">{result.distance_meters.toFixed(1)} m</span>
          ) : null}
          {typeof result.bearing_degrees === 'number' ? (
            <span className="inline-meta-chip">
              {result.bearing_degrees.toFixed(1)} deg{result.bearing_label ? ` ${result.bearing_label}` : ''}
            </span>
          ) : null}
          {typeof result.travel_minutes === 'number' ? (
            <span className="inline-meta-chip">{result.travel_minutes.toFixed(1)} min</span>
          ) : null}
          {Object.prototype.hasOwnProperty.call(result, 'visible') ? (
            <span className={`inline-meta-chip ${result.visible ? 'success' : 'warning'}`}>
              {result.visible ? 'visible' : 'blocked'}
            </span>
          ) : null}
        </div>
        {path ? (
          <div className="corrigibility-inline-block">
            <strong>Path</strong>
            <p>{path}</p>
          </div>
        ) : null}
        {blockers ? (
          <div className="corrigibility-inline-block">
            <strong>Blocked By</strong>
            <p>{blockers}</p>
          </div>
        ) : null}
        {result.reason ? (
          <div className="corrigibility-inline-block">
            <strong>Reason</strong>
            <p>{result.reason}</p>
          </div>
        ) : null}
        {renderCapabilityMeta()}
        <UlTraceBlock
          ulTrace={toolResult?.ul_trace}
          ulSubstrate={toolResult?.ul_substrate}
        />
      </div>
    );
  }

  if (toolResult.type === 'mystic_reading') {
    const reading = toolResult.result || {};
    const stateLabel = reading.state_label || humanizeMysticLabel(reading.state || 'seeking');
    const dominantLabel = reading.dominant_archetype_label || humanizeMysticLabel(reading.dominant_archetype || 'witness');
    const opposingLabel = reading.opposing_archetype_label || humanizeMysticLabel(reading.opposing_archetype || 'trickster');
    const detectedSignals = Array.isArray(reading.detected_signals) ? reading.detected_signals : [];
    const readingContext = [
      `State: ${stateLabel}`,
      `Dominant archetype: ${dominantLabel}`,
      `Opposing archetype: ${opposingLabel}`,
      `Trial: ${reading.trial || 'Action vs avoidance'}`,
      `Meaning: ${reading.meaning || ''}`,
      `Risk: ${reading.risk || ''}`,
      `Next action: ${reading.next_action || 'Choose one small action and complete it fully.'}`,
    ].filter(Boolean).join('\n');

    return (
      <div className="jarvis-inline-card mystic-inline-card">
        <div className="jarvis-inline-card-header">
          <span>Mystic Engine</span>
          <strong>{stateLabel}</strong>
        </div>
        <p>{toolResult.summary || 'Mystic reading completed.'}</p>
        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip">{dominantLabel}</span>
          <span className="inline-meta-chip warning">Opposed by {opposingLabel}</span>
          <span className={`inline-meta-chip ${toolResult.status === 'failed' ? 'danger' : 'success'}`}>
            {toolResult.status || 'completed'}
          </span>
        </div>
        <div className="mystic-reading-grid">
          <div className="mystic-reading-block">
            <strong>Trial</strong>
            <p>{reading.trial || 'Action vs avoidance'}</p>
          </div>
          <div className="mystic-reading-block">
            <strong>Meaning</strong>
            <p>{reading.meaning || 'Your current path is still coming into focus.'}</p>
          </div>
          <div className="mystic-reading-block">
            <strong>Risk</strong>
            <p>{reading.risk || 'Inaction reinforces the current negative pattern.'}</p>
          </div>
          <div className="mystic-reading-block">
            <strong>Next Action</strong>
            <p>{reading.next_action || 'Choose one small action and complete it fully.'}</p>
          </div>
        </div>
        {detectedSignals.length ? (
          <div className="mystic-reading-block mystic-reading-signals">
            <strong>Detected Signals</strong>
            <p>{detectedSignals.slice(0, 6).join(', ')}</p>
          </div>
        ) : null}
        {renderCapabilityMeta()}
        <button
          type="button"
          className="inline-card-action"
          onClick={() => onAppendDraftContext('Mystic reading:', readingContext)}
        >
          <FiArrowUpRight />
          Use in Chat
        </button>
      </div>
    );
  }

  if (toolResult.type === 'v9_core') {
    const result = toolResult.result || {};
    const pipeline = Array.isArray(result.pipeline) ? result.pipeline : [];
    const stageLabels = pipeline.map((stage) => String(stage || '').replace(/_/g, ' '));
    const summaryContext = [
      `Location: ${result.location || ''}`,
      `Characters: ${(result.characters || []).join(', ')}`,
      `Pipeline: ${stageLabels.join(' -> ')}`,
      `Provider: ${result.provider || ''}`,
    ].filter(Boolean).join('\n');

    return (
      <div className={`jarvis-inline-card v10-inline-card ${toolResult.status === 'failed' ? 'action-failed' : ''}`}>
        <div className="jarvis-inline-card-header">
          <span>V9 Core</span>
          <strong>{result.location || 'scene continuation'}</strong>
        </div>
        <p>{toolResult.summary || 'V9 core completed.'}</p>
        <div className="jarvis-inline-meta">
          <span className={`inline-meta-chip ${toolResult.status === 'failed' ? 'danger' : 'success'}`}>
            {toolResult.status || 'completed'}
          </span>
          {result.location ? (
            <span className="inline-meta-chip">{result.location}</span>
          ) : null}
          {result.provider ? (
            <span className="inline-meta-chip">{result.provider}</span>
          ) : null}
        </div>
        {stageLabels.length ? (
          <div className="mystic-reading-block v10-stage-block">
            <strong>Pipeline</strong>
            <p>{stageLabels.join(' -> ')}</p>
          </div>
        ) : null}
        {renderCapabilityMeta()}
        <button
          type="button"
          className="inline-card-action"
          onClick={() => onAppendDraftContext('V9 core:', summaryContext)}
        >
          <FiArrowUpRight />
          Use in Chat
        </button>
      </div>
    );
  }

  if (toolResult.type === 'v10_core') {
    const result = toolResult.result || {};
    const sceneBrief = result.scene_brief || {};
    const qualityReport = result.quality_report || {};
    const pipeline = Array.isArray(result.pipeline) ? result.pipeline : [];
    const stageLabels = pipeline.map((stage) => String(stage || '').replace(/_/g, ' '));
    const qualityScore = qualityReport.quality_score;
    const summaryContext = [
      `Focus: ${sceneBrief.focus || ''}`,
      `Objective: ${sceneBrief.objective || ''}`,
      `Tension: ${sceneBrief.tension || ''}`,
      `Ending pressure: ${sceneBrief.ending_pressure || ''}`,
      `Pipeline: ${stageLabels.join(' -> ')}`,
      `Quality score: ${qualityScore ?? 'unknown'}`,
      `Readiness: ${qualityReport.readiness || ''}`,
      `Next revision focus: ${qualityReport.next_revision_focus || ''}`,
    ].filter(Boolean).join('\n');

    return (
      <div className={`jarvis-inline-card v10-inline-card ${toolResult.status === 'failed' ? 'action-failed' : ''}`}>
        <div className="jarvis-inline-card-header">
          <span>V10 Core</span>
          <strong>{qualityReport.readiness || 'structured draft'}</strong>
        </div>
        <p>{toolResult.summary || 'V10 core completed.'}</p>
        <div className="jarvis-inline-meta">
          <span className={`inline-meta-chip ${toolResult.status === 'failed' ? 'danger' : 'success'}`}>
            {toolResult.status || 'completed'}
          </span>
          {typeof qualityScore === 'number' ? (
            <span className="inline-meta-chip">score {qualityScore}/100</span>
          ) : null}
          {result.location ? (
            <span className="inline-meta-chip">{result.location}</span>
          ) : null}
          {result.provider ? (
            <span className="inline-meta-chip">{result.provider}</span>
          ) : null}
        </div>
        <div className="v10-reading-grid">
          <div className="mystic-reading-block">
            <strong>Focus</strong>
            <p>{sceneBrief.focus || 'Advance the scene clearly.'}</p>
          </div>
          <div className="mystic-reading-block">
            <strong>Objective</strong>
            <p>{sceneBrief.objective || 'Move the scene toward a consequential beat.'}</p>
          </div>
          <div className="mystic-reading-block">
            <strong>Tension</strong>
            <p>{sceneBrief.tension || 'rising'}</p>
          </div>
          <div className="mystic-reading-block">
            <strong>Next Revision Focus</strong>
            <p>{qualityReport.next_revision_focus || 'Tighten specificity and keep the pressure live.'}</p>
          </div>
        </div>
        {stageLabels.length ? (
          <div className="mystic-reading-block v10-stage-block">
            <strong>Pipeline</strong>
            <p>{stageLabels.join(' -> ')}</p>
          </div>
        ) : null}
        {renderCapabilityMeta()}
        <button
          type="button"
          className="inline-card-action"
          onClick={() => onAppendDraftContext('V10 core:', summaryContext)}
        >
          <FiArrowUpRight />
          Use in Chat
        </button>
      </div>
    );
  }

  if (toolResult.type === 'action_result' && toolResult.action) {
    const previewText = toolResult.stdout || toolResult.stderr || '';
    return (
      <div className={`jarvis-inline-card ${toolResult.status === 'failed' ? 'action-failed' : ''}`}>
        <div className="jarvis-inline-card-header">
          <span>Operator Action</span>
          <strong>{toolResult.action.label}</strong>
        </div>
        <p>{toolResult.summary || 'Action completed.'}</p>
        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip">{toolResult.action.command_preview}</span>
          <span className={`inline-meta-chip ${toolResult.status === 'failed' ? 'danger' : 'success'}`}>
            {toolResult.status} · exit {toolResult.exit_code}
          </span>
        </div>
        {previewText ? (
          <div className="jarvis-inline-output">
            <strong>Output Preview</strong>
            <pre>{previewText}</pre>
          </div>
        ) : null}
      </div>
    );
  }

  return null;
}

function ContextCards({
  workspaceContext,
  liveResearch,
  persistentMemories,
  onOpenFile,
  onOpenSource,
  onSearchWorkspace,
  onAppendDraftContext,
}) {
  const hasWorkspace = Boolean(workspaceContext?.results?.length);
  const hasLiveResearch = Boolean(liveResearch?.sources?.length);
  const hasMemories = Boolean(persistentMemories?.length);

  if (!hasWorkspace && !hasLiveResearch && !hasMemories) {
    return null;
  }

  return (
    <div className="jarvis-inline-card-grid">
      {hasWorkspace && (
        <div className="jarvis-inline-card">
          <div className="jarvis-inline-card-header">
            <span>Attached Context</span>
            <strong>{workspaceContext.query || 'Workspace'}</strong>
          </div>
          <p>{workspaceContext.summary || 'Jarvis attached local workspace context for this reply.'}</p>
          <div className="jarvis-inline-list">
            {(workspaceContext.files || []).map((file) => (
              <button
                key={file.relative_path}
                type="button"
                className="workspace-context-chip"
                onClick={() => onOpenFile(file.relative_path)}
              >
                {file.relative_path}
              </button>
            ))}
          </div>
          {workspaceContext.query && (
            <div className="jarvis-inline-actions">
              <button
                type="button"
                className="inline-card-action"
                onClick={() => onSearchWorkspace(workspaceContext.query)}
              >
                <FiSearch />
                Review Matches
              </button>
            </div>
          )}
        </div>
      )}

      {hasLiveResearch && (
        <div className="jarvis-inline-card">
          <div className="jarvis-inline-card-header">
            <span>Live Research</span>
            <strong>{liveResearch.query}</strong>
          </div>
          <p>{liveResearch.summary || 'Jarvis attached fresh web sources for this reply.'}</p>
          <div className="jarvis-inline-source-list">
            {(liveResearch.sources || []).map((source) => (
              <button
                key={`${source.id}-${source.url}`}
                type="button"
                className="jarvis-inline-source"
                onClick={() => onOpenSource(source.url)}
              >
                <strong>[{source.id}] {source.title}</strong>
                <span>{source.display_url || source.url}</span>
                <p>{source.snippet || source.excerpt}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {hasMemories && (
        <div className="jarvis-inline-card">
          <div className="jarvis-inline-card-header">
            <span>Memory Cues</span>
            <strong>{persistentMemories.length} loaded</strong>
          </div>
          <div className="jarvis-inline-memory-list">
            {persistentMemories.slice(0, 3).map((memory) => (
              <button
                key={memory.id}
                type="button"
                className="jarvis-inline-memory"
                onClick={() => onAppendDraftContext('Saved memory context:', `- ${memory.text}`)}
              >
                <p>{memory.text}</p>
                {memory.tags?.length > 0 && (
                  <div className="memory-tags">
                    {memory.tags.map((tag) => (
                      <span key={tag} className="memory-tag">{tag}</span>
                    ))}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ResponseTraceCard({ responseTrace }) {
  if (!responseTrace) {
    return null;
  }

  const formatTraceLabel = (value) => String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
  const specialistFocusLabel = responseTrace.specialist_domain && responseTrace.specialist_focus
    ? `${responseTrace.specialist_domain} / ${responseTrace.specialist_focus.replace(/_/g, ' ')}`
    : null;
  const specialistPresetLabel = responseTrace.specialist_preset?.label || null;
  const metrics = [
    `${responseTrace.contract_label || responseTrace.contract || 'direct answer'}`,
    `${responseTrace.workspace_hits || 0} workspace`,
    `${responseTrace.research_sources || 0} sources`,
    `${responseTrace.memory_count || 0} memories`,
  ];
  const specialistLenses = responseTrace.specialist_lenses || [];
  const godBrain = responseTrace.god_brain || null;
  const godBrainCouncil = godBrain?.council || [];
  const godBrainExecutionPath = godBrain?.execution_path || [];
  const godBrainArbiter = godBrain?.arbiter || null;
  const governedPipeline = responseTrace.governed_pipeline || null;
  const capabilityBridge = responseTrace.capability_bridge || governedPipeline?.capability || null;
  const modelRoute = responseTrace.model_route || null;
  const traceDetailSummary = [
    modelRoute?.label || null,
    specialistFocusLabel || specialistPresetLabel || null,
    capabilityBridge?.module ? `${capabilityBridge.module} bridge` : null,
    responseTrace.plan_summary ? 'plan captured' : null,
  ].filter(Boolean).join(' · ');

  return (
    <div className="jarvis-inline-card response-trace-card">
      <div className="jarvis-inline-card-header">
        <span>Response Trace</span>
        <strong>{getResponseModeLabel(responseTrace.mode)} Contract</strong>
      </div>
      <p>{responseTrace.summary || 'Jarvis recorded how this answer was put together.'}</p>
      <div className="jarvis-inline-meta">
        {metrics.map((metric) => (
          <span key={metric} className="inline-meta-chip">{metric}</span>
        ))}
      </div>
      <details className="jarvis-collapsible-panel response-trace-panel">
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Inspect trace</span>
            <strong>{traceDetailSummary || 'Route, specialists, and planning details'}</strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          {(specialistFocusLabel || specialistPresetLabel || responseTrace.specialist_selection_source) && (
            <div className="jarvis-inline-meta">
              {specialistFocusLabel ? (
                <span className="inline-meta-chip">{specialistFocusLabel}</span>
              ) : null}
              {specialistPresetLabel ? (
                <span className="inline-meta-chip">{specialistPresetLabel}</span>
              ) : null}
              {responseTrace.specialist_selection_source ? (
                <span className="inline-meta-chip">
                  {responseTrace.specialist_selection_source === 'auto'
                    ? 'auto specialists'
                    : responseTrace.specialist_selection_source}
                </span>
              ) : null}
            </div>
          )}
          {responseTrace.specialist_summary && (
            <p>{responseTrace.specialist_summary}</p>
          )}
          {modelRoute && (
            <div className="jarvis-inline-output model-route-trace">
              <strong>Model Route</strong>
              <p>{modelRoute.summary || 'Jarvis selected a turn-specific local route.'}</p>
              <div className="jarvis-inline-meta">
                <span className="inline-meta-chip">{modelRoute.label || 'Local Route'}</span>
                {modelRoute.reason ? (
                  <span className="inline-meta-chip">{formatTraceLabel(modelRoute.reason)}</span>
                ) : null}
                {modelRoute.adapter_mode ? (
                  <span className="inline-meta-chip">Adapter {formatTraceLabel(modelRoute.adapter_mode)}</span>
                ) : null}
              </div>
            </div>
          )}
          {(capabilityBridge?.module || governedPipeline?.active_lane) && (
            <div className="jarvis-inline-output">
              <strong>Capability Route</strong>
              <p>
                {capabilityBridge?.module
                  ? `${capabilityBridge.module}.${capabilityBridge.action || 'execute'} stayed on the governed ${governedPipeline?.active_lane || 'service_tools'} lane.`
                  : `This turn stayed on the governed ${governedPipeline?.active_lane || 'service_tools'} lane.`}
              </p>
              <div className="jarvis-inline-meta">
                {capabilityBridge?.module ? (
                  <span className="inline-meta-chip">{capabilityBridge.module}</span>
                ) : null}
                {capabilityBridge?.provider ? (
                  <span className="inline-meta-chip">{capabilityBridge.provider}</span>
                ) : null}
                {capabilityBridge?.requested_provider_mode ? (
                  <span className="inline-meta-chip">{capabilityBridge.requested_provider_mode}</span>
                ) : null}
                {capabilityBridge?.governance_mode ? (
                  <span className="inline-meta-chip">{capabilityBridge.governance_mode}</span>
                ) : null}
                {governedPipeline?.active_lane ? (
                  <span className="inline-meta-chip">{governedPipeline.active_lane}</span>
                ) : null}
                {capabilityBridge?.audit_sequence ? (
                  <span className="inline-meta-chip">audit #{capabilityBridge.audit_sequence}</span>
                ) : null}
              </div>
              {governedPipeline?.direct_route?.length ? (
                <div className="trace-step-list">
                  {governedPipeline.direct_route.map((step) => (
                    <span key={step} className="trace-step">{step}</span>
                  ))}
                </div>
              ) : null}
              {governedPipeline?.validation ? (
                <p className="god-brain-rule">
                  {governedPipeline.validation.tool_traffic_isolated
                    ? 'Tool traffic isolated.'
                    : 'Tool traffic isolation failed.'}
                  {' '}
                  {governedPipeline.validation.direct_lane_tool_free
                    ? 'Direct lane stayed tool-free.'
                    : 'Direct lane included tool traffic.'}
                </p>
              ) : null}
            </div>
          )}
          {godBrain && (
            <div className="jarvis-inline-output god-brain-trace">
              <strong>God Brain</strong>
              <p>{godBrain.summary || godBrain.strategy_summary || 'The sovereign core shaped this turn.'}</p>
              <div className="jarvis-inline-meta">
                <span className="inline-meta-chip">{godBrain.strategy_label || 'Sovereign Core'}</span>
                {godBrain.action_bias_label ? (
                  <span className="inline-meta-chip">{godBrain.action_bias_label}</span>
                ) : null}
                {godBrainArbiter?.confidence_label ? (
                  <span className="inline-meta-chip">{godBrainArbiter.confidence_label}</span>
                ) : null}
                {godBrainArbiter?.disagreement_label ? (
                  <span className="inline-meta-chip">{godBrainArbiter.disagreement_label}</span>
                ) : null}
              </div>
              {godBrainCouncil.length > 0 && (
                <div className="jarvis-inline-list god-brain-council-list">
                  {godBrainCouncil.map((member) => (
                    <span key={member.id || member.label} className="workspace-context-chip god-brain-chip">
                      {member.label}
                      {member.role ? ` · ${formatTraceLabel(member.role)}` : ''}
                    </span>
                  ))}
                </div>
              )}
              {godBrainExecutionPath.length > 0 && (
                <div className="trace-step-list">
                  {godBrainExecutionPath.map((step) => (
                    <span key={step.id || step.label} className="trace-step">
                      {step.label || formatTraceLabel(step.id)}
                    </span>
                  ))}
                </div>
              )}
              {godBrainArbiter?.rule && (
                <p className="god-brain-rule">{godBrainArbiter.rule}</p>
              )}
            </div>
          )}
          {specialistLenses.length > 0 && (
            <div className="jarvis-inline-list">
              {specialistLenses.map((lens) => (
                <span key={lens.id || lens.label} className="workspace-context-chip">
                  {lens.label}
                </span>
              ))}
            </div>
          )}
          {responseTrace.steps?.length > 0 && (
            <div className="trace-step-list">
              {responseTrace.steps.map((step) => (
                <span key={step} className="trace-step">{step}</span>
              ))}
            </div>
          )}
          {responseTrace.plan_summary && (
            <div className="jarvis-inline-output trace-plan">
              <strong>Plan Pass</strong>
              <pre>{responseTrace.plan_summary}</pre>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}

function CapabilityBridgeConsoleCard({
  snapshot,
  busy,
  loadError,
  executeBusy,
  selectedCapabilityId,
  selectedActionId,
  providerMode,
  governanceMode,
  fieldValues,
  latestExecution,
  onCapabilityChange,
  onActionChange,
  onProviderModeChange,
  onGovernanceModeChange,
  onFieldValueChange,
  onRun,
  onStagePrompt,
  onRefresh,
  formatRelativeTime,
  onOpenFile,
  onSearchWorkspace,
  onAppendDraftContext,
  onRunAction,
  actionBusyId,
}) {
  const capabilities = snapshot?.available_capabilities || [];
  const selectedCapability = capabilities.find((capability) => capability.id === selectedCapabilityId)
    || capabilities[0]
    || null;
  const selectedAction = selectedCapability?.actions?.find((action) => action.id === selectedActionId)
    || selectedCapability?.actions?.[0]
    || null;
  const selectedHealth = selectedCapability ? snapshot?.module_health?.[selectedCapability.id] : null;
  const recentEvents = selectedCapability
    ? (snapshot?.recent_events || [])
      .filter((event) => event.capability_id === selectedCapability.id)
      .slice()
      .reverse()
      .slice(0, 4)
    : [];
  const executionPreview = latestExecution?.execution_preview || (
    selectedCapability && selectedAction
      ? {
          capability_label: selectedCapability.label,
          action_label: selectedAction.label,
          module: selectedCapability.module,
          path: 'capability_service_bridge',
          service_lane: 'service_tools',
          provider_mode_requested: providerMode || selectedAction.default_provider_mode,
          governance_mode: governanceMode || selectedAction.default_governance_mode,
        }
      : null
  );
  const registryStatusLabel = busy
    ? 'Loading registry...'
    : (loadError ? 'Fallback registry' : 'Registry live');
  const registryStatusTone = busy ? 'warning' : (loadError ? 'warning' : 'success');

  return (
    <div className="jarvis-side-card page-panel capability-bridge-card">
      <div className="jarvis-side-title">
        <FiCpu />
        <h3>Capability Dropdown</h3>
      </div>
      <p className="session-empty capability-bridge-summary">
        Governed selector for service-lane execution through the capability bridge.
      </p>
      {loadError ? (
        <div className="capability-bridge-warning">
          Using fallback registry: {loadError}
        </div>
      ) : null}

      <div className="capability-bridge-head">
        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip">{snapshot?.path || 'capability_service_bridge'}</span>
          <span className="inline-meta-chip">{snapshot?.service_lane || 'service_tools'}</span>
          <span className={`inline-meta-chip ${registryStatusTone}`}>
            {registryStatusLabel}
          </span>
          {!busy ? (
            <span className="inline-meta-chip">{snapshot?.event_count || 0} events</span>
          ) : null}
        </div>
        <button
          type="button"
          className="jarvis-secondary-button"
          onClick={onRefresh}
          disabled={busy || executeBusy}
        >
          <FiRefreshCw />
          {busy ? 'Refreshing...' : 'Refresh Bridge'}
        </button>
      </div>

      {!selectedCapability || !selectedAction ? (
        <p className="session-empty capability-bridge-empty">
          No governed capability registry is available yet.
        </p>
      ) : (
        <>
          <div className="capability-bridge-select-grid">
            <label className="jarvis-intake-field">
              <span>Capability</span>
              <select
                value={selectedCapability.id}
                onChange={(event) => onCapabilityChange(event.target.value)}
              >
                {capabilities.map((capability) => (
                  <option key={capability.id} value={capability.id}>{capability.label}</option>
                ))}
              </select>
            </label>

            <label className="jarvis-intake-field">
              <span>Action</span>
              <select
                value={selectedAction.id}
                onChange={(event) => onActionChange(event.target.value)}
              >
                {(selectedCapability.actions || []).map((action) => (
                  <option key={action.id} value={action.id}>{action.label}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="capability-bridge-select-grid capability-bridge-select-grid--advanced">
            <label className="jarvis-intake-field">
              <span>Provider</span>
              <select
                value={providerMode || selectedAction.default_provider_mode}
                onChange={(event) => onProviderModeChange(event.target.value)}
              >
                {(selectedAction.provider_modes || []).map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>

            <label className="jarvis-intake-field">
              <span>Mode</span>
              <select
                value={governanceMode || selectedAction.default_governance_mode}
                onChange={(event) => onGovernanceModeChange(event.target.value)}
              >
                {(selectedAction.governance_modes || []).map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="capability-bridge-field-grid">
            {(selectedAction.input_fields || []).map((field) => {
              const fieldValue = fieldValues[field.id];
              if (field.type === 'textarea') {
                return (
                  <label key={field.id} className="jarvis-intake-field capability-bridge-field capability-bridge-field--wide">
                    <span>{field.label}</span>
                    <textarea
                      rows="3"
                      value={fieldValue ?? ''}
                      placeholder={field.placeholder || ''}
                      onChange={(event) => onFieldValueChange(field.id, event.target.value)}
                    />
                  </label>
                );
              }
              if (field.type === 'select') {
                return (
                  <label key={field.id} className="jarvis-intake-field capability-bridge-field">
                    <span>{field.label}</span>
                    <select
                      value={fieldValue ?? field.default ?? ''}
                      onChange={(event) => onFieldValueChange(field.id, event.target.value)}
                    >
                      {(field.options || []).map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </label>
                );
              }
              if (field.type === 'boolean') {
                return (
                  <label key={field.id} className="capability-bridge-boolean">
                    <input
                      type="checkbox"
                      checked={Boolean(fieldValue)}
                      onChange={(event) => onFieldValueChange(field.id, event.target.checked)}
                    />
                    <span>{field.label}</span>
                  </label>
                );
              }
              return (
                <label key={field.id} className="jarvis-intake-field capability-bridge-field">
                  <span>{field.label}</span>
                  <input
                    type="text"
                    value={fieldValue ?? ''}
                    placeholder={field.placeholder || ''}
                    onChange={(event) => onFieldValueChange(field.id, event.target.value)}
                  />
                </label>
              );
            })}
          </div>

          <div className="capability-bridge-actions">
            <button
              type="button"
              className="jarvis-primary-button"
              onClick={onRun}
              disabled={executeBusy}
            >
              <FiPlay />
              {executeBusy ? 'Executing...' : 'Run Through Bridge'}
            </button>
            <button
              type="button"
              className="jarvis-secondary-button"
              onClick={onStagePrompt}
              disabled={executeBusy}
            >
              <FiBookmark />
              Stage In Chat
            </button>
          </div>

          <div className="capability-bridge-preview">
            <div className="capability-bridge-preview-head">
              <div>
                <span>Execution Preview</span>
                <strong>{executionPreview?.capability_label || selectedCapability.label}</strong>
              </div>
              {selectedHealth ? (
                <span className={`inline-meta-chip ${selectedHealth.status === 'degraded' ? 'warning' : 'success'}`}>
                  {selectedHealth.status}
                </span>
              ) : null}
            </div>
            <div className="capability-bridge-preview-grid">
              <div className="capability-bridge-preview-cell">
                <span>Module</span>
                <strong>{executionPreview?.module || selectedCapability.module}</strong>
              </div>
              <div className="capability-bridge-preview-cell">
                <span>Action</span>
                <strong>{executionPreview?.action_label || selectedAction.label}</strong>
              </div>
              <div className="capability-bridge-preview-cell">
                <span>Route</span>
                <strong>{executionPreview?.path || 'capability_service_bridge'}</strong>
              </div>
              <div className="capability-bridge-preview-cell">
                <span>Mode</span>
                <strong>{executionPreview?.governance_mode || governanceMode || selectedAction.default_governance_mode}</strong>
              </div>
              <div className="capability-bridge-preview-cell">
                <span>Provider</span>
                <strong>{executionPreview?.provider_mode_requested || providerMode || selectedAction.default_provider_mode}</strong>
              </div>
              <div className="capability-bridge-preview-cell">
                <span>Lane</span>
                <strong>{executionPreview?.service_lane || snapshot?.service_lane || 'service_tools'}</strong>
              </div>
            </div>
            <p>{executionPreview?.authority_note || 'Selection remains governed input only.'}</p>
          </div>

          {latestExecution?.tool_result ? (
            <div className="capability-bridge-result">
              <div className="capability-bridge-preview-head">
                <div>
                  <span>Latest Execution</span>
                  <strong>{latestExecution.tool_result.type.replace(/_/g, ' ')}</strong>
                </div>
                <span className={`inline-meta-chip ${latestExecution.tool_result.status === 'failed' ? 'warning' : 'success'}`}>
                  {latestExecution.tool_result.status || 'completed'}
                </span>
              </div>
              <ToolResultCard
                toolResult={latestExecution.tool_result}
                onOpenFile={onOpenFile}
                onSearchWorkspace={onSearchWorkspace}
                onAppendDraftContext={onAppendDraftContext}
                onRunAction={onRunAction}
                actionBusyId={actionBusyId}
              />
              {latestExecution.response_trace ? (
                <ResponseTraceCard responseTrace={latestExecution.response_trace} />
              ) : null}
              <UlTraceBlock
                ulTrace={latestExecution?.ul_trace}
                ulSubstrate={latestExecution?.ul_substrate}
                label="Capability UL Trace"
              />
            </div>
          ) : null}

          <div className="capability-bridge-events">
            <div className="capability-bridge-preview-head">
              <div>
                <span>Recent Events</span>
                <strong>{selectedCapability.label}</strong>
              </div>
            </div>
            {recentEvents.length === 0 ? (
              <p className="session-empty capability-bridge-empty">
                No recent bridge events for this capability yet.
              </p>
            ) : (
              recentEvents.map((event) => (
                <div key={`${event.sequence}-${event.trace_id || event.tool_type}`} className="capability-bridge-event">
                  <strong>{event.tool_label || event.tool_type}</strong>
                  <span>{event.ok ? 'ok' : event.error_type || 'failed'}</span>
                  <p>
                    {event.provider || 'unknown provider'}
                    {event.model ? ` · ${event.model}` : ''}
                    {event.requested_provider_mode ? ` · ${event.requested_provider_mode}` : ''}
                  </p>
                  <small>{formatRelativeTime(event.timestamp)}</small>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}

function MysticConsoleCard({
  prompt,
  onPromptChange,
  onRun,
  onStagePrompt,
  busy,
  latestToolResult,
  onOpenFile,
  onSearchWorkspace,
  onAppendDraftContext,
  onRunAction,
  actionBusyId,
}) {
  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiCpu />
        <h3>Mystic Deck</h3>
      </div>

      <div className="mystic-console">
        <div className="mystic-console-copy">
          <span>Mystic Interface</span>
          <strong>Run a symbolic reading without leaving Jarvis</strong>
          <p>
            Mystic runs as a direct Jarvis tool pass, then lands in the active session like any
            other assistant turn.
          </p>
        </div>

        <div className="mystic-preset-grid">
          {mysticPresets.map((preset) => (
            <button
              key={preset.id}
              type="button"
              className={`provider-chip mystic-preset-chip ${prompt.trim() === preset.prompt ? 'active' : ''}`}
              onClick={() => onPromptChange(preset.prompt)}
            >
              <strong>{preset.label}</strong>
              <span>{preset.prompt}</span>
            </button>
          ))}
        </div>

        <textarea
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
              event.preventDefault();
              onRun();
            }
          }}
          placeholder="What do you want Mystic to read?"
          rows="4"
        />

        <div className="mystic-console-actions">
          <button
            type="button"
            className="jarvis-primary-button"
            onClick={onRun}
            disabled={busy}
          >
            <FiCpu />
            {busy ? 'Reading...' : 'Run Mystic Reading'}
          </button>
          <button
            type="button"
            className="jarvis-secondary-button"
            onClick={onStagePrompt}
            disabled={!prompt.trim() || busy}
          >
            <FiArrowUpRight />
            Stage Prompt in Chat
          </button>
        </div>

        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip">Direct tool pass</span>
          <span className="inline-meta-chip">Session-native</span>
          <span className="inline-meta-chip">No provider hop</span>
        </div>

        {latestToolResult ? (
          <div className="mystic-latest-stack">
            <ToolResultCard
              toolResult={latestToolResult}
              onOpenFile={onOpenFile}
              onSearchWorkspace={onSearchWorkspace}
              onAppendDraftContext={onAppendDraftContext}
              onRunAction={onRunAction}
              actionBusyId={actionBusyId}
            />
            <UlTraceBlock
              ulTrace={latestToolResult?.ul_trace}
              ulSubstrate={latestToolResult?.ul_substrate}
              label="Mystic UL Trace"
            />
          </div>
        ) : (
          <p className="session-empty">
            No Mystic reading has been run in this session yet.
          </p>
        )}
      </div>
    </div>
  );
}

function V10CoreConsoleCard({
  prompt,
  onPromptChange,
  onRun,
  onStagePrompt,
  busy,
  latestToolResult,
  onOpenFile,
  onSearchWorkspace,
  onAppendDraftContext,
  onRunAction,
  actionBusyId,
}) {
  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiCpu />
        <h3>V10 Core</h3>
      </div>

      <div className="mystic-console v10-console">
        <div className="mystic-console-copy">
          <span>Structured Scene Core</span>
          <strong>Run the next-gen scene pass without leaving Jarvis</strong>
          <p>
            V10 Core builds a scene brief, runs the refinement stack, and lands a critic
            score in the active session like any other Jarvis direct tool turn.
          </p>
        </div>

        <div className="mystic-preset-grid">
          {v10Presets.map((preset) => (
            <button
              key={preset.id}
              type="button"
              className={`provider-chip mystic-preset-chip ${prompt.trim() === preset.prompt ? 'active' : ''}`}
              onClick={() => onPromptChange(preset.prompt)}
            >
              <strong>{preset.label}</strong>
              <span>{preset.prompt}</span>
            </button>
          ))}
        </div>

        <textarea
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
              event.preventDefault();
              onRun();
            }
          }}
          placeholder="What scene or beat should V10 Core run?"
          rows="4"
        />

        <div className="mystic-console-actions">
          <button
            type="button"
            className="jarvis-primary-button"
            onClick={onRun}
            disabled={busy}
          >
            <FiCpu />
            {busy ? 'Running...' : 'Run V10 Core'}
          </button>
          <button
            type="button"
            className="jarvis-secondary-button"
            onClick={onStagePrompt}
            disabled={!prompt.trim() || busy}
          >
            <FiArrowUpRight />
            Stage Prompt in Chat
          </button>
        </div>

        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip">Scene brief</span>
          <span className="inline-meta-chip">Critic score</span>
          <span className="inline-meta-chip">Session-native</span>
        </div>

        {latestToolResult ? (
          <div className="mystic-latest-stack">
            <ToolResultCard
              toolResult={latestToolResult}
              onOpenFile={onOpenFile}
              onSearchWorkspace={onSearchWorkspace}
              onAppendDraftContext={onAppendDraftContext}
              onRunAction={onRunAction}
              actionBusyId={actionBusyId}
            />
            <UlTraceBlock
              ulTrace={latestToolResult?.ul_trace}
              ulSubstrate={latestToolResult?.ul_substrate}
              label="V10 UL Trace"
            />
          </div>
        ) : (
          <p className="session-empty">
            No V10 Core pass has been run in this session yet.
          </p>
        )}
      </div>
    </div>
  );
}

function CreativeRuntimeCard({ label, runtime, formatRelativeTime }) {
  const recentEvents = runtime?.recent_events || [];
  const status = runtime?.status || 'idle';
  const tone = status === 'degraded' ? 'danger' : status === 'running' ? 'warning' : 'success';

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiCpu />
        <h3>{label}</h3>
      </div>

      <details className="jarvis-collapsible-panel">
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Installed creative runtime</span>
            <strong>{runtime?.last_summary || `${label} is ready for the next direct tool pass.`}</strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          <div className="jarvis-inline-meta">
            <span className={`inline-meta-chip ${tone}`}>{status}</span>
            <span className="inline-meta-chip">{runtime?.run_count || 0} runs</span>
            <span className="inline-meta-chip">{runtime?.failure_count || 0} failures</span>
            {runtime?.last_quality_score != null && (
              <span className="inline-meta-chip">score {runtime.last_quality_score}</span>
            )}
          </div>

          {(runtime?.last_provider || runtime?.last_model || runtime?.last_location) && (
            <div className="jarvis-inline-card">
              <div className="jarvis-inline-card-header">
                <span>Last Runtime State</span>
                <strong>{runtime?.last_location || 'Unknown location'}</strong>
              </div>
              <div className="jarvis-inline-meta">
                {runtime?.last_provider && <span className="inline-meta-chip">{runtime.last_provider}</span>}
                {runtime?.last_model && <span className="inline-meta-chip">{runtime.last_model}</span>}
                {runtime?.last_run_at && <span className="inline-meta-chip">{formatRelativeTime(runtime.last_run_at)}</span>}
              </div>
              {runtime?.last_pipeline?.length > 0 && (
                <div className="v8-guidance-list">
                  {runtime.last_pipeline.map((stage) => (
                    <span key={`${label}-${stage}`} className="v8-guidance-chip">{stage}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {recentEvents.length === 0 ? (
            <p className="session-empty">No runtime events recorded yet.</p>
          ) : (
            <div className="v8-event-list">
              {recentEvents.slice().reverse().map((event) => (
                <div key={event.id} className="v8-event-item">
                  <div className="v8-event-header">
                    <strong>{event.event_type}</strong>
                    <span>{event.timestamp ? formatRelativeTime(event.timestamp) : status}</span>
                  </div>
                  <p>{event.summary}</p>
                </div>
              ))}
            </div>
          )}

          <UlTraceBlock
            ulTrace={runtime?.ul_trace}
            ulSubstrate={runtime?.ul_substrate}
            label={`${label} UL Trace`}
          />
        </div>
      </details>
    </div>
  );
}

function AAISBlueprintCard({
  blueprint,
  protocolSession,
  protocolBusy,
  busy,
  onRefresh,
  onOpenFile,
}) {
  const metrics = blueprint?.metrics || {};
  const providers = blueprint?.providers || [];
  const guardrailState = protocolSession?.guardrail_state || null;
  const ulTrace = protocolSession?.ul_trace || null;
  const ulSubstrate = protocolSession?.ul_substrate || null;
  const doctrine = protocolSession?.doctrine || null;
  const guardrailEvaluation = protocolSession?.guardrail_evaluation
    || protocolSession?.canonical_guardrail_evaluation
    || null;
  const executionOutcome = guardrailEvaluation?.execution_outcome
    || protocolSession?.execution_outcome
    || protocolSession?.final_judgment
    || null;
  const doctrinePosture = guardrailEvaluation?.doctrine_posture
    || protocolSession?.doctrine_posture
    || protocolSession?.doctrine_summary
    || null;
  const activeDoctrineTags = guardrailEvaluation?.active_tags || protocolSession?.active_doctrine_tags || [];
  const overrideResult = guardrailEvaluation?.override_result || protocolSession?.override_result || null;
  const escalationResult = guardrailEvaluation?.escalation_result || protocolSession?.escalation_result || null;
  const reasoningPacket = protocolSession?.reasoning_packet || null;
  const reasoningRoute = reasoningPacket?.route || {};
  const reasoningActionState = reasoningPacket?.action_state || {};
  const reasoningRefs = Array.isArray(reasoningPacket?.workspace_refs) ? reasoningPacket.workspace_refs : [];
  const reasoningRisks = Array.isArray(reasoningPacket?.risks) ? reasoningPacket.risks : [];
  const verificationTargets = Array.isArray(reasoningPacket?.verification_targets)
    ? reasoningPacket.verification_targets
    : [];
  const metricCards = [
    {
      id: 'model',
      label: 'Model route',
      value: metrics.active_model_mode || metrics.requested_model_mode || 'unloaded',
    },
    {
      id: 'guard',
      label: 'Guard',
      value: metrics.system_guard_status || 'nominal',
    },
    {
      id: 'dreamspace',
      label: 'Dreamspace',
      value: metrics.dreamspace_status || 'stopped',
    },
    {
      id: 'providers',
      label: 'Providers',
      value: `${metrics.provider_enabled_count || 0}/${metrics.provider_count || 0}`,
    },
    {
      id: 'specialists',
      label: 'Specialists',
      value: `${metrics.specialist_count || 0}`,
    },
    {
      id: 'protocol',
      label: 'Protocol channels',
      value: `${metrics.protocol_channel_count || 0}`,
    },
  ];

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiCpu />
        <h3>AAIS Blueprint</h3>
        <button
          type="button"
          className="jarvis-inline-icon-button"
          onClick={onRefresh}
          disabled={busy}
          aria-label="Refresh AAIS blueprint"
        >
          <FiRefreshCw />
        </button>
      </div>

      {!blueprint ? (
        <p className="session-empty">Loading the live AAIS system map...</p>
      ) : (
        <div className="aais-blueprint-shell">
          <div className="aais-blueprint-summary">
            <strong>{blueprint.title}</strong>
            <p>{blueprint.summary}</p>
          </div>

          <div className="aais-blueprint-metrics">
            {metricCards.map((metric) => (
              <div key={metric.id} className="aais-blueprint-metric">
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </div>

          {providers.length > 0 ? (
            <details className="jarvis-collapsible-panel aais-blueprint-collapse">
              <summary className="jarvis-collapsible-summary">
                <div className="jarvis-collapsible-copy">
                  <span>Provider fabric</span>
                  <strong>{providers.length} route{providers.length === 1 ? '' : 's'} available</strong>
                </div>
              </summary>
              <div className="jarvis-collapsible-body">
                <div className="aais-blueprint-provider-list">
                  {providers.map((provider) => (
                    <div key={provider.id} className="aais-blueprint-provider">
                      <div className="aais-blueprint-provider-head">
                        <strong>{provider.label}</strong>
                        <span className={`aais-blueprint-badge ${provider.available ? 'success' : 'warning'}`}>
                          {provider.available ? 'Online' : 'Offline'}
                        </span>
                      </div>
                      <p>{provider.summary || 'Jarvis provider route.'}</p>
                      <div className="jarvis-inline-meta">
                        {provider.is_default ? <span className="inline-meta-chip success">default</span> : null}
                        {provider.kind ? <span className="inline-meta-chip">{provider.kind}</span> : null}
                        {provider.supports_stream ? <span className="inline-meta-chip">stream</span> : null}
                      </div>
                      {provider.model ? (
                        <span className="aais-blueprint-detail">
                          Model: {provider.model}
                        </span>
                      ) : null}
                      {provider.reason ? (
                        <span className="aais-blueprint-detail">
                          {provider.available ? 'Ready' : 'Why offline'}: {provider.reason}
                          {!provider.available && provider.activation_hint ? ` · ${provider.activation_hint}` : ''}
                        </span>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            </details>
          ) : null}

            {blueprint.principles?.length > 0 ? (
              <div className="aais-blueprint-principles">
                {blueprint.principles.map((principle) => (
                  <span key={principle} className="spiral-chip">{principle}</span>
                ))}
              </div>
            ) : null}

            <details className="jarvis-collapsible-panel aais-blueprint-collapse">
              <summary className="jarvis-collapsible-summary">
                <div className="jarvis-collapsible-copy">
                  <span>Reasoning & Guardrails</span>
                  <strong>
                    {executionOutcome?.summary
                      || guardrailState?.summary
                      || protocolSession?.reasoning_summary
                      || 'Inspect the active runtime judgment, doctrine posture, and bounded reasoning packet.'}
                  </strong>
                </div>
              </summary>
              <div className="jarvis-collapsible-body">
            <div className="aais-blueprint-guardrails">
              <div className="aais-blueprint-guardrail-head">
                <span>Modular Guardrails</span>
                {protocolBusy ? (
                  <span className="aais-blueprint-badge neutral">Refreshing</span>
                ) : executionOutcome ? (
                  <span className={`aais-blueprint-badge ${getGuardrailStatusTone(executionOutcome.status)}`}>
                    {getGuardrailStatusLabel(executionOutcome.status)}
                  </span>
                ) : guardrailState ? (
                  <span className={`aais-blueprint-badge ${getGuardrailStatusTone(guardrailState.status)}`}>
                    {getGuardrailStatusLabel(guardrailState.status)}
                  </span>
                ) : (
                  <span className="aais-blueprint-badge neutral">No session</span>
                )}
              </div>
              {guardrailState ? (
                <>
                  <strong>
                    {executionOutcome?.summary
                      || guardrailState.summary
                      || 'Jarvis is exposing the current modular guardrail contract.'}
                  </strong>
                  <div className="jarvis-inline-meta">
                    <span className={`inline-meta-chip ${getGuardrailStatusTone(executionOutcome?.status || guardrailState.status)}`}>
                      runtime: {getGuardrailStatusLabel(executionOutcome?.status || guardrailState.status)}
                    </span>
                    {doctrinePosture ? (
                      <span className={`inline-meta-chip ${getGuardrailStatusTone(doctrinePosture.status)}`}>
                        doctrine: {getGuardrailStatusLabel(doctrinePosture.status)}
                      </span>
                    ) : null}
                    {guardrailEvaluation?.id ? (
                      <span className="inline-meta-chip">
                        {guardrailEvaluation.id}
                      </span>
                    ) : null}
                    {guardrailEvaluation?.evaluated_at ? (
                      <span className="inline-meta-chip">
                        {formatRelativeTime(guardrailEvaluation.evaluated_at)}
                      </span>
                    ) : null}
                    {guardrailEvaluation?.source ? (
                      <span className="inline-meta-chip">
                        {String(guardrailEvaluation.source).replace(/_/g, ' ')}
                      </span>
                    ) : null}
                    <span className="inline-meta-chip">
                      {getResponseModeLabel(guardrailEvaluation?.pipeline_mode || protocolSession?.pipeline_mode || guardrailState.pipeline_mode)}
                    </span>
                    {guardrailEvaluation?.runtime_effect ? (
                      <span className="inline-meta-chip">
                        {String(guardrailEvaluation.runtime_effect).replace(/_/g, ' ')}
                      </span>
                    ) : null}
                    <span className={`inline-meta-chip ${guardrailState.preserve_core ? 'success' : 'warning'}`}>
                      {guardrailState.preserve_core ? 'core preserved' : 'core drift'}
                    </span>
                    <span className={`inline-meta-chip ${guardrailState.inspectable ? 'success' : 'warning'}`}>
                      {guardrailState.inspectable ? 'inspectable' : 'opaque'}
                    </span>
                    {guardrailState.adaptive_zone ? (
                      <span className={`inline-meta-chip ${guardrailState.adaptive_zone_allowed ? 'success' : 'warning'}`}>
                        zone: {String(guardrailState.adaptive_zone).replace(/_/g, ' ')}
                      </span>
                    ) : null}
                  </div>
                  <div className="aais-blueprint-guardrail-grid">
                    <div className="aais-blueprint-guardrail-block">
                      <span>Execution Outcome</span>
                      <strong>{executionOutcome?.summary || 'No canonical runtime outcome is available yet.'}</strong>
                      <div className="jarvis-inline-meta">
                        <span className={`inline-meta-chip ${getGuardrailStatusTone(executionOutcome?.status || guardrailState.status)}`}>
                          {getGuardrailStatusLabel(executionOutcome?.status || guardrailState.status)}
                        </span>
                        {guardrailEvaluation?.id ? (
                          <span className="inline-meta-chip">
                            {guardrailEvaluation.id}
                          </span>
                        ) : null}
                      </div>
                    </div>
                    <div className="aais-blueprint-guardrail-block">
                      <span>Doctrine Posture</span>
                      <strong>{doctrinePosture?.summary || 'No doctrine posture is available yet.'}</strong>
                      <div className="jarvis-inline-meta">
                        <span className={`inline-meta-chip ${getGuardrailStatusTone(doctrinePosture?.status || 'nominal')}`}>
                          {getGuardrailStatusLabel(doctrinePosture?.status || 'nominal')}
                        </span>
                        {guardrailEvaluation?.evaluation_version ? (
                          <span className="inline-meta-chip">
                            {guardrailEvaluation.evaluation_version}
                          </span>
                        ) : null}
                      </div>
                    </div>
                    <div className="aais-blueprint-guardrail-block">
                      <span>Effective Pipeline</span>
                      <div className="aais-blueprint-file-row">
                        {(guardrailState.effective_pipeline || []).map((moduleName) => (
                          <span key={`effective-${moduleName}`} className="spiral-chip">{moduleName}</span>
                        ))}
                      </div>
                    </div>
                    {guardrailState.requested_override ? (
                      <div className="aais-blueprint-guardrail-block">
                        <span>Requested Override</span>
                        <div className="aais-blueprint-file-row">
                          {(guardrailState.requested_pipeline || []).map((moduleName) => (
                            <span key={`requested-${moduleName}`} className="spiral-chip">{moduleName}</span>
                          ))}
                        </div>
                        {guardrailState.override_blocked ? (
                          <p>Jarvis rejected the override because it fell outside approved modular growth zones.</p>
                        ) : (
                          <p>Jarvis allowed this override inside an approved adaptive zone.</p>
                        )}
                      </div>
                    ) : null}
                    <div className="aais-blueprint-guardrail-block">
                      <span>Protected Zones</span>
                      <div className="aais-blueprint-file-row">
                        {(guardrailState.protected_zones || []).map((zone) => (
                          <span key={`protected-${zone}`} className="inline-meta-chip danger">
                            {String(zone).replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                    {ulTrace ? (
                      <div className="aais-blueprint-guardrail-block">
                        <span>AAIS-UL Trace</span>
                        <strong>
                          {ulTrace.count || 0} payload{ulTrace.count === 1 ? '' : 's'} adapted
                        </strong>
                        {ulSubstrate?.contract_version ? (
                          <div className="jarvis-inline-meta">
                            <span className="inline-meta-chip">
                              substrate {ulSubstrate.contract_version}
                            </span>
                            {ulSubstrate.primary ? (
                              <span className="inline-meta-chip success">primary</span>
                            ) : null}
                          </div>
                        ) : null}
                        <div className="aais-blueprint-file-row">
                          {(ulTrace.sections || []).map((section) => (
                            <span key={`ul-${section}`} className="spiral-chip">
                              {String(section).replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : null}
                    {doctrine ? (
                      <div className="aais-blueprint-guardrail-block">
                        <span>Doctrine Summary</span>
                        <strong>
                          {doctrinePosture?.summary
                            || (doctrine.preserve_core
                              ? 'UL doctrine is preserving the Jarvis core.'
                              : 'Doctrine detected a boundary or stability risk.')}
                        </strong>
                        <div className="jarvis-inline-meta">
                          <span className={`inline-meta-chip ${getGuardrailStatusTone(doctrinePosture?.status || (doctrine.preserve_core ? 'approved' : 'blocked'))}`}>
                            {getGuardrailStatusLabel(doctrinePosture?.status || (doctrine.preserve_core ? 'approved' : 'blocked'))}
                          </span>
                          <span
                            className={`inline-meta-chip ${
                              doctrine.angels_and_wards?.angel_passed ? 'success' : 'warning'
                            }`}
                          >
                            {doctrine.angels_and_wards?.angel_passed ? 'angels passed' : 'angel alert'}
                          </span>
                          <span
                            className={`inline-meta-chip ${
                              doctrine.six_wards?.passed ? 'success' : 'warning'
                            }`}
                          >
                            {doctrine.six_wards?.passed ? 'six wards passed' : 'six wards blocked'}
                          </span>
                        </div>
                        {activeDoctrineTags.length > 0 ? (
                          <div className="aais-blueprint-file-row">
                            {activeDoctrineTags.map((tag) => (
                              <span key={`tag-${tag}`} className="spiral-chip">{tag}</span>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                    {(overrideResult || escalationResult) ? (
                      <div className="aais-blueprint-guardrail-block">
                        <span>Override / Escalation</span>
                        <div className="jarvis-inline-meta">
                          {overrideResult ? (
                            <span className={`inline-meta-chip ${getGuardrailStatusTone(overrideResult.status)}`}>
                              override: {getGuardrailStatusLabel(overrideResult.status)}
                            </span>
                          ) : null}
                          {escalationResult ? (
                            <span className={`inline-meta-chip ${getGuardrailStatusTone(escalationResult.status)}`}>
                              escalation: {getGuardrailStatusLabel(escalationResult.status)}
                            </span>
                          ) : null}
                        </div>
                        {overrideResult?.summary ? <p>{overrideResult.summary}</p> : null}
                        {escalationResult?.status && escalationResult.status !== 'none' ? (
                          <p>{escalationResult.summary}</p>
                        ) : null}
                      </div>
                    ) : null}
                    {reasoningPacket ? (
                      <div className="aais-blueprint-guardrail-block aais-blueprint-reasoning-block">
                        <span>Reasoning Protocol</span>
                        <strong>
                          {protocolSession?.reasoning_summary
                            || reasoningPacket.summary
                            || 'Jarvis is exposing the bounded reasoning contract for this turn.'}
                        </strong>
                        <div className="jarvis-inline-meta">
                          {reasoningPacket.stage ? (
                            <span className="inline-meta-chip">
                              stage: {formatProtocolLabel(reasoningPacket.stage)}
                            </span>
                          ) : null}
                          {reasoningPacket.mode ? (
                            <span className="inline-meta-chip">
                              mode: {getResponseModeLabel(reasoningPacket.mode)}
                            </span>
                          ) : null}
                          {reasoningRoute.provider ? (
                            <span className="inline-meta-chip">
                              route: {getProviderLabel(reasoningRoute.provider, providers)}
                            </span>
                          ) : null}
                          {reasoningRoute.specialist_domain ? (
                            <span className="inline-meta-chip">
                              {formatProtocolLabel(reasoningRoute.specialist_domain)}
                              {reasoningRoute.specialist_focus
                                ? ` / ${String(reasoningRoute.specialist_focus).replace(/_/g, ' ')}`
                                : ''}
                            </span>
                          ) : null}
                          {reasoningActionState.stage ? (
                            <span className="inline-meta-chip">
                              action: {formatProtocolLabel(reasoningActionState.stage)}
                            </span>
                          ) : null}
                        </div>
                        <div className="aais-blueprint-reasoning-grid">
                          <div className="aais-blueprint-reasoning-section">
                            <span>Goal</span>
                            <strong>{reasoningPacket.goal || 'No explicit goal captured.'}</strong>
                            {reasoningRoute.provider_reason ? (
                              <p>Route reason: {formatProtocolLabel(reasoningRoute.provider_reason)}</p>
                            ) : null}
                          </div>
                          <div className="aais-blueprint-reasoning-section">
                            <span>Action State</span>
                            <strong>
                              {reasoningActionState.stage
                                ? formatProtocolLabel(reasoningActionState.stage)
                                : 'No active action lifecycle'}
                            </strong>
                            <div className="jarvis-inline-meta">
                              {reasoningActionState.approval_state ? (
                                <span className="inline-meta-chip">
                                  approval: {formatProtocolLabel(reasoningActionState.approval_state)}
                                </span>
                              ) : null}
                              {reasoningActionState.execution_state ? (
                                <span className="inline-meta-chip">
                                  execution: {formatProtocolLabel(reasoningActionState.execution_state)}
                                </span>
                              ) : null}
                              {reasoningActionState.action_id ? (
                                <span className="inline-meta-chip">{reasoningActionState.action_id}</span>
                              ) : null}
                            </div>
                          </div>
                          <div className="aais-blueprint-reasoning-section">
                            <span>Workspace Evidence</span>
                            {reasoningRefs.length > 0 ? (
                              <div className="aais-blueprint-file-row">
                                {reasoningRefs.map((ref, index) => {
                                  const key = `${ref.file_path || 'ref'}-${ref.symbol || index}`;
                                  const label = ref.symbol
                                    ? `${ref.file_path} · ${ref.symbol}`
                                    : ref.file_path;
                                  return (
                                    <button
                                      key={key}
                                      type="button"
                                      className="aais-blueprint-file-button"
                                      onClick={() => onOpenFile(ref.file_path)}
                                    >
                                      {label}
                                    </button>
                                  );
                                })}
                              </div>
                            ) : (
                              <p>No workspace evidence was attached to this turn yet.</p>
                            )}
                          </div>
                          <div className="aais-blueprint-reasoning-section">
                            <span>Verification Targets</span>
                            {verificationTargets.length > 0 ? (
                              <div className="aais-blueprint-note-list">
                                {verificationTargets.map((target, index) => {
                                  const key = `${target.target || target.kind || 'target'}-${index}`;
                                  const content = (
                                    <>
                                      <strong>{target.target}</strong>
                                      <p>{target.reason}</p>
                                    </>
                                  );
                                  return isProjectFileTarget(target.target) ? (
                                    <button
                                      key={key}
                                      type="button"
                                      className="aais-blueprint-note aais-blueprint-note-button"
                                      onClick={() => onOpenFile(target.target)}
                                    >
                                      {content}
                                    </button>
                                  ) : (
                                    <div key={key} className="aais-blueprint-note">
                                      {content}
                                    </div>
                                  );
                                })}
                              </div>
                            ) : (
                              <p>No verification targets were inferred for this turn.</p>
                            )}
                          </div>
                          <div className="aais-blueprint-reasoning-section aais-blueprint-reasoning-section-wide">
                            <span>Risk Posture</span>
                            {reasoningRisks.length > 0 ? (
                              <div className="aais-blueprint-note-list">
                                {reasoningRisks.map((risk, index) => (
                                  <div key={`${risk.message || 'risk'}-${index}`} className="aais-blueprint-note">
                                    <strong>{formatProtocolLabel(risk.level || 'note')}</strong>
                                    <p>{risk.message}</p>
                                    {risk.target && isProjectFileTarget(risk.target) ? (
                                      <button
                                        type="button"
                                        className="aais-blueprint-file-button secondary"
                                        onClick={() => onOpenFile(risk.target)}
                                      >
                                        {risk.target}
                                      </button>
                                    ) : null}
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p>No active risks were attached to this reasoning packet.</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : null}
                    <div className="aais-blueprint-guardrail-block">
                      <span>Approved Growth Zones</span>
                      <div className="aais-blueprint-file-row">
                        {(guardrailState.allowed_growth_zones || []).map((zone) => (
                          <span key={`growth-${zone}`} className="inline-meta-chip success">
                            {String(zone).replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <p className="aais-blueprint-detail">
                  Load or create a Jarvis session to inspect the active modular guardrail contract.
                </p>
              )}
            </div>
              </div>
            </details>

            <details className="jarvis-collapsible-panel aais-blueprint-collapse">
              <summary className="jarvis-collapsible-summary">
                <div className="jarvis-collapsible-copy">
                  <span>System Map</span>
                  <strong>{blueprint.subsystems?.length || 0} live subsystem{(blueprint.subsystems?.length || 0) === 1 ? '' : 's'}</strong>
                </div>
              </summary>
              <div className="jarvis-collapsible-body">
            <div className="aais-blueprint-list">
              {blueprint.subsystems?.map((subsystem) => (
                <div key={subsystem.id} className="aais-blueprint-section">
                <div className="aais-blueprint-head">
                  <strong>{subsystem.label}</strong>
                  <span className={`aais-blueprint-badge ${getBlueprintStatusTone(subsystem.status)}`}>
                    {getBlueprintStatusLabel(subsystem.status)}
                  </span>
                </div>
                <p>{subsystem.summary}</p>
                {subsystem.detail ? <span className="aais-blueprint-detail">{subsystem.detail}</span> : null}

                {subsystem.live_files?.length > 0 ? (
                  <div className="aais-blueprint-files">
                    <span>Live now</span>
                    <div className="aais-blueprint-file-row">
                      {subsystem.live_files.map((file) => (
                        <button
                          key={`${subsystem.id}-live-${file.path}`}
                          type="button"
                          className="aais-blueprint-file-button"
                          onClick={() => onOpenFile(file.path)}
                        >
                          {file.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}

                {subsystem.source_files?.length > 0 ? (
                  <div className="aais-blueprint-files">
                    <span>Built from</span>
                    <div className="aais-blueprint-file-row">
                      {subsystem.source_files.map((file) => (
                        <button
                          key={`${subsystem.id}-source-${file.path}`}
                          type="button"
                          className="aais-blueprint-file-button secondary"
                          onClick={() => onOpenFile(file.path)}
                        >
                          {file.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
              </div>
            </details>

          {blueprint.lineage?.length > 0 ? (
            <details className="jarvis-collapsible-panel aais-blueprint-collapse">
              <summary className="jarvis-collapsible-summary">
                <div className="jarvis-collapsible-copy">
                  <span>Lineage</span>
                  <strong>{blueprint.lineage.length} source thread{blueprint.lineage.length === 1 ? '' : 's'}</strong>
                </div>
              </summary>
              <div className="jarvis-collapsible-body">
                <div className="aais-blueprint-lineage-list">
                  {blueprint.lineage.map((entry) => (
                    <div key={entry.id} className="aais-blueprint-lineage-item">
                      <strong>{entry.label}</strong>
                      <p>{entry.summary}</p>
                      <div className="aais-blueprint-lineage-row">
                        {entry.sources?.map((file) => (
                          <button
                            key={`${entry.id}-source-${file.path}`}
                            type="button"
                            className="aais-blueprint-file-button secondary"
                            onClick={() => onOpenFile(file.path)}
                          >
                            {file.label}
                          </button>
                        ))}
                      </div>
                      <div className="aais-blueprint-lineage-row">
                        {entry.targets?.map((file) => (
                          <button
                            key={`${entry.id}-target-${file.path}`}
                            type="button"
                            className="aais-blueprint-file-button"
                            onClick={() => onOpenFile(file.path)}
                          >
                            {file.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </details>
          ) : null}
        </div>
      )}
    </div>
  );
}

function MissionBoardCard({
  missionBoard,
  titleDraft,
  objectiveDraft,
  nextStepDraft,
  busy,
  onCreatePreset,
  onApplyCriticSuggestion,
  onTitleChange,
  onObjectiveChange,
  onNextStepChange,
  onCreateMission,
  onRefresh,
  onFocusMission,
  onSetMissionStatus,
  onDeleteMission,
  onAppendDraftContext,
  onOpenFile,
}) {
  const counts = missionBoard?.counts || defaultMissionBoard.counts;
  const missions = missionBoard?.missions || [];
  const activeMission = missionBoard?.active_mission || null;
  const activeMissionCritic = activeMission?.critic || null;
  const activeMissionHistory = activeMission?.history || [];
  const recommendedNext = missionBoard?.recommended_next || null;
  const presets = missionBoard?.presets || [];

  const missionContextText = (mission) => [
    `Mission: ${mission.title}`,
    mission.objective ? `Objective: ${mission.objective}` : null,
    mission.next_step ? `Next step: ${mission.next_step}` : null,
    mission.blocker ? `Blocker: ${mission.blocker}` : null,
  ].filter(Boolean).join('\n');

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiBookmark />
        <h3>Mission Board</h3>
        <button
          type="button"
          className="jarvis-inline-icon-button"
          onClick={onRefresh}
          disabled={busy}
          aria-label="Refresh Mission Board"
        >
          <FiRefreshCw />
        </button>
      </div>

      <div className="mission-board-shell">
        <div className="mission-board-summary">
          <strong>{activeMission ? activeMission.title : 'No active mission yet'}</strong>
          <p>{missionBoard?.summary || defaultMissionBoard.summary}</p>
        </div>

        <div className="jarvis-inline-meta">
          <span className="inline-meta-chip success">{counts.active || 0} active</span>
          <span className="inline-meta-chip warning">{counts.queued || 0} queued</span>
          <span className="inline-meta-chip danger">{counts.blocked || 0} blocked</span>
          <span className="inline-meta-chip">{counts.done || 0} done</span>
        </div>

        {recommendedNext ? (
          <div className="mission-board-recommendation">
            <strong>Recommended next move</strong>
            <p>{recommendedNext.summary}</p>
            <button
              type="button"
              className="jarvis-secondary-button"
              onClick={() => onAppendDraftContext('Mission Board', recommendedNext.summary)}
            >
              <FiArrowUpRight />
              Use In Chat
            </button>
          </div>
        ) : null}

        {activeMissionCritic ? (
          <div className="mission-board-recommendation">
            <strong>Mission Critic</strong>
            <p>{activeMissionCritic.summary}</p>
            <div className="jarvis-inline-meta">
              <span className={`inline-meta-chip ${getMissionCriticTone(activeMissionCritic.status)}`}>
                {getMissionCriticLabel(activeMissionCritic.status)}
              </span>
              <span className="inline-meta-chip">score {Math.round((activeMissionCritic.score || 0) * 100)}%</span>
              {activeMissionCritic.suggested_mission_status ? (
                <span className="inline-meta-chip">
                  suggest {getMissionStatusLabel(activeMissionCritic.suggested_mission_status)}
                </span>
              ) : null}
            </div>
            {(activeMissionCritic.suggested_mission_status || activeMissionCritic.recommended_next) ? (
              <div className="mission-critic-actions">
                {activeMissionCritic.recommended_next ? (
                  <button
                    type="button"
                    className="jarvis-secondary-button"
                    onClick={() => onAppendDraftContext('Mission Critic', activeMissionCritic.recommended_next)}
                  >
                    <FiArrowUpRight />
                    Use Critic Next Step
                  </button>
                ) : null}
                <button
                  type="button"
                  className="jarvis-secondary-button"
                  onClick={() => onApplyCriticSuggestion(activeMission.id)}
                  disabled={busy}
                >
                  <FiCheckCircle />
                  Apply Critic Suggestion
                </button>
              </div>
            ) : null}
          </div>
        ) : null}

        {activeMissionHistory.length > 0 ? (
          <div className="mission-board-recommendation mission-replay-card">
            <strong>Mission Replay</strong>
            <p>
              Chronological chain for the active mission. This shows what happened first,
              so critic judgments read in context instead of as isolated scores.
            </p>
            <div className="mission-replay-list">
              {activeMissionHistory.slice(-8).map((entry) => (
                <div key={entry.id} className="mission-replay-item">
                  <div className="mission-replay-head">
                    <strong>{getMissionStatusLabel(entry.kind)}</strong>
                    <span>{formatRelativeTime(entry.timestamp)}</span>
                  </div>
                  <p>{entry.summary}</p>
                  <div className="jarvis-inline-meta">
                    {entry.source ? <span className="inline-meta-chip">{entry.source.replace(/_/g, ' ')}</span> : null}
                    {entry.status ? (
                      <span className={`inline-meta-chip ${getMissionReplayTone(entry.status)}`}>
                        {getMissionStatusLabel(entry.status)}
                      </span>
                    ) : null}
                    {entry.label ? <span className="inline-meta-chip">{entry.label}</span> : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {presets.length > 0 ? (
          <div className="mission-board-presets">
            <strong>Recipes</strong>
            <div className="mission-board-preset-grid">
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  className="mission-board-preset"
                  onClick={() => onCreatePreset(preset.id)}
                  disabled={busy}
                >
                  <strong>{preset.label}</strong>
                  <span>{preset.summary}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mission-board-compose">
          <input
            type="text"
            value={titleDraft}
            onChange={(event) => onTitleChange(event.target.value)}
            placeholder="Mission title"
          />
          <textarea
            value={objectiveDraft}
            onChange={(event) => onObjectiveChange(event.target.value)}
            placeholder="What should this mission accomplish?"
            rows="3"
          />
          <input
            type="text"
            value={nextStepDraft}
            onChange={(event) => onNextStepChange(event.target.value)}
            placeholder="Optional next step"
          />
          <button
            type="button"
            className="jarvis-primary-button"
            onClick={onCreateMission}
            disabled={busy}
          >
            <FiPlus />
            Create Mission
          </button>
        </div>

        <div className="mission-board-list">
          {missions.length === 0 ? (
            <p className="session-empty">No missions yet.</p>
          ) : (
            missions.map((mission) => (
              <div key={mission.id} className={`mission-item ${mission.focused ? 'focused' : ''}`}>
                <div className="mission-item-head">
                  <div>
                    <strong>{mission.title}</strong>
                    <p>{mission.objective || 'No objective written yet.'}</p>
                  </div>
                  <span className={`aais-blueprint-badge ${getMissionStatusTone(mission.status)}`}>
                    {getMissionStatusLabel(mission.status)}
                  </span>
                </div>

                <div className="jarvis-inline-meta">
                  {mission.focused ? <span className="inline-meta-chip success">focused</span> : null}
                  {mission.linked_to_active_session ? <span className="inline-meta-chip">this session</span> : null}
                  {mission.next_step ? <span className="inline-meta-chip">next step ready</span> : null}
                  {mission.status === 'blocked' ? <span className="inline-meta-chip danger">blocked</span> : null}
                </div>

                {mission.next_step ? (
                  <div className="mission-item-detail">
                    <span>Next step</span>
                    <p>{mission.next_step}</p>
                  </div>
                ) : null}

                {mission.status === 'blocked' && mission.blocker ? (
                  <div className="mission-item-detail blocked">
                    <span>Blocker</span>
                    <p>{mission.blocker}</p>
                  </div>
                ) : null}

                {mission.critic ? (
                  <div className="mission-item-detail">
                    <span>Mission critic</span>
                    <p>{mission.critic.summary}</p>
                    <div className="jarvis-inline-meta">
                      <span className={`inline-meta-chip ${getMissionCriticTone(mission.critic.status)}`}>
                        {getMissionCriticLabel(mission.critic.status)}
                      </span>
                      <span className="inline-meta-chip">score {Math.round((mission.critic.score || 0) * 100)}%</span>
                    </div>
                    {(mission.critic.suggested_mission_status || mission.critic.recommended_next) ? (
                      <button
                        type="button"
                        className="jarvis-secondary-button mission-critic-apply"
                        onClick={() => onApplyCriticSuggestion(mission.id)}
                        disabled={busy}
                      >
                        <FiCheckCircle />
                        Apply Critic Suggestion
                      </button>
                    ) : null}
                  </div>
                ) : null}

                {mission.links?.length > 0 ? (
                  <div className="mission-item-links">
                    <span>Linked artifacts</span>
                    <div className="mission-item-link-row">
                      {mission.links.map((link) => (
                        <button
                          key={`${mission.id}-${link.kind}-${link.value}`}
                          type="button"
                          className="aais-blueprint-file-button secondary"
                          onClick={() => {
                            if (link.kind === 'file') {
                              onOpenFile(link.value);
                              return;
                            }
                            onAppendDraftContext(
                              'Mission Artifact',
                              `${link.label}\n${link.kind}: ${link.value}`,
                            );
                          }}
                        >
                          {link.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}

                {mission.activity?.length > 0 ? (
                  <div className="mission-item-activity">
                    <span>Recent activity</span>
                    <div className="mission-item-activity-list">
                      {mission.activity.slice(0, 2).map((entry) => (
                        <div key={entry.id} className="mission-item-activity-entry">
                          <strong>{getMissionStatusLabel(entry.kind)}</strong>
                          <p>{entry.summary}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

                {mission.history?.length > 1 ? (
                  <div className="mission-item-activity mission-item-replay">
                    <span>Replay</span>
                    <div className="mission-replay-list compact">
                      {mission.history.slice(-4).map((entry) => (
                        <div key={`${mission.id}-${entry.id}`} className="mission-replay-item compact">
                          <div className="mission-replay-head">
                            <strong>{getMissionStatusLabel(entry.kind)}</strong>
                            <span>{formatRelativeTime(entry.timestamp)}</span>
                          </div>
                          <p>{entry.summary}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

                <div className="mission-item-actions">
                  <button
                    type="button"
                    className="jarvis-secondary-button"
                    onClick={() => onFocusMission(mission.id)}
                    disabled={busy}
                  >
                    <FiActivity />
                    Focus
                  </button>
                  <button
                    type="button"
                    className="jarvis-secondary-button"
                    onClick={() => onAppendDraftContext('Mission Board', missionContextText(mission))}
                  >
                    <FiArrowUpRight />
                    Use In Chat
                  </button>
                  <button
                    type="button"
                    className="jarvis-secondary-button"
                    onClick={() => onSetMissionStatus(mission.id, 'active')}
                    disabled={busy || mission.status === 'active'}
                  >
                    Active
                  </button>
                  <button
                    type="button"
                    className="jarvis-secondary-button"
                    onClick={() => onSetMissionStatus(mission.id, 'blocked')}
                    disabled={busy || mission.status === 'blocked'}
                  >
                    Block
                  </button>
                  <button
                    type="button"
                    className="jarvis-secondary-button"
                    onClick={() => onSetMissionStatus(mission.id, 'done')}
                    disabled={busy || mission.status === 'done'}
                  >
                    Done
                  </button>
                  <button
                    type="button"
                    className="jarvis-secondary-button"
                    onClick={() => onDeleteMission(mission.id)}
                    disabled={busy}
                  >
                    <FiTrash2 />
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function V8RuntimeCard({
  sessionRuntime,
  latestEvent,
  eventCount,
  onRefresh,
  eventsBusy,
  onAdoptRecommendedMode,
}) {
  const formatTraceLabel = (value) => String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
  const sessionState = sessionRuntime.sessionState || {};
  const policyStatus = sessionRuntime.policyStatus || {};
  const trace = sessionRuntime.responseTrace || {};
  const godBrain = sessionRuntime.godBrain || trace.god_brain || null;
  const modelRoute = sessionRuntime.modelRoute || trace.model_route || null;
  const modeGuidance = sessionRuntime.modeGuidance || {};
  const requestedMode = modeGuidance.requested_mode || sessionRuntime.requestedResponseMode || 'fast';
  const effectiveMode = modeGuidance.effective_mode || sessionRuntime.responseMode || requestedMode;
  const recommendedMode = modeGuidance.recommended_mode || effectiveMode;
  const showModeGuidance = Boolean(
    modeGuidance.status
      && (
        modeGuidance.status !== 'aligned'
        || requestedMode !== effectiveMode
        || recommendedMode !== requestedMode
      )
  );
  const postureClass = policyStatus.posture === 'degraded'
    ? 'danger'
    : policyStatus.posture === 'cautious'
      ? 'warning'
      : 'success';

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiShield />
        <h3>V8 Loop</h3>
      </div>

      <div className="v8-state-grid">
        <div className="v8-metric-card">
          <span>Session State</span>
          <strong>{sessionState.state || 'idle'}</strong>
          <p>{sessionState.summary || 'Session initialized.'}</p>
        </div>
        <div className="v8-metric-card">
          <span>Policy Posture</span>
          <strong>{policyStatus.posture || 'nominal'}</strong>
          <p>{policyStatus.summary || 'No policy checks have been triggered yet.'}</p>
        </div>
      </div>

      <div className="jarvis-inline-meta">
        <span className="inline-meta-chip">{trace.contract_label || trace.contract || 'direct answer'}</span>
        <span className={`inline-meta-chip ${postureClass}`}>{policyStatus.status || 'allow'}</span>
        <span className="inline-meta-chip">{eventCount} events</span>
      </div>

      {policyStatus.violations?.length > 0 && (
        <div className="v8-guidance-list danger">
          {policyStatus.violations.map((violation) => (
            <span key={violation} className="v8-guidance-chip">{violation}</span>
          ))}
        </div>
      )}

      <div className="v8-event-summary">
        <div>
          <span>Latest Event</span>
          <strong>{latestEvent?.event_type || sessionState.last_event_type || 'session_created'}</strong>
          <p>{latestEvent?.summary || sessionState.summary || 'Session initialized.'}</p>
        </div>
        <button
          type="button"
          className="compact-action-button"
          onClick={onRefresh}
          disabled={eventsBusy}
          aria-label="Refresh V8 event log"
        >
          <FiRefreshCw />
        </button>
      </div>

      <details className="jarvis-collapsible-panel">
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Inspect runtime reasoning</span>
            <strong>Mode guidance, sovereign planning, and route detail</strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          {policyStatus.guidance?.length > 0 && (
            <div className="v8-guidance-list">
              {policyStatus.guidance.map((guidance) => (
                <span key={guidance} className="v8-guidance-chip">{guidance}</span>
              ))}
            </div>
          )}

          {showModeGuidance && (
            <div className="jarvis-inline-card v8-mode-guidance-card">
              <div className="jarvis-inline-card-header">
                <span>Mode Guidance</span>
                <strong>{getResponseModeLabel(effectiveMode)}</strong>
              </div>
              <p>{modeGuidance.summary || 'Jarvis evaluated the best operating mode for this turn.'}</p>
              <div className="jarvis-inline-meta">
                <span className="inline-meta-chip">Requested: {getResponseModeLabel(requestedMode)}</span>
                <span className="inline-meta-chip">Effective: {getResponseModeLabel(effectiveMode)}</span>
                <span className={`inline-meta-chip ${modeGuidance.auto_applied ? 'warning' : ''}`}>
                  Confidence {Math.round((modeGuidance.confidence || 0) * 100)}%
                </span>
              </div>
              {modeGuidance.reason && (
                <p className="mode-guidance-reason">{modeGuidance.reason}</p>
              )}
              {modeGuidance.signals?.length > 0 && (
                <div className="v8-guidance-list">
                  {modeGuidance.signals.map((signal) => (
                    <span key={signal} className="v8-guidance-chip">{signal}</span>
                  ))}
                </div>
              )}
              {recommendedMode !== requestedMode && (
                <button
                  type="button"
                  className="inline-card-action"
                  onClick={() => onAdoptRecommendedMode(recommendedMode)}
                >
                  <FiCommand />
                  {modeGuidance.auto_applied
                    ? `Keep ${getResponseModeLabel(recommendedMode)} Mode`
                    : `Use ${getResponseModeLabel(recommendedMode)} Next`}
                </button>
              )}
            </div>
          )}

          {godBrain && (
            <div className="jarvis-inline-card god-brain-side-card">
              <div className="jarvis-inline-card-header">
                <span>God Brain</span>
                <strong>{godBrain.strategy_label || 'Sovereign Core'}</strong>
              </div>
              <p>{godBrain.strategy_summary || godBrain.summary || 'The sovereign core is shaping the turn.'}</p>
              <div className="jarvis-inline-meta">
                {godBrain.lead?.label ? (
                  <span className="inline-meta-chip">Lead: {godBrain.lead.label}</span>
                ) : null}
                {godBrain.action_bias_label ? (
                  <span className="inline-meta-chip">{godBrain.action_bias_label}</span>
                ) : null}
                {godBrain.arbiter?.confidence_label ? (
                  <span className="inline-meta-chip">{godBrain.arbiter.confidence_label}</span>
                ) : null}
              </div>
              {godBrain.council?.length > 0 && (
                <div className="v8-guidance-list">
                  {godBrain.council.map((member) => (
                    <span key={member.id || member.label} className="v8-guidance-chip">
                      {member.label}
                      {member.role ? ` · ${formatTraceLabel(member.role)}` : ''}
                    </span>
                  ))}
                </div>
              )}
              {godBrain.arbiter?.rule ? (
                <p className="god-brain-rule">{godBrain.arbiter.rule}</p>
              ) : null}
            </div>
          )}

          {modelRoute && (
            <div className="jarvis-inline-card model-route-side-card">
              <div className="jarvis-inline-card-header">
                <span>Model Route</span>
                <strong>{modelRoute.label || 'Local Route'}</strong>
              </div>
              <p>{modelRoute.summary || 'Jarvis selected a turn-specific local generation route.'}</p>
              <div className="jarvis-inline-meta">
                {modelRoute.reason ? (
                  <span className="inline-meta-chip">{formatTraceLabel(modelRoute.reason)}</span>
                ) : null}
                {modelRoute.adapter_mode ? (
                  <span className="inline-meta-chip">Adapter {formatTraceLabel(modelRoute.adapter_mode)}</span>
                ) : null}
              </div>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}

function V8EventFeed({ events, formatRelativeTime }) {
  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiActivity />
        <h3>Event Log</h3>
      </div>

      <details className="jarvis-collapsible-panel">
        <summary className="jarvis-collapsible-summary">
          <div className="jarvis-collapsible-copy">
            <span>Inspect event log</span>
            <strong>
              {events.length === 0
                ? 'No session events yet'
                : `${events.length} recent event${events.length === 1 ? '' : 's'}`}
            </strong>
          </div>
        </summary>
        <div className="jarvis-collapsible-body">
          {events.length === 0 ? (
            <p className="session-empty">No session events yet.</p>
          ) : (
            <div className="v8-event-list">
              {events.map((event) => (
                <div key={event.id} className="v8-event-item">
                  <div className="v8-event-header">
                    <strong>{event.event_type}</strong>
                    <span>{formatRelativeTime(event.timestamp)}</span>
                  </div>
                  <p>{event.summary}</p>
                  <div className="jarvis-inline-meta">
                    <span className="inline-meta-chip">{event.state}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </details>
    </div>
  );
}

function BrowserVerificationPanel({
  targetPath,
  expectation,
  suggestedExpectation,
  quickTargets,
  activeTargetKey,
  suiteBusy,
  suiteResults,
  verification,
  busy,
  onTargetPathChange,
  onExpectationChange,
  onUseSuggestedExpectation,
  onRunQuickTarget,
  onVerifyAll,
  onVerify,
  onOpenFile,
  onRunAction,
  onSearchWorkspace,
  onAppendDraftContext,
  actionBusyId,
}) {
  const strongestFile = verification?.workspace_context?.results?.[0] || null;
  const routeExpectation = verification?.route_expectation || null;
  const statusTone = verification?.status === 'fail'
    ? 'danger'
    : verification?.status === 'warning'
      ? 'warning'
      : 'success';
  const suiteCounts = (suiteResults || []).reduce((counts, result) => {
    counts[result.status] = (counts[result.status] || 0) + 1;
    return counts;
  }, { healthy: 0, warning: 0, fail: 0 });
  const suiteOverallStatus = suiteResults?.some((result) => result.status === 'fail')
    ? 'fail'
    : suiteResults?.some((result) => result.status === 'warning')
      ? 'warning'
      : suiteResults?.length
        ? 'healthy'
        : null;
  const suiteIssue = suiteResults?.find((result) => result.status !== 'healthy') || null;
  const suiteFocusKey = suiteIssue?.key || activeTargetKey || suiteResults?.[0]?.key || null;
  const suiteOverallTone = getBrowserSuiteTone(suiteOverallStatus);

  return (
    <div className="jarvis-side-card page-panel">
      <div className="jarvis-side-title">
        <FiMonitor />
        <h3>Browser Verify</h3>
      </div>

      <p className="session-empty">
        Load a live route in a hidden browser frame, inspect what actually rendered,
        and map it back to the strongest local code path. Known AAIS routes can use built-in
        expected UI states automatically.
      </p>

      {quickTargets?.length > 0 && (
        <div className="browser-suite-card">
          <div className="browser-suite-header">
            <div className="browser-suite-copy">
              <span>Core Route Sweep</span>
              <strong>Verify All Core Routes</strong>
              <p>
                Run the Jarvis Console, Image Analyzer, and Settings checks in sequence,
                then jump straight into the first route that needs attention.
              </p>
            </div>
            <button
              type="button"
              className="jarvis-secondary-button browser-suite-run"
              onClick={onVerifyAll}
              disabled={busy || suiteBusy}
            >
              <FiActivity />
              {suiteBusy ? 'Running Suite...' : suiteResults?.length ? 'Rerun Core Routes' : 'Verify All Core Routes'}
            </button>
          </div>

          {suiteResults?.length > 0 && (
            <>
              <div className="jarvis-inline-meta">
                <span className={`inline-meta-chip ${suiteOverallTone}`}>
                  {suiteOverallStatus === 'healthy'
                    ? 'all core routes aligned'
                    : suiteOverallStatus === 'warning'
                      ? 'core routes need review'
                      : 'core route failure'}
                </span>
                <span className="inline-meta-chip">{suiteCounts.healthy} pass</span>
                {suiteCounts.warning > 0 && (
                  <span className="inline-meta-chip warning">{suiteCounts.warning} warn</span>
                )}
                {suiteCounts.fail > 0 && (
                  <span className="inline-meta-chip danger">{suiteCounts.fail} fail</span>
                )}
              </div>

              <p className="browser-suite-note">
                {suiteIssue
                  ? `First route to review: ${suiteIssue.label}. ${suiteIssue.summary}`
                  : 'All saved core checks matched their expected UI state on the last sweep.'}
              </p>

              <div className="browser-suite-list">
                {suiteResults.map((result) => {
                  const isFocused = suiteFocusKey === result.key;
                  const resultTone = getBrowserSuiteTone(result.status);
                  return (
                    <div
                      key={result.key}
                      className={`browser-suite-item ${result.status} ${isFocused ? 'active' : ''}`}
                    >
                      <div className="browser-suite-main">
                        <div className="browser-suite-heading">
                          <span>{result.label}</span>
                          <strong>{result.path}</strong>
                        </div>
                        <p>{result.summary}</p>
                        <div className="jarvis-inline-meta">
                          <span className={`inline-meta-chip ${resultTone}`}>{result.statusLabel}</span>
                          {result.routeFit && (
                            <span className="inline-meta-chip">UI fit · {result.routeFit}</span>
                          )}
                          {result.topMatch?.relative_path && (
                            <span className="inline-meta-chip">{result.topMatch.relative_path}</span>
                          )}
                        </div>
                      </div>

                      <div className="browser-suite-actions">
                        <button
                          type="button"
                          className="inline-card-action browser-target-run"
                          onClick={() => onRunQuickTarget(result)}
                          disabled={busy || suiteBusy}
                        >
                          <FiRefreshCw />
                          {busy && isFocused ? 'Running...' : 'Rerun'}
                        </button>

                        {result.suggestedAction && (
                          <button
                            type="button"
                            className="inline-card-action"
                            onClick={() => onRunAction(result.suggestedAction)}
                            disabled={actionBusyId === result.suggestedAction.id}
                          >
                            <FiCommand />
                            {actionBusyId === result.suggestedAction.id ? 'Running...' : result.suggestedAction.label}
                          </button>
                        )}

                        {result.topMatch?.relative_path && (
                          <button
                            type="button"
                            className="inline-card-action"
                            onClick={() => onOpenFile(result.topMatch.relative_path)}
                          >
                            <FiFolder />
                            Open File
                          </button>
                        )}

                        {result.workspaceQuery && (
                          <button
                            type="button"
                            className="inline-card-action"
                            onClick={() => onSearchWorkspace(result.workspaceQuery)}
                          >
                            <FiSearch />
                            Review Matches
                          </button>
                        )}

                        {result.draftContext && (
                          <button
                            type="button"
                            className="inline-card-action"
                            onClick={() => onAppendDraftContext('Browser verification context:', result.draftContext)}
                          >
                            <FiArrowUpRight />
                            Use in Chat
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      )}

      {quickTargets?.length > 0 && (
        <div className="browser-verify-targets">
          {quickTargets.map((target) => {
            const isActive = activeTargetKey === target.key;
            return (
              <div
                key={target.key}
                className={`browser-target-card ${isActive ? 'active' : ''}`}
              >
                <div className="browser-target-copy">
                  <span>{target.label}</span>
                  <strong>{target.path}</strong>
                  <p>{target.summary}</p>
                </div>
                <button
                  type="button"
                  className="inline-card-action browser-target-run"
                  onClick={() => onRunQuickTarget(target)}
                  disabled={busy || suiteBusy}
                >
                  <FiRefreshCw />
                  {suiteBusy
                    ? 'Queued'
                    : busy && isActive
                      ? 'Running...'
                      : isActive
                        ? 'Rerun'
                        : 'Run Check'}
                </button>
              </div>
            );
          })}
        </div>
      )}

      <div className="browser-verify-form">
        <label>
          Route path or local URL
          <input
            type="text"
            value={targetPath}
            onChange={(event) => onTargetPathChange(event.target.value)}
            placeholder="/image-analyzer or http://localhost:3000/"
          />
        </label>

        {suggestedExpectation && (
          <div className="browser-verify-card browser-verify-guide">
            <span>Auto Expectation</span>
            <strong>{suggestedExpectation.label}</strong>
            <p>{suggestedExpectation.expectation}</p>
            <div className="browser-verify-chip-list">
              {suggestedExpectation.expectedHeadings.map((heading) => (
                <span key={`heading-${heading}`} className="workspace-context-chip">{heading}</span>
              ))}
              {suggestedExpectation.expectedButtons.map((buttonLabel) => (
                <span key={`button-${buttonLabel}`} className="workspace-context-chip">{buttonLabel}</span>
              ))}
            </div>
            <button
              type="button"
              className="inline-card-action"
              onClick={onUseSuggestedExpectation}
            >
              <FiArrowUpRight />
              Copy to Manual Override
            </button>
          </div>
        )}

        <label>
          {suggestedExpectation ? 'Manual override' : 'Expected outcome'}
          <textarea
            value={expectation}
            onChange={(event) => onExpectationChange(event.target.value)}
            placeholder={suggestedExpectation?.expectation || 'What should this route show or do when it is healthy?'}
            rows="3"
          />
        </label>
        {suggestedExpectation && (
          <p className="browser-verify-note">
            Leave the manual override blank and Jarvis will use the built-in route expectation automatically.
          </p>
        )}

        <button
          type="button"
          className="jarvis-secondary-button browser-verify-button"
          onClick={onVerify}
          disabled={busy || suiteBusy}
        >
          <FiMonitor />
          {suiteBusy ? 'Suite Running...' : busy ? 'Verifying...' : 'Verify Route'}
        </button>
      </div>

      {verification && (
        <div className="browser-verify-result">
          <div className="jarvis-inline-card">
            <div className="jarvis-inline-card-header">
              <span>Browser Route</span>
              <strong>{verification.target_path || targetPath || '/'}</strong>
            </div>
            <p>{verification.summary}</p>
            <div className="jarvis-inline-meta">
              <span className={`inline-meta-chip ${statusTone}`}>{verification.status}</span>
              <span className="inline-meta-chip">{verification.capture_mode || 'iframe'}</span>
              {verification.page_title ? (
                <span className="inline-meta-chip">{verification.page_title}</span>
              ) : null}
            </div>
            {verification.expectation_fit?.status && verification.expectation_fit.status !== 'not_provided' && (
              <div className="jarvis-inline-meta">
                <span className="inline-meta-chip">
                  Expectation {verification.expectation_source === 'manual' ? 'manual' : 'auto'} · {verification.expectation_fit.status}
                </span>
                <span className="inline-meta-chip">
                  {Math.round((verification.expectation_fit.confidence || 0) * 100)}%
                </span>
              </div>
            )}
            {verification.debug_signals?.length > 0 && (
              <div className="v8-guidance-list">
                {verification.debug_signals.map((signal) => (
                  <span key={signal} className="v8-guidance-chip">{signal}</span>
                ))}
              </div>
            )}
          </div>

          {(verification.page?.headings?.length > 0
            || verification.page?.alerts?.length > 0
            || verification.page?.buttons?.length > 0) && (
            <div className="browser-verify-grid">
              {verification.page?.headings?.length > 0 && (
                <div className="browser-verify-card">
                  <span>Headings</span>
                  <div className="browser-verify-chip-list">
                    {verification.page.headings.map((heading) => (
                      <span key={heading} className="workspace-context-chip">{heading}</span>
                    ))}
                  </div>
                </div>
              )}

              {verification.page?.alerts?.length > 0 && (
                <div className="browser-verify-card warning">
                  <span>Alerts</span>
                  <div className="browser-verify-alert-list">
                    {verification.page.alerts.map((alert) => (
                      <p key={alert}>{alert}</p>
                    ))}
                  </div>
                </div>
              )}

              {verification.page?.buttons?.length > 0 && (
                <div className="browser-verify-card">
                  <span>Buttons</span>
                  <div className="browser-verify-chip-list">
                    {verification.page.buttons.slice(0, 6).map((buttonLabel) => (
                      <span key={buttonLabel} className="workspace-context-chip">{buttonLabel}</span>
                    ))}
                  </div>
                </div>
              )}

              {routeExpectation?.source && routeExpectation.source !== 'none' && (
                <div className="browser-verify-card">
                  <span>Expected UI</span>
                  <strong>{routeExpectation.route_label || 'Expected route state'}</strong>
                  <div className="jarvis-inline-meta">
                    <span className="inline-meta-chip">
                      {routeExpectation.source === 'manual' ? 'manual override' : 'built-in guide'}
                    </span>
                    {routeExpectation.fit?.status && routeExpectation.fit.status !== 'not_available' && (
                      <span className="inline-meta-chip">
                        {routeExpectation.fit.status} · {Math.round((routeExpectation.fit.confidence || 0) * 100)}%
                      </span>
                    )}
                  </div>
                  {(routeExpectation.expected_headings?.length > 0 || routeExpectation.expected_buttons?.length > 0) && (
                    <div className="browser-verify-chip-list">
                      {(routeExpectation.expected_headings || []).map((heading) => (
                        <span key={`expected-heading-${heading}`} className="workspace-context-chip">{heading}</span>
                      ))}
                      {(routeExpectation.expected_buttons || []).map((buttonLabel) => (
                        <span key={`expected-button-${buttonLabel}`} className="workspace-context-chip">{buttonLabel}</span>
                      ))}
                    </div>
                  )}
                  {routeExpectation.fit?.matched_headings?.length > 0 && (
                    <p className="browser-verify-match-copy">
                      Matched headings: {routeExpectation.fit.matched_headings.join(', ')}
                    </p>
                  )}
                  {routeExpectation.fit?.matched_buttons?.length > 0 && (
                    <p className="browser-verify-match-copy">
                      Matched controls: {routeExpectation.fit.matched_buttons.join(', ')}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="jarvis-inline-actions">
            {verification.suggested_action && (
              <button
                type="button"
                className="inline-card-action"
                onClick={() => onRunAction(verification.suggested_action)}
                disabled={actionBusyId === verification.suggested_action.id}
              >
                <FiCommand />
                {actionBusyId === verification.suggested_action.id
                  ? 'Running...'
                  : verification.suggested_action.label}
              </button>
            )}

            {strongestFile && (
              <button
                type="button"
                className="inline-card-action"
                onClick={() => onOpenFile(strongestFile.relative_path)}
              >
                <FiFolder />
                Open Strongest File
              </button>
            )}

            {verification.workspace_query && (
              <button
                type="button"
                className="inline-card-action"
                onClick={() => onSearchWorkspace(verification.workspace_query)}
              >
                <FiSearch />
                Review Matches
              </button>
            )}

            {verification.draft_context && (
              <button
                type="button"
                className="inline-card-action"
                onClick={() => onAppendDraftContext('Browser verification context:', verification.draft_context)}
              >
                <FiArrowUpRight />
                Use in Chat
              </button>
            )}
          </div>

          {verification.workspace_context?.results?.length > 0 && (
            <div className="browser-verify-card">
              <span>Matched Files</span>
              <div className="browser-verify-hit-list">
                {verification.workspace_context.results.map((result) => (
                  <button
                    key={`${result.relative_path}-${result.kind}`}
                    type="button"
                    className="workspace-result-main browser-verify-hit"
                    onClick={() => onOpenFile(result.relative_path)}
                  >
                    <strong>{result.relative_path}</strong>
                    <span>{result.snippet}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {verification.next_steps?.length > 0 && (
            <div className="browser-verify-card">
              <span>Next Steps</span>
              <div className="trace-step-list">
                {verification.next_steps.map((step) => (
                  <span key={step} className="trace-step">{step}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConversationMessage({
  message,
  profile,
  onOpenFile,
  onOpenSource,
  onSearchWorkspace,
  onAppendDraftContext,
  onRunAction,
  actionBusyId,
}) {
  const label = message.role === 'assistant' ? profile.assistantName : profile.operatorName;
  const content = message.content || (message.streaming ? 'Thinking through it...' : '');

  return (
    <article className={`jarvis-message ${message.role} ${message.streaming ? 'streaming' : ''}`}>
      <div className="message-role">{label}</div>
      <div className="message-bubble">
        {message.role === 'assistant' && (
          <>
            <ResponseTraceCard responseTrace={message.responseTrace} />
            <ContextCards
              workspaceContext={message.workspaceContext}
              liveResearch={message.liveResearch}
              persistentMemories={message.persistentMemories}
              onOpenFile={onOpenFile}
              onOpenSource={onOpenSource}
              onSearchWorkspace={onSearchWorkspace}
              onAppendDraftContext={onAppendDraftContext}
            />
            <ToolResultCard
              toolResult={message.toolResult}
              onOpenFile={onOpenFile}
              onSearchWorkspace={onSearchWorkspace}
              onAppendDraftContext={onAppendDraftContext}
              onRunAction={onRunAction}
              actionBusyId={actionBusyId}
            />
          </>
        )}
        {content ? <p>{content}</p> : null}
      </div>
    </article>
  );
}

function JarvisConsole() {
  const [profile, setProfile] = useState(() => getJarvisProfile());
  const [sessionId, setSessionId] = useState('');
  const [recentSessions, setRecentSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [conversationLane, setConversationLane] = useState('chat');
  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [fileIntakeBusy, setFileIntakeBusy] = useState(false);
  const [textIntakeBusy, setTextIntakeBusy] = useState(false);
  const [urlIntakeBusy, setUrlIntakeBusy] = useState(false);
  const [textIntakeDraft, setTextIntakeDraft] = useState('');
  const [urlIntakeDraft, setUrlIntakeDraft] = useState('');
  const [memories, setMemories] = useState([]);
  const [memoryDraft, setMemoryDraft] = useState('');
  const [savingMemory, setSavingMemory] = useState(false);
  const [workspaceProjects, setWorkspaceProjects] = useState([]);
  const [workspaceQuery, setWorkspaceQuery] = useState('');
  const [workspaceResults, setWorkspaceResults] = useState([]);
  const [workspaceBusy, setWorkspaceBusy] = useState(false);
  const [filePreview, setFilePreview] = useState(null);
  const [availableSpecialistDomains, setAvailableSpecialistDomains] = useState([]);
  const [availableSpecialistPresets, setAvailableSpecialistPresets] = useState([]);
  const [selectedSpecialists, setSelectedSpecialists] = useState([]);
  const [selectedSpecialistPreset, setSelectedSpecialistPreset] = useState(null);
  const [browserTargetPath, setBrowserTargetPath] = useState(() => (
    window.location.pathname.toLowerCase().includes('jarvis') ? '/' : (window.location.pathname || '/')
  ));
  const [browserExpectation, setBrowserExpectation] = useState('');
  const [browserVerification, setBrowserVerification] = useState(null);
  const [browserBusy, setBrowserBusy] = useState(false);
  const [browserSuiteBusy, setBrowserSuiteBusy] = useState(false);
  const [browserSuiteResults, setBrowserSuiteResults] = useState([]);
  const [availableActions, setAvailableActions] = useState([]);
  const [actionBusyId, setActionBusyId] = useState('');
  const [patchReviews, setPatchReviews] = useState([]);
  const [patchPreview, setPatchPreview] = useState(null);
  const [patchPreviewBusy, setPatchPreviewBusy] = useState(false);
  const [attachedWorkspaceContext, setAttachedWorkspaceContext] = useState(null);
  const [attachedLiveResearch, setAttachedLiveResearch] = useState(null);
  const [sessionEvents, setSessionEvents] = useState([]);
  const [eventsBusy, setEventsBusy] = useState(false);
  const [booting, setBooting] = useState(true);
  const [sending, setSending] = useState(false);
  const [listening, setListening] = useState(false);
  const [guardBusy, setGuardBusy] = useState(false);
  const [dreamspaceBusy, setDreamspaceBusy] = useState(false);
  const [health, setHealth] = useState({
    status: 'checking',
    active_model_mode: null,
    ai_status: 'not_initialized',
    request_latency_ms: null,
    timestamp: null,
  });
  const [systemGuard, setSystemGuard] = useState(defaultSystemGuard);
  const [corrigibility, setCorrigibility] = useState(defaultCorrigibility);
  const [dreamspace, setDreamspace] = useState(defaultDreamspace);
  const [dreamspacePresentation, setDreamspacePresentation] = useState('');
  const [missionBoard, setMissionBoard] = useState(defaultMissionBoard);
  const [missionTitleDraft, setMissionTitleDraft] = useState('');
  const [missionObjectiveDraft, setMissionObjectiveDraft] = useState('');
  const [missionNextStepDraft, setMissionNextStepDraft] = useState('');
  const [missionBusy, setMissionBusy] = useState(false);
  const [blueprint, setBlueprint] = useState(null);
  const [blueprintBusy, setBlueprintBusy] = useState(false);
  const [protocolSession, setProtocolSession] = useState(null);
  const [protocolBusy, setProtocolBusy] = useState(false);
  const [sessionRuntime, setSessionRuntime] = useState(() => mapSessionRuntime());
  const [composeReceipt, setComposeReceipt] = useState(null);
  const [deepComposeEnabled, setDeepComposeEnabled] = useState(
    () => window.localStorage.getItem(DEEP_COMPOSE_STORAGE_KEY) === 'true',
  );
  const [activeComposeTab, setActiveComposeTab] = useState('mode');
  const [activeSideTab, setActiveSideTab] = useState('conversation');
  const [mysticPrompt, setMysticPrompt] = useState('my current state and the next move I need to make');
  const [v10Prompt, setV10Prompt] = useState('continue the next scene beat and score whether the draft is strong enough to keep');
  const [capabilityBridgeSnapshot, setCapabilityBridgeSnapshot] = useState(DEFAULT_CAPABILITY_BRIDGE_SNAPSHOT);
  const [capabilityBridgeBusy, setCapabilityBridgeBusy] = useState(false);
  const [capabilityBridgeLoadError, setCapabilityBridgeLoadError] = useState('');
  const [capabilityExecuteBusy, setCapabilityExecuteBusy] = useState(false);
  const [selectedCapabilityId, setSelectedCapabilityId] = useState('');
  const [selectedCapabilityActionId, setSelectedCapabilityActionId] = useState('');
  const [selectedCapabilityProviderMode, setSelectedCapabilityProviderMode] = useState('');
  const [selectedCapabilityGovernanceMode, setSelectedCapabilityGovernanceMode] = useState('');
  const [capabilityFieldValues, setCapabilityFieldValues] = useState({});
  const [latestCapabilityExecution, setLatestCapabilityExecution] = useState(null);
  const [evolveTaskDraft, setEvolveTaskDraft] = useState(
    'Improve this candidate until it scores cleanly without leaving the bounded lane.',
  );
  const [evolvePreset, setEvolvePreset] = useState('prompt_polish');
  const [evolveSeedDraft, setEvolveSeedDraft] = useState('');
  const [evolveCriteriaDraft, setEvolveCriteriaDraft] = useState('task alignment, clarity, bounded improvement');
  const [evolvePopulationDraft, setEvolvePopulationDraft] = useState('4');
  const [evolveGenerationsDraft, setEvolveGenerationsDraft] = useState('3');
  const [evolveBusy, setEvolveBusy] = useState(false);
  const [evolveRefreshBusy, setEvolveRefreshBusy] = useState(false);
  const [evolveHandoffBusy, setEvolveHandoffBusy] = useState(false);
  const [evolveSnapshot, setEvolveSnapshot] = useState(null);
  const [evolveJobTrace, setEvolveJobTrace] = useState(null);
  const [evolveJobEvaluations, setEvolveJobEvaluations] = useState([]);
  const [evolveHallOfFame, setEvolveHallOfFame] = useState([]);
  const [evolveHallOfShame, setEvolveHallOfShame] = useState([]);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const streamAbortRef = useRef(null);
  const fileIntakeRef = useRef(null);
  const selectedSpecialistsRef = useRef([]);
  const selectedSpecialistPresetRef = useRef(null);

  const voiceSupported = useMemo(() => {
    return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  }, []);

  const browserExpectationGuide = useMemo(
    () => getBrowserExpectationGuide(browserTargetPath),
    [browserTargetPath],
  );
  const quickBrowserTargets = useMemo(
    () => listBrowserVerificationTargets(),
    [],
  );
  const specialistCatalog = useMemo(
    () => flattenSpecialistCatalog(availableSpecialistDomains),
    [availableSpecialistDomains],
  );
  const selectedSpecialistObjects = useMemo(
    () => selectedSpecialists
      .map((specialistId) => specialistCatalog.find((specialist) => specialist.id === specialistId))
      .filter(Boolean),
    [selectedSpecialists, specialistCatalog],
  );
  const selectedSpecialistPresetObject = useMemo(
    () => availableSpecialistPresets.find((preset) => preset.id === selectedSpecialistPreset) || null,
    [availableSpecialistPresets, selectedSpecialistPreset],
  );
  const latestMysticToolResult = useMemo(
    () => [...messages]
      .reverse()
      .find((message) => message?.toolResult?.type === 'mystic_reading')
      ?.toolResult || null,
    [messages],
  );
  const latestV10ToolResult = useMemo(
    () => [...messages]
      .reverse()
      .find((message) => message?.toolResult?.type === 'v10_core')
      ?.toolResult || null,
    [messages],
  );
  const availableCapabilityDecks = useMemo(
    () => capabilityBridgeSnapshot?.available_capabilities || [],
    [capabilityBridgeSnapshot],
  );
  const selectedCapabilityDeck = useMemo(
    () => availableCapabilityDecks.find((capability) => capability.id === selectedCapabilityId)
      || availableCapabilityDecks[0]
      || null,
    [availableCapabilityDecks, selectedCapabilityId],
  );
  const selectedCapabilityAction = useMemo(
    () => selectedCapabilityDeck?.actions?.find((action) => action.id === selectedCapabilityActionId)
      || selectedCapabilityDeck?.actions?.[0]
      || null,
    [selectedCapabilityActionId, selectedCapabilityDeck],
  );
  const latestEvolveJobId = useMemo(
    () => evolveSnapshot?.job_id
      || sessionRuntime?.evolveLastJob?.job_id
      || '',
    [evolveSnapshot?.job_id, sessionRuntime],
  );
  const activeBrowserTargetKey = browserVerification?.route_expectation?.route_key
    || browserExpectationGuide?.key
    || null;

  const refreshSessions = useCallback(async () => {
    try {
      const response = await apiGet('/api/chat/sessions');
      const sessions = [...(response.data.sessions || [])].sort((left, right) => {
        return new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime();
      });
      setRecentSessions(sessions);
    } catch (error) {
      setRecentSessions([]);
    }
  }, []);

  const refreshMemories = useCallback(async () => {
    try {
      const response = await apiGet('/api/jarvis/memory', {
        params: { limit: 4, active: true, sort: 'priority' },
      });
      setMemories(response.data.memories || []);
    } catch (error) {
      setMemories([]);
    }
  }, []);

  const refreshDocuments = useCallback(async () => {
    setDocumentsLoading(true);
    try {
      const response = await apiGet('/api/documents');
      setDocuments([...(response.data.documents || [])].reverse());
    } catch (error) {
      setDocuments([]);
    } finally {
      setDocumentsLoading(false);
    }
  }, []);

  const refreshWorkspaceProjects = useCallback(async () => {
    try {
      const response = await apiGet('/api/jarvis/workspace/projects', {
        params: { limit: 8 },
      });
      setWorkspaceProjects(response.data.projects || []);
    } catch (error) {
      setWorkspaceProjects([]);
    }
  }, []);

  const refreshActions = useCallback(async () => {
    try {
      const response = await apiGet('/api/jarvis/actions');
      setAvailableActions(response.data.actions || []);
    } catch (error) {
      setAvailableActions([]);
    }
  }, []);

  const refreshCapabilityBridge = useCallback(async () => {
    setCapabilityBridgeBusy(true);
    setCapabilityBridgeLoadError('');
    try {
      const response = await apiGet('/api/jarvis/capability-bridge');
      setCapabilityBridgeSnapshot(normalizeCapabilityBridgeSnapshot(response.data));
    } catch (error) {
      setCapabilityBridgeSnapshot(DEFAULT_CAPABILITY_BRIDGE_SNAPSHOT);
      setCapabilityBridgeLoadError(
        getApiErrorMessage(error, 'Capability bridge registry unavailable.'),
      );
    } finally {
      setCapabilityBridgeBusy(false);
    }
  }, []);

  const refreshPatchReviews = useCallback(async (targetSessionId) => {
    const activeSessionId = targetSessionId || sessionId;
    try {
      const response = await apiGet('/api/jarvis/patch/reviews', {
        params: activeSessionId ? { session_id: activeSessionId, limit: 6 } : { limit: 6 },
      });
      setPatchReviews(response.data.reviews || []);
    } catch (error) {
      setPatchReviews([]);
    }
  }, [sessionId]);

  const refreshSpecialists = useCallback(async () => {
    try {
      const response = await apiGet('/api/jarvis/specialists');
      setAvailableSpecialistDomains(response.data.domains || []);
      setAvailableSpecialistPresets(response.data.presets || []);
    } catch (error) {
      setAvailableSpecialistDomains([]);
      setAvailableSpecialistPresets([]);
    }
  }, []);

  const refreshSessionEvents = useCallback(async (targetSessionId) => {
    const activeSessionId = targetSessionId || sessionId;
    if (!activeSessionId) {
      setSessionEvents([]);
      return;
    }

    setEventsBusy(true);
    try {
      const response = await apiGet(`/api/chat/sessions/${activeSessionId}/events`, {
        params: { limit: 24 },
      });
      startTransition(() => {
        setSessionEvents([...(response.data.events || [])].reverse());
      });
    } catch (error) {
      setSessionEvents([]);
    } finally {
      setEventsBusy(false);
    }
  }, [sessionId]);

  const applySystemGuard = useCallback((payload) => {
    const nextGuard = payload?.system_guard || payload;
    if (!nextGuard || typeof nextGuard !== 'object' || !Object.prototype.hasOwnProperty.call(nextGuard, 'status')) {
      return;
    }
    setSystemGuard({
      ...defaultSystemGuard,
      ...nextGuard,
      recent_events: nextGuard.recent_events || [],
    });
  }, []);

  const applyCorrigibility = useCallback((payload) => {
    const nextCorrigibility = payload?.corrigibility || payload?.tool_result?.corrigibility;
    if (!nextCorrigibility || typeof nextCorrigibility !== 'object') {
      return;
    }
    setCorrigibility({
      ...defaultCorrigibility,
      ...nextCorrigibility,
      pending: nextCorrigibility.pending || null,
      recent: nextCorrigibility.recent || [],
    });
  }, []);

  const applyDreamspace = useCallback((payload) => {
    const nextDreamspace = payload?.dreamspace || payload;
    if (nextDreamspace && typeof nextDreamspace === 'object' && Object.prototype.hasOwnProperty.call(nextDreamspace, 'status')) {
      setDreamspace({
        ...defaultDreamspace,
        ...nextDreamspace,
        recent_dreams: nextDreamspace.recent_dreams || [],
      });
    }
    if (typeof payload?.presentation === 'string') {
      setDreamspacePresentation(payload.presentation);
    }
  }, []);

  const refreshHealth = useCallback(async () => {
    const startedAt = typeof window.performance?.now === 'function'
      ? window.performance.now()
      : Date.now();
    try {
      const response = await apiGet('/health');
      const completedAt = typeof window.performance?.now === 'function'
        ? window.performance.now()
        : Date.now();
      setHealth({
        ...response.data,
        request_latency_ms: Math.max(0, Math.round(completedAt - startedAt)),
        timestamp: Date.now(),
      });
      applySystemGuard(response.data);
      applyDreamspace(response.data);
    } catch (error) {
      const completedAt = typeof window.performance?.now === 'function'
        ? window.performance.now()
        : Date.now();
      setHealth({
        status: 'offline',
        active_model_mode: null,
        ai_status: 'unreachable',
        request_latency_ms: Math.max(0, Math.round(completedAt - startedAt)),
        timestamp: Date.now(),
      });
      setDreamspace(defaultDreamspace);
    }
  }, [applyDreamspace, applySystemGuard]);

  const refreshSystemGuard = useCallback(async () => {
    try {
      const response = await apiGet('/api/system/guard');
      applySystemGuard(response.data);
      applyDreamspace(response.data);
      setHealth((current) => ({
        ...current,
        requested_model_mode: response.data.requested_model_mode,
        active_model_mode: response.data.active_model_mode,
        ai_status: response.data.ai_status,
      }));
    } catch (error) {
      // Keep the current view if the guard endpoint is temporarily unavailable.
    }
  }, [applyDreamspace, applySystemGuard]);

  const refreshDreamspace = useCallback(async () => {
    try {
      const response = await apiGet('/api/system/dreamspace');
      applySystemGuard(response.data);
      applyDreamspace(response.data);
      setHealth((current) => ({
        ...current,
        requested_model_mode: response.data.requested_model_mode,
        active_model_mode: response.data.active_model_mode,
        ai_status: response.data.ai_status,
      }));
    } catch (error) {
      // Keep the current view if the Dreamspace endpoint is temporarily unavailable.
    }
  }, [applyDreamspace, applySystemGuard]);

  const refreshMissionBoard = useCallback(async (targetSessionId) => {
    try {
      const activeSessionId = targetSessionId || sessionId;
      const response = await apiGet('/api/jarvis/missions', {
        params: activeSessionId ? { session_id: activeSessionId } : undefined,
      });
      setMissionBoard({
        ...defaultMissionBoard,
        ...(response.data.mission_board || {}),
      });
    } catch (error) {
      setMissionBoard(defaultMissionBoard);
    }
  }, [sessionId]);

  const refreshBlueprint = useCallback(async () => {
    setBlueprintBusy(true);
    try {
      const response = await apiGet('/api/jarvis/blueprint');
      setBlueprint(response.data.blueprint || null);
    } catch (error) {
      setBlueprint(null);
    } finally {
      setBlueprintBusy(false);
    }
  }, []);

  const refreshProtocol = useCallback(async (targetSessionId) => {
    const activeSessionId = targetSessionId || sessionId;
    if (!activeSessionId) {
      setProtocolSession(null);
      return;
    }

    setProtocolBusy(true);
    try {
      const response = await apiGet('/api/jarvis/protocol', {
        params: { session_id: activeSessionId },
      });
      setProtocolSession(response.data.session || null);
    } catch (error) {
      setProtocolSession(null);
    } finally {
      setProtocolBusy(false);
    }
  }, [sessionId]);

  const refreshEvolveDeck = useCallback(async (targetJobId) => {
    setEvolveRefreshBusy(true);
    try {
      const [hallOfFameResponse, hallOfShameResponse] = await Promise.all([
        apiGet('/api/jarvis/evolve/hall-of-fame', { params: { limit: 6 } }),
        apiGet('/api/jarvis/evolve/hall-of-shame', { params: { limit: 6 } }),
      ]);

      startTransition(() => {
        setEvolveHallOfFame(hallOfFameResponse.data.entries || []);
        setEvolveHallOfShame(hallOfShameResponse.data.entries || []);
      });

      const activeJobId = targetJobId || latestEvolveJobId;
      if (!activeJobId) {
        setEvolveJobTrace(null);
        setEvolveJobEvaluations([]);
        return;
      }

      const [traceResponse, evaluationsResponse] = await Promise.all([
        apiGet(`/api/jarvis/evolve/jobs/${activeJobId}`),
        apiGet(`/api/jarvis/evolve/jobs/${activeJobId}/evaluations`, { params: { limit: 24 } }),
      ]);

      startTransition(() => {
        setEvolveJobTrace(traceResponse.data || null);
        setEvolveJobEvaluations(evaluationsResponse.data.evaluations || []);
      });
    } catch (error) {
      if (!targetJobId && !latestEvolveJobId) {
        setEvolveJobTrace(null);
        setEvolveJobEvaluations([]);
      }
    } finally {
      setEvolveRefreshBusy(false);
    }
  }, [latestEvolveJobId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  useEffect(() => {
    refreshHealth().catch(() => {});
  }, [refreshHealth]);

  useEffect(() => {
    refreshSessions();
    refreshMemories();
    refreshDocuments();
    refreshWorkspaceProjects();
    refreshActions();
    refreshCapabilityBridge();
    refreshPatchReviews();
    refreshSpecialists();
    refreshSystemGuard();
    refreshDreamspace();
    refreshBlueprint();
  }, [
    refreshActions,
    refreshBlueprint,
    refreshCapabilityBridge,
    refreshDocuments,
    refreshDreamspace,
    refreshEvolveDeck,
    refreshMemories,
    refreshPatchReviews,
    refreshSessions,
    refreshSpecialists,
    refreshSystemGuard,
    refreshWorkspaceProjects,
  ]);

  useEffect(() => {
    refreshEvolveDeck(latestEvolveJobId || undefined);
  }, [latestEvolveJobId, refreshEvolveDeck]);

  useEffect(() => {
    refreshSessionEvents(sessionId);
  }, [refreshSessionEvents, sessionId]);

  useEffect(() => {
    refreshPatchReviews(sessionId);
  }, [messages.length, refreshPatchReviews, sessionId]);

  useEffect(() => {
    if (!sessionId) {
      setProtocolSession(null);
      return;
    }

    if (sending) {
      return;
    }

    refreshProtocol(sessionId);
  }, [messages.length, refreshProtocol, sending, sessionId]);

  useEffect(() => {
    refreshMissionBoard(sessionId);
  }, [refreshMissionBoard, sessionId]);

  useEffect(() => {
    selectedSpecialistsRef.current = selectedSpecialists;
  }, [selectedSpecialists]);

  useEffect(() => {
    selectedSpecialistPresetRef.current = selectedSpecialistPreset;
  }, [selectedSpecialistPreset]);

  useEffect(() => {
    if (!availableCapabilityDecks.length) {
      setSelectedCapabilityId('');
      return;
    }
    if (!availableCapabilityDecks.some((capability) => capability.id === selectedCapabilityId)) {
      setSelectedCapabilityId(availableCapabilityDecks[0].id);
    }
  }, [availableCapabilityDecks, selectedCapabilityId]);

  useEffect(() => {
    if (!selectedCapabilityDeck) {
      setSelectedCapabilityActionId('');
      return;
    }
    if (!selectedCapabilityDeck.actions?.some((action) => action.id === selectedCapabilityActionId)) {
      setSelectedCapabilityActionId(
        selectedCapabilityDeck.default_action || selectedCapabilityDeck.actions?.[0]?.id || '',
      );
    }
  }, [selectedCapabilityActionId, selectedCapabilityDeck]);

  useEffect(() => {
    if (!selectedCapabilityAction) {
      setSelectedCapabilityProviderMode('');
      setSelectedCapabilityGovernanceMode('');
      setCapabilityFieldValues({});
      return;
    }
    setSelectedCapabilityProviderMode((current) => (
      selectedCapabilityAction.provider_modes?.includes(current)
        ? current
        : (selectedCapabilityAction.default_provider_mode || selectedCapabilityAction.provider_modes?.[0] || '')
    ));
    setSelectedCapabilityGovernanceMode((current) => (
      selectedCapabilityAction.governance_modes?.includes(current)
        ? current
        : (selectedCapabilityAction.default_governance_mode || selectedCapabilityAction.governance_modes?.[0] || '')
    ));
    setCapabilityFieldValues((current) => buildCapabilityFieldState(
      selectedCapabilityAction.input_fields,
      current,
    ));
  }, [selectedCapabilityAction]);

  const applySessionRuntime = useCallback((payload) => {
    setSessionRuntime(mapSessionRuntime(payload));
    const nextReceipt = normalizeComposeReceipt(payload);
    if (nextReceipt) {
      setComposeReceipt(nextReceipt);
    }
    applySystemGuard(payload);
    applyCorrigibility(payload);
    applyDreamspace(payload);
    if (payload?.mission_board) {
      setMissionBoard({
        ...defaultMissionBoard,
        ...payload.mission_board,
      });
    }
    if (payload?.evolve_last_job) {
      setEvolveSnapshot({
        job_id: payload.evolve_last_job.job_id,
        task: payload.evolve_last_job.task,
        result: payload.evolve_last_job.result,
      });
    }
    if (Array.isArray(payload?.requested_specialists)) {
      setSelectedSpecialists(payload.requested_specialists);
    }
    if (Object.prototype.hasOwnProperty.call(payload || {}, 'requested_specialist_preset')) {
      setSelectedSpecialistPreset(payload?.requested_specialist_preset || null);
    }
    if (
      payload?.persona_mode
      || payload?.requested_response_mode
      || payload?.response_mode
      || payload?.preferred_provider
    ) {
      setProfile((current) => applyRuntimeProfileSelection(current, payload));
    }
  }, [applyCorrigibility, applyDreamspace, applySystemGuard]);

  const applyWorkspaceContext = useCallback((payload) => {
    setAttachedWorkspaceContext(payload?.workspace_context || null);
    setAttachedLiveResearch(payload?.live_research || null);
  }, []);

  const applyBrowserVerification = useCallback((payload) => {
    setBrowserVerification(payload?.browser_verification || null);
  }, []);

  const toggleDeepCompose = useCallback(() => {
    setDeepComposeEnabled((current) => {
      const next = !current;
      window.localStorage.setItem(DEEP_COMPOSE_STORAGE_KEY, next ? 'true' : 'false');
      return next;
    });
  }, []);

  const buildStreamComposeFlags = useCallback((responseMode) => {
    const deepModes = new Set(['think', 'research', 'debug']);
    const usesDeepCompose = deepComposeEnabled || deepModes.has(responseMode);
    const usesThinkSpeaking = responseMode === 'think';
    return {
      cognitive_runtime: usesDeepCompose,
      compose_full: deepComposeEnabled && !deepModes.has(responseMode),
      operator_speaking_wrap: usesThinkSpeaking,
      speaking_runtime: usesThinkSpeaking,
    };
  }, [deepComposeEnabled]);

  const patchMessage = useCallback((messageId, updates) => {
    startTransition(() => {
      setMessages((current) => current.map((message) => {
        if (message.id !== messageId) {
          return message;
        }

        const nextUpdates = typeof updates === 'function' ? updates(message) : updates;
        return {
          ...message,
          ...nextUpdates,
        };
      }));
    });
  }, []);

  const pushSessionEvent = useCallback((eventRecord) => {
    if (!eventRecord?.id) {
      return;
    }

    startTransition(() => {
      setSessionEvents((current) => [
        eventRecord,
        ...current.filter((entry) => entry.id !== eventRecord.id),
      ].slice(0, 24));
    });
  }, []);

  const appendDraftContext = useCallback((label, content) => {
    const cleanedContent = String(content || '').trim();
    if (!cleanedContent) {
      return;
    }

    setDraft((current) => {
      const prefix = current.trim() ? `${current.trim()}\n\n` : '';
      return `${prefix}${label}\n${cleanedContent}`.trim();
    });
  }, []);

  const handleRunEvolveJob = useCallback(async () => {
    const cleanedTask = String(evolveTaskDraft || '').trim();
    if (!cleanedTask) {
      toast.error('Add an evolve task first.');
      return;
    }

    const criteria = String(evolveCriteriaDraft || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

    setEvolveBusy(true);
    try {
      const response = await apiPost('/api/jarvis/evolve/run', {
        session_id: sessionId || undefined,
        preset: evolvePreset,
        task: cleanedTask,
        config: {
          seed_candidates: String(evolveSeedDraft || '').trim()
            ? [String(evolveSeedDraft || '').trim()]
            : [],
        },
        evaluation: {
          mode: 'forge_eval',
          forge_eval_mode: 'llm_rubric',
          candidate_field: 'program',
          payload: {
            config: {
              criteria: criteria.length > 0
                ? criteria
                : ['task alignment', 'clarity', 'bounded improvement'],
            },
          },
        },
        constraints: {
          population_size: Math.max(1, Number(evolvePopulationDraft) || 4),
          max_generations: Math.max(1, Number(evolveGenerationsDraft) || 3),
        },
      });

      startTransition(() => {
        setEvolveSnapshot(response.data || null);
      });

      if (sessionId) {
        refreshProtocol(sessionId).catch(() => {});
      }
      await refreshEvolveDeck(response.data?.job_id);
      toast.success('EvolveEngine finished a bounded run.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not run EvolveEngine.'));
    } finally {
      setEvolveBusy(false);
    }
  }, [
    evolveCriteriaDraft,
    evolveGenerationsDraft,
    evolvePopulationDraft,
    evolvePreset,
    evolveSeedDraft,
    evolveTaskDraft,
    refreshEvolveDeck,
    refreshProtocol,
    sessionId,
  ]);

  const handleEvolveForgeHandoff = useCallback(async () => {
    const activeJobId = latestEvolveJobId;
    if (!activeJobId) {
      toast.error('Run an evolve job first so there is a winner to review.');
      return;
    }

    setEvolveHandoffBusy(true);
    try {
      const response = await apiPost(`/api/jarvis/evolve/jobs/${activeJobId}/handoff/forge`, {
        session_id: sessionId || undefined,
        kind: 'analyze',
      });
      const forge = response.data?.forge || null;
      const analysis = forge?.result?.result?.analysis || null;
      const forgeSummary = forge?.operator_safe_analysis_summary || analysis?.summary || '';
      if (forgeSummary) {
        appendDraftContext('Forge review of evolve winner:', forgeSummary);
      }
      if (sessionId) {
        refreshProtocol(sessionId).catch(() => {});
      }
      toast.success('Sent the evolve winner to Forge for review.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not hand the evolve winner to Forge.'));
    } finally {
      setEvolveHandoffBusy(false);
    }
  }, [appendDraftContext, latestEvolveJobId, refreshProtocol, sessionId]);

  const toggleSpecialist = useCallback((specialistId) => {
    setSelectedSpecialists((current) => {
      if (current.includes(specialistId)) {
        return current.filter((candidate) => candidate !== specialistId);
      }
      if (current.length >= SPECIALIST_SELECTION_LIMIT) {
        toast.error(`You can pin up to ${SPECIALIST_SELECTION_LIMIT} specialists at once.`);
        return current;
      }
      return [...current, specialistId];
    });
  }, []);

  const clearSelectedSpecialists = useCallback(() => {
    setSelectedSpecialists([]);
  }, []);

  const applySpecialistPreset = useCallback((preset) => {
    if (!preset) {
      setSelectedSpecialistPreset(null);
      return;
    }
    setSelectedSpecialistPreset(preset.id);
    setSelectedSpecialists((preset.specialists || []).map((specialist) => specialist.id));
    if (preset.preferred_mode) {
      setProfile((current) => applyResponseModeProfileSelection(current, preset.preferred_mode));
    }
  }, []);

  const clearSpecialistPreset = useCallback(() => {
    setSelectedSpecialistPreset(null);
  }, []);

  const pinPreferredProvider = useCallback((providerId) => {
    setProfile((current) => ({
      ...current,
      preferredProvider: providerId,
      providerPreferencePinned: providerId !== 'auto',
    }));
  }, []);

  const openExternalUrl = useCallback((url) => {
    if (!url) {
      return;
    }
    window.open(url, '_blank', 'noopener,noreferrer');
  }, []);

  const speakReply = (text) => {
    if (!profile.voiceOutputEnabled || !window.speechSynthesis) {
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 0.9;
    window.speechSynthesis.speak(utterance);
  };

  const createFreshSession = useCallback(async (nextProfile, activeFlag = true) => {
    const effectiveProfile = nextProfile || getJarvisProfile();
    const response = await apiPost('/api/chat/sessions', {
      system_prompt: effectiveProfile.systemPrompt,
      persona_mode: effectiveProfile.personaMode,
      response_mode: effectiveProfile.responseMode,
      provider: effectiveProfile.providerPreferencePinned ? effectiveProfile.preferredProvider : undefined,
      provider_mode: effectiveProfile.providerPreferencePinned ? undefined : 'auto_best',
      requested_specialists: selectedSpecialistsRef.current,
      requested_specialist_preset: selectedSpecialistPresetRef.current,
    });

    if (!activeFlag) {
      return response.data.session_id;
    }

    setActiveJarvisSessionId(response.data.session_id);
    setSessionId(response.data.session_id);
    setMessages([]);
    applySessionRuntime(response.data);
    applyWorkspaceContext(response.data);
    applyBrowserVerification(response.data);
    refreshSessionEvents(response.data.session_id);
    setBooting(false);
    refreshSessions();
    return response.data.session_id;
  }, [applyBrowserVerification, applySessionRuntime, applyWorkspaceContext, refreshSessionEvents, refreshSessions]);

  useEffect(() => {
    let active = true;

    const bootstrap = async () => {
      setBooting(true);
      const storedSessionId = getActiveJarvisSessionId();

      if (storedSessionId) {
        try {
          const response = await apiGet(`/api/chat/sessions/${storedSessionId}`);
          if (!active) {
            return;
          }

          setSessionId(storedSessionId);
          setMessages(mapSessionTurns(response.data.turns));
          applySessionRuntime(response.data);
          applyWorkspaceContext(response.data);
          applyBrowserVerification(response.data);
          refreshSessionEvents(storedSessionId);
          refreshSessions();
          setBooting(false);
          return;
        } catch (error) {
          clearActiveJarvisSessionId();
        }
      }

      try {
        await createFreshSession(getJarvisProfile(), active);
      } catch (error) {
        if (active) {
          toast.error(`Unable to start Jarvis: ${getApiErrorMessage(error)}`);
          setBooting(false);
        }
      }
    };

    bootstrap();

    return () => {
      active = false;
      recognitionRef.current?.abort?.();
      recognitionRef.current = null;
      streamAbortRef.current?.abort?.();
      streamAbortRef.current = null;
      window.speechSynthesis?.cancel?.();
    };
  }, [applyBrowserVerification, applySessionRuntime, applyWorkspaceContext, createFreshSession, refreshSessionEvents, refreshSessions]);

  useEffect(() => {
    if (booting) {
      return;
    }

    const pendingDraft = consumePendingJarvisDraft();
    if (!pendingDraft?.text) {
      return;
    }

    setDraft((current) => {
      const existing = String(current || '').trim();
      return existing ? `${existing}\n\n${pendingDraft.text}` : pendingDraft.text;
    });
    toast.success('Screenshot context loaded into Jarvis.');
  }, [booting]);

  const ensureSession = useCallback(async () => {
    if (sessionId) {
      return sessionId;
    }
    return createFreshSession(profile);
  }, [createFreshSession, profile, sessionId]);

  const handleFileIntake = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setFileIntakeBusy(true);
    try {
      const normalizedName = slugifyDocumentId(file.name);
      const isPdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name);
      const isText = file.type.startsWith('text/') || /\.(md|txt)$/i.test(file.name);

      if (isPdf) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('doc_id', normalizedName);
        formData.append('role', 'input_artifact');
        formData.append('operator_context', 'Jarvis console intake');
        formData.append('metadata', JSON.stringify({ source: file.name }));
        await apiPost('/api/documents/upload/pdf', formData);
      } else if (isText) {
        const text = await file.text();
        await apiPost('/api/documents/upload/text', {
          text,
          doc_id: normalizedName,
          role: 'input_artifact',
          operator_context: 'Jarvis console intake',
          metadata: { source: file.name },
        });
      } else {
        throw new Error('Upload a PDF, TXT, or MD file for Jarvis intake.');
      }

      setConversationLane('documents');
      await refreshDocuments();
      toast.success(`${file.name} added to Jarvis intake.`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Jarvis intake failed.'));
    } finally {
      event.target.value = '';
      setFileIntakeBusy(false);
    }
  };

  const handleTextIntake = async () => {
    const text = textIntakeDraft.trim();
    if (!text) {
      toast.error('Paste text before sending it to Jarvis intake.');
      return;
    }

    setTextIntakeBusy(true);
    try {
      await apiPost('/api/documents/upload/text', {
        text,
        doc_id: slugifyDocumentId(`jarvis_note_${Date.now()}`),
        role: 'input_artifact',
        operator_context: 'Jarvis pasted intake',
        metadata: { source: 'Jarvis pasted note' },
      });
      setTextIntakeDraft('');
      setConversationLane('documents');
      await refreshDocuments();
      toast.success('Pasted note added to Jarvis intake.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Jarvis text intake failed.'));
    } finally {
      setTextIntakeBusy(false);
    }
  };

  const handleUrlIntake = async () => {
    const url = urlIntakeDraft.trim();
    if (!url) {
      toast.error('Add a URL before sending it to Jarvis intake.');
      return;
    }

    setUrlIntakeBusy(true);
    try {
      await apiPost('/api/documents/upload/url', {
        url,
        doc_id: slugifyDocumentId(url),
        role: 'input_artifact',
        operator_context: 'Jarvis URL intake',
        metadata: { source: url },
      });
      setUrlIntakeDraft('');
      setConversationLane('documents');
      await refreshDocuments();
      toast.success('URL added to Jarvis intake.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Jarvis URL intake failed.'));
    } finally {
      setUrlIntakeBusy(false);
    }
  };

  const handleSend = async (nextMessage) => {
    const text = (nextMessage ?? draft).trim();
    if (!text || sending || booting) {
      return;
    }

    if (conversationLane === 'documents' && documents.length === 0) {
      toast.error('Add a document to Jarvis intake before asking that lane.');
      return;
    }

    const userTurn = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setDraft('');
    setSending(true);
    const assistantTurnId = `assistant-${Date.now()}-stream`;
    setMessages((current) => [
      ...current,
      userTurn,
      {
        id: assistantTurnId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        streaming: true,
        persistentMemories: [],
        workspaceContext: null,
        liveResearch: null,
        responseTrace: null,
        toolResult: null,
      },
    ]);

    try {
      if (conversationLane === 'documents') {
        const response = await apiPost('/api/documents/ask', {
          query: text,
          top_k: 5,
          max_length: 512,
        });

        const answer = response.data?.answer || 'No document-grounded answer was returned.';
        const documentSources = response.data?.sources || [];

        patchMessage(assistantTurnId, {
          content: answer,
          streaming: false,
          toolResult: {
            type: 'document_answer',
            query: text,
            summary: `Jarvis answered from ${documentSources.length} matched intake source${documentSources.length === 1 ? '' : 's'}.`,
            sources: documentSources,
          },
        });

        addHistoryEntry({
          type: 'chat',
          prompt: text,
          output: answer,
          model: 'Jarvis intake',
        });
        speakReply(answer);
        return;
      }

      const activeSessionId = await ensureSession();
      const abortController = new AbortController();
      streamAbortRef.current = abortController;
      let finalPayload = null;
      let streamError = null;

      await apiPostStream(
        `/api/chat/sessions/${activeSessionId}/stream`,
        {
          message: text,
          use_research: profile.liveResearchEnabled,
          persona_mode: profile.personaMode,
          response_mode: profile.responseMode,
          provider: profile.preferredProvider,
          requested_specialists: selectedSpecialists,
          requested_specialist_preset: selectedSpecialistPreset,
          ...buildStreamComposeFlags(profile.responseMode),
        },
        {
          signal: abortController.signal,
          onEvent: (payload) => {
            if (payload.event === 'v8_event') {
              applySessionRuntime(payload);
              pushSessionEvent(payload.v8_event);
              return;
            }

            if (payload.event === 'context') {
              applySessionRuntime(payload);
              applyWorkspaceContext(payload);
              applyBrowserVerification(payload);
              patchMessage(assistantTurnId, {
                persistentMemories: payload.persistent_memories || [],
                workspaceContext: payload.workspace_context || null,
                liveResearch: payload.live_research || null,
                responseTrace: payload.response_trace || null,
                toolResult: payload.tool_result || null,
              });
              if (payload.workspace_context?.results?.length) {
                setWorkspaceResults(payload.workspace_context.results);
              }
              return;
            }

            if (payload.event === 'token') {
              patchMessage(assistantTurnId, {
                content: payload.text_so_far || '',
                streaming: !payload.finished,
              });
              return;
            }

            if (payload.event === 'final') {
              finalPayload = payload;
              patchMessage(assistantTurnId, {
                content: payload.response || '',
                streaming: false,
                persistentMemories: payload.persistent_memories || [],
                workspaceContext: payload.workspace_context || null,
                liveResearch: payload.live_research || null,
                responseTrace: payload.response_trace || null,
                toolResult: payload.tool_result || null,
              });
              applySessionRuntime(payload);
              applyWorkspaceContext(payload);
              applyBrowserVerification(payload);
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

      refreshSessions();
      refreshSessionEvents(activeSessionId);

      if (finalPayload?.tool_result?.type === 'memory_add') {
        refreshMemories();
      }
      if (finalPayload?.tool_result?.type === 'workspace_search') {
        setWorkspaceResults(finalPayload.tool_result.results || []);
        setFilePreview(null);
      }
      if (finalPayload?.tool_result?.type === 'workspace_file') {
        setFilePreview(finalPayload.tool_result);
      }
      if (finalPayload?.workspace_context?.results?.length) {
        setWorkspaceResults(finalPayload.workspace_context.results);
      }
      if (finalPayload?.tool_result?.capability?.module) {
        refreshCapabilityBridge();
      }

      if (finalPayload?.response) {
        addHistoryEntry({
          type: 'chat',
          prompt: text,
          output: finalPayload.response,
          model: `Jarvis (${health.active_model_mode || 'local'})`,
        });
        speakReply(finalPayload.response);
      }
    } catch (error) {
      setMessages((current) => current.filter(
        (entry) => entry.id !== userTurn.id && entry.id !== assistantTurnId,
      ));
      applySystemGuard(error?.response?.data || error?.payload);
      refreshHealth();
      refreshSessionEvents();
      toast.error(`Jarvis could not reply: ${getApiErrorMessage(error)}`);
    } finally {
      streamAbortRef.current = null;
      setSending(false);
    }
  };

  const handleVoiceCapture = () => {
    if (!profile.voiceInputEnabled) {
      toast.error('Voice input is turned off in your Jarvis profile.');
      return;
    }

    if (!voiceSupported) {
      toast.error('Speech recognition is not supported in this browser.');
      return;
    }

    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
      return;
    }

    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Recognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setListening(true);
    recognition.onerror = () => {
      setListening(false);
      toast.error('Voice capture failed. Try again.');
    };
    recognition.onend = () => setListening(false);
    recognition.onresult = (event) => {
      const spokenText = event.results?.[0]?.[0]?.transcript?.trim();
      if (!spokenText) {
        return;
      }
      setDraft(spokenText);
      handleSend(spokenText);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const handleRunMysticReading = async () => {
    const requestText = buildMysticRequestText(mysticPrompt);
    if (!requestText || sending || booting) {
      return;
    }

    const preservedDraft = draft;
    await handleSend(requestText);
    setDraft((current) => {
      if (String(current || '').trim()) {
        return current;
      }
      return preservedDraft;
    });
  };

  const handleStageMysticPrompt = () => {
    const requestText = buildMysticRequestText(mysticPrompt);
    if (!requestText) {
      return;
    }

    setDraft((current) => {
      const existing = String(current || '').trim();
      return existing ? `${existing}\n\n${requestText}` : requestText;
    });
    toast.success('Mystic prompt staged in the main chat draft.');
  };

  const handleRunV10Core = async () => {
    const requestText = buildV10RequestText(v10Prompt);
    if (!requestText || sending || booting) {
      return;
    }

    const preservedDraft = draft;
    await handleSend(requestText);
    setDraft((current) => {
      if (String(current || '').trim()) {
        return current;
      }
      return preservedDraft;
    });
  };

  const handleStageV10Prompt = () => {
    const requestText = buildV10RequestText(v10Prompt);
    if (!requestText) {
      return;
    }

    setDraft((current) => {
      const existing = String(current || '').trim();
      return existing ? `${existing}\n\n${requestText}` : requestText;
    });
    toast.success('V10 Core prompt staged in the main chat draft.');
  };

  const handleCapabilityFieldValueChange = useCallback((fieldId, nextValue) => {
    setCapabilityFieldValues((current) => ({
      ...current,
      [fieldId]: nextValue,
    }));
  }, []);

  const buildCapabilityPayload = useCallback(() => {
    if (!selectedCapabilityDeck || !selectedCapabilityAction) {
      return null;
    }
    return {
      capability: selectedCapabilityDeck.id,
      action: selectedCapabilityAction.id,
      args: serializeCapabilityArgs(selectedCapabilityAction.input_fields, capabilityFieldValues),
      execution_profile: {
        provider_mode: selectedCapabilityProviderMode || selectedCapabilityAction.default_provider_mode,
        governance_mode: selectedCapabilityGovernanceMode || selectedCapabilityAction.default_governance_mode,
      },
    };
  }, [
    capabilityFieldValues,
    selectedCapabilityAction,
    selectedCapabilityDeck,
    selectedCapabilityGovernanceMode,
    selectedCapabilityProviderMode,
  ]);

  const handleStageCapabilityPrompt = useCallback(() => {
    const payload = buildCapabilityPayload();
    if (!payload || !selectedCapabilityAction) {
      return;
    }
    const stagedEnvelope = JSON.stringify(
      {
        capability: payload.capability,
        action: payload.action,
        provider: payload.execution_profile?.provider_mode,
        mode: payload.execution_profile?.governance_mode,
        tool: selectedCapabilityAction.tool,
        args: payload.args,
      },
      null,
      2,
    );
    setDraft((current) => {
      const existing = String(current || '').trim();
      return existing ? `${existing}\n\n${stagedEnvelope}` : stagedEnvelope;
    });
    toast.success('Capability payload staged in the main chat draft.');
  }, [buildCapabilityPayload, selectedCapabilityAction]);

  const handleRunCapabilitySelection = useCallback(async () => {
    const payload = buildCapabilityPayload();
    if (!payload || capabilityExecuteBusy) {
      return;
    }

    setCapabilityExecuteBusy(true);
    try {
      const response = await apiPost('/api/jarvis/capability-bridge/execute', payload);
      setLatestCapabilityExecution(response.data || null);
      if (response.data?.tool_result?.capability) {
        refreshCapabilityBridge();
      }
      toast.success(`${selectedCapabilityDeck?.label || 'Capability'} executed through the governed bridge.`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Capability execution failed.'));
    } finally {
      setCapabilityExecuteBusy(false);
    }
  }, [
    buildCapabilityPayload,
    capabilityExecuteBusy,
    refreshCapabilityBridge,
    selectedCapabilityDeck?.label,
  ]);

  const handleProfileSave = () => {
    const saved = saveJarvisProfile(profile);
    setProfile(saved);
    toast.success('Jarvis profile saved');
  };

  const handleSystemGuardAction = useCallback(async (action) => {
    const normalizedAction = String(action || '').trim();
    if (!normalizedAction || guardBusy) {
      return;
    }

    if (
      normalizedAction === 'safe_stop'
      && !window.confirm(
        'Safe Stop will unload the local model and block new AI work until you resume. Continue?',
      )
    ) {
      return;
    }

    const reasonMap = {
      pause: 'Operator paused Jarvis from the command deck.',
      safe_stop: 'Operator requested a safe stop from the command deck.',
      resume: 'Operator resumed Jarvis from the command deck.',
    };

    setGuardBusy(true);
    try {
      const response = await apiPost('/api/system/guard', {
        action: normalizedAction,
        reason: reasonMap[normalizedAction] || 'Operator updated the system guard.',
      });
      applySystemGuard(response.data);
      applyDreamspace(response.data);
      await refreshHealth();
      refreshBlueprint();
      refreshSessions();
      if (sessionId) {
        refreshSessionEvents(sessionId);
      }
      toast.success(`System Guard ${normalizedAction.replace(/_/g, ' ')} complete.`);
    } catch (error) {
      applySystemGuard(error?.response?.data || error?.payload);
      applyDreamspace(error?.response?.data || error?.payload);
      refreshHealth();
      toast.error(`Could not update System Guard: ${getApiErrorMessage(error)}`);
    } finally {
      setGuardBusy(false);
    }
  }, [
    applyDreamspace,
    applySystemGuard,
    guardBusy,
    refreshHealth,
    refreshBlueprint,
    refreshSessionEvents,
    refreshSessions,
    sessionId,
  ]);

  const handleDreamspaceAction = useCallback(async (action) => {
    const normalizedAction = String(action || '').trim();
    if (!normalizedAction || dreamspaceBusy) {
      return;
    }

    const reasonMap = {
      start: 'Operator started Dreamspace from the command deck.',
      pause: 'Operator paused Dreamspace from the command deck.',
      resume: 'Operator resumed Dreamspace from the command deck.',
      stop: 'Operator stopped Dreamspace from the command deck.',
      run_once: 'Operator triggered one manual Dreamspace reflection.',
    };

    setDreamspaceBusy(true);
    try {
      const response = await apiPost('/api/system/dreamspace', {
        action: normalizedAction,
        reason: reasonMap[normalizedAction] || 'Operator updated Dreamspace from the command deck.',
      });
      applySystemGuard(response.data);
      applyDreamspace(response.data);
      setHealth((current) => ({
        ...current,
        requested_model_mode: response.data.requested_model_mode,
        active_model_mode: response.data.active_model_mode,
        ai_status: response.data.ai_status,
      }));
      refreshBlueprint();
      toast.success(
        normalizedAction === 'run_once'
          ? 'Dreamspace generated one private reflection.'
          : `Dreamspace ${normalizedAction.replace(/_/g, ' ')} complete.`,
      );
    } catch (error) {
      applySystemGuard(error?.response?.data || error?.payload);
      applyDreamspace(error?.response?.data || error?.payload);
      toast.error(`Could not update Dreamspace: ${getApiErrorMessage(error)}`);
    } finally {
      setDreamspaceBusy(false);
    }
  }, [applyDreamspace, applySystemGuard, dreamspaceBusy, refreshBlueprint]);

  const handleCreateMission = useCallback(async () => {
    const title = missionTitleDraft.trim();
    const objective = missionObjectiveDraft.trim();
    const nextStep = missionNextStepDraft.trim();

    if (!title && !objective) {
      toast.error('Add a mission title or objective first.');
      return;
    }

    setMissionBusy(true);
    try {
      const response = await apiPost('/api/jarvis/missions', {
        title,
        objective,
        next_step: nextStep,
        session_id: sessionId || null,
        status: 'active',
        focus: true,
      });
      setMissionBoard({
        ...defaultMissionBoard,
        ...(response.data.mission_board || {}),
      });
      setMissionTitleDraft('');
      setMissionObjectiveDraft('');
      setMissionNextStepDraft('');
      toast.success('Mission created');
    } catch (error) {
      toast.error(`Could not create mission: ${getApiErrorMessage(error)}`);
    } finally {
      setMissionBusy(false);
    }
  }, [missionNextStepDraft, missionObjectiveDraft, missionTitleDraft, sessionId]);

  const handleCreateMissionPreset = useCallback(async (presetId) => {
    if (!presetId) {
      return;
    }

    setMissionBusy(true);
    try {
      const response = await apiPost('/api/jarvis/missions/from-preset', {
        preset_id: presetId,
        session_id: sessionId || null,
        focus: true,
      });
      setMissionBoard({
        ...defaultMissionBoard,
        ...(response.data.mission_board || {}),
      });
      toast.success('Mission recipe loaded');
    } catch (error) {
      toast.error(`Could not load mission recipe: ${getApiErrorMessage(error)}`);
    } finally {
      setMissionBusy(false);
    }
  }, [sessionId]);

  const handleFocusMission = useCallback(async (missionId) => {
    setMissionBusy(true);
    try {
      const response = await apiPost(`/api/jarvis/missions/${missionId}/focus`);
      setMissionBoard({
        ...defaultMissionBoard,
        ...(response.data.mission_board || {}),
      });
      toast.success('Mission focused');
    } catch (error) {
      toast.error(`Could not focus mission: ${getApiErrorMessage(error)}`);
    } finally {
      setMissionBusy(false);
    }
  }, []);

  const handleSetMissionStatus = useCallback(async (missionId, status) => {
    setMissionBusy(true);
    try {
      const response = await apiPatch(`/api/jarvis/missions/${missionId}`, {
        status,
      });
      setMissionBoard({
        ...defaultMissionBoard,
        ...(response.data.mission_board || {}),
      });
      toast.success(`Mission marked ${status}`);
    } catch (error) {
      toast.error(`Could not update mission: ${getApiErrorMessage(error)}`);
    } finally {
      setMissionBusy(false);
    }
  }, []);

  const handleApplyMissionCriticSuggestion = useCallback(async (missionId) => {
    setMissionBusy(true);
    try {
      const response = await apiPost(`/api/jarvis/missions/${missionId}/apply-critic`, {
        adopt_status: true,
        adopt_next_step: true,
      });
      setMissionBoard({
        ...defaultMissionBoard,
        ...(response.data.mission_board || {}),
      });
      toast.success('Mission Critic suggestion applied');
    } catch (error) {
      toast.error(`Could not apply Mission Critic suggestion: ${getApiErrorMessage(error)}`);
    } finally {
      setMissionBusy(false);
    }
  }, []);

  const handleDeleteMission = useCallback(async (missionId) => {
    if (!window.confirm('Delete this mission from Mission Board?')) {
      return;
    }

    setMissionBusy(true);
    try {
      const response = await apiDelete(`/api/jarvis/missions/${missionId}`);
      setMissionBoard({
        ...defaultMissionBoard,
        ...(response.data.mission_board || {}),
      });
      toast.success('Mission deleted');
    } catch (error) {
      toast.error(`Could not delete mission: ${getApiErrorMessage(error)}`);
    } finally {
      setMissionBusy(false);
    }
  }, []);

  const handleDraftKeyDown = (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault();
      handleSend();
    }
  };

  const handleWorkspaceKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleWorkspaceSearch();
    }
  };

  const handleLoadSession = async (nextSessionId) => {
    if (!nextSessionId || nextSessionId === sessionId) {
      return;
    }

    try {
      const response = await apiGet(`/api/chat/sessions/${nextSessionId}`);
      setActiveJarvisSessionId(nextSessionId);
      setSessionId(nextSessionId);
      setMessages(mapSessionTurns(response.data.turns));
      applySessionRuntime(response.data);
      applyWorkspaceContext(response.data);
      applyBrowserVerification(response.data);
      refreshSessionEvents(nextSessionId);
      toast.success('Session loaded');
    } catch (error) {
      toast.error(`Could not load session: ${getApiErrorMessage(error)}`);
      refreshSessions();
    }
  };

  const handleDeleteSession = async (targetSessionId) => {
    try {
      await apiDelete(`/api/chat/sessions/${targetSessionId}`);
      if (targetSessionId === sessionId) {
        clearActiveJarvisSessionId();
        await createFreshSession(profile);
      } else {
        refreshSessions();
      }
      toast.success('Session deleted');
    } catch (error) {
      toast.error(`Could not delete session: ${getApiErrorMessage(error)}`);
    }
  };

  const handleSaveMemory = async () => {
    const text = memoryDraft.trim();
    if (!text || savingMemory) {
      return;
    }

    setSavingMemory(true);
    try {
      await apiPost('/api/jarvis/memory', {
        text,
        category: 'operator',
        priority: 60,
        tags: ['console'],
        source: 'console',
      });
      setMemoryDraft('');
      refreshMemories();
      toast.success('Saved to long-term memory');
    } catch (error) {
      toast.error(`Could not save memory: ${getApiErrorMessage(error)}`);
    } finally {
      setSavingMemory(false);
    }
  };

  const handleDeleteMemory = async (memoryId) => {
    try {
      await apiDelete(`/api/jarvis/memory/${memoryId}`);
      refreshMemories();
      toast.success('Memory deleted');
    } catch (error) {
      toast.error(`Could not delete memory: ${getApiErrorMessage(error)}`);
    }
  };

  const handleWorkspaceSearch = async (nextQuery) => {
    const cleanedQuery = String(nextQuery ?? workspaceQuery).trim();
    if (!cleanedQuery) {
      toast.error('Enter something to search for.');
      return;
    }

    setWorkspaceBusy(true);
    setWorkspaceQuery(cleanedQuery);
    try {
      const response = await apiPost('/api/jarvis/workspace/search', {
        query: cleanedQuery,
        limit: 8,
      });
      setWorkspaceResults(response.data.results || []);
      setFilePreview(null);
    } catch (error) {
      toast.error(`Workspace search failed: ${getApiErrorMessage(error)}`);
    } finally {
      setWorkspaceBusy(false);
    }
  };

  const loadFilePreview = async (relativePath) => {
    try {
      const response = await apiGet('/api/jarvis/workspace/file', {
        params: { path: relativePath, max_chars: 2500 },
      });
      setFilePreview(response.data);
    } catch (error) {
      toast.error(`Could not open file preview: ${getApiErrorMessage(error)}`);
    }
  };

  const handleProjectOpen = async (project) => {
    if (project.readme_path) {
      await loadFilePreview(project.readme_path);
      return;
    }

    setWorkspaceQuery(project.name);
    await handleWorkspaceSearch(project.name);
  };

  const handleRunAction = async (actionInput) => {
    const actionId = typeof actionInput === 'string' ? actionInput : actionInput?.id;
    const action = availableActions.find((candidate) => candidate.id === actionId) || actionInput;

    if (!actionId || !action) {
      toast.error('That action is not available right now.');
      return;
    }

    const approved = window.confirm(
      `Run "${action.label}"?\n\n${action.description}\n\nCommand: ${action.command_preview}`,
    );
    if (!approved) {
      return;
    }

    setActionBusyId(actionId);
    try {
      const activeSessionId = await ensureSession();
      const response = await apiPost(`/api/chat/sessions/${activeSessionId}/actions/execute`, {
        action_id: actionId,
        review_id: action.review_id || undefined,
        approved: true,
        persona_mode: profile.personaMode,
        response_mode: profile.responseMode,
        provider: profile.preferredProvider,
        requested_specialists: selectedSpecialists,
        requested_specialist_preset: selectedSpecialistPreset,
      });
      const payload = response.data;

      setMessages((current) => [
        ...current,
        {
          id: `assistant-action-${Date.now()}`,
          role: 'assistant',
          content: payload.response || '',
          timestamp: new Date().toISOString(),
          streaming: false,
          persistentMemories: payload.persistent_memories || [],
          workspaceContext: payload.workspace_context || null,
          liveResearch: payload.live_research || null,
          responseTrace: payload.response_trace || null,
          toolResult: payload.tool_result || null,
        },
      ]);
      applySessionRuntime(payload);
      applyWorkspaceContext(payload);
      applyBrowserVerification(payload);
      refreshSessions();
      refreshSessionEvents(activeSessionId);
      refreshPatchReviews(activeSessionId);
      toast.success(payload.tool_result?.summary || `${action.label} completed`);
    } catch (error) {
      applySystemGuard(error?.response?.data || error?.payload);
      refreshHealth();
      refreshSessionEvents();
      toast.error(`Could not run action: ${getApiErrorMessage(error)}`);
    } finally {
      setActionBusyId('');
    }
  };

  const handlePreviewPatchReview = async (reviewId) => {
    setPatchPreviewBusy(true);
    try {
      const response = await apiPost('/api/jarvis/patch/preview', { review_id: reviewId });
      setPatchPreview({
        reviewId,
        ...(response.data.preview || {}),
        ul_trace: response.data.ul_trace,
        ul_substrate: response.data.ul_substrate,
      });
    } catch (error) {
      toast.error(`Could not preview patch review: ${getApiErrorMessage(error)}`);
    } finally {
      setPatchPreviewBusy(false);
    }
  };

  const handleApplyPatchReview = (review) => {
    handleRunAction({
      id: 'apply_patch_review',
      review_id: review.id,
      label: 'Apply Approved Patch',
      description: review.goal
        ? `Apply the accepted review for: ${review.goal}`
        : 'Apply the accepted patch review to the workspace.',
      command_preview: `apply reviewed patch ${review.id} to ${(review.target_files || []).length} file(s)`,
    });
  };

  const performBrowserVerification = useCallback(async ({
    targetPath,
    expectationOverride,
    syncInputs = true,
    setAsActiveResult = true,
  } = {}) => {
    const requestedPath = String(targetPath ?? browserTargetPath ?? '').trim() || '/';
    const requestedExpectation = expectationOverride ?? browserExpectation;
    const normalizedManualExpectation = String(requestedExpectation || '').trim();

    if (syncInputs && targetPath !== undefined) {
      setBrowserTargetPath(requestedPath);
    }
    if (syncInputs && expectationOverride !== undefined) {
      setBrowserExpectation(normalizedManualExpectation);
    }

    const snapshot = await captureBrowserSnapshot(requestedPath);
    const resolvedPath = snapshot?.path || requestedPath;
    if (syncInputs || setAsActiveResult) {
      setBrowserTargetPath(resolvedPath);
    }

    const activeSessionId = await ensureSession();
    const response = await apiPost(`/api/chat/sessions/${activeSessionId}/browser/verify`, {
      snapshot,
      expectation: normalizedManualExpectation || undefined,
      persona_mode: profile.personaMode,
      response_mode: profile.responseMode,
      provider: profile.preferredProvider,
      requested_specialists: selectedSpecialists,
      requested_specialist_preset: selectedSpecialistPreset,
    });
    const payload = response.data;

    applySessionRuntime(payload);
    applyWorkspaceContext(payload);
    if (setAsActiveResult) {
      applyBrowserVerification(payload);
      if (payload.browser_verification?.workspace_context?.results?.length) {
        setWorkspaceResults(payload.browser_verification.workspace_context.results);
      }
    }
    refreshSessions();
    refreshSessionEvents(activeSessionId);

    return {
      payload,
      verification: payload.browser_verification || null,
      resolvedPath,
    };
  }, [
    applyBrowserVerification,
    applySessionRuntime,
    applyWorkspaceContext,
    browserExpectation,
    browserTargetPath,
    ensureSession,
    profile.personaMode,
    profile.preferredProvider,
    profile.responseMode,
    selectedSpecialistPreset,
    selectedSpecialists,
    refreshSessionEvents,
    refreshSessions,
  ]);

  const handleBrowserVerify = async (options = {}) => {
    if (browserBusy || browserSuiteBusy || booting) {
      return;
    }

    setBrowserBusy(true);
    try {
      const result = await performBrowserVerification({
        targetPath: options.targetPath,
        expectationOverride: options.expectationOverride,
      });
      toast.success(result.verification?.summary || 'Browser verification complete');
    } catch (error) {
      toast.error(`Browser verification failed: ${getApiErrorMessage(error)}`);
    } finally {
      setBrowserBusy(false);
    }
  };

  const handleQuickBrowserVerify = (target) => {
    handleBrowserVerify({
      targetPath: target.path,
      expectationOverride: '',
    });
  };

  const handleVerifyAllCoreRoutes = async () => {
    if (browserBusy || browserSuiteBusy || booting || quickBrowserTargets.length === 0) {
      return;
    }

    setBrowserSuiteBusy(true);
    setBrowserSuiteResults([]);
    try {
      const nextResults = [];
      for (const target of quickBrowserTargets) {
        const result = await performBrowserVerification({
          targetPath: target.path,
          expectationOverride: '',
          syncInputs: false,
          setAsActiveResult: false,
        });

        const suiteEntry = buildBrowserSuiteResult(target, result.verification);
        nextResults.push(suiteEntry);
        startTransition(() => {
          setBrowserSuiteResults([...nextResults]);
        });
      }

      const focusResult = nextResults.find((result) => result.status !== 'healthy') || nextResults[0] || null;
      if (focusResult?.verification) {
        applyBrowserVerification({ browser_verification: focusResult.verification });
        if (focusResult.verification.workspace_context?.results?.length) {
          setWorkspaceResults(focusResult.verification.workspace_context.results);
        }
        setBrowserTargetPath(focusResult.path || '/');
        setBrowserExpectation('');
      }

      const overallStatus = nextResults.some((result) => result.status === 'fail')
        ? 'fail'
        : nextResults.some((result) => result.status === 'warning')
          ? 'warning'
          : 'healthy';

      if (overallStatus === 'healthy') {
        toast.success('All core routes aligned with their expected UI state.');
      } else if (focusResult) {
        toast((toastMessage) => (
          <span>
            Core route sweep flagged <strong>{focusResult.label}</strong>.
          </span>
        ), {
          icon: overallStatus === 'fail' ? '!' : 'i',
        });
      }
    } catch (error) {
      toast.error(`Core route sweep failed: ${getApiErrorMessage(error)}`);
    } finally {
      setBrowserSuiteBusy(false);
    }
  };

  const orbState = listening ? 'listening' : sending || booting ? 'thinking' : 'ready';
  const spiralMetrics = [
    { label: 'Focus', value: sessionRuntime.spiralState.focus },
    { label: 'Confidence', value: sessionRuntime.spiralState.confidence },
    { label: 'Convergence', value: sessionRuntime.spiralState.goal_convergence },
  ];
  const preferenceEntries = Object.entries(sessionRuntime.memorySummary.preferences || {});
  const activePersona = profile.personaMode || sessionRuntime.personaMode || 'builder';
  const selectedResponseMode = profile.responseMode || sessionRuntime.requestedResponseMode || 'fast';
  const activeOperatingMode = resolveOperatingModeDisplay(profile, sessionRuntime, {
    forceRuntimeMode: sending || booting,
  });
  const companionNovaActive = [SMALL_NOVA_PERSONA_MODE, TINY_NOVA_PERSONA_MODE].includes(activePersona)
    || ['small', 'tiny'].includes(selectedResponseMode);
  const activeResponseTrace = sessionRuntime.responseTrace;
  const latestSessionEvent = sessionEvents[0] || null;
  const availableProviders = useMemo(() => {
    const providerList = Array.isArray(blueprint?.providers) && blueprint.providers.length > 0
      ? blueprint.providers
      : [
        {
          id: 'local',
          label: 'Local Heroine',
          available: true,
          summary: 'Primary on-laptop AAIS model path.',
          model: 'AAIS local runtime',
          kind: 'local',
        },
      ];

    return [
      {
        id: 'auto',
        label: 'Auto Best',
        available: true,
        summary: 'Jarvis chooses the strongest available provider for each turn while keeping manual pins available.',
        reason: '',
        activation_hint: '',
        model: 'Dynamic turn routing',
        kind: 'virtual',
      },
      ...providerList.map((provider) => ({
        id: provider.id || provider.name || 'local',
        label: provider.label || provider.display_name || provider.name || 'Local Heroine',
        available: provider.available !== false,
        summary: provider.summary || '',
        reason: provider.reason || '',
        activation_hint: provider.activation_hint || '',
        model: provider.model || '',
        kind: provider.kind || 'local',
      })),
    ];
  }, [blueprint]);
  const selectedProvider = sessionRuntime.preferredProvider
    || (profile.providerPreferencePinned ? profile.preferredProvider : 'auto')
    || 'auto';
  const selectedProviderObject = availableProviders.find((provider) => provider.id === selectedProvider)
    || availableProviders.find((provider) => provider.id === sessionRuntime.preferredProvider)
    || availableProviders[0]
    || null;
  const activeComposeTabObject = composeControlTabs.find((tab) => tab.id === activeComposeTab)
    || composeControlTabs[0];
  const activeSideTabObject = sidePanelTabs.find((tab) => tab.id === activeSideTab)
    || sidePanelTabs[0];
  const showConversationPanel = activeSideTab === 'conversation' || activeSideTab === 'all';
  const showReasoningPanel = activeSideTab === 'reasoning' || activeSideTab === 'all';
  const showCodingPanel = activeSideTab === 'coding' || activeSideTab === 'all';
  const showOperatorPanel = activeSideTab === 'operator' || activeSideTab === 'all';
  const securityProtocol = protocolSession?.security_protocol
    || sessionRuntime.securityProtocol
    || null;
  const immuneSystem = protocolSession?.immune_system
    || sessionRuntime.immuneSystem
    || null;
  const governance = protocolSession?.governance
    || sessionRuntime.governance
    || null;
  const moduleGovernance = protocolSession?.module_governance
    || sessionRuntime.moduleGovernance
    || null;
  const continuityProfile = protocolSession?.continuity_profile
    || sessionRuntime.continuityProfile
    || null;
  const v9Runtime = protocolSession?.v9_runtime
    || sessionRuntime.v9Runtime
    || null;
  const v10Runtime = protocolSession?.v10_runtime
    || sessionRuntime.v10Runtime
    || null;
  const activeProviderLabel = sessionRuntime.modelRoute?.provider_label
    || getProviderLabel(selectedProviderObject?.id || selectedProvider, availableProviders);
  const providerNotice = sessionRuntime.providerNotice || null;
  const networkStatusProviderLabels = useMemo(
    () => Object.fromEntries(availableProviders.map((provider) => [provider.id, provider.label])),
    [availableProviders],
  );
  const networkStatusData = useMemo(() => {
    const activeProviderId = sessionRuntime.modelRoute?.provider
      || selectedProviderObject?.id
      || selectedProvider
      || 'local';
    const requestedProviderId = providerNotice?.requested_provider
      || sessionRuntime.preferredProvider
      || selectedProvider
      || activeProviderId;
    const fallbackProviderId = providerNotice?.resolved_provider
      || sessionRuntime.providerFallback
      || activeProviderId;
    const fallbackActive = Boolean(
      providerNotice
      || health.ai_fallback_active
      || sessionRuntime.responseTrace?.fallback
      || `${sessionRuntime.modelRoute?.provider_reason || ''}`.startsWith('fallback_from_'),
    );

    return buildNetworkStatusData({
      latency_ms: health.request_latency_ms,
      backend_healthy: health.status === 'healthy',
      fallback_active: fallbackActive,
      quarantined: ['paused', 'stopped'].includes(systemGuard.status),
      timestamp: health.timestamp || Date.now(),
      providers: availableProviders.map((provider) => ({
        id: provider.id,
        available: provider.available,
        kind: provider.kind,
        requested: provider.id === requestedProviderId,
        active: provider.id === activeProviderId,
        fallback_target: fallbackActive && provider.id === fallbackProviderId,
      })),
    });
  }, [
    availableProviders,
    health.ai_fallback_active,
    health.request_latency_ms,
    health.status,
    health.timestamp,
    providerNotice,
    selectedProvider,
    selectedProviderObject,
    sessionRuntime.modelRoute,
    sessionRuntime.preferredProvider,
    sessionRuntime.providerFallback,
    sessionRuntime.responseTrace,
    systemGuard.status,
  ]);
  const cockpitToolStats = [
    {
      label: 'documents',
      value: documents.length,
      detail: conversationLane === 'documents' ? 'intake armed' : 'intake standby',
    },
    {
      label: 'memory',
      value: memories.length,
      detail: 'durable notes online',
    },
    {
      label: 'actions',
      value: availableActions.length,
      detail: 'operator actions loaded',
    },
    {
      label: 'workspace',
      value: workspaceProjects.length,
      detail: workspaceResults.length > 0 ? `${workspaceResults.length} live hits` : 'search ready',
    },
  ];

  return (
    <div className="jarvis-console">
      <section className="jarvis-hero">
        <div className="jarvis-hero-copy">
          <div className={`status-pill ${health.status === 'healthy' ? 'connected' : 'error'}`}>
            <FiActivity />
            {health.status === 'healthy' ? 'private local core online' : 'backend unavailable'}
          </div>
          {systemGuard.status !== 'nominal' && (
            <div className="status-pill warning">
              <FiShield />
              System Guard {getSystemGuardLabel(systemGuard.status)}
            </div>
          )}
          {corrigibility.status === 'pending' && (
            <div className="status-pill warning">
              <FiRefreshCw />
              Correction queued for next reply
            </div>
          )}
          {dreamspace.status === 'dreaming' && (
            <div className="status-pill">
              <FiCpu />
              Dreamspace weaving a background reflection
            </div>
          )}
            <h1>{profile.assistantName} | Operator Cockpit</h1>
          <p>
            {companionNovaActive
              ? 'Nova holds the cognitive lane in the center deck while Jarvis keeps authority, approvals, routing, and operational state on the control side. Tools stay visible.'
              : 'This cockpit keeps cognition, authority, and tools separate: Nova handles the soft working lane, Jarvis keeps operational control, and system tools remain continuously accessible.'}
          </p>

          <div className="jarvis-hero-actions">
            <button
              type="button"
              className="jarvis-primary-button"
              onClick={handleVoiceCapture}
              disabled={booting || !profile.voiceInputEnabled}
            >
              {listening ? <FiMicOff /> : <FiMic />}
              {listening ? 'Stop Listening' : profile.voiceInputEnabled ? `Speak to ${profile.assistantName}` : 'Voice Disabled'}
            </button>
            <button
              type="button"
              className="jarvis-secondary-button"
              onClick={() => createFreshSession(profile)}
              disabled={booting || sending}
            >
              <FiRefreshCw />
              New Session
            </button>
          </div>

          <div className="jarvis-readout-strip">
            <div className="readout-cell">
              <span>MODEL</span>
              <strong>{health.active_model_mode || 'offline'}</strong>
            </div>
            <div className="readout-cell">
              <span>PROVIDER</span>
              <strong>{activeProviderLabel}</strong>
            </div>
            <div className="readout-cell">
              <span>MODE</span>
              <strong>{sessionRuntime.activeMode}</strong>
            </div>
            <div className="readout-cell">
              <span>STATE</span>
              <strong>{sessionRuntime.sessionState.state}</strong>
            </div>
            <div className="readout-cell">
              <span>PERSONA</span>
              <strong>{activePersona}</strong>
            </div>
            <div className="readout-cell">
              <span>OPERATING</span>
              <strong>{getResponseModeLabel(activeOperatingMode)}</strong>
            </div>
            <div className="readout-cell">
              <span>POLICY</span>
              <strong>{sessionRuntime.policyStatus.posture}</strong>
            </div>
            <div className="readout-cell">
              <span>VOICE</span>
              <strong>
                {profile.voiceInputEnabled ? (voiceSupported ? 'ready' : 'n/a') : 'off'}
              </strong>
            </div>
            <div className="readout-cell">
              <span>WEB</span>
              <strong>{profile.liveResearchEnabled ? 'armed' : 'manual'}</strong>
            </div>
            <div className="readout-cell">
              <span>GUARD</span>
              <strong>{systemGuard.status}</strong>
            </div>
            <div className="readout-cell">
              <span>COURSE</span>
              <strong>
                {corrigibility.status === 'pending'
                  ? 'queued'
                  : getCorrigibilityActionLabel(corrigibility.last_action || corrigibility.status)}
              </strong>
            </div>
            <div className="readout-cell">
              <span>DREAMSPACE</span>
              <strong>{dreamspace.status}</strong>
            </div>
          </div>
        </div>

        <div className="jarvis-orb-panel page-panel">
          <div className={`jarvis-orb ${orbState}`}>
            <div className="jarvis-orb-core" />
            <div className="jarvis-orb-ring ring-one" />
            <div className="jarvis-orb-ring ring-two" />
            <div className="jarvis-orb-ring ring-three" />
          </div>
          <div className="jarvis-orb-meta">
            <strong>{listening ? 'Listening...' : sending ? 'Thinking...' : 'Standing by'}</strong>
            <span>{profile.operatorName} linked to {profile.assistantName}</span>
          </div>
        </div>
      </section>

      <section className="jarvis-layout">
        <aside className="jarvis-tool-panel" id="jarvis-tool-layer">
          <div className="jarvis-side-card page-panel tool-layer-card">
            <div className="jarvis-side-title">
              <FiMonitor />
              <h3>Tool Layer</h3>
            </div>
            <p className="session-empty tool-layer-summary">
              Tools are system capabilities, not optional decorations. This rail stays visible so workspace,
              memory, analysis, and execution access never disappear.
            </p>

            <div className="tool-layer-stat-grid">
              {cockpitToolStats.map((stat) => (
                <div key={stat.label} className="tool-layer-stat">
                  <span>{stat.label}</span>
                  <strong>{stat.value}</strong>
                  <p>{stat.detail}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="jarvis-side-card page-panel tool-layer-card">
            <div className="tool-layer-header">
              <div>
                <span>Always Visible</span>
                <strong>Operational tools</strong>
              </div>
              <span className="inline-meta-chip success">never hidden</span>
            </div>

            <div className="tool-layer-grid">
              {cockpitToolLinks.map((tool) => (
                <Link key={tool.id} to={tool.to} className="tool-layer-link">
                  <strong>{tool.label}</strong>
                  <span>{tool.detail}</span>
                </Link>
              ))}
            </div>
          </div>

          <div className="jarvis-side-card page-panel tool-layer-card">
            <div className="tool-layer-header">
              <div>
                <span>Internal Decks</span>
                <strong>Control surfaces</strong>
              </div>
              <span className="inline-meta-chip">{activeSideTabObject.label}</span>
            </div>

            <div className="tool-layer-grid">
              <button type="button" className="tool-layer-switch" onClick={() => setActiveSideTab('coding')}>
                <strong>Code Execution</strong>
                <span>Workspace, browser verify, patch review, and evolve controls.</span>
              </button>
              <button type="button" className="tool-layer-switch" onClick={() => setActiveSideTab('operator')}>
                <strong>Jarvis Control</strong>
                <span>Approvals, provider routing, system state, and governance.</span>
              </button>
              <button type="button" className="tool-layer-switch" onClick={() => setActiveSideTab('reasoning')}>
                <strong>Logs and Traces</strong>
                <span>Reasoning state, continuity, protocol records, and blueprint views.</span>
              </button>
              <button type="button" className="tool-layer-switch" onClick={() => setActiveSideTab('all')}>
                <strong>Open Full Cockpit</strong>
                <span>Show every control section at once.</span>
              </button>
            </div>

            <div className="tool-layer-search">
              <label className="jarvis-intake-field">
                <span>Workspace Search</span>
                <input
                  type="text"
                  value={workspaceQuery}
                  onChange={(event) => setWorkspaceQuery(event.target.value)}
                  onKeyDown={handleWorkspaceKeyDown}
                  placeholder="Search files, code, notes, and routes..."
                />
              </label>
              <button
                type="button"
                className="jarvis-secondary-button"
                onClick={() => {
                  setActiveSideTab('coding');
                  handleWorkspaceSearch();
                }}
                disabled={workspaceBusy}
              >
                <FiSearch />
                {workspaceBusy ? 'Searching...' : 'Search Workspace'}
              </button>
            </div>
          </div>

          <CapabilityBridgeConsoleCard
            snapshot={capabilityBridgeSnapshot}
            busy={capabilityBridgeBusy}
            loadError={capabilityBridgeLoadError}
            executeBusy={capabilityExecuteBusy}
            selectedCapabilityId={selectedCapabilityId}
            selectedActionId={selectedCapabilityActionId}
            providerMode={selectedCapabilityProviderMode}
            governanceMode={selectedCapabilityGovernanceMode}
            fieldValues={capabilityFieldValues}
            latestExecution={latestCapabilityExecution}
            onCapabilityChange={setSelectedCapabilityId}
            onActionChange={setSelectedCapabilityActionId}
            onProviderModeChange={setSelectedCapabilityProviderMode}
            onGovernanceModeChange={setSelectedCapabilityGovernanceMode}
            onFieldValueChange={handleCapabilityFieldValueChange}
            onRun={handleRunCapabilitySelection}
            onStagePrompt={handleStageCapabilityPrompt}
            onRefresh={refreshCapabilityBridge}
            formatRelativeTime={formatRelativeTime}
            onOpenFile={loadFilePreview}
            onSearchWorkspace={handleWorkspaceSearch}
            onAppendDraftContext={appendDraftContext}
            onRunAction={handleRunAction}
            actionBusyId={actionBusyId}
          />
        </aside>

        <div className="jarvis-chat-shell page-panel">
          <div className="jarvis-chat-header">
            <div>
              <h2>Nova Surface</h2>
              <p>Cognitive interface · Session {sessionId || 'starting...'}</p>
            </div>
            <div className="jarvis-chat-health">
              <span><FiCpu /> {health.active_model_mode || 'offline'}</span>
              <span><FiCommand /> {health.ai_status}</span>
              <span><FiActivity /> {sessionRuntime.activeMode}</span>
            </div>
          </div>

          <input
            ref={fileIntakeRef}
            type="file"
            accept=".pdf,.txt,.md,text/plain,application/pdf"
            className="jarvis-hidden-input"
            onChange={handleFileIntake}
          />

          <div className="jarvis-context-card jarvis-intake-card">
            <div className="jarvis-context-header">
              <div>
                <span>Jarvis Intake</span>
                <strong>Private source lane for documents, notes, and URLs</strong>
              </div>
              <div className="jarvis-inline-meta">
                <span className="inline-meta-chip">{documents.length} documents</span>
                <span className={`inline-meta-chip ${conversationLane === 'documents' ? 'warning' : ''}`}>
                  {conversationLane === 'documents' ? 'intake lane armed' : 'chat lane armed'}
                </span>
              </div>
            </div>

            <div className="jarvis-tab-row">
              <button
                type="button"
                className={`jarvis-tab-button ${conversationLane === 'chat' ? 'active' : ''}`}
                onClick={() => setConversationLane('chat')}
              >
                <strong>Chat Lane</strong>
              </button>
              <button
                type="button"
                className={`jarvis-tab-button ${conversationLane === 'documents' ? 'active' : ''}`}
                onClick={() => setConversationLane('documents')}
                disabled={documents.length === 0}
              >
                <strong>Ask Intake</strong>
              </button>
              <button
                type="button"
                className="jarvis-secondary-button"
                onClick={() => fileIntakeRef.current?.click()}
                disabled={fileIntakeBusy}
              >
                <FiFolder />
                {fileIntakeBusy ? 'Uploading...' : 'Upload File'}
              </button>
              <button
                type="button"
                className="jarvis-secondary-button"
                onClick={() => refreshDocuments()}
                disabled={documentsLoading}
              >
                <FiRefreshCw />
                {documentsLoading ? 'Refreshing...' : 'Refresh Intake'}
              </button>
            </div>

            <div className="jarvis-intake-grid">
              <label className="jarvis-intake-field">
                <span>Paste text</span>
                <textarea
                  value={textIntakeDraft}
                  onChange={(event) => setTextIntakeDraft(event.target.value)}
                  rows="4"
                  placeholder="Paste notes, excerpts, or operator context for Jarvis to ingest."
                />
                <button
                  type="button"
                  className="jarvis-secondary-button"
                  onClick={handleTextIntake}
                  disabled={textIntakeBusy || !textIntakeDraft.trim()}
                >
                  <FiPlus />
                  {textIntakeBusy ? 'Ingesting...' : 'Ingest Text'}
                </button>
              </label>

              <label className="jarvis-intake-field">
                <span>Remote URL</span>
                <input
                  type="text"
                  value={urlIntakeDraft}
                  onChange={(event) => setUrlIntakeDraft(event.target.value)}
                  placeholder="https://example.com/reference"
                />
                <button
                  type="button"
                  className="jarvis-secondary-button"
                  onClick={handleUrlIntake}
                  disabled={urlIntakeBusy || !urlIntakeDraft.trim()}
                >
                  <FiGlobe />
                  {urlIntakeBusy ? 'Ingesting...' : 'Ingest URL'}
                </button>
              </label>
            </div>

            <div className="jarvis-document-strip">
              {documentsLoading ? (
                <span className="session-empty">Refreshing intake...</span>
              ) : documents.length === 0 ? (
                <span className="session-empty">No documents in Jarvis intake yet.</span>
              ) : (
                documents.slice(0, 4).map((document) => (
                  <button
                    key={document.doc_id}
                    type="button"
                    className="workspace-context-chip jarvis-document-chip"
                    onClick={() => {
                      setConversationLane('documents');
                      appendDraftContext(
                        `Document intake (${document.doc_id}):`,
                        `${document.metadata?.source || document.doc_id} | ${formatDocumentRole(document.metadata?.document_role)} | ${document.chunk_count} chunks`,
                      );
                    }}
                  >
                    {document.metadata?.source || document.doc_id}
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="jarvis-quick-actions">
            {quickActions.map((action) => (
              <button
                key={action}
                type="button"
                className="quick-action-chip"
                onClick={() => setDraft(action)}
              >
                {action}
              </button>
            ))}
          </div>

          {(attachedWorkspaceContext?.results?.length > 0 || attachedLiveResearch?.sources?.length > 0) && (
            <div className="jarvis-context-card">
              <div className="jarvis-context-header">
                <div>
                  <span>{attachedLiveResearch?.sources?.length ? 'Live Research Attached' : 'Auto Workspace Context'}</span>
                  <strong>{attachedLiveResearch?.query || attachedWorkspaceContext?.query}</strong>
                </div>
                {attachedLiveResearch?.sources?.length ? (
                  <button
                    type="button"
                    className="compact-action-button"
                    onClick={() => openExternalUrl(attachedLiveResearch.sources[0]?.url)}
                    aria-label="Open top live research source"
                  >
                    <FiArrowUpRight />
                  </button>
                ) : (
                  <button
                    type="button"
                    className="compact-action-button"
                    onClick={() => handleWorkspaceSearch(attachedWorkspaceContext.query)}
                    aria-label="Open attached context in workspace tools"
                  >
                    <FiSearch />
                  </button>
                )}
              </div>
              <p>{attachedLiveResearch?.summary || attachedWorkspaceContext?.summary}</p>
              {attachedLiveResearch?.sources?.length > 0 ? (
                <div className="spiral-chip-row">
                  {attachedLiveResearch.sources.map((source) => (
                    <button
                      key={`${source.id}-${source.url}`}
                      type="button"
                      className="workspace-context-chip"
                      onClick={() => openExternalUrl(source.url)}
                    >
                      [{source.id}] {source.title}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="spiral-chip-row">
                  {(attachedWorkspaceContext.files || []).map((file) => (
                    <button
                      key={file.relative_path}
                      type="button"
                      className="workspace-context-chip"
                      onClick={() => loadFilePreview(file.relative_path)}
                    >
                      {file.relative_path}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {providerNotice && (
            <div className="jarvis-context-card provider-notice-card">
              <div className="jarvis-context-header">
                <div>
                  <span>Provider Fallback</span>
                  <strong>{providerNotice.requested_label || 'Requested provider unavailable'}</strong>
                </div>
              </div>
              <p>{providerNotice.summary || providerNotice.reason || 'Jarvis fell back to a different provider for this turn.'}</p>
            </div>
          )}

          {sessionRuntime.providerMode && (
            <div className="jarvis-inline-meta">
              <span className="inline-meta-chip">
                {getProviderPathLabel(sessionRuntime.providerMode)}
              </span>
              <span className="inline-meta-chip">
                fallback {getProviderLabel(sessionRuntime.providerFallback, availableProviders)}
              </span>
              {providerNotice ? (
                <span className="inline-meta-chip warning">
                  {`${providerNotice.requested_label || activeProviderLabel} -> ${providerNotice.resolved_label || getProviderLabel(sessionRuntime.providerFallback, availableProviders)}`}
                </span>
              ) : null}
            </div>
          )}

          <div className="jarvis-messages">
            {booting ? (
              <div className="jarvis-empty-state">
                <p>{`Starting your private ${profile.assistantName} session...`}</p>
              </div>
            ) : messages.length === 0 ? (
              <div className="jarvis-empty-state">
                <p>
                  {companionNovaActive
                    ? `${profile.assistantName} is here. Start with what you are noticing, feeling, or trying to understand.`
                    : `${profile.assistantName} is online. Ask for help, planning, coding, or a second brain.`}
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <ConversationMessage
                  key={message.id}
                  message={message}
                  profile={profile}
                  onOpenFile={loadFilePreview}
                  onOpenSource={openExternalUrl}
                  onSearchWorkspace={handleWorkspaceSearch}
                  onAppendDraftContext={appendDraftContext}
                  onRunAction={handleRunAction}
                  actionBusyId={actionBusyId}
                />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="jarvis-compose">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleDraftKeyDown}
              placeholder={
                companionNovaActive
                  ? `Talk to ${profile.assistantName}...`
                  : `Tell ${profile.assistantName} what you need...`
              }
              rows="4"
            />
            <div className="compose-category-shell">
              <div className="compose-category-header">
                <div>
                  <span>Conversation Controls</span>
                  <strong>{activeComposeTabObject.label}</strong>
                </div>
                <p>{activeComposeTabObject.summary}</p>
              </div>
              <div className="jarvis-tab-row compose-tab-row">
                {composeControlTabs.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    className={`jarvis-tab-button ${activeComposeTab === tab.id ? 'active' : ''}`}
                    onClick={() => setActiveComposeTab(tab.id)}
                  >
                    <strong>{tab.label}</strong>
                  </button>
                ))}
              </div>

              {(activeComposeTab === 'mode' || activeComposeTab === 'all') && (
                <div className="response-mode-row">
                  {responseModes.map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      className={`response-mode-chip ${selectedResponseMode === mode.id ? 'active' : ''}`}
                      onClick={() => setProfile((current) => applyResponseModeProfileSelection(current, mode.id))}
                    >
                      <strong>{mode.label}</strong>
                      <span>{mode.blurb}</span>
                    </button>
                  ))}
                </div>
              )}

              {(activeComposeTab === 'mode' || activeComposeTab === 'all') && (
                <label className="jarvis-toggle-field compose-deep-toggle">
                  <input
                    type="checkbox"
                    checked={deepComposeEnabled}
                    onChange={toggleDeepCompose}
                  />
                  <span>
                    Deep compose — run full Nova Cortex on operator turns (Spine, ARIS, all lobes).
                  </span>
                </label>
              )}

              {(activeComposeTab === 'provider' || activeComposeTab === 'all') && (
                <div className="provider-row">
                  {availableProviders.map((provider) => {
                    const isSelected = selectedProvider === provider.id;
                    const detail = provider.available
                      ? provider.model || provider.summary || 'Ready'
                      : provider.activation_hint || provider.reason || 'Offline';
                    return (
                      <button
                        key={provider.id}
                        type="button"
                        className={`provider-chip ${isSelected ? 'active' : ''} ${provider.available ? '' : 'offline'}`}
                        onClick={() => pinPreferredProvider(provider.id)}
                        title={provider.summary || provider.reason || provider.label}
                      >
                        <strong>{provider.label}</strong>
                        <span>{detail}</span>
                      </button>
                    );
                  })}
                </div>
              )}

              {(activeComposeTab === 'persona' || activeComposeTab === 'all') && (
                <div className="persona-mode-row">
                  {personaModes.map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      className={`persona-mode-chip ${activePersona === mode.id ? 'active' : ''}`}
                      onClick={() => setProfile((current) => applyPersonaProfileSelection(current, mode.id))}
                    >
                      <strong>{mode.label}</strong>
                      <span>{mode.blurb}</span>
                    </button>
                  ))}
                </div>
              )}

              {(activeComposeTab === 'specialists' || activeComposeTab === 'all') && (
                <div className="specialist-panel">
                  <div className="specialist-panel-header">
                    <div className="specialist-panel-copy">
                      <span>Specialist Registry</span>
                      <strong>Pin named Jarvis minds for this session</strong>
                      <p>
                        Force expert passes like Debug, Architecture, Fine-Tune, or Continuity Check on top of the normal auto-routing.
                      </p>
                    </div>
                    <div className="specialist-panel-actions">
                      <span className="inline-meta-chip">
                        {selectedSpecialists.length}/{SPECIALIST_SELECTION_LIMIT} pinned
                      </span>
                      {selectedSpecialistPresetObject ? (
                        <span className="inline-meta-chip">
                          Preset {selectedSpecialistPresetObject.label}
                        </span>
                      ) : null}
                      <button
                        type="button"
                        className="inline-card-action"
                        onClick={clearSelectedSpecialists}
                        disabled={selectedSpecialists.length === 0}
                      >
                        Clear
                      </button>
                      <button
                        type="button"
                        className="inline-card-action"
                        onClick={clearSpecialistPreset}
                        disabled={!selectedSpecialistPreset}
                      >
                        Clear Preset
                      </button>
                    </div>
                  </div>

                  {availableSpecialistPresets.length > 0 && (
                    <div className="specialist-preset-grid">
                      {availableSpecialistPresets.map((preset) => {
                        const isActive = selectedSpecialistPreset === preset.id;
                        return (
                          <button
                            key={preset.id}
                            type="button"
                            className={`specialist-preset-card ${isActive ? 'selected' : ''}`}
                            onClick={() => applySpecialistPreset(preset)}
                            title={preset.summary}
                          >
                            <span>{preset.domain}</span>
                            <strong>{preset.label}</strong>
                            <p>{preset.summary}</p>
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {selectedSpecialistObjects.length > 0 && (
                    <div className="selected-specialist-strip">
                      {selectedSpecialistObjects.map((specialist) => (
                        <button
                          key={`selected-${specialist.id}`}
                          type="button"
                          className="specialist-chip selected"
                          onClick={() => toggleSpecialist(specialist.id)}
                          title={specialist.purpose}
                        >
                          <strong>{specialist.label}</strong>
                          <span>{specialist.domain}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="specialist-domain-grid">
                    {availableSpecialistDomains.length === 0 ? (
                      <p className="session-empty">No specialists loaded yet.</p>
                    ) : (
                      availableSpecialistDomains.map((domain) => (
                        <div key={domain.id} className="specialist-domain-card">
                          <span>{domain.label}</span>
                          <div className="specialist-chip-grid">
                            {(domain.specialists || []).map((specialist) => {
                              const isSelected = selectedSpecialists.includes(specialist.id);
                              return (
                                <button
                                  key={specialist.id}
                                  type="button"
                                  className={`specialist-chip ${isSelected ? 'selected' : ''}`}
                                  onClick={() => toggleSpecialist(specialist.id)}
                                  title={specialist.purpose}
                                >
                                  <strong>{specialist.label}</strong>
                                  <span>{specialist.purpose}</span>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className="jarvis-compose-actions">
              <div className="compose-meta">
                <span>{activePersona} persona</span>
                <span>{getResponseModeLabel(selectedResponseMode)} selected</span>
                <span>{getProviderLabel(selectedProvider, availableProviders)} provider</span>
                <span>{selectedSpecialistPresetObject ? `${selectedSpecialistPresetObject.label} preset` : `${selectedSpecialists.length || 0} specialists pinned`}</span>
                <span>{conversationLane === 'documents' ? `intake ${documents.length} docs` : 'direct chat lane'}</span>
                <span>{draft.length} chars</span>
                <span>Ctrl/Cmd + Enter</span>
              </div>
              <div className="compose-button-cluster">
                <button
                  type="button"
                  className="jarvis-secondary-button"
                  onClick={handleVoiceCapture}
                  disabled={!profile.voiceInputEnabled || booting}
                >
                  {voiceSupported ? <FiMic /> : <FiMicOff />}
                  Voice
                </button>
                <button
                  type="button"
                  className={`toggle-pill ${profile.liveResearchEnabled ? 'active' : ''}`}
                  onClick={() => setProfile((current) => ({
                    ...current,
                    liveResearchEnabled: !current.liveResearchEnabled,
                  }))}
                >
                  <FiGlobe />
                  {profile.liveResearchEnabled ? 'Live Research On' : 'Live Research Off'}
                </button>
                <button
                  type="button"
                  className="jarvis-primary-button"
                  onClick={() => handleSend()}
                  disabled={sending || booting}
                >
                  {conversationLane === 'documents' ? 'Ask Intake' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        </div>

        <aside className="jarvis-side-panel">
          <div className="jarvis-side-card page-panel side-panel-category-card">
            <div className="jarvis-side-title">
              <FiCommand />
              <h3>Jarvis Control Panel</h3>
            </div>
            <div className="jarvis-tab-row side-panel-tab-row">
              {sidePanelTabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={`jarvis-tab-button ${activeSideTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveSideTab(tab.id)}
                >
                  <strong>{tab.label}</strong>
                </button>
              ))}
            </div>
            <p className="session-empty side-panel-category-summary">
              Authority, approvals, routing, logs, and governance live here. {activeSideTabObject.summary}
            </p>
          </div>

          {showConversationPanel && (
            <div className="jarvis-side-card page-panel">
              <div className="jarvis-side-title">
                <FiFolder />
                <h3>Sessions</h3>
              </div>

              <div className="session-list">
                {recentSessions.length === 0 ? (
                  <p className="session-empty">No saved sessions yet.</p>
                ) : (
                  recentSessions.map((session) => (
                    <div
                      key={session.session_id}
                      className={`session-item ${session.session_id === sessionId ? 'active' : ''}`}
                    >
                      <button
                        type="button"
                        className="session-main"
                        onClick={() => handleLoadSession(session.session_id)}
                      >
                        <strong>{session.session_id.slice(0, 8)}</strong>
                        <span>
                          {(session.session_state?.state || 'idle')} state · {(session.active_mode || 'explore')} mode
                        </span>
                        <span>
                          {(session.persona_mode || 'builder')} persona · {getResponseModeLabel(session.response_mode || 'fast')} mode · {(session.policy_posture || 'nominal')} policy
                        </span>
                        <span>{session.current_goal || `${session.turn_count} turns`}</span>
                        <span>{formatRelativeTime(session.updated_at)}</span>
                      </button>
                      <button
                        type="button"
                        className="session-delete"
                        onClick={() => handleDeleteSession(session.session_id)}
                        aria-label="Delete session"
                      >
                        <FiTrash2 />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {showReasoningPanel && (
          <div className="jarvis-side-card page-panel">
            <div className="jarvis-side-title">
              <FiActivity />
              <h3>Spiral State</h3>
            </div>

            <div className="spiral-state-grid">
              {spiralMetrics.map((metric) => (
                <div key={metric.label} className="spiral-metric">
                  <span>{metric.label}</span>
                  <strong>{Math.round(Number(metric.value || 0) * 100)}%</strong>
                </div>
              ))}
            </div>

            <div className="spiral-goal-block">
              <span>Current goal</span>
              <strong>{sessionRuntime.currentGoal}</strong>
              <p>{sessionRuntime.spiralState.last_reflection}</p>
            </div>

            {sessionRuntime.memorySummary.recent_topics?.length > 0 && (
              <div className="spiral-chip-row">
                {sessionRuntime.memorySummary.recent_topics.map((topic) => (
                  <span key={topic} className="spiral-chip">{topic}</span>
                ))}
              </div>
            )}

            {sessionRuntime.memorySummary.active_projects?.length > 0 && (
              <div className="spiral-memory-list">
                <span>Active threads</span>
                <p>{sessionRuntime.memorySummary.active_projects.join(' | ')}</p>
              </div>
            )}

            {preferenceEntries.length > 0 && (
              <div className="spiral-memory-list">
                <span>Operator preferences</span>
                <p>{preferenceEntries.map(([key, value]) => `${key}: ${value}`).join(' | ')}</p>
              </div>
            )}

            {activeResponseTrace && (
              <div className="spiral-memory-list">
                <span>Response contract</span>
                <p>{activeResponseTrace.summary}</p>
                {activeResponseTrace.specialist_domain && activeResponseTrace.specialist_focus ? (
                  <p>
                    Specialist focus:
                    {' '}
                    {activeResponseTrace.specialist_domain}
                    {' / '}
                    {activeResponseTrace.specialist_focus.replace(/_/g, ' ')}
                  </p>
                ) : null}
                {activeResponseTrace.specialist_lenses?.length > 0 ? (
                  <p>
                    Specialist lenses:
                    {' '}
                    {activeResponseTrace.specialist_lenses.map((lens) => lens.label).join(' | ')}
                  </p>
                ) : null}
                {activeResponseTrace.specialist_selection_source ? (
                  <p>
                    Specialist selection:
                    {' '}
                    {activeResponseTrace.specialist_selection_source}
                  </p>
                ) : null}
                {activeResponseTrace.plan_summary ? (
                  <code>{activeResponseTrace.plan_summary}</code>
                ) : null}
              </div>
            )}
          </div>
          )}

          {showReasoningPanel && (
          <ComposeReceiptPanel
            receipt={composeReceipt}
            title="Composed turn"
            compact
          />
          )}

          {showReasoningPanel && (
          <V8RuntimeCard
            sessionRuntime={sessionRuntime}
            latestEvent={latestSessionEvent}
            eventCount={sessionEvents.length}
            onRefresh={() => refreshSessionEvents()}
            eventsBusy={eventsBusy}
            onAdoptRecommendedMode={(modeId) => setProfile((current) => applyResponseModeProfileSelection(current, modeId))}
          />
          )}

          {showConversationPanel && (
          <MissionBoardCard
            missionBoard={missionBoard}
            titleDraft={missionTitleDraft}
            objectiveDraft={missionObjectiveDraft}
            nextStepDraft={missionNextStepDraft}
            busy={missionBusy}
            onCreatePreset={handleCreateMissionPreset}
            onApplyCriticSuggestion={handleApplyMissionCriticSuggestion}
            onTitleChange={setMissionTitleDraft}
            onObjectiveChange={setMissionObjectiveDraft}
            onNextStepChange={setMissionNextStepDraft}
            onCreateMission={handleCreateMission}
            onRefresh={() => refreshMissionBoard(sessionId)}
            onFocusMission={handleFocusMission}
            onSetMissionStatus={handleSetMissionStatus}
            onDeleteMission={handleDeleteMission}
            onAppendDraftContext={appendDraftContext}
            onOpenFile={loadFilePreview}
          />
          )}

          {showReasoningPanel && (
          <V8EventFeed
            events={sessionEvents}
            formatRelativeTime={formatRelativeTime}
          />
          )}

          {showOperatorPanel && (
          <div className="jarvis-side-card page-panel">
            <div className="jarvis-side-title">
              <FiCommand />
              <h3>Operator Actions</h3>
            </div>

            <p className="session-empty">
              Repo-safe local actions that require approval before they run.
            </p>

            <div className="action-list">
              {availableActions.length === 0 ? (
                <p className="session-empty">No operator actions loaded.</p>
              ) : (
                availableActions.map((action) => (
                  <div key={action.id} className="action-item">
                    <div className="action-main">
                      <strong>{action.label}</strong>
                      <span>{action.description}</span>
                      <code>{action.command_preview}</code>
                    </div>
                    <button
                      type="button"
                      className="jarvis-secondary-button action-run-button"
                      onClick={() => handleRunAction(action)}
                      disabled={actionBusyId === action.id}
                    >
                      <FiCommand />
                      {actionBusyId === action.id ? 'Running' : 'Run'}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
          )}

          {showOperatorPanel && (
          <SystemGuardCard
            systemGuard={systemGuard}
            busy={guardBusy}
            onAction={handleSystemGuardAction}
          />
          )}

          {showOperatorPanel && (
          <SecurityProtocolCard
            securityProtocol={securityProtocol}
          />
          )}

          {showOperatorPanel && (
          <ImmuneSystemCard
            immuneSystem={immuneSystem}
          />
          )}

          {showOperatorPanel && (
          <GovernanceCard
            governance={governance}
          />
          )}

          {showOperatorPanel && (
          <UGRCloudForgeConsoleCard />
          )}

          {showOperatorPanel && (
          <ModuleGovernanceCard
            moduleGovernance={moduleGovernance}
          />
          )}

          {showReasoningPanel && (
          <ContinuityProfileCard
            continuityProfile={continuityProfile}
          />
          )}

          {showReasoningPanel && (
          <CorrigibilityCard
            corrigibility={corrigibility}
            onAppendDraftContext={appendDraftContext}
          />
          )}

          {showConversationPanel && (
          <DreamspaceCard
            dreamspace={dreamspace}
            presentation={dreamspacePresentation}
            busy={dreamspaceBusy}
            onAction={handleDreamspaceAction}
            onAppendDraftContext={appendDraftContext}
            formatRelativeTime={formatRelativeTime}
          />
          )}

          {showConversationPanel && (
          <MysticConsoleCard
            prompt={mysticPrompt}
            onPromptChange={setMysticPrompt}
            onRun={handleRunMysticReading}
            onStagePrompt={handleStageMysticPrompt}
            busy={sending || booting}
            latestToolResult={latestMysticToolResult}
            onOpenFile={loadFilePreview}
            onSearchWorkspace={handleWorkspaceSearch}
            onAppendDraftContext={appendDraftContext}
            onRunAction={handleRunAction}
            actionBusyId={actionBusyId}
          />
          )}

          {showConversationPanel && (
          <V10CoreConsoleCard
            prompt={v10Prompt}
            onPromptChange={setV10Prompt}
            onRun={handleRunV10Core}
            onStagePrompt={handleStageV10Prompt}
            busy={sending || booting}
            latestToolResult={latestV10ToolResult}
            onOpenFile={loadFilePreview}
            onSearchWorkspace={handleWorkspaceSearch}
            onAppendDraftContext={appendDraftContext}
            onRunAction={handleRunAction}
            actionBusyId={actionBusyId}
          />
          )}

          {showConversationPanel && (
          <CreativeRuntimeCard
            label="V9 Runtime"
            runtime={v9Runtime}
            formatRelativeTime={formatRelativeTime}
          />
          )}

          {showConversationPanel && (
          <CreativeRuntimeCard
            label="V10 Runtime"
            runtime={v10Runtime}
            formatRelativeTime={formatRelativeTime}
          />
          )}

          {showCodingPanel && (
          <PatchReviewCard
            reviews={patchReviews}
            preview={patchPreview}
            previewBusy={patchPreviewBusy}
            actionBusyId={actionBusyId}
            onRefresh={() => refreshPatchReviews(sessionId)}
            onPreview={handlePreviewPatchReview}
            onApply={handleApplyPatchReview}
            formatRelativeTime={formatRelativeTime}
          />
          )}

          {showCodingPanel && (
          <BrowserVerificationPanel
            targetPath={browserTargetPath}
            expectation={browserExpectation}
            suggestedExpectation={browserExpectationGuide}
            quickTargets={quickBrowserTargets}
            activeTargetKey={activeBrowserTargetKey}
            suiteBusy={browserSuiteBusy}
            suiteResults={browserSuiteResults}
            verification={browserVerification}
            busy={browserBusy}
            onTargetPathChange={setBrowserTargetPath}
            onExpectationChange={setBrowserExpectation}
            onUseSuggestedExpectation={() => setBrowserExpectation(browserExpectationGuide?.expectation || '')}
            onRunQuickTarget={handleQuickBrowserVerify}
            onVerifyAll={handleVerifyAllCoreRoutes}
            onVerify={handleBrowserVerify}
            onOpenFile={loadFilePreview}
            onRunAction={handleRunAction}
            onSearchWorkspace={handleWorkspaceSearch}
            onAppendDraftContext={appendDraftContext}
            actionBusyId={actionBusyId}
          />
          )}

          {showConversationPanel && (
          <div className="jarvis-side-card page-panel">
            <div className="jarvis-side-title">
              <FiBookmark />
              <h3>Memory Bank</h3>
            </div>

            <div className="memory-compose">
              <p className="memory-bank-copy">
                Save quick durable notes here, then use the dedicated Memory Bank to rewrite,
                deactivate, or override memory cleanly.
              </p>
              <textarea
                value={memoryDraft}
                onChange={(event) => setMemoryDraft(event.target.value)}
                placeholder="Capture a durable note for Jarvis..."
                rows="3"
              />
              <div className="memory-compose-row compact">
                <button
                  type="button"
                  className="jarvis-primary-button"
                  onClick={handleSaveMemory}
                  disabled={savingMemory || !memoryDraft.trim()}
                >
                  <FiPlus />
                  {savingMemory ? 'Saving' : 'Quick Save'}
                </button>
                <Link to="/memory" className="jarvis-secondary-link-button">
                  Open Memory Bank
                </Link>
              </div>
            </div>

            <div className="memory-list">
              {memories.length === 0 ? (
                <p className="session-empty">No saved memories yet.</p>
              ) : (
                memories.map((memory) => (
                  <div key={memory.id} className="memory-item">
                    <div className="memory-main">
                      <p>{memory.content || memory.text}</p>
                      <div className="memory-meta">
                        <span>{formatRelativeTime(memory.updated_at)}</span>
                        {memory.category && <span className="memory-pinned-badge">{memory.category}</span>}
                        {memory.pinned && <span className="memory-pinned-badge">Pinned</span>}
                        {memory.override && <span className="memory-pinned-badge warning">Override</span>}
                        {memory.tags?.length > 0 && (
                          <div className="memory-tags">
                            {memory.tags.map((tag) => (
                              <span key={tag} className="memory-tag">{tag}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="memory-actions">
                      <button
                        type="button"
                        className="compact-action-button"
                        onClick={() => appendDraftContext('Saved memory context:', `- ${memory.content || memory.text}`)}
                      >
                        <FiArrowUpRight />
                      </button>
                      <Link to="/memory" className="compact-action-button link">
                        Edit
                      </Link>
                      <button
                        type="button"
                        className="compact-action-button danger"
                        onClick={() => handleDeleteMemory(memory.id)}
                      >
                        <FiTrash2 />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          )}

          {showCodingPanel && (
          <div className="jarvis-side-card page-panel">
            <div className="jarvis-side-title">
              <FiSearch />
              <h3>Workspace Tools</h3>
            </div>

            <div className="workspace-search-row">
              <input
                type="text"
                value={workspaceQuery}
                onChange={(event) => setWorkspaceQuery(event.target.value)}
                onKeyDown={handleWorkspaceKeyDown}
                placeholder="Search files, notes, and code in project infi..."
              />
              <button
                type="button"
                className="jarvis-secondary-button"
                onClick={() => handleWorkspaceSearch()}
                disabled={workspaceBusy}
              >
                <FiSearch />
                Search
              </button>
            </div>

            {workspaceProjects.length > 0 && (
              <div className="workspace-project-grid">
                {workspaceProjects.map((project) => (
                  <button
                    key={project.relative_path}
                    type="button"
                    className="workspace-project"
                    onClick={() => handleProjectOpen(project)}
                  >
                    <strong>{project.name}</strong>
                    <span>{project.summary || 'Open project context'}</span>
                  </button>
                ))}
              </div>
            )}

            <div className="workspace-results">
              {workspaceResults.map((result) => (
                <div key={`${result.relative_path}-${result.kind}`} className="workspace-result">
                  <button
                    type="button"
                    className="workspace-result-main"
                    onClick={() => loadFilePreview(result.relative_path)}
                  >
                    <strong>{result.relative_path}</strong>
                    <span>{result.snippet}</span>
                  </button>
                  <button
                    type="button"
                    className="compact-action-button"
                    onClick={() => appendDraftContext(
                      `Workspace result (${result.relative_path}):`,
                      result.snippet,
                    )}
                  >
                    <FiArrowUpRight />
                  </button>
                </div>
              ))}
            </div>

            {filePreview && (
              <div className="workspace-preview">
                <div className="workspace-preview-header">
                  <div>
                    <span>File preview</span>
                    <strong>{filePreview.relative_path}</strong>
                  </div>
                  <button
                    type="button"
                    className="compact-action-button"
                    onClick={() => appendDraftContext(
                      `File context (${filePreview.relative_path}):`,
                      filePreview.content.slice(0, 1200),
                    )}
                  >
                    <FiArrowUpRight />
                  </button>
                </div>
                <pre>{filePreview.content}</pre>
              </div>
            )}
          </div>
          )}

          {showCodingPanel && (
          <EvolveEngineCard
            snapshot={evolveSnapshot}
            jobTrace={evolveJobTrace}
            jobEvaluations={evolveJobEvaluations}
            hallOfFame={evolveHallOfFame}
            hallOfShame={evolveHallOfShame}
            selectedPreset={evolvePreset}
            busy={evolveBusy}
            refreshBusy={evolveRefreshBusy}
            handoffBusy={evolveHandoffBusy}
            taskDraft={evolveTaskDraft}
            seedDraft={evolveSeedDraft}
            criteriaDraft={evolveCriteriaDraft}
            populationDraft={evolvePopulationDraft}
            generationsDraft={evolveGenerationsDraft}
            onPresetChange={setEvolvePreset}
            onTaskChange={setEvolveTaskDraft}
            onSeedChange={setEvolveSeedDraft}
            onCriteriaChange={setEvolveCriteriaDraft}
            onPopulationChange={setEvolvePopulationDraft}
            onGenerationsChange={setEvolveGenerationsDraft}
            onRun={handleRunEvolveJob}
            onRefresh={() => refreshEvolveDeck().catch(() => {})}
            onHandoff={handleEvolveForgeHandoff}
            onUseCandidate={appendDraftContext}
          />
          )}

          {showReasoningPanel && (
          <AAISBlueprintCard
            blueprint={blueprint}
            protocolSession={protocolSession}
            protocolBusy={protocolBusy}
            busy={blueprintBusy}
            onRefresh={() => {
              refreshBlueprint();
              refreshProtocol(sessionId);
            }}
            onOpenFile={loadFilePreview}
          />
          )}

          {showOperatorPanel && (
          <NetworkStatusCard
            data={networkStatusData}
            providerLabels={networkStatusProviderLabels}
            activeProviderLabel={activeProviderLabel}
            lastUpdatedLabel={formatRelativeTime(networkStatusData?.timestamp)}
            busy={health.status === 'checking'}
            onRefresh={() => {
              refreshHealth().catch(() => {});
              refreshBlueprint().catch(() => {});
            }}
          />
          )}

          {showOperatorPanel && (
          <div className="jarvis-side-card page-panel">
            <div className="jarvis-side-title">
              <FiSettings />
              <h3>Profile</h3>
            </div>

            <label>
              Assistant name
              <input
                type="text"
                value={profile.assistantName}
                onChange={(event) => setProfile((current) => ({
                  ...current,
                  assistantName: event.target.value,
                }))}
              />
            </label>

            <label>
              Operator name
              <input
                type="text"
                value={profile.operatorName}
                onChange={(event) => setProfile((current) => ({
                  ...current,
                  operatorName: event.target.value,
                }))}
              />
            </label>

            <label>
              Core directive
              <textarea
                value={profile.systemPrompt}
                onChange={(event) => setProfile((current) => ({
                  ...current,
                  systemPrompt: event.target.value,
                }))}
                rows="5"
              />
            </label>

            <div className="persona-profile-block">
              <span className="profile-section-label">Assistant persona</span>
              <div className="persona-mode-row compact">
                {personaModes.map((mode) => (
                  <button
                    key={`profile-${mode.id}`}
                    type="button"
                    className={`persona-mode-chip ${activePersona === mode.id ? 'active' : ''}`}
                    onClick={() => setProfile((current) => applyPersonaProfileSelection(current, mode.id))}
                  >
                    <strong>{mode.label}</strong>
                    <span>{mode.blurb}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="persona-profile-block">
              <span className="profile-section-label">Operating mode</span>
              <div className="response-mode-row compact">
                {responseModes.map((mode) => (
                  <button
                    key={`response-${mode.id}`}
                    type="button"
                    className={`response-mode-chip ${selectedResponseMode === mode.id ? 'active' : ''}`}
                    onClick={() => setProfile((current) => applyResponseModeProfileSelection(current, mode.id))}
                  >
                    <strong>{mode.label}</strong>
                    <span>{mode.blurb}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="persona-profile-block">
              <span className="profile-section-label">Provider route</span>
              <div className="provider-row compact">
                {availableProviders.map((provider) => (
                  <button
                    key={`provider-${provider.id}`}
                    type="button"
                    className={`provider-chip ${selectedProvider === provider.id ? 'active' : ''} ${provider.available ? '' : 'offline'}`}
                    onClick={() => pinPreferredProvider(provider.id)}
                  >
                    <strong>{provider.label}</strong>
                    <span>
                      {provider.available
                        ? provider.model || 'ready'
                        : provider.activation_hint || provider.reason || 'offline'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="jarvis-toggle-row">
              <button
                type="button"
                className={`toggle-pill ${profile.voiceInputEnabled ? 'active' : ''}`}
                onClick={() => setProfile((current) => ({
                  ...current,
                  voiceInputEnabled: !current.voiceInputEnabled,
                }))}
              >
                {profile.voiceInputEnabled ? <FiMic /> : <FiMicOff />}
                Voice Input
              </button>

              <button
                type="button"
                className={`toggle-pill ${profile.voiceOutputEnabled ? 'active' : ''}`}
                onClick={() => setProfile((current) => ({
                  ...current,
                  voiceOutputEnabled: !current.voiceOutputEnabled,
                }))}
              >
                {profile.voiceOutputEnabled ? <FiVolume2 /> : <FiVolumeX />}
                Voice Output
              </button>

              <button
                type="button"
                className={`toggle-pill ${profile.liveResearchEnabled ? 'active' : ''}`}
                onClick={() => setProfile((current) => ({
                  ...current,
                  liveResearchEnabled: !current.liveResearchEnabled,
                }))}
              >
                <FiGlobe />
                Live Research
              </button>
            </div>

            <button type="button" className="jarvis-primary-button full" onClick={handleProfileSave}>
              Save Profile
            </button>
          </div>
          )}

          {showOperatorPanel && (
          <div className="jarvis-side-card page-panel">
            <div className="jarvis-side-title">
              <FiCommand />
              <h3>System</h3>
            </div>
            <div className="system-row">
              <span>API</span>
              <strong>{getApiBaseUrl()}</strong>
            </div>
            <div className="system-row">
              <span>Model mode</span>
              <strong>{health.active_model_mode || 'offline'}</strong>
            </div>
            <div className="system-row">
              <span>Session mode</span>
              <strong>{sessionRuntime.activeMode}</strong>
            </div>
            <div className="system-row">
              <span>Persona</span>
              <strong>{activePersona}</strong>
            </div>
            <div className="system-row">
              <span>Operating mode</span>
              <strong>{getResponseModeLabel(activeOperatingMode)}</strong>
            </div>
            <div className="system-row">
              <span>Saved memories</span>
              <strong>{memories.length}</strong>
            </div>
            <div className="system-row">
              <span>Workspace projects</span>
              <strong>{workspaceProjects.length}</strong>
            </div>
            <div className="system-row">
              <span>Voice input</span>
              <strong>
                {profile.voiceInputEnabled ? (voiceSupported ? 'armed' : 'unsupported') : 'disabled'}
              </strong>
            </div>
            <div className="system-row">
              <span>Live research</span>
              <strong>{profile.liveResearchEnabled ? 'enabled' : 'off'}</strong>
            </div>
            <div className="system-row">
              <span>System Guard</span>
              <strong>{getSystemGuardLabel(systemGuard.status)}</strong>
            </div>
            <div className="system-links">
              <Link to="/">Nova Home</Link>
              <Link to="/memory">Memory Bank</Link>
              <Link to="/prompt-lab">Prompt Lab</Link>
              <Link to="/history">Memory Log</Link>
            </div>
          </div>
          )}
        </aside>
      </section>
    </div>
  );
}

export default JarvisConsole;
