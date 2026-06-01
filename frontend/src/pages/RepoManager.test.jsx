import React from 'react';
import { act } from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import RepoManager from './RepoManager';

const repoManagerMocks = vi.hoisted(() => ({
  apiPost: vi.fn(),
  getApiErrorMessage: vi.fn((error, fallback) => fallback || error?.message || 'Request failed'),
  getActiveJarvisSessionId: vi.fn(() => 'session-repo-manager'),
  setPendingJarvisDraft: vi.fn(),
  navigate: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  apiPost: repoManagerMocks.apiPost,
  getApiErrorMessage: repoManagerMocks.getApiErrorMessage,
}));

vi.mock('../lib/jarvis', () => ({
  getActiveJarvisSessionId: repoManagerMocks.getActiveJarvisSessionId,
  setPendingJarvisDraft: repoManagerMocks.setPendingJarvisDraft,
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: repoManagerMocks.toastSuccess,
    error: repoManagerMocks.toastError,
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => repoManagerMocks.navigate,
  };
});

function renderRepoManager() {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <RepoManager />
    </MemoryRouter>,
  );
}

describe('RepoManager', () => {
  beforeEach(() => {
    repoManagerMocks.apiPost.mockReset();
    repoManagerMocks.getApiErrorMessage.mockClear();
    repoManagerMocks.getActiveJarvisSessionId.mockClear();
    repoManagerMocks.setPendingJarvisDraft.mockReset();
    repoManagerMocks.navigate.mockReset();
    repoManagerMocks.toastSuccess.mockReset();
    repoManagerMocks.toastError.mockReset();
    Object.defineProperty(window.navigator, 'clipboard', {
      value: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
      configurable: true,
    });
  });

  afterEach(() => {
    cleanup();
  });

  it('shows the operator boundary and hard scope controls at a glance', () => {
    renderRepoManager();

    expect(screen.getByText('Repo Manager inspects and proposes. Forge executes only after explicit handoff.')).toBeTruthy();
    expect(screen.getByText('What this lane can do')).toBeTruthy();
    expect(screen.getByText('What it cannot do')).toBeTruthy();
    expect(screen.getByText('Why the result is inspectable')).toBeTruthy();
    expect(screen.getByTestId('repo-manager-objective')).toBeTruthy();
    expect(screen.getByTestId('repo-manager-max-files')).toBeTruthy();
    expect(screen.getByTestId('repo-manager-max-depth')).toBeTruthy();
    expect(screen.getByTestId('repo-manager-no-execution')).toBeTruthy();
  });

  it('submits a structured request and renders panelized results', async () => {
    repoManagerMocks.apiPost.mockResolvedValueOnce({
      data: {
        task_id: 'repo-pass-1',
        task: 'Inspect the evolve boundary',
        kind: 'repo_manager',
        result: {
          ok: true,
          task_id: 'repo-pass-1',
          kind: 'repo_manager',
          result: {
            repo_manager: {
              repo_summary: 'The boundary is mostly clean but one contract seam needs tightening.',
              target_scope: 'src/api.py + src/jarvis_operator.py',
              focus_files: ['src/api.py', 'src/jarvis_operator.py'],
              risks: [
                {
                  file: 'src/api.py',
                  issue: 'Route and contractor context could drift.',
                  evidence: 'The route forwards scope data directly into the Forge bridge.',
                  confidence: 'medium',
                },
              ],
              plan: [
                {
                  step: 'Inspect the route contract',
                  file: 'src/api.py',
                  purpose: 'Confirm the request fields stay aligned.',
                  expected_effect: 'Keep the repo-manager lane bounded.',
                  rollback_note: 'Revert the route-only change.',
                  validation: 'Run the focused forge route tests.',
                },
              ],
              validations: ['Run focused forge route tests'],
              execution_ready: false,
            },
          },
        },
        auto_approve: false,
        forge_context: {
          target_scope: 'src/api.py + src/jarvis_operator.py',
          focus_files: ['src/api.py', 'src/jarvis_operator.py'],
          file_path_allowlist: ['src/*'],
          max_directory_depth: 2,
        },
        workspace_context: {
          project_scope: 'AAIS-main',
          files: [{ relative_path: 'src/api.py' }, { relative_path: 'src/jarvis_operator.py' }],
        },
      },
    });

    renderRepoManager();

    fireEvent.change(screen.getByTestId('repo-manager-objective'), {
      target: { value: 'Inspect the evolve boundary' },
    });
    fireEvent.change(screen.getByTestId('repo-manager-target-scope'), {
      target: { value: 'src/api.py + src/jarvis_operator.py' },
    });
    fireEvent.change(screen.getByTestId('repo-manager-allowed-files'), {
      target: { value: 'src/api.py\nsrc/jarvis_operator.py' },
    });
    fireEvent.change(screen.getByTestId('repo-manager-excluded-files'), {
      target: { value: 'frontend/src/App.jsx' },
    });
    fireEvent.change(screen.getByTestId('repo-manager-validation-target'), {
      target: { value: 'route parity' },
    });
    fireEvent.change(screen.getByTestId('repo-manager-max-files'), {
      target: { value: '3' },
    });
    fireEvent.change(screen.getByTestId('repo-manager-max-depth'), {
      target: { value: '2' },
    });
    fireEvent.change(screen.getByTestId('repo-manager-allowlist'), {
      target: { value: 'src/*' },
    });
    fireEvent.change(screen.getByTestId('repo-manager-denylist'), {
      target: { value: 'frontend/*' },
    });

    fireEvent.click(screen.getByRole('button', { name: /run inspection/i }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(repoManagerMocks.apiPost).toHaveBeenCalledWith('/api/jarvis/forge/repo-manager', {
      task: 'Inspect the evolve boundary',
      session_id: 'session-repo-manager',
      target_scope: 'src/api.py + src/jarvis_operator.py',
      focus_files: ['src/api.py', 'src/jarvis_operator.py'],
      excluded_files: ['frontend/src/App.jsx'],
      change_intent: 'review_only',
      max_change_budget: 'one narrow seam',
      validation_target: 'route parity',
      operation_mode: 'inspect_only',
      max_files_to_inspect: 3,
      max_directory_depth: 2,
      file_path_allowlist: ['src/*'],
      explicit_denylist: ['frontend/*'],
      no_execution_without_handoff: true,
    });
    expect(screen.getByText('Scope envelope')).toBeTruthy();
    expect(screen.getByText('Focus files')).toBeTruthy();
    expect(screen.getByText('Risks')).toBeTruthy();
    expect(screen.getByText('Smallest safe plan')).toBeTruthy();
    expect(screen.getByText('Validations')).toBeTruthy();
    expect(screen.getByText('Handoff ready')).toBeTruthy();
    expect(screen.getByText('Draft Forge handoff')).toBeTruthy();
    expect(screen.getByText('Copy bounded plan')).toBeTruthy();
  });
});
