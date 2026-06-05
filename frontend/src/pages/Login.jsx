import React, { useEffect, useMemo, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiGet, apiPost, getApiErrorMessage } from '../lib/api';
import { cacheAuthStatus, clearTokens, setTokens } from '../lib/auth';
import './Login.css';

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const nextPath = useMemo(() => {
    const params = new URLSearchParams(location.search);
    const next = params.get('next');
    return next && next.startsWith('/') ? next : '/jarvis';
  }, [location.search]);

  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [registrationAllowed, setRegistrationAllowed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    apiGet('/auth/status', { skipAuth: true })
      .then((response) => {
        if (!active) {
          return;
        }
        const status = response.data || {};
        cacheAuthStatus(status);
        setRegistrationAllowed(Boolean(status.registration_allowed));
        if (status.authenticated) {
          navigate(nextPath, { replace: true });
        }
      })
      .catch(() => {
        if (active) {
          setRegistrationAllowed(true);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [navigate, nextPath]);

  const submit = async (event) => {
    event.preventDefault();
    if (!username.trim() || !password) {
      toast.error('Enter a username and password.');
      return;
    }

    setBusy(true);
    try {
      const path = mode === 'register' ? '/auth/register' : '/auth/login';
      const response = await apiPost(path, { username: username.trim(), password }, { skipAuth: true });
      setTokens(response.data || {});
      cacheAuthStatus({ auth_required: true, authenticated: true, user: response.data?.user });
      toast.success(mode === 'register' ? 'Account created.' : 'Signed in.');
      navigate(nextPath, { replace: true });
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Authentication failed'));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="login-page page-shell page-shell--loading" role="status" aria-live="polite">
        <div className="page-shell__content">Checking sign-in state...</div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-shell page-panel">
        <div className="login-copy">
          <p className="login-eyebrow">AAIS Operator</p>
          <h1>{mode === 'register' ? 'Create operator account' : 'Sign in to continue'}</h1>
          <p>
            Use your operator credentials to access workflows, Jarvis console routes, and protected API surfaces.
          </p>
        </div>

        <form className="login-form" onSubmit={submit}>
          <label>
            Username
            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="operator.name"
              disabled={busy}
            />
          </label>

          <label>
            Password
            <input
              type="password"
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Minimum 8 characters"
              disabled={busy}
            />
          </label>

          <button type="submit" className="login-submit" disabled={busy}>
            {busy ? 'Working...' : mode === 'register' ? 'Create account' : 'Sign in'}
          </button>

          {registrationAllowed ? (
            <button
              type="button"
              className="login-toggle"
              onClick={() => setMode((current) => (current === 'login' ? 'register' : 'login'))}
              disabled={busy}
            >
              {mode === 'login' ? 'Need an account? Register' : 'Already have an account? Sign in'}
            </button>
          ) : null}
        </form>
      </div>
    </div>
  );
}

export default Login;
