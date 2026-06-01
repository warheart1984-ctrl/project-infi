/* @vitest-environment jsdom */

import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import NovaLandingPage from './NovaLandingPage';

const profileStore = vi.hoisted(() => ({
  current: {
    personaMode: 'small_nova',
    responseMode: 'small',
    assistantName: 'Small Nova',
    systemPrompt: 'Nova system prompt',
  },
}));

const superNovaStore = vi.hoisted(() => ({
  current: {
    activation: {
      current_state: 'dormant',
      activation_token_present: false,
      last_watchdog_result: 'not_run',
      last_failure_reasons: [],
    },
    continuity: {
      status: 'not_checked',
      failure_reasons: [],
    },
    trace: [],
    immune_coupling: 'blocked',
  },
}));

const {
  applyPersonaProfileSelection,
  apiGet,
  apiPost,
  apiPostStream,
  clearActiveJarvisSessionId,
  getActiveJarvisSessionId,
  getJarvisProfile,
  mapSessionTurns,
  saveJarvisProfile,
  setActiveJarvisSessionId,
} = vi.hoisted(() => ({
  applyPersonaProfileSelection: vi.fn((profile, personaMode) => ({
    ...(profile || {}),
    personaMode,
    responseMode: personaMode === 'tiny_nova'
      ? 'tiny'
      : personaMode === 'super_nova'
        ? 'governed_full'
        : 'small',
    assistantName: personaMode === 'tiny_nova'
      ? 'Tiny Nova'
      : personaMode === 'super_nova'
        ? 'Super Nova'
        : 'Small Nova',
    systemPrompt: personaMode === 'tiny_nova'
      ? 'Tiny Nova system prompt'
      : personaMode === 'super_nova'
        ? 'Super Nova system prompt'
        : 'Nova system prompt',
  })),
  apiGet: vi.fn(async (path) => {
    if (path === '/health') {
      return {
        data: {
          ai_status: 'initialized',
          active_model_mode: 'mock',
        },
      };
    }

    if (path === '/api/documents') {
      return {
        data: {
          documents: [],
        },
      };
    }

    if (path === '/api/chat/sessions/mock-session/super-nova/status') {
      return {
        data: {
          super_nova: superNovaStore.current,
        },
      };
    }

    return { data: {} };
  }),
  apiPost: vi.fn(async (path) => {
    if (path === '/api/chat/sessions') {
      return {
        data: {
          session_id: 'mock-session',
          turns: [],
        },
      };
    }

    if (path === '/api/chat/sessions/mock-session/super-nova/activate') {
      superNovaStore.current = {
        activation: {
          current_state: 'activation_ready',
          activation_token_present: true,
          last_watchdog_result: 'pass',
          last_failure_reasons: [],
        },
        continuity: {
          status: 'verified',
          failure_reasons: [],
        },
        trace: [{ event_type: 'activation_granted' }],
        immune_coupling: 'blocked',
      };
      return {
        data: {
          super_nova: superNovaStore.current,
        },
      };
    }

    if (path === '/api/chat/sessions/mock-session/super-nova/pause') {
      superNovaStore.current = {
        ...superNovaStore.current,
        activation: {
          ...superNovaStore.current.activation,
          current_state: 'paused',
        },
      };
      return {
        data: {
          super_nova: superNovaStore.current,
        },
      };
    }

    if (path === '/api/chat/sessions/mock-session/super-nova/resume') {
      superNovaStore.current = {
        ...superNovaStore.current,
        activation: {
          ...superNovaStore.current.activation,
          current_state: 'activation_ready',
          activation_token_present: true,
        },
      };
      return {
        data: {
          super_nova: superNovaStore.current,
        },
      };
    }

    if (path === '/api/chat/sessions/mock-session/super-nova/stop') {
      superNovaStore.current = {
        ...superNovaStore.current,
        activation: {
          ...superNovaStore.current.activation,
          current_state: 'stopped',
          activation_token_present: false,
        },
      };
      return {
        data: {
          super_nova: superNovaStore.current,
        },
      };
    }

    return { data: {} };
  }),
  apiPostStream: vi.fn(async (_path, payload, options) => {
    options?.onEvent?.({
      event: 'final',
      response: payload?.persona_mode === 'super_nova'
        ? 'Super Nova stayed inside the governed lane.'
        : 'Small Nova stayed with the loaded session.',
      super_nova: payload?.persona_mode === 'super_nova'
        ? superNovaStore.current
        : undefined,
    });
  }),
  clearActiveJarvisSessionId: vi.fn(),
  getActiveJarvisSessionId: vi.fn(() => ''),
  getJarvisProfile: vi.fn(() => profileStore.current),
  mapSessionTurns: vi.fn(() => []),
  saveJarvisProfile: vi.fn((profile) => {
    profileStore.current = profile;
    return profile;
  }),
  setActiveJarvisSessionId: vi.fn(),
}));

const archiveState = vi.hoisted(() => ({
  entries: [],
  active: null,
  pending: null,
}));

vi.mock('../lib/api', () => ({
  apiGet,
  apiPost,
  apiPostStream,
  getApiErrorMessage: (_error, fallbackMessage) => fallbackMessage,
}));

vi.mock('../lib/jarvis', () => ({
  applyPersonaProfileSelection,
  clearActiveJarvisSessionId,
  consumePendingJarvisDraft: vi.fn(() => null),
  getActiveJarvisSessionId,
  getJarvisProfile,
  mapSessionTurns,
  saveJarvisProfile,
  SMALL_NOVA_ASSISTANT_NAME: 'Small Nova',
  setActiveJarvisSessionId,
  SMALL_NOVA_PERSONA_MODE: 'small_nova',
  SMALL_NOVA_RESPONSE_MODE: 'small',
  SMALL_NOVA_SYSTEM_PROMPT: 'Nova system prompt',
  SUPER_NOVA_ASSISTANT_NAME: 'Super Nova',
  SUPER_NOVA_PERSONA_MODE: 'super_nova',
  SUPER_NOVA_RESPONSE_MODE: 'governed_full',
  SUPER_NOVA_SYSTEM_PROMPT: 'Super Nova system prompt',
  TINY_NOVA_ASSISTANT_NAME: 'Tiny Nova',
  TINY_NOVA_PERSONA_MODE: 'tiny_nova',
  TINY_NOVA_RESPONSE_MODE: 'tiny',
  TINY_NOVA_SYSTEM_PROMPT: 'Tiny Nova system prompt',
}));

vi.mock('../lib/novaSessionArchive', () => ({
  buildDefaultNovaArchiveTitle: vi.fn((assistantName) => `${assistantName} Session`),
  clearActiveNovaSessionArchive: vi.fn(() => {
    archiveState.active = null;
  }),
  consumePendingNovaSessionArchive: vi.fn(() => {
    const value = archiveState.pending;
    archiveState.pending = null;
    return value;
  }),
  getActiveNovaSessionArchive: vi.fn(() => archiveState.active),
  listNovaSessionArchives: vi.fn(async () => archiveState.entries),
  openNovaSessionArchive: vi.fn(async (archiveId) => (
    archiveState.entries.find((entry) => entry.id === archiveId) || archiveState.active
  )),
  saveNovaSessionArchive: vi.fn(async ({ title, assistantName, personaMode, responseMode, passphrase }) => {
    const preview = {
      id: `archive-${archiveState.entries.length + 1}`,
      title,
      assistantName,
      personaMode,
      responseMode,
      messageCount: 2,
      requiresPassphrase: Boolean(passphrase),
      encryptionMode: passphrase ? 'passphrase' : 'device',
      savedAt: '2026-04-16T12:00:00Z',
    };
    archiveState.entries = [preview, ...archiveState.entries];
    return preview;
  }),
  setActiveNovaSessionArchive: vi.fn((archive) => {
    archiveState.active = archive;
    return archive;
  }),
  toLoadedSessionArchivePayload: vi.fn((archive) => ({
    id: archive.id,
    title: archive.title,
    transcript_text: archive.transcriptText,
    excerpt: archive.excerpt,
  })),
}));

function buildDormantSuperNovaState() {
  return {
    activation: {
      current_state: 'dormant',
      activation_token_present: false,
      last_watchdog_result: 'not_run',
      last_failure_reasons: [],
    },
    continuity: {
      status: 'not_checked',
      failure_reasons: [],
    },
    trace: [],
    immune_coupling: 'blocked',
  };
}

describe('Nova landing categories', () => {
  beforeEach(() => {
    profileStore.current = {
      personaMode: 'small_nova',
      responseMode: 'small',
      assistantName: 'Small Nova',
      systemPrompt: 'Nova system prompt',
    };
    superNovaStore.current = buildDormantSuperNovaState();
    applyPersonaProfileSelection.mockClear();
    apiGet.mockClear();
    apiPost.mockClear();
    apiPostStream.mockClear();
    clearActiveJarvisSessionId.mockClear();
    getActiveJarvisSessionId.mockReset();
    getActiveJarvisSessionId.mockReturnValue('');
    getJarvisProfile.mockClear();
    mapSessionTurns.mockReset();
    mapSessionTurns.mockReturnValue([]);
    saveJarvisProfile.mockClear();
    setActiveJarvisSessionId.mockClear();
    archiveState.entries = [];
    archiveState.active = null;
    archiveState.pending = null;
  });

  it('shows the restored Small Nova architecture near the banner', async () => {
    render(
      <MemoryRouter>
        <NovaLandingPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /Ask Small Nova directly/i })).toBeTruthy();
    expect(await screen.findByText(/System Categories/i)).toBeTruthy();
    expect(screen.getAllByText(/^Small Nova$/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/^Console$/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/^Memory$/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/^Tools$/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/^Workflows$/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/^System$/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Jarvis still holds routing, state, and execution authority/i)).toBeTruthy();
  });

  it('bootstraps a Small Nova session on load', async () => {
    render(
      <MemoryRouter>
        <NovaLandingPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(apiPost).toHaveBeenCalledWith('/api/chat/sessions', {
        system_prompt: 'Nova system prompt',
        persona_mode: 'small_nova',
        response_mode: 'small',
      });
    });

    expect(setActiveJarvisSessionId).toHaveBeenCalledWith('mock-session');
  });

  it('reuses an existing Small Nova session instead of creating a new one', async () => {
    getActiveJarvisSessionId.mockReturnValue('existing-small-session');
    apiGet.mockImplementation(async (path) => {
      if (path === '/health') {
        return {
          data: {
            ai_status: 'initialized',
            active_model_mode: 'mock',
          },
        };
      }

      if (path === '/api/documents') {
        return {
          data: {
            documents: [],
          },
        };
      }

      if (path === '/api/chat/sessions/existing-small-session') {
        return {
          data: {
            session_id: 'existing-small-session',
            persona_mode: 'small_nova',
            turns: [],
          },
        };
      }

      return { data: {} };
    });

    render(
      <MemoryRouter>
        <NovaLandingPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(apiGet).toHaveBeenCalledWith('/api/chat/sessions/existing-small-session');
    });

    expect(apiPost).not.toHaveBeenCalledWith('/api/chat/sessions', expect.anything());
    expect(setActiveJarvisSessionId).not.toHaveBeenCalled();
  });

  it('bootstraps Tiny Nova when the saved profile is already on the tiny tier', async () => {
    profileStore.current = {
      personaMode: 'tiny_nova',
      responseMode: 'tiny',
      assistantName: 'Tiny Nova',
      systemPrompt: 'Tiny Nova system prompt',
    };

    render(
      <MemoryRouter>
        <NovaLandingPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /Ask Tiny Nova directly/i })).toBeTruthy();

    await waitFor(() => {
      expect(apiPost).toHaveBeenCalledWith('/api/chat/sessions', {
        system_prompt: 'Tiny Nova system prompt',
        persona_mode: 'tiny_nova',
        response_mode: 'tiny',
      });
    });
  });

  it('switches from Small Nova to Tiny Nova on the live surface', async () => {
    render(
      <MemoryRouter>
        <NovaLandingPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(apiPost).toHaveBeenCalledWith('/api/chat/sessions', {
        system_prompt: 'Nova system prompt',
        persona_mode: 'small_nova',
        response_mode: 'small',
      });
    });

    apiPost.mockClear();

    fireEvent.click(screen.getByRole('button', { name: /Tiny Nova/i }));

    expect(await screen.findByRole('heading', { name: /Ask Tiny Nova directly/i })).toBeTruthy();

    await waitFor(() => {
      expect(apiPost).toHaveBeenCalledWith('/api/chat/sessions', {
        system_prompt: 'Tiny Nova system prompt',
        persona_mode: 'tiny_nova',
        response_mode: 'tiny',
      });
    });

    expect(clearActiveJarvisSessionId).toHaveBeenCalled();
  });

  it('bootstraps Super Nova when the saved profile is already on the governed tier', async () => {
    profileStore.current = {
      personaMode: 'super_nova',
      responseMode: 'governed_full',
      assistantName: 'Super Nova',
      systemPrompt: 'Super Nova system prompt',
    };

    render(
      <MemoryRouter>
        <NovaLandingPage />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /Ask Super Nova directly/i })).toBeTruthy();

    await waitFor(() => {
      expect(apiPost).toHaveBeenCalledWith('/api/chat/sessions', {
        system_prompt: 'Super Nova system prompt',
        persona_mode: 'super_nova',
        response_mode: 'governed_full',
      });
    });

    await waitFor(() => {
      expect(apiGet).toHaveBeenCalledWith('/api/chat/sessions/mock-session/super-nova/status');
    });

    expect(await screen.findByText(/Super Nova Control/i)).toBeTruthy();
    expect(screen.getByText(/Needs activation/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /Activate First/i })).toBeTruthy();
  });

  it('requires activation before Super Nova can send and keeps the governed lane after activation', async () => {
    profileStore.current = {
      personaMode: 'super_nova',
      responseMode: 'governed_full',
      assistantName: 'Super Nova',
      systemPrompt: 'Super Nova system prompt',
    };

    render(
      <MemoryRouter>
        <NovaLandingPage />
      </MemoryRouter>,
    );

    const composer = await screen.findByPlaceholderText(
      /Activate Super Nova, then bring the deeper thread/i,
    );

    fireEvent.change(composer, { target: { value: 'Hold the full shape of this problem.' } });

    const gatedSendButton = screen.getByRole('button', { name: /Activate First/i });
    expect(gatedSendButton.disabled).toBe(true);

    fireEvent.click(screen.getByRole('button', { name: /^Activate$/i }));

    await waitFor(() => {
      expect(apiPost).toHaveBeenCalledWith('/api/chat/sessions/mock-session/super-nova/activate', {});
    });

    await waitFor(() => {
      expect(screen.getByText(/Activation ready/i)).toBeTruthy();
    });

    const sendButton = screen.getByRole('button', { name: /^Send$/i });
    expect(sendButton.disabled).toBe(false);

    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(apiPostStream).toHaveBeenCalledWith(
        '/api/chat/sessions/mock-session/stream',
        expect.objectContaining({
          message: 'Hold the full shape of this problem.',
          persona_mode: 'super_nova',
          response_mode: 'governed_full',
        }),
        expect.any(Object),
      );
    });

    expect(await screen.findByText(/Super Nova stayed inside the governed lane/i)).toBeTruthy();
  });

  it('restores a pending loaded archive onto the Nova surface', async () => {
    archiveState.pending = {
      id: 'archive-7',
      title: 'Loaded gentle session',
      excerpt: 'A saved session excerpt.',
      transcriptText: 'Saved session transcript.',
      assistantName: 'Small Nova',
      personaMode: 'small_nova',
      responseMode: 'small',
      messageCount: 3,
      encryptionMode: 'device',
    };

    render(
      <MemoryRouter>
        <NovaLandingPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/Loaded gentle session/i)).toBeTruthy();
    expect(
      screen.getByText(/Loaded as document context from this device/i),
    ).toBeTruthy();
  });

  it('sends the loaded archive as explicit session context on chat turns', async () => {
    archiveState.pending = {
      id: 'archive-9',
      title: 'Reopened session',
      excerpt: 'Saved session excerpt.',
      transcriptText: 'Saved session transcript.',
      assistantName: 'Small Nova',
      personaMode: 'small_nova',
      responseMode: 'small',
      messageCount: 4,
      encryptionMode: 'device',
    };

    render(
      <MemoryRouter>
        <NovaLandingPage />
      </MemoryRouter>,
    );

    const composer = await screen.findByPlaceholderText(
      /Bring Small Nova the question, the draft, or the feeling/i,
    );
    fireEvent.change(composer, { target: { value: 'Stay with the earlier thread.' } });
    fireEvent.click(screen.getByRole('button', { name: /^Send$/i }));

    await waitFor(() => {
      expect(apiPostStream).toHaveBeenCalledWith(
        '/api/chat/sessions/mock-session/stream',
        expect.objectContaining({
          message: 'Stay with the earlier thread.',
          loaded_session_archive: expect.objectContaining({
            id: 'archive-9',
            title: 'Reopened session',
            transcript_text: 'Saved session transcript.',
          }),
        }),
        expect.any(Object),
      );
    });
  });
});
