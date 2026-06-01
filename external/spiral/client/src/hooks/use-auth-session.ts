import { useCallback, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AuthSession, AuthProvider } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";

const AUTH_ME_QUERY_KEY = ["/api/me"] as const;
const ANONYMOUS_SCOPE_KEY = "local";

function normalizeScopeKey(session: AuthSession | null | undefined): string {
  const explicitPrincipal = session?.principalId?.trim().toLowerCase();
  if (explicitPrincipal) {
    return explicitPrincipal;
  }
  if (session?.authenticated && session.user) {
    const identityId = session.user.identityId.trim().toLowerCase() || "unknown";
    return `auth:${identityId}`;
  }
  return ANONYMOUS_SCOPE_KEY;
}

export function useAuthSession() {
  const queryClient = useQueryClient();

  const meQuery = useQuery<AuthSession>({
    queryKey: [...AUTH_ME_QUERY_KEY],
    queryFn: async () => {
      const response = await fetch("/api/me", {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) {
        throw new Error(`${response.status}: ${response.statusText}`);
      }
      const payload = (await response.json()) as AuthSession;
      return payload;
    },
    staleTime: 30_000,
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest("POST", "/api/auth/logout", {});
      return response.json() as Promise<{ ok: boolean }>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...AUTH_ME_QUERY_KEY] });
    },
  });

  const refreshSession = useCallback(async (): Promise<void> => {
    await queryClient.invalidateQueries({ queryKey: [...AUTH_ME_QUERY_KEY] });
  }, [queryClient]);

  const buildAuthStartUrl = useCallback((provider: AuthProvider): string => {
    const params = new URLSearchParams({ mode: "popup" });
    return `/api/auth/${provider}/start?${params.toString()}`;
  }, []);

  const session = meQuery.data || { authenticated: false };
  const scopeKey = useMemo(() => normalizeScopeKey(session), [session]);

  return {
    session,
    scopeKey,
    isLoading: meQuery.isLoading,
    isRefreshing: meQuery.isFetching,
    isLoggingOut: logoutMutation.isPending,
    buildAuthStartUrl,
    refreshSession,
    logout: logoutMutation.mutateAsync,
  };
}
