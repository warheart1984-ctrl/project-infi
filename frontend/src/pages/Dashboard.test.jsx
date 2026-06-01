import React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from './Dashboard';

const dashboardMocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPatch: vi.fn(),
  apiPost: vi.fn(),
  getApiErrorMessage: vi.fn((error, fallback) => fallback || error?.message || 'Request failed'),
  getActiveJarvisSessionId: vi.fn(() => 'session-otem'),
  toastError: vi.fn(),
  toastSuccess: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  apiGet: dashboardMocks.apiGet,
  apiPatch: dashboardMocks.apiPatch,
  apiPost: dashboardMocks.apiPost,
  getApiErrorMessage: dashboardMocks.getApiErrorMessage,
}));

vi.mock('../lib/jarvis', () => ({
  getActiveJarvisSessionId: dashboardMocks.getActiveJarvisSessionId,
}));

vi.mock('react-hot-toast', () => ({
  default: {
    error: dashboardMocks.toastError,
    success: dashboardMocks.toastSuccess,
  },
}));

function renderDashboard() {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Dashboard />
    </MemoryRouter>,
  );
}

describe('Dashboard OTEM surface', () => {
  beforeEach(() => {
    dashboardMocks.apiGet.mockReset();
    dashboardMocks.apiPatch.mockReset();
    dashboardMocks.apiPost.mockReset();
    dashboardMocks.toastError.mockReset();
    dashboardMocks.toastSuccess.mockReset();

    dashboardMocks.apiGet.mockImplementation((path) => {
      if (path === '/api/jarvis/workbench') {
        return Promise.resolve({
          data: {
            patch_reviews: [],
            runs: [],
            mission_board: { missions: [] },
            memory_bank: { summary: {}, memories: [], governance: {} },
            otem: { workflow_catalog: [], tool_registry: [], execution_boundaries: [] },
            forge: { contractor: { kinds: [], latest: null }, evaluator: { modes: [], latest: null } },
            knowledge_authority: {
              active_authorities: [],
              preferences: {},
              presets: [],
              summary: {},
              conflict_policy: {},
              conflict_inbox: [],
              surface_priority: {},
              sovereignty_guard: {},
            },
            state_hygiene: { truth_scope: 'live', memory: {}, reviews: {}, runs: {}, governance: {} },
            governance: { active_break_glass: {}, open_policy_requests: [], recent_events: [] },
            workspace_lane: { profile: {}, projects: [] },
            health: {},
            execution_cockpit: {},
          },
        });
      }
      if (path === '/api/jarvis/state-hygiene') {
        return Promise.resolve({
          data: { state_hygiene: { truth_scope: 'live', memory: {}, reviews: {}, runs: {}, governance: {} } },
        });
      }
      if (path === '/api/chat/sessions/session-otem') {
        return Promise.resolve({
          data: {
            session_id: 'session-otem',
            turns: [],
            state_snapshots: [],
            response_trace: {},
            mode_guidance: {},
            turn_contract: {},
            thread_contract: {},
            drift_state: {},
            sovereignty_contract: {},
            provider_notice: {},
            authority_preferences: {},
            otem_state: {
              status: 'rejected',
              task: 'do stuff',
              restated_task: 'Handle this operator task: do stuff.',
              rejection_reason: 'Task is too vague to produce a deterministic plan.',
              allowed_alternative: 'Provide a specific, outcome-focused task.',
              plan: [],
              session_context: {
                active: false,
                operation: 'rejected',
                note: "No plan was generated. This preserves OTEM's reasoning-only contract.",
                plan: [],
              },
              execution_awareness: { recommendations: [] },
              workflow_handoff: null,
              tool_awareness: { suggestions: [] },
            },
          },
        });
      }
      return Promise.resolve({ data: {} });
    });
  });

  afterEach(() => {
    cleanup();
  });

  it('renders OTEM rejection state with reason and allowed alternative', async () => {
    renderDashboard();

    expect(await screen.findByTestId('otem-rejection')).toBeTruthy();
    expect(screen.getByText(/OTEM rejected this task before planning/i)).toBeTruthy();
    expect(screen.getByText(/Task is too vague to produce a deterministic plan/i)).toBeTruthy();
    expect(screen.getByText(/Allowed alternative: Provide a specific, outcome-focused task/i)).toBeTruthy();
    expect(screen.getByTestId('otem-no-plan')).toBeTruthy();
  });
});
