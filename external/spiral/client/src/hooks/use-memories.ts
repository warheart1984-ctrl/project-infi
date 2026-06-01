import { useCallback, useEffect, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Memory } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";

interface UpdateMemoryInput {
  id: string;
  updates: {
    confidenceScore?: number;
    source?: string;
    halfLifeDays?: number;
    requiresConfirmation?: boolean;
    intentBias?: number;
    memoryType?: Memory["memoryType"];
    status?: Memory["status"];
    domain?: Memory["domain"];
  };
}

function normalizeScopeKey(scopeKey: string): string {
  const normalized = scopeKey.trim().toLowerCase();
  return normalized || "local";
}

export function useMemories(scopeKey = "local") {
  const queryClient = useQueryClient();
  const normalizedScopeKey = normalizeScopeKey(scopeKey);
  const queryKey = useMemo(
    () => ["/api/memories", normalizedScopeKey] as const,
    [normalizedScopeKey],
  );

  useEffect(() => {
    queryClient.removeQueries({ queryKey: ["/api/memories"] });
  }, [normalizedScopeKey, queryClient]);

  const memoriesQuery = useQuery<Memory[]>({
    queryKey,
    queryFn: async () => {
      const response = await apiRequest("GET", "/api/memories");
      return response.json() as Promise<Memory[]>;
    },
    staleTime: 5_000,
  });

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey });
  }, [queryClient, queryKey]);

  const updateMutation = useMutation({
    mutationFn: async ({ id, updates }: UpdateMemoryInput) => {
      const response = await apiRequest("PATCH", `/api/memories/${id}`, updates);
      return response.json() as Promise<Memory>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  const confirmMutation = useMutation({
    mutationFn: async (memoryId: string) => {
      const response = await apiRequest("POST", `/api/memories/${memoryId}/confirm`, {});
      return response.json() as Promise<Memory>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  const releaseMutation = useMutation({
    mutationFn: async (memoryId: string) => {
      await apiRequest("DELETE", `/api/memories/${memoryId}`);
      return memoryId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    memories: memoriesQuery.data || [],
    isLoading: memoriesQuery.isLoading,
    isRefreshing: memoriesQuery.isFetching,
    refresh,
    updateMemory: updateMutation.mutateAsync,
    confirmMemory: confirmMutation.mutateAsync,
    releaseMemory: releaseMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    isConfirming: confirmMutation.isPending,
    isReleasing: releaseMutation.isPending,
  };
}

