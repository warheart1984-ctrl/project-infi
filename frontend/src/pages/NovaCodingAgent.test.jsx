import React from 'react';
import { act } from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import NovaCodingAgent from './NovaCodingAgent';

const cockpitMocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  getApiErrorMessage: vi.fn((error, fallback) => fallback || error?.message || 'Request failed'),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
}));

vi.mock('../lib/api', () => ({
  apiGet: cockpitMocks.apiGet,
  apiPost: cockpitMocks.apiPost,
  getApiErrorMessage: cockpitMocks.getApiErrorMessage,
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: cockpitMocks.toastSuccess,
    error: cockpitMocks.toastError,
  },
}));

const planEvent = {
  id: 'event-plan',
  name: 'Manual.Plan',
  parentId: null,
  payload: { path: 'notes.txt' },
  createdAt: '2026-06-20T12:00:00Z',
};

const openedEvent = {
  id: 'event-open',
  name: 'File.Opened',
  parentId: 'event-plan',
  payload: { path: 'notes.txt' },
  createdAt: '2026-06-20T12:01:00Z',
};

const savedEvent = {
  id: 'event-save',
  name: 'File.Saved',
  parentId: 'event-open',
  payload: { path: 'notes.txt' },
  createdAt: '2026-06-20T12:02:00Z',
};

describe('NovaCodingAgent', () => {
  beforeEach(() => {
    cockpitMocks.apiGet.mockReset();
    cockpitMocks.apiPost.mockReset();
    cockpitMocks.toastSuccess.mockReset();
    cockpitMocks.toastError.mockReset();
    cockpitMocks.getApiErrorMessage.mockClear();

    cockpitMocks.apiGet.mockImplementation((path, config) => {
      if (path === '/api/continuity/events') {
        return Promise.resolve({ data: { events: [planEvent] } });
      }
      if (path === '/api/continuity/lineage/event-plan') {
        return Promise.resolve({
          data: {
            event: planEvent,
            lineage: [
              { depth: 0, event: planEvent },
            ],
          },
        });
      }
      if (path === '/api/continuity/lineage/event-save') {
        return Promise.resolve({
          data: {
            event: savedEvent,
            lineage: [
              { depth: 0, event: savedEvent },
              { depth: 1, event: openedEvent },
            ],
          },
        });
      }
      if (path === '/api/continuity/receipts') {
        expect(config).toEqual({ params: expect.objectContaining({ eventId: expect.any(String) }) });
        return Promise.resolve({ data: { receipts: [] } });
      }
      return Promise.reject(new Error(`Unhandled GET ${path}`));
    });

    cockpitMocks.apiPost.mockImplementation((path, payload, config) => {
      if (path === '/api/continuity/file/open') {
        expect(payload).toEqual({ path: 'notes.txt' });
        expect(config).toBeUndefined();
        return Promise.resolve({
          data: {
            path: 'notes.txt',
            content: 'first draft',
            event: openedEvent,
          },
        });
      }
      if (path === '/api/continuity/file/save') {
        expect(payload).toEqual({ path: 'notes.txt', content: 'second draft' });
        return Promise.resolve({
          data: {
            path: 'notes.txt',
            event: savedEvent,
          },
        });
      }
      if (path === '/api/continuity/receipts') {
        expect(payload).toEqual({ eventId: 'event-save', status: 'PASS', details: 'operator accepted patch' });
        return Promise.resolve({
          data: {
            receipt: {
              id: 'receipt-1',
              eventId: 'event-save',
              status: 'PASS',
              details: 'operator accepted patch',
              createdAt: '2026-06-20T12:03:00Z',
            },
          },
        });
      }
      return Promise.reject(new Error(`Unhandled POST ${path}`));
    });
  });

  it('loads timeline events and drives file continuity through open, save, lineage, and receipt', async () => {
    render(<NovaCodingAgent />);

    expect(await screen.findByRole('heading', { name: /NOVA STUDIO/i })).toBeTruthy();
    expect(screen.getByText(/Full Operational Cockpit/i)).toBeTruthy();
    expect(screen.getByText(/CKCE-1 ENFORCEMENT/i)).toBeTruthy();
    expect(screen.getByText(/WAVE SIGNATURE/i)).toBeTruthy();
    expect(screen.getByText(/NOVA REASONING CORRIDOR/i)).toBeTruthy();
    expect(screen.getByText(/LIVE EVENT LOG/i)).toBeTruthy();
    expect(screen.getByText(/REPLAY CONTROLS/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /Accept Patch/i })).toBeTruthy();
    expect(screen.getAllByText('Manual.Plan').length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText(/File path/i), {
      target: { value: 'notes.txt' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Open file/i }));

    await screen.findByDisplayValue('first draft');
    expect(screen.getAllByText('File.Opened').length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText(/File content/i), {
      target: { value: 'second draft' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Save file/i }));

    await screen.findAllByText('File.Saved');
    expect(cockpitMocks.toastSuccess).toHaveBeenCalledWith('File saved into continuity');

    const timeline = screen.getByLabelText(/Continuity timeline/i);
    fireEvent.click(within(timeline).getByRole('button', { name: /File\.Saved/i }));

    await act(async () => {
      await Promise.resolve();
    });

    const lineagePanel = screen.getByLabelText(/Selected lineage/i);
    expect(within(lineagePanel).getAllByText('File.Saved').length).toBeGreaterThan(0);
    expect(within(lineagePanel).getByText('File.Opened')).toBeTruthy();

    fireEvent.change(screen.getByLabelText(/Receipt details/i), {
      target: { value: 'operator accepted patch' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Issue receipt/i }));

    await screen.findByText(/operator accepted patch/i);
    expect(cockpitMocks.toastSuccess).toHaveBeenCalledWith('Receipt issued');
  });
});
