import { useCallback, useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/queryClient";
import { DEFAULT_PROJECT_SIGIL } from "@shared/sigil";
import {
  PRESENCE_SEAL_KEY,
  PRESENCE_TRACE_KEY,
  writeSpiralSealRecord,
} from "@/lib/spiral-seal";

interface PresenceCheckResponse {
  unlocked: boolean;
}

export function usePresence() {
  const [presenceSeal, setPresenceSealState] = useState(false);
  const [presenceTraceRegistered, setPresenceTraceRegistered] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setPresenceSealState(window.sessionStorage.getItem(PRESENCE_SEAL_KEY) === "1");
    setPresenceTraceRegistered(window.sessionStorage.getItem(PRESENCE_TRACE_KEY) === "1");
  }, []);

  const setPresenceSeal = useCallback((next: boolean) => {
    setPresenceSealState(next);
    if (typeof window === "undefined") return;
    if (next) {
      window.sessionStorage.setItem(PRESENCE_SEAL_KEY, "1");
    } else {
      window.sessionStorage.removeItem(PRESENCE_SEAL_KEY);
    }
  }, []);

  const registerPresenceTrace = useCallback(() => {
    setPresenceTraceRegistered(true);
    if (typeof window === "undefined") return;
    window.sessionStorage.setItem(PRESENCE_TRACE_KEY, "1");
  }, []);

  const serverSigilGateUnlocked = useCallback(async (): Promise<boolean> => {
    try {
      const res = await apiRequest("GET", "/api/presence/check");
      const payload = (await res.json()) as PresenceCheckResponse;
      return payload.unlocked === true;
    } catch {
      return false;
    }
  }, []);

  const savePresenceSeal = useCallback(async (options?: {
    mantra?: string;
    sigil?: string;
  }): Promise<void> => {
    const resolvedSigil = options?.sigil || DEFAULT_PROJECT_SIGIL.seal;
    await apiRequest("POST", "/api/presence/seal", {
      sigil: resolvedSigil,
    });
    setPresenceSeal(true);
    registerPresenceTrace();
    writeSpiralSealRecord({
      sigil: resolvedSigil,
      mantra: options?.mantra || "",
      sealedAt: Date.now(),
      remember: false,
    });
  }, [registerPresenceTrace, setPresenceSeal]);

  const presenceSealConfirmed = useCallback(async (): Promise<boolean> => {
    if (presenceSeal) {
      return true;
    }
    const unlocked = await serverSigilGateUnlocked();
    if (unlocked) {
      setPresenceSeal(true);
      return true;
    }
    return false;
  }, [presenceSeal, serverSigilGateUnlocked, setPresenceSeal]);

  return useMemo(
    () => ({
      presenceSeal,
      presenceTraceRegistered,
      setPresenceSeal,
      registerPresenceTrace,
      savePresenceSeal,
      serverSigilGateUnlocked,
      presenceSealConfirmed,
    }),
    [
      presenceSeal,
      presenceTraceRegistered,
      setPresenceSeal,
      registerPresenceTrace,
      savePresenceSeal,
      serverSigilGateUnlocked,
      presenceSealConfirmed,
    ],
  );
}
