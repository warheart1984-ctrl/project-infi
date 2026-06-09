import React, { useEffect } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { isAmplifyAuthEnabled } from '../lib/auth';
import { ensureAmplifySession, isAmplifyAuthActive } from '../lib/amplifyAuth';
import './AmplifySignIn.css';

function RedirectAfterSignIn({ returnTo }) {
  useEffect(() => {
    void ensureAmplifySession();
  }, []);

  return <Navigate to={returnTo} replace />;
}

function AmplifySignInUnavailable({ title, detail }) {
  return (
    <div className="amplify-sign-in page-shell">
      <div className="amplify-sign-in__panel page-panel">
        <p className="amplify-sign-in__eyebrow">Operator access</p>
        <h1>{title}</h1>
        <p className="amplify-sign-in__copy">{detail}</p>
        <p className="amplify-sign-in__copy">
          See <code>deploy/amplify/README.md</code> for sandbox deploy steps.
        </p>
        <Link className="amplify-sign-in__link" to="/operator">
          Continue to Operator Console
        </Link>
      </div>
    </div>
  );
}

export default function AmplifySignIn() {
  const location = useLocation();
  const returnTo = location.state?.from?.pathname || '/operator';

  if (!isAmplifyAuthEnabled()) {
    return (
      <AmplifySignInUnavailable
        title="Cognito sign-in is disabled"
        detail="Set VITE_AMPLIFY_AUTH=1 in frontend/.env.local after generating amplify_outputs.json."
      />
    );
  }

  if (!isAmplifyAuthActive()) {
    return (
      <AmplifySignInUnavailable
        title="Cognito is not configured"
        detail="Run npx ampx generate outputs --out-dir ../../frontend/src from deploy/amplify/, then restart the dev server."
      />
    );
  }

  return (
    <div className="amplify-sign-in page-shell">
      <div className="amplify-sign-in__panel page-panel">
        <p className="amplify-sign-in__eyebrow">Operator access</p>
        <h1>Sign in with Cognito</h1>
        <p className="amplify-sign-in__copy">
          Authenticated sessions feed the existing API client with Bearer JWTs.
          Operator and Platform routes require a signed-in Cognito user when Amplify auth is enabled.
        </p>
        <Authenticator
          loginMechanisms={['email']}
          hideSignUp
          socialProviders={[]}
        >
          <RedirectAfterSignIn returnTo={returnTo} />
        </Authenticator>
      </div>
    </div>
  );
}
