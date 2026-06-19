import { Amplify } from 'aws-amplify';
import { fetchAuthSession, signOut } from 'aws-amplify/auth';
import { isAmplifyAuthEnabled } from './auth';

const amplifyOutputsModules = import.meta.glob('../amplify_outputs.json');

let initialized = false;
let initializePromise = null;
let initError = null;

async function loadAmplifyOutputs() {
  const loader = amplifyOutputsModules['../amplify_outputs.json'];
  if (!loader) {
    return null;
  }

  const mod = await loader();
  return mod.default || mod;
}

export function isAmplifyAuthActive() {
  return initialized && !initError;
}

export async function initAmplifyAuth() {
  if (!isAmplifyAuthEnabled()) {
    initialized = false;
    initError = null;
    return false;
  }

  if (initialized) {
    return true;
  }

  if (!initializePromise) {
    initializePromise = loadAmplifyOutputs()
      .then((outputs) => {
        if (!outputs) {
          initialized = false;
          return false;
        }

        Amplify.configure(outputs);
        initialized = true;
        initError = null;
        return true;
      })
      .catch((error) => {
        initialized = false;
        initError = error;
        console.warn('Amplify auth bootstrap failed:', error);
        return false;
      });
  }

  return initializePromise;
}

export async function ensureAmplifySession() {
  if (!isAmplifyAuthEnabled()) {
    return '';
  }

  const active = initialized || (await initAmplifyAuth());
  if (!active) {
    return '';
  }

  try {
    const session = await fetchAuthSession();
    return session.tokens?.idToken?.toString() || session.tokens?.accessToken?.toString() || '';
  } catch {
    return '';
  }
}

export async function refreshAmplifySession() {
  return Boolean(await ensureAmplifySession());
}

export async function signOutAmplify() {
  if (!isAmplifyAuthActive()) {
    return;
  }
  await signOut();
}

export function teardownAmplifyAuth() {
  initialized = false;
  initializePromise = null;
  initError = null;
}
