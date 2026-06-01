import { useCallback, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  ExternalStorageProvider,
  SaveTranscriptRequest,
  SaveTranscriptResponse,
  StorageLink,
  StorageLinkRequest,
  StoragePointer,
  StorageVaultEntry,
} from "@shared/schema";
import { apiRequest, getSpiralSealHeaders } from "@/lib/queryClient";
import { getClientEnvValue } from "@/lib/client-env";

interface StorageLinksResponse {
  links: StorageLink[];
}

interface StoragePointersResponse {
  pointers: StoragePointer[];
}

interface RestoreTranscriptResponse {
  chatId: string;
  title: string;
  restoredMessages: number;
  activated: boolean;
}

interface StorageVaultResponse {
  entries: StorageVaultEntry[];
}

export function useExternalStorage(scopeKey = "local") {
  const queryClient = useQueryClient();
  const normalizedScopeKey = scopeKey.trim().toLowerCase() || "local";

  useEffect(() => {
    queryClient.removeQueries({ queryKey: ["/api/storage-link"] });
    queryClient.removeQueries({ queryKey: ["/api/storage-pointer"] });
    queryClient.removeQueries({ queryKey: ["/api/storage-vault"] });
  }, [normalizedScopeKey, queryClient]);

  const { data: linksData, isLoading: linksLoading } = useQuery<StorageLinksResponse>({
    queryKey: ["/api/storage-link"],
    queryFn: async () => {
      const res = await fetch("/api/storage-link", {
        method: "GET",
        headers: getSpiralSealHeaders(),
        credentials: "include",
        cache: "no-store",
      });
      if (res.status === 401) {
        return { links: [] } satisfies StorageLinksResponse;
      }
      if (!res.ok) {
        const raw = (await res.text()) || res.statusText;
        throw new Error(`${res.status}: ${raw}`);
      }
      return res.json();
    },
  });

  const links = linksData?.links || [];

  const linkMutation = useMutation({
    mutationFn: async (input: StorageLinkRequest) => {
      const res = await apiRequest("POST", "/api/storage-link", input);
      return res.json() as Promise<{ link: StorageLink }>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/storage-link"] });
    },
  });

  const unlinkMutation = useMutation({
    mutationFn: async (linkId: string) => {
      const res = await apiRequest("DELETE", `/api/storage-link/${linkId}`);
      return res.json() as Promise<{ removed: boolean }>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/storage-link"] });
    },
  });

  const saveTranscriptMutation = useMutation({
    mutationFn: async (input: SaveTranscriptRequest) => {
      const res = await apiRequest("POST", "/api/save-transcript", input);
      return res.json() as Promise<SaveTranscriptResponse>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/storage-pointer"] });
    },
  });

  const restoreTranscriptMutation = useMutation({
    mutationFn: async (input: { transcript: unknown; title?: string; activate?: boolean }) => {
      const res = await apiRequest("POST", "/api/restore-transcript", input);
      return res.json() as Promise<RestoreTranscriptResponse>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/chats"] });
      queryClient.invalidateQueries({ queryKey: ["/api/chats/search"] });
    },
  });

  const listPointers = useCallback(async (options: { chatId?: string; type?: SaveTranscriptRequest["type"] } = {}) => {
    const params = new URLSearchParams();
    if (options.chatId) {
      params.set("chatId", options.chatId);
    }
    if (options.type) {
      params.set("type", options.type);
    }
    const query = params.toString();
    const res = await apiRequest("GET", `/api/storage-pointer${query ? `?${query}` : ""}`);
    const payload = (await res.json()) as StoragePointersResponse;
    return payload.pointers || [];
  }, []);

  const listVaultEntries = useCallback(async (options: {
    sigil?: string;
    provider?: ExternalStorageProvider;
    limit?: number;
  } = {}) => {
    const params = new URLSearchParams();
    if (options.sigil) {
      params.set("sigil", options.sigil);
    }
    if (options.provider) {
      params.set("provider", options.provider);
    }
    if (typeof options.limit === "number" && Number.isFinite(options.limit)) {
      params.set("limit", String(Math.trunc(options.limit)));
    }
    const query = params.toString();
    const res = await fetch(`/api/storage-vault${query ? `?${query}` : ""}`, {
      method: "GET",
      headers: getSpiralSealHeaders(),
      credentials: "include",
      cache: "no-store",
    });
    const raw = await res.text();
    if (!res.ok) {
      let reason = res.statusText;
      if (raw) {
        try {
          const parsed = JSON.parse(raw) as { error?: unknown };
          if (typeof parsed.error === "string" && parsed.error.trim()) {
            reason = parsed.error.trim();
          } else {
            reason = raw;
          }
        } catch {
          reason = raw;
        }
      }
      throw new Error(`${res.status}: ${reason}`);
    }

    let payload: StorageVaultResponse = { entries: [] };
    if (raw.trim()) {
      try {
        payload = JSON.parse(raw) as StorageVaultResponse;
      } catch {
        throw new Error("Invalid storage vault response.");
      }
    }
    return payload.entries || [];
  }, []);

  const resolvePreferredProvider = useCallback((): ExternalStorageProvider | undefined => {
    return links[0]?.provider;
  }, [links]);

  const refreshLinks = useCallback(async (): Promise<void> => {
    await queryClient.invalidateQueries({ queryKey: ["/api/storage-link"] });
  }, [queryClient]);

  const buildGoogleOAuthStartUrl = useCallback((options: { folderId?: string; label?: string } = {}): string => {
    const params = new URLSearchParams();
    const seal = getClientEnvValue("VITE_SPIRAL_API_SEAL").trim();
    if (seal) {
      params.set("seal", seal);
    }
    if (options.folderId) {
      params.set("folderId", options.folderId);
    }
    if (options.label) {
      params.set("label", options.label);
    }
    const query = params.toString();
    return `/api/storage-link/google/start${query ? `?${query}` : ""}`;
  }, []);

  const buildDropboxOAuthStartUrl = useCallback((options: { folderId?: string; label?: string } = {}): string => {
    const params = new URLSearchParams();
    const seal = getClientEnvValue("VITE_SPIRAL_API_SEAL").trim();
    if (seal) {
      params.set("seal", seal);
    }
    if (options.folderId) {
      params.set("folderId", options.folderId);
    }
    if (options.label) {
      params.set("label", options.label);
    }
    const query = params.toString();
    return `/api/storage-link/dropbox/start${query ? `?${query}` : ""}`;
  }, []);

  return {
    links,
    linksLoading,
    linkStorage: linkMutation.mutateAsync,
    unlinkStorage: unlinkMutation.mutateAsync,
    saveTranscript: saveTranscriptMutation.mutateAsync,
    listPointers,
    listVaultEntries,
    resolvePreferredProvider,
    refreshLinks,
    buildGoogleOAuthStartUrl,
    buildDropboxOAuthStartUrl,
    restoreTranscript: restoreTranscriptMutation.mutateAsync,
    isLinking: linkMutation.isPending,
    isUnlinking: unlinkMutation.isPending,
    isSavingTranscript: saveTranscriptMutation.isPending,
    isRestoringTranscript: restoreTranscriptMutation.isPending,
  };
}
