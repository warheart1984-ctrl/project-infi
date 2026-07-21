import type {
  AgentEvent,
  AgentProfile,
  CancelTaskResponse,
  CreateTaskResult,
  PatchApprovalResponse,
  TaskMeta,
  TaskStatusResponse,
  WorkspaceFileResponse,
  WorkspaceTreeResponse,
} from "./types";
import type { OperatorSettings } from "./settings";

function baseUrl(settings: OperatorSettings): string {
  return settings.kernelUrl.replace(/\/$/, "");
}

async function kernelFetch<T>(
  settings: OperatorSettings,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${baseUrl(settings)}${path}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(text || `Kernel API ${response.status} ${path}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function checkHealth(settings: OperatorSettings): Promise<boolean> {
  try {
    const data = await kernelFetch<{ status?: string }>(settings, "/health");
    return data?.status === "ok";
  } catch {
    return false;
  }
}

export async function listProfiles(settings: OperatorSettings): Promise<AgentProfile[]> {
  const data = await kernelFetch<AgentProfile[]>(settings, "/agent/profiles");
  return Array.isArray(data) ? data : [];
}

export async function createTask(
  settings: OperatorSettings,
  goal: string,
): Promise<CreateTaskResult> {
  return kernelFetch<CreateTaskResult>(settings, "/agent/tasks", {
    method: "POST",
    body: JSON.stringify({
      goal,
      agent_id: settings.defaultAgentId,
      constraints: {
        read_only: settings.readOnly,
        allow_shell: settings.allowShell,
        allow_git_commit: settings.allowGitCommit,
        allow_network: settings.allowNetwork,
        max_steps: settings.maxSteps,
      },
    }),
  });
}

export async function getTask(settings: OperatorSettings, taskId: string): Promise<TaskMeta> {
  const detail = await kernelFetch<{ task_id: string; meta: TaskMeta; events: AgentEvent[] }>(
    settings,
    `/agent/tasks/${encodeURIComponent(taskId)}`,
  );
  return detail.meta;
}

export async function cancelTask(
  settings: OperatorSettings,
  taskId: string,
): Promise<CancelTaskResponse> {
  return kernelFetch<CancelTaskResponse>(
    settings,
    `/agent/tasks/${encodeURIComponent(taskId)}/cancel`,
    {
      method: "POST",
      body: "{}",
    },
  );
}

export async function appendMessage(
  settings: OperatorSettings,
  taskId: string,
  content: string,
): Promise<TaskStatusResponse> {
  return kernelFetch<TaskStatusResponse>(
    settings,
    `/agent/tasks/${encodeURIComponent(taskId)}/message`,
    {
      method: "POST",
      body: JSON.stringify({ text: content }),
    },
  );
}

export async function approvePatch(
  settings: OperatorSettings,
  taskId: string,
): Promise<PatchApprovalResponse> {
  return kernelFetch<PatchApprovalResponse>(
    settings,
    `/agent/tasks/${encodeURIComponent(taskId)}/approve_patch`,
    {
      method: "POST",
      body: "{}",
    },
  );
}

export async function rejectPatch(
  settings: OperatorSettings,
  taskId: string,
  reason = "",
): Promise<PatchApprovalResponse> {
  return kernelFetch<PatchApprovalResponse>(
    settings,
    `/agent/tasks/${encodeURIComponent(taskId)}/reject_patch`,
    {
      method: "POST",
      body: JSON.stringify({ reason }),
    },
  );
}

export function streamEvents(
  settings: OperatorSettings,
  taskId: string,
  after: number,
  onEvent: (event: AgentEvent) => void,
  onError?: (err: Event) => void,
): EventSource {
  const url = `${baseUrl(settings)}/agent/tasks/${encodeURIComponent(taskId)}/events?after=${after}`;
  const source = new EventSource(url);

  source.onmessage = (msg) => {
    try {
      const raw = JSON.parse(msg.data) as AgentEvent;
      onEvent(raw);
    } catch {
      // ignore malformed frames
    }
  };

  source.onerror = (err) => {
    onError?.(err);
  };

  return source;
}

export async function fetchWorkspaceTree(
  settings: OperatorSettings,
): Promise<WorkspaceTreeResponse> {
  return kernelFetch<WorkspaceTreeResponse>(settings, "/workspace/tree");
}

export async function fetchWorkspaceFile(
  settings: OperatorSettings,
  path: string,
): Promise<WorkspaceFileResponse> {
  const q = new URLSearchParams({ path });
  return kernelFetch<WorkspaceFileResponse>(settings, `/workspace/file?${q}`);
}

export async function previewWorkspacePatch(
  settings: OperatorSettings,
  path: string,
  oldContent: string,
  newContent: string,
): Promise<{ path: string; diff: string }> {
  return kernelFetch<{ path: string; diff: string }>(settings, "/workspace/patch/preview", {
    method: "POST",
    body: JSON.stringify({
      path,
      old_content: oldContent,
      new_content: newContent,
    }),
  });
}

export async function applyWorkspacePatch(
  settings: OperatorSettings,
  path: string,
  diff: string,
): Promise<{ path: string; applied: boolean; method?: string }> {
  return kernelFetch<{ path: string; applied: boolean; method?: string }>(
    settings,
    "/workspace/apply_patch",
    {
      method: "POST",
      body: JSON.stringify({ path, diff }),
    },
  );
}

export async function listTasks(
  settings: OperatorSettings,
): Promise<Array<Record<string, unknown>>> {
  const data = await kernelFetch<{ tasks?: Array<Record<string, unknown>> }>(
    settings,
    "/agent/tasks",
  );
  return Array.isArray(data.tasks) ? data.tasks : [];
}
