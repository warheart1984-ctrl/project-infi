import { initAmplifyAuth, isAmplifyAuthActive } from './amplifyAuth';
import { isAmplifyAuthEnabled } from './auth';

export async function bootstrapAuth() {
  if (!isAmplifyAuthEnabled()) {
    return { enabled: false, active: false };
  }

  const active = await initAmplifyAuth();
  return { enabled: true, active: active && isAmplifyAuthActive() };
}
