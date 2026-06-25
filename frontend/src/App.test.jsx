import React from 'react';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

vi.mock('./lib/amplifyAuth', () => ({
  isAmplifyAuthActive: () => false,
  ensureAmplifySession: async () => '',
  initAmplifyAuth: async () => false,
  refreshAmplifySession: async () => false,
  signOutAmplify: async () => {},
  teardownAmplifyAuth: () => {},
}));

vi.mock('./pages/NovaPage', () => ({
  default: function MockNovaPage() {
    return (
      <main>
        <h1>Small Nova</h1>
        <p>Companion surface under Jarvis authority</p>
      </main>
    );
  },
}));

vi.mock('./pages/NovaCodingAgent', () => ({
  default: function MockNovaCodingAgent() {
    return (
      <main>
        <h1>Nova Coding Agent</h1>
        <p>Continuity cockpit sandbox</p>
      </main>
    );
  },
}));

vi.mock('./pages/JarvisPage', () => ({
  default: function MockJarvisPage() {
    return (
      <main>
        <h1>Jarvis</h1>
        <p>Private command deck / operator console</p>
      </main>
    );
  },
}));

describe('App routing', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/');
  });

  it('keeps Small Nova as the home surface', async () => {
    render(<App />);

    expect(await screen.findByRole('heading', { name: /Small Nova/i })).toBeTruthy();
    expect(screen.getByText(/Companion surface under Jarvis authority/i)).toBeTruthy();
    expect(screen.getByRole('link', { name: /^Categories$/i })).toBeTruthy();
    expect(screen.getByRole('link', { name: /^Console$/i })).toBeTruthy();
    expect(screen.getByRole('link', { name: /^Memory Bank$/i })).toBeTruthy();
  });

  it('renders the coding-agent cockpit without replacing the Nova landing page', async () => {
    window.history.pushState({}, '', '/nova/coding-agent');

    render(<App />);

    expect(await screen.findByRole('heading', { name: /Nova Coding Agent/i })).toBeTruthy();
    expect(screen.getByText(/Continuity cockpit sandbox/i)).toBeTruthy();
    expect(screen.queryByRole('heading', { name: /Small Nova/i })).toBeNull();
  });

  it('jarvis route remains accessible', async () => {
    window.history.pushState({}, '', '/jarvis');

    render(<App />);

    expect(await screen.findByRole('heading', { name: /Jarvis/i })).toBeTruthy();
    expect(screen.getByText(/Private command deck \/ operator console/i)).toBeTruthy();
    expect(screen.getByText(/^Operator Console$/i)).toBeTruthy();
    expect(screen.getByRole('link', { name: /^Memory Bank$/i })).toBeTruthy();
  });
});
