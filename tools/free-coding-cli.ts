#!/usr/bin/env node
/**
 * Free coding CLI — uses any locally running agent (Ollama, LM Studio, etc.)
 *
 * Usage:
 *   pnpm free-coding "Write a TypeScript sort function"
 *   pnpm free-coding --infinity "Build a REST API in Node.js"
 */
import { createFreeCodingAssistant } from '@aaes-os/coding-assistant';

const args = process.argv.slice(2);
const infinity = args[0] === '--infinity';
const prompt = (infinity ? args.slice(1) : args).join(' ').trim();

if (!prompt) {
  console.error('Usage: free-coding [--infinity] "<your coding prompt>"');
  console.error('');
  console.error('Requires a free local agent: Ollama, LM Studio, Cursor, or Devin.');
  console.error('  ollama serve');
  console.error('  ollama pull qwen2.5-coder:3b');
  process.exit(1);
}

const identity = { actorId: process.env.USER ?? process.env.USERNAME ?? 'developer', role: 'developer' };

const { assistant, discovery } = await createFreeCodingAssistant();

console.error('Free agents available:', discovery.available.map((a) => a.name).join(', ') || 'none');
if (discovery.skipped.length > 0) {
  console.error('Skipped:', discovery.skipped.map((s) => `${s.name} (${s.reason})`).join(', '));
}

if (infinity) {
  const solution = await assistant.infinity(identity).solve(prompt);
  console.log('## Plan\n');
  console.log(solution.plan);
  console.log('\n## Results\n');
  for (const [i, result] of solution.results.entries()) {
    console.log(`### Step ${i + 1}\n`);
    console.log(result);
    console.log('');
  }
} else {
  const result = await assistant.nova(identity).runCommand(prompt);
  console.log(result.output.text);
}
