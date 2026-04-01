import OpenAI from 'openai';
import { AAIS_SYSTEM_PROMPT } from '@/lib/core/prompts';
import { selectModel } from '@/lib/core/router';
import { buildShortTermMemory } from '@/lib/memory/short-term';
import { retrieveLongTermMemory, storeLongTermMemory } from '@/lib/memory/long-term';
import { runPlanner } from '@/lib/core/planner';
import { executeToolCall } from '@/lib/core/executor';
import { formatToolDescriptions } from '@/lib/tools/registry';
import type { ChatMessage } from '@/lib/types/chat';

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export interface RunAAISInput {
  messages: ChatMessage[];
}

function buildSystemMessages(shortTermSummary: string, longTermBlock: string, toolDescriptions: string) {
  const parts = [
    AAIS_SYSTEM_PROMPT,
    `\n\n--- Short-term memory ---\n${shortTermSummary}`,
    `\n\n--- Long-term memory ---\n${longTermBlock}`,
  ];

  if (toolDescriptions) {
    parts.push(`\n\n--- Available tools ---\n${toolDescriptions}`);
    parts.push(
      `\nWhen you need to use a tool, respond with a JSON block like:\n` +
      '```tool\n{"tool": "tool_name", "input": { ... }}\n```\n' +
      `Then I will execute it and give you the result.`,
    );
  }

  return parts.join('');
}

async function buildContext(messages: ChatMessage[]) {
  const shortTerm = buildShortTermMemory(messages);
  const latestUserMessage = [...messages].reverse().find((m) => m.role === 'user');
  const longTerm = latestUserMessage
    ? await retrieveLongTermMemory(latestUserMessage.content)
    : [];

  const longTermBlock =
    longTerm.map((entry) => `- (${entry.kind}) ${entry.content}`).join('\n') || 'None';

  const toolDescriptions = formatToolDescriptions();

  const systemContent = buildSystemMessages(
    shortTerm.conversationSummary,
    longTermBlock,
    toolDescriptions,
  );

  // Check if this needs planning
  const userContent = latestUserMessage?.content ?? '';
  const plan = await runPlanner(userContent);
  const planBlock = plan
    ? `\n\n--- Execution plan ---\n${plan.steps.map((s, i) => `${i + 1}. ${s}`).join('\n')}`
    : '';

  return {
    systemContent: systemContent + planBlock,
    recentMessages: shortTerm.recentMessages,
    userContent,
  };
}

export async function runAAIS({ messages }: RunAAISInput): Promise<string> {
  const { systemContent, recentMessages, userContent } = await buildContext(messages);

  const response = await client.responses.create({
    model: selectModel(),
    input: [
      {
        role: 'system',
        content: [{ type: 'input_text', text: systemContent }],
      },
      ...recentMessages.map((message) => ({
        role: message.role,
        content: [{ type: 'input_text' as const, text: message.content }],
      })),
    ],
  });

  let output = response.output_text || 'AAIS did not return text.';

  // Check if the response contains a tool call
  const toolMatch = output.match(/```tool\s*\n([\s\S]*?)\n```/);
  if (toolMatch) {
    try {
      const toolCall = JSON.parse(toolMatch[1]) as { tool: string; input: Record<string, unknown> };
      const toolResult = await executeToolCall(toolCall.tool, toolCall.input);

      // Send the tool result back for a final response
      const followUp = await client.responses.create({
        model: selectModel(),
        input: [
          {
            role: 'system',
            content: [{ type: 'input_text', text: systemContent }],
          },
          ...recentMessages.map((message) => ({
            role: message.role,
            content: [{ type: 'input_text' as const, text: message.content }],
          })),
          {
            role: 'assistant',
            content: [{ type: 'input_text' as const, text: output }],
          },
          {
            role: 'user',
            content: [
              {
                type: 'input_text' as const,
                text: `Tool "${toolCall.tool}" returned:\n${JSON.stringify(toolResult, null, 2)}\n\nPlease incorporate this result into your response.`,
              },
            ],
          },
        ],
      });
      output = followUp.output_text || output;
    } catch {
      // If tool parsing/execution fails, return the original response
    }
  }

  // Store this exchange in long-term memory
  if (userContent) {
    await storeLongTermMemory(userContent, output);
  }

  return output;
}

export async function* runAAISStream({ messages }: RunAAISInput): AsyncGenerator<{ token: string }> {
  const { systemContent, recentMessages, userContent } = await buildContext(messages);

  const stream = await client.responses.create({
    model: selectModel(),
    stream: true,
    input: [
      {
        role: 'system',
        content: [{ type: 'input_text', text: systemContent }],
      },
      ...recentMessages.map((message) => ({
        role: message.role,
        content: [{ type: 'input_text' as const, text: message.content }],
      })),
    ],
  });

  let fullOutput = '';
  for await (const event of stream) {
    if (
      event.type === 'response.output_text.delta' &&
      'delta' in event &&
      typeof event.delta === 'string'
    ) {
      fullOutput += event.delta;
      yield { token: event.delta };
    }
  }

  // Store in long-term memory
  if (userContent) {
    await storeLongTermMemory(userContent, fullOutput);
  }
}
