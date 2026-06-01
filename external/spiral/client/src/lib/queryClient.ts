import { QueryClient, QueryFunction } from "@tanstack/react-query";
import { getClientEnvValue } from "@/lib/client-env";

const spiralApiSeal = getClientEnvValue("VITE_SPIRAL_API_SEAL").trim();

export function getSpiralSealHeaders(): Record<string, string> {
  if (!spiralApiSeal) return {};
  return { "X-Spiral-Seal": spiralApiSeal };
}

function parseErrorMessage(raw: string): string {
  if (!raw) return "";
  try {
    const parsed = JSON.parse(raw) as { error?: unknown; message?: unknown };
    if (typeof parsed.error === "string" && parsed.error.trim()) {
      return parsed.error.trim();
    }
    if (typeof parsed.message === "string" && parsed.message.trim()) {
      return parsed.message.trim();
    }
  } catch {
    // Fall through to plain text.
  }
  return raw;
}

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    const raw = (await res.text()) || res.statusText;
    const text = parseErrorMessage(raw) || res.statusText;
    throw new Error(`${res.status}: ${text}`);
  }
}

export async function apiRequest(
  method: string,
  url: string,
  data?: unknown | undefined,
): Promise<Response> {
  const res = await fetch(url, {
    method,
    headers: data
      ? { "Content-Type": "application/json", ...getSpiralSealHeaders() }
      : getSpiralSealHeaders(),
    body: data ? JSON.stringify(data) : undefined,
    credentials: "include",
  });

  await throwIfResNotOk(res);
  return res;
}

type UnauthorizedBehavior = "returnNull" | "throw";
export const getQueryFn: <T>(options: {
  on401: UnauthorizedBehavior;
}) => QueryFunction<T> =
  ({ on401: unauthorizedBehavior }) =>
  async ({ queryKey }) => {
    const res = await fetch(queryKey.join("/") as string, {
      headers: getSpiralSealHeaders(),
      credentials: "include",
    });

    if (unauthorizedBehavior === "returnNull" && res.status === 401) {
      return null;
    }

    await throwIfResNotOk(res);
    return await res.json();
  };

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});
