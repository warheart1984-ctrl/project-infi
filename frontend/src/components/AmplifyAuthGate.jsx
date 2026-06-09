import React, { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { isAmplifyAuthEnabled } from '../lib/auth';
import { ensureAmplifySession, isAmplifyAuthActive } from '../lib/amplifyAuth';

function AuthGateFallback() {
  return (
    <div className="page-shell page-shell--loading" role="status" aria-live="polite">
      <div className="page-shell__content">Checking Cognito session…</div>
    </div>
  );
}

export default function AmplifyAuthGate() {
  const location = useLocation();
  const [checking, setChecking] = useState(true);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function verifySession() {
      if (!isAmplifyAuthEnabled() || !isAmplifyAuthActive()) {
        if (!cancelled) {
          setAuthed(true);
          setChecking(false);
        }
        return;
      }

      const token = await ensureAmplifySession();
      if (!cancelled) {
        setAuthed(Boolean(token));
        setChecking(false);
      }
    }

    void verifySession();
    return () => {
      cancelled = true;
    };
  }, [location.pathname]);

  if (checking) {
    return <AuthGateFallback />;
  }

  if (!authed) {
    return <Navigate to="/auth/sign-in" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
