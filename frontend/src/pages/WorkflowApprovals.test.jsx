import React from 'react';
import { act } from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import WorkflowApprovals from './WorkflowApprovals';

const approvalMocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  getApiErrorMessage: vi.fn((error, fallback) => fallback || error?.message || 'Request failed'),
  navigate: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  apiGet: approvalMocks.apiGet,
  apiPost: approvalMocks.apiPost,
  getApiErrorMessage: approvalMocks.getApiErrorMessage,
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: approvalMocks.toastSuccess,
    error: approvalMocks.toastError,
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => approvalMocks.navigate,
  };
});

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('WorkflowApprovals', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    approvalMocks.apiGet.mockReset();
    approvalMocks.apiPost.mockReset();
    approvalMocks.navigate.mockReset();
    approvalMocks.toastSuccess.mockReset();
    approvalMocks.toastError.mockReset();
    approvalMocks.getApiErrorMessage.mockClear();
  });

  afterEach(() => {
    cleanup();
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('disables approval buttons while an approval action is in flight', async () => {
    const postRequest = deferred();
    approvalMocks.apiGet.mockResolvedValueOnce({
      data: {
        approvals: [
          {
            id: 'approval-1',
            step_label: 'Send to Slack',
            step_type: 'slack.send',
            reason: 'This step posts a message to Slack.',
            payload: { step: { id: 'action-2' } },
            workflow_run_id: 'run-1',
            workflow_run: {
              workflow: {
                name: 'Email Summary to Slack',
              },
            },
          },
        ],
      },
    });
    approvalMocks.apiPost.mockReturnValueOnce(postRequest.promise);

    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <WorkflowApprovals />
      </MemoryRouter>,
    );

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByText(/Email Summary to Slack/)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Approve' }));

    const busyButton = screen.getByRole('button', { name: 'Approving...' });
    expect(busyButton.disabled).toBe(true);
    expect(screen.getByRole('button', { name: 'Reject' }).disabled).toBe(true);

    await act(async () => {
      postRequest.resolve({ data: { ok: true, status: 'approved' } });
      await postRequest.promise;
      await Promise.resolve();
    });

    expect(approvalMocks.navigate).toHaveBeenCalledWith('/workflows/runs/run-1');
    expect(approvalMocks.toastSuccess).toHaveBeenCalledWith('Approval granted');
  });
});
