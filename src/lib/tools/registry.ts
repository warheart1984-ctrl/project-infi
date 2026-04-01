import { z } from 'zod';

export interface ToolContext {
  userId?: string;
}

export interface ToolDefinition<TInput = unknown, TResult = unknown> {
  name: string;
  description: string;
  inputSchema: z.ZodType<TInput>;
  execute: (input: TInput, context: ToolContext) => Promise<TResult>;
}

// ── Echo (test tool) ──

const echoTool: ToolDefinition<{ text: string }, { echoed: string }> = {
  name: 'echo',
  description: 'Echoes text back. Useful for testing tool wiring.',
  inputSchema: z.object({
    text: z.string().min(1),
  }),
  async execute(input) {
    return { echoed: input.text };
  },
};

// ── Calculator ──

const calculatorTool: ToolDefinition<
  { expression: string },
  { result: number | string }
> = {
  name: 'calculator',
  description:
    'Evaluates a mathematical expression. Supports +, -, *, /, **, %, sqrt(), abs(), round(), floor(), ceil(), sin(), cos(), tan(), log(), PI, E.',
  inputSchema: z.object({
    expression: z.string().min(1),
  }),
  async execute(input) {
    try {
      // Safe math evaluation using Function constructor with limited scope
      const mathFns: Record<string, unknown> = {
        sqrt: Math.sqrt,
        abs: Math.abs,
        round: Math.round,
        floor: Math.floor,
        ceil: Math.ceil,
        sin: Math.sin,
        cos: Math.cos,
        tan: Math.tan,
        log: Math.log,
        log10: Math.log10,
        pow: Math.pow,
        min: Math.min,
        max: Math.max,
        PI: Math.PI,
        E: Math.E,
      };

      // Validate: only allow numbers, operators, parentheses, dots, and math function names
      const sanitized = input.expression.replace(/\s/g, '');
      const allowed = /^[0-9+\-*/().,%^a-zA-Z]+$/;
      if (!allowed.test(sanitized)) {
        return { result: 'Invalid expression: contains disallowed characters' };
      }

      const fn = new Function(
        ...Object.keys(mathFns),
        `"use strict"; return (${input.expression});`,
      );
      const result = fn(...Object.values(mathFns)) as number;

      if (typeof result !== 'number' || !isFinite(result)) {
        return { result: 'Expression did not evaluate to a finite number' };
      }
      return { result };
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Evaluation error';
      return { result: `Error: ${msg}` };
    }
  },
};

// ── Date & Time ──

const dateTimeTool: ToolDefinition<
  { timezone?: string },
  { iso: string; readable: string; timestamp: number; timezone: string }
> = {
  name: 'datetime',
  description:
    'Returns the current date, time, and Unix timestamp. Optionally accepts a timezone (e.g. "America/New_York").',
  inputSchema: z.object({
    timezone: z.string().optional(),
  }),
  async execute(input) {
    const now = new Date();
    const tz = input.timezone ?? 'UTC';
    let readable: string;
    try {
      readable = now.toLocaleString('en-US', { timeZone: tz });
    } catch {
      readable = now.toLocaleString('en-US', { timeZone: 'UTC' });
    }
    return {
      iso: now.toISOString(),
      readable,
      timestamp: now.getTime(),
      timezone: tz,
    };
  },
};

// ── Web Search (stub — returns guidance) ──

const webSearchTool: ToolDefinition<
  { query: string },
  { message: string; suggestion: string }
> = {
  name: 'web_search',
  description:
    'Searches the web for information. Currently a stub that guides the user to add a real search API (SerpAPI, Tavily, Brave Search, etc.).',
  inputSchema: z.object({
    query: z.string().min(1),
  }),
  async execute(input) {
    return {
      message: `Web search for "${input.query}" is not yet connected to a live API.`,
      suggestion:
        'To enable real search, add a SEARCH_API_KEY to .env.local and implement the search provider in src/lib/tools/registry.ts. Recommended providers: Tavily (tavily.com), SerpAPI, or Brave Search API.',
    };
  },
};

// ── JSON Formatter ──

const jsonFormatterTool: ToolDefinition<
  { json: string; indent?: number },
  { formatted: string } | { error: string }
> = {
  name: 'json_format',
  description: 'Parses and pretty-prints a JSON string.',
  inputSchema: z.object({
    json: z.string().min(1),
    indent: z.number().int().min(1).max(8).optional(),
  }),
  async execute(input) {
    try {
      const parsed = JSON.parse(input.json) as unknown;
      return { formatted: JSON.stringify(parsed, null, input.indent ?? 2) };
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Parse error';
      return { error: `Invalid JSON: ${msg}` };
    }
  },
};

// ── Text Utilities ──

const textUtilsTool: ToolDefinition<
  { text: string; operation: string },
  { result: string | number }
> = {
  name: 'text_utils',
  description:
    'Text utility operations: "word_count", "char_count", "uppercase", "lowercase", "reverse", "slugify", "trim", "summarize_length".',
  inputSchema: z.object({
    text: z.string(),
    operation: z.enum([
      'word_count',
      'char_count',
      'uppercase',
      'lowercase',
      'reverse',
      'slugify',
      'trim',
      'summarize_length',
    ]),
  }),
  async execute(input) {
    switch (input.operation) {
      case 'word_count':
        return { result: input.text.split(/\s+/).filter(Boolean).length };
      case 'char_count':
        return { result: input.text.length };
      case 'uppercase':
        return { result: input.text.toUpperCase() };
      case 'lowercase':
        return { result: input.text.toLowerCase() };
      case 'reverse':
        return { result: input.text.split('').reverse().join('') };
      case 'slugify':
        return {
          result: input.text
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, ''),
        };
      case 'trim':
        return { result: input.text.trim() };
      case 'summarize_length': {
        const words = input.text.split(/\s+/).filter(Boolean).length;
        const chars = input.text.length;
        const sentences = input.text.split(/[.!?]+/).filter(Boolean).length;
        return {
          result: `${words} words, ${chars} characters, ~${sentences} sentences`,
        };
      }
      default:
        return { result: 'Unknown operation' };
    }
  },
};

// ── UUID Generator ──

const uuidTool: ToolDefinition<
  { count?: number },
  { uuids: string[] }
> = {
  name: 'uuid',
  description: 'Generates one or more UUIDs (v4).',
  inputSchema: z.object({
    count: z.number().int().min(1).max(50).optional(),
  }),
  async execute(input) {
    const count = input.count ?? 1;
    const uuids: string[] = [];
    for (let i = 0; i < count; i++) {
      uuids.push(crypto.randomUUID());
    }
    return { uuids };
  },
};

// ── Base64 Encoder/Decoder ──

const base64Tool: ToolDefinition<
  { text: string; operation: string },
  { result: string }
> = {
  name: 'base64',
  description: 'Encodes or decodes base64 text. Operations: "encode", "decode".',
  inputSchema: z.object({
    text: z.string(),
    operation: z.enum(['encode', 'decode']),
  }),
  async execute(input) {
    if (input.operation === 'encode') {
      return { result: Buffer.from(input.text).toString('base64') };
    }
    try {
      return { result: Buffer.from(input.text, 'base64').toString('utf-8') };
    } catch {
      return { result: 'Error: invalid base64 input' };
    }
  },
};

// ── Registry ──

export const toolRegistry = {
  echo: echoTool,
  calculator: calculatorTool,
  datetime: dateTimeTool,
  web_search: webSearchTool,
  json_format: jsonFormatterTool,
  text_utils: textUtilsTool,
  uuid: uuidTool,
  base64: base64Tool,
} as const;

export type ToolName = keyof typeof toolRegistry;

/**
 * Format all tool descriptions for inclusion in the system prompt.
 */
export function formatToolDescriptions(): string {
  return Object.values(toolRegistry)
    .map((tool) => `- **${tool.name}**: ${tool.description}`)
    .join('\n');
}
