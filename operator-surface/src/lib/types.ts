export interface AgentEvent {
  type: string;
  task_id: string;
  seq: number;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface AgentProfile {
  id: string;
  label: string;
  description?: string;
  constraints?: TaskConstraints;
}

export interface TaskConstraints {
  read_only?: boolean;
  allow_shell?: boolean;
  allow_git_commit?: boolean;
  allow_network?: boolean;
  max_steps?: number;
}

export interface TaskMeta {
  task_id: string;
  goal?: string;
  title?: string;
  agent_id?: string;
  status?: string;
  pending_patch?: {
    id?: string;
    path?: string;
    diff?: string;
    args?: Record<string, unknown>;
  };
  messages?: Array<{ role: string; content: string }>;
  updated_at?: string;
}

export interface CreateTaskResult {
  task_id: string;
  status: string;
}

export interface TaskDetailResponse {
  task_id: string;
  meta: TaskMeta;
  events: AgentEvent[];
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
}

export interface PatchApprovalResponse {
  task_id: string;
  status: string;
  applied: boolean;
  path: string;
  message: string;
}

export interface CancelTaskResponse {
  task_id: string;
  status: string;
}

export interface WorkspaceTreeResponse {
  files: string[];
  nodes: Array<{ path: string }>;
  count: number;
}

export interface WorkspaceFileResponse {
  path: string;
  content: string;
  line_count: number;
}
