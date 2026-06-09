import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@aws-amplify/ui-react', () => ({
  Authenticator: ({ children }) => <div data-testid="authenticator">{children}</div>,
}));

vi.mock('@aws-amplify/ui-react/styles.css', () => ({}));

vi.mock('../lib/amplifyAuth', () => ({
  ensureAmplifySession: vi.fn(async () => ''),
  isAmplifyAuthActive: vi.fn(() => false),
}));

import AmplifySignIn from './AmplifySignIn';

describe('AmplifySignIn', () => {
  it('shows disabled state when VITE_AMPLIFY_AUTH is off', () => {
    vi.stubEnv('VITE_AMPLIFY_AUTH', '');

    render(
      <MemoryRouter>
        <AmplifySignIn />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /Cognito sign-in is disabled/i })).toBeTruthy();
    vi.unstubAllEnvs();
  });
});
