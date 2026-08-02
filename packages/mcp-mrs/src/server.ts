import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { MrsEngineBridge } from './bridge.js';
import {
  RenderRt4dPreviewInput,
  RenderRt4dPreviewOutput,
  EngineReceipt,
} from './schemas.js';

const TOOL_NAME = 'render_rt4d_preview';

export function createMcpServer(engineBaseUrl: string, apiKey?: string) {
  const bridge = new MrsEngineBridge({
    baseUrl: engineBaseUrl,
    apiKey,
    timeoutMs: 120000,
  });

  const server = new Server(
    {
      name: 'mrs-mcp',
      version: '0.1.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      {
        name: TOOL_NAME,
        description:
          'Render a scene via the MRS RT4D engine and return the full layered evidence bundle. ' +
          'Use this whenever the user requests an RT4D, 4D, governed, replayable, or constitutionally evidenced render.',
        inputSchema: {
          type: 'object',
          properties: {
            sceneSpec: {
              type: 'object',
              description: 'Canonical JSON scene specification',
            },
            surface: {
              type: 'string',
              description: 'Surface identifier validated against engine capability gate',
            },
            seed: {
              type: 'integer',
              description: 'Optional deterministic seed',
            },
            camera: {
              type: 'object',
              properties: {
                fov: { type: 'number', minimum: 1, maximum: 179 },
                position: { type: 'array', items: { type: 'number' }, minItems: 3, maxItems: 3 },
                target: { type: 'array', items: { type: 'number' }, minItems: 3, maxItems: 3 },
                rotations: { type: 'array', items: { type: 'number' }, minItems: 3, maxItems: 3 },
              },
              description: 'Camera configuration: fov, position, target, optional rotations',
            },
            quality: {
              type: 'object',
              properties: {
                resolution: { type: 'array', items: { type: 'integer', minimum: 1 }, minItems: 2, maxItems: 2 },
                spp: { type: 'integer', minimum: 1 },
                maxDepth: { type: 'integer', minimum: 1 },
              },
              description: 'Render quality: resolution, samples per pixel, max ray depth',
            },
            trajectory: {
              type: 'array',
              items: { type: 'array', items: { type: 'number' } },
              description: 'Optional trajectory waypoints',
            },
          },
          required: ['sceneSpec', 'surface'],
        },
        annotations: {
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: true,
          openWorld: false,
        },
      },
    ],
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    if (name !== TOOL_NAME) {
      return {
        isError: true,
        structuredContent: { code: 'UNKNOWN_TOOL', message: `Unknown tool: ${name}` },
        content: [{ type: 'text', text: `Unknown tool: ${name}` }],
      };
    }

    const parseResult = RenderRt4dPreviewInput.safeParse(args);
    if (!parseResult.success) {
      return {
        isError: true,
        structuredContent: {
          code: 'INVALID_INPUT',
          issues: parseResult.error.issues.map((i) => ({
            path: i.path.map(String),
            message: i.message,
          })),
        },
        content: [
          {
            type: 'text',
            text: `Invalid input: ${parseResult.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join('; ')}`,
          },
        ],
      };
    }

    try {
      const receipt = await bridge.renderComplete(parseResult.data);
      const validated = RenderRt4dPreviewOutput.parse(receipt);

      const content: Array<{ type: string; data?: string; mimeType?: string; text?: string }> = [];

      if (receipt.pngBase64) {
        content.push({
          type: 'image',
          data: receipt.pngBase64,
          mimeType: 'image/png',
        });
      }

      content.push({
        type: 'text',
        text: JSON.stringify(validated, null, 2),
      });

      return {
        structuredContent: validated,
        content,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);

      if (message.includes('MRS scene creation failed') || message.includes('MRS render failed')) {
        return {
          isError: true,
          structuredContent: { code: 'MRS_ENGINE_UNAVAILABLE', message },
          content: [
            {
              type: 'text',
              text: `MRS engine unavailable: ${message}. No fallback rendering was performed.`,
            },
          ],
        };
      }

      if (message.includes('Scene spec hash mismatch')) {
        return {
          isError: true,
          structuredContent: { code: 'ENGINE_EVIDENCE_INTEGRITY_ERROR', message },
          content: [
            {
              type: 'text',
              text: `Engine evidence integrity error: ${message}`,
            },
          ],
        };
      }

      return {
        isError: true,
        structuredContent: { code: 'RENDER_ERROR', message },
        content: [{ type: 'text', text: `Render failed: ${message}` }],
      };
    }
  });

  return server;
}

export async function startMcpServer(engineBaseUrl: string, apiKey?: string) {
  const server = createMcpServer(engineBaseUrl, apiKey);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  return server;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const baseUrl = process.env.MRS_ENGINE_URL ?? 'http://127.0.0.1:8080';
  const apiKey = process.env.MRS_API_KEY;
  startMcpServer(baseUrl, apiKey).catch((err) => {
    console.error('MCP server failed:', err);
    process.exit(1);
  });
}