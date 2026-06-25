export { AgentRuntime } from "./runtime/agent-runtime";
export * as governance from "./governance";
export * as continuity from "./continuity";
export * as events from "./events/lifecycle";
export * from "./types";
export type { KernelStatus, KernelHeartbeat } from "./governance/kernelStatus";

/** @deprecated Use AgentRuntime — kept for backward compatibility */
export * as nova from "./core/agent";
/** @deprecated Use AgentRuntime.workspace helpers */
export * as runtime from "./runtime";
