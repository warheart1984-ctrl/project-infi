/**
 * Executor module — runs tool calls requested by the orchestrator.
 *
 * Validates tool name and input against the registry, executes the tool,
 * and returns a structured result or error.
 */

import { toolRegistry } from '@/lib/tools/registry';
import type { ToolName } from '@/lib/tools/registry';

export interface ToolResult {
  success: boolean;
  toolName: string;
  output: unknown;
  error?: string;
}

export async function executeToolCall(
  toolName: string,
  input: Record<string, unknown>,
): Promise<ToolResult> {
  const tool = toolRegistry[toolName as ToolName];

  if (!tool) {
    return {
      success: false,
      toolName,
      output: null,
      error: `Unknown tool: "${toolName}". Available tools: ${Object.keys(toolRegistry).join(', ')}`,
    };
  }

  try {
    const parsed = tool.inputSchema.safeParse(input);
    if (!parsed.success) {
      return {
        success: false,
        toolName,
        output: null,
        error: `Invalid input for "${toolName}": ${parsed.error.message}`,
      };
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const output = await (tool.execute as (input: any, ctx: any) => Promise<unknown>)(parsed.data, {});
    return { success: true, toolName, output };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Tool execution failed';
    return { success: false, toolName, output: null, error: message };
  }
}
