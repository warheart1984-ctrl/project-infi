/**
 * Planner module — breaks complex user requests into actionable steps.
 *
 * For simple queries (greetings, single questions) it returns null so the
 * orchestrator skips planning overhead. For multi-step requests it produces
 * an ordered list of steps the LLM can follow.
 */

import OpenAI from 'openai';
import { selectModel } from '@/lib/core/router';

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export interface Plan {
  goal: string;
  steps: string[];
}

const PLANNING_PROMPT = `You are a planning module inside AAIS.
Given the user's request, decide if it requires multiple steps.
If the request is simple (greeting, single question, quick task), respond with exactly: NO_PLAN
If the request is complex (multi-step build, analysis, research), respond with a JSON plan:
{"goal": "brief goal description", "steps": ["step 1", "step 2", ...]}
Keep plans to 2-6 steps. Be concrete and actionable. Respond ONLY with NO_PLAN or the JSON.`;

export async function runPlanner(userMessage: string): Promise<Plan | null> {
  if (!userMessage || userMessage.length < 10) {
    return null;
  }

  try {
    const response = await client.responses.create({
      model: selectModel(),
      input: [
        { role: 'system', content: [{ type: 'input_text', text: PLANNING_PROMPT }] },
        { role: 'user', content: [{ type: 'input_text', text: userMessage }] },
      ],
    });

    const text = (response.output_text ?? '').trim();

    if (text === 'NO_PLAN' || !text.startsWith('{')) {
      return null;
    }

    const parsed = JSON.parse(text) as Plan;
    if (parsed.goal && Array.isArray(parsed.steps) && parsed.steps.length > 0) {
      return parsed;
    }
  } catch {
    // Planning is best-effort; don't block the main flow
  }

  return null;
}
