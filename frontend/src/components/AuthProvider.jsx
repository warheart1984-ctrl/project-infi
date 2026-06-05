import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { apiGet } from '../lib/api';
import {
  cacheAuthStatus,
  clearTokens,
  getCachedAuthStatus,
} from '../lib/auth';

const AuthContext = createContext({
  loading: true,
  authRequired: false,
  authenticated: false,
  user: null,
  refreshAuthStatus: async () => {},
  signOut: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [loading, setLoading] = useState(true);
  const [authRequired, setAuthRequired] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  const refreshAuthStatus = useCallback(async () => {
    try {
      const response = await apiGet('/auth/status');
      const status = response.data || {};
      cacheAuthStatus(status);
      setAuthRequired(Boolean(status.auth_required));
      setAuthenticated(Boolean(status.authenticated));
      setUser(status.user || null);
      return status;
    } catch {
      const cached = getCachedAuthStatus();
      if (cached) {
      setAuthRequired(Boolean(cached.auth_required));
      setAuthenticated(Boolean(cached.authenticated));
        setUser(cached.user || null);
        return cached;
      }
      setAuthRequired(false);
      setAuthenticated(false);
      setUser(null);
      return null;
    }
  }, []);

  const signOut = useCallback(() => {
    clearTokens();
    setAuthenticated(false);
    setUser(null);
    cacheAuthStatus({ auth_required: authRequired, authenticated: false, user: null });
  }, [authRequired]);

  useEffect(() => {
    let active = true;

    refreshAuthStatus().finally(() => {
      if (active) {
        setLoading(false);
      }
    });

    return () => {
      active = false;
    };
  }, [refreshAuthStatus]);

  const value = useMemo(
    () => ({
      loading,
      authRequired,
      authenticated,
      user,
      refreshAuthStatus,
      signOut,
    }),
    [loading, authRequired, authenticated, user, refreshAuthStatus, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AuthGate({ children }) {
  const location = useLocation();
  const { loading, authenticated } = useAuth();

  if (loading) {
    return (
      <div className="page-shell page-shell--loading" role="status" aria-live="polite">
        <div className="page-shell__content">Loading interface...</div>
      </div>
    );
  }

  if (authenticated && location.pathname === '/login') {
    const params = new URLSearchParams(location.search);
    const next = params.get('next');
    return <Navigate to={next && next.startsWith('/') ? next : '/jarvis'} replace />;
  }

  return children;
}
