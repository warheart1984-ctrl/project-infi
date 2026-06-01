import React from 'react';
import { act } from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import WorkflowRunDetail from './WorkflowRunDetail';

const apiModule = vi.hoisted(() => ({
  apiGet: vi.fn(),
  getApiErrorMessage: vi.fn((error, fallback) => fallback || error?.message || 'Request failed'),
}));

vi.mock('../lib/api', () => ({
  apiGet: apiModule.apiGet,
  getApiErrorMessage: apiModule.getApiErrorMessage,
}));

function renderRunDetail(initialPath = '/workflows/runs/run-1') {
  return render(
    <MemoryRouter
      initialEntries={[initialPath]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/workflows/runs/:runId" element={<WorkflowRunDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('WorkflowRunDetail', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    apiModule.apiGet.mockReset();
    apiModule.getApiErrorMessage.mockClear();
  });

  afterEach(() => {
    cleanup();
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('polls active runs until they complete', async () => {
    apiModule.apiGet
      .mockResolvedValueOnce({
        data: {
          run: {
            id: 'run-1',
            status: 'running',
            created_at: '2026-04-08T00:00:00Z',
            workflow: { name: 'Email Summary to Slack' },
            output: {
              message: 'Running step 1 of 2',
              totalSteps: 2,
              currentStep: 1,
              currentStepLabel: 'Summarize with AI',
              plannedSteps: [],
              steps: [],
            },
          },
        },
      })
      .mockResolvedValueOnce({
        data: {
          run: {
            id: 'run-1',
            status: 'running',
            created_at: '2026-04-08T00:00:00Z',
            workflow: { name: 'Email Summary to Slack' },
            output: {
              message: 'Running step 1 of 2',
              totalSteps: 2,
              currentStep: 1,
              currentStepLabel: 'Summarize with AI',
              plannedSteps: [],
              steps: [],
            },
          },
        },
      })
      .mockResolvedValueOnce({
        data: {
          run: {
            id: 'run-1',
            status: 'completed',
            created_at: '2026-04-08T00:00:00Z',
            workflow: { name: 'Email Summary to Slack' },
            output: {
              message: 'Completed step 2 of 2',
              totalSteps: 2,
              currentStep: 2,
              currentStepLabel: null,
              plannedSteps: [],
              steps: [],
            },
          },
        },
      })
      .mockResolvedValueOnce({
        data: {
          run: {
            id: 'run-1',
            status: 'completed',
            created_at: '2026-04-08T00:00:00Z',
            workflow: { name: 'Email Summary to Slack' },
            output: {
              message: 'Completed step 2 of 2',
              totalSteps: 2,
              currentStep: 2,
              currentStepLabel: null,
              plannedSteps: [],
              steps: [],
            },
          },
        },
      });

    renderRunDetail();

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByText('Running step 1 of 2')).toBeTruthy();
    expect(apiModule.apiGet).toHaveBeenCalledTimes(2);

    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
    });

    expect(apiModule.apiGet).toHaveBeenCalledTimes(4);
    expect(screen.getByText('Completed step 2 of 2')).toBeTruthy();
    expect(screen.getAllByText('completed').length).toBeGreaterThan(0);
  });

  it('shows a clear message when the run has been deleted', async () => {
    apiModule.apiGet.mockRejectedValueOnce({
      response: { status: 404 },
      message: 'Missing',
    });

    renderRunDetail();

    await act(async () => {
      await Promise.resolve();
    });

    expect(screen.getByText('This workflow run no longer exists.')).toBeTruthy();
    expect(screen.getByText('Back to runs')).toBeTruthy();
  });
});
