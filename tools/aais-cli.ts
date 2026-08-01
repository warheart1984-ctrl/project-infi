#!/usr/bin/env node
/**
 * AAIS free-runtime CLI — text via free coding stack; images via image-studio providers.
 *
 * Usage:
 *   pnpm aais
 *   pnpm aais "Write a TypeScript reverse-string helper"
 *   pnpm aais --status
 *   pnpm aais --model qwen-3b "quick fix sketch"
 *   pnpm aais --image "a red fox in snow"
 *   pnpm aais --image --provider gemini "watercolor mountain lake"
 *   pnpm aais --image --out ./fox.png "a red fox"
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join } from 'node:path';

import { createFreeCodingAssistant } from '@aaes-os/coding-assistant';
import {
  createAvailableProviders,
  imageExtension,
  pickProvider,
} from '@aaes-os/image-studio';

const args = process.argv.slice(2);
const statusOnly = args.includes('--status');
const imageMode = args.includes('--image');

const modelFlagIdx = args.indexOf('--model');
const modelPref =
  modelFlagIdx >= 0
    ? (args[modelFlagIdx + 1] as 'auto' | 'qwen-3b' | 'qwen-7b' | undefined)
    : undefined;

const providerFlagIdx = args.indexOf('--provider');
const providerName = providerFlagIdx >= 0 ? args[providerFlagIdx + 1] : undefined;

const outFlagIdx = args.indexOf('--out');
const outPath = outFlagIdx >= 0 ? args[outFlagIdx + 1] : undefined;

const widthFlagIdx = args.indexOf('--width');
const width = widthFlagIdx >= 0 ? Number.parseInt(args[widthFlagIdx + 1] ?? '', 10) : undefined;

const heightFlagIdx = args.indexOf('--height');
const height = heightFlagIdx >= 0 ? Number.parseInt(args[heightFlagIdx + 1] ?? '', 10) : undefined;

const consumed = new Set<number>();
for (const [flagIdx, consumesValue] of [
  [modelFlagIdx, true],
  [providerFlagIdx, true],
  [outFlagIdx, true],
  [widthFlagIdx, true],
  [heightFlagIdx, true],
] as const) {
  if (flagIdx >= 0) {
    consumed.add(flagIdx);
    if (consumesValue) consumed.add(flagIdx + 1);
  }
}

const promptParts = args.filter((a, i) => {
  if (a === '--status' || a === '--image') return false;
  if (consumed.has(i)) return false;
  return true;
});
const prompt = promptParts.join(' ').trim();

if (imageMode) {
  await runImageMode();
} else {
  await runTextMode();
}

async function runImageMode(): Promise<void> {
  const providers = createAvailableProviders();
  const configured = providers.filter((p) => p.configured);

  if (statusOnly) {
    console.log(
      JSON.stringify(
        {
          mode: 'image',
          providers: providers.map((p) => ({
            name: p.name,
            configured: p.configured,
            requiresApiKey: p.requiresApiKey,
            configHelp: p.configHelp,
          })),
          defaultProvider: pickProvider(providers, undefined).name,
        },
        null,
        2,
      ),
    );
    process.exit(0);
  }

  console.error(
    'Image providers:',
    configured.map((p) => p.name).join(', ') || 'none configured',
  );
  const skipped = providers.filter((p) => !p.configured);
  if (skipped.length > 0) {
    console.error(
      'Skipped:',
      skipped.map((p) => `${p.name}${p.configHelp ? ` (${p.configHelp})` : ''}`).join('; '),
    );
  }

  if (!prompt) {
    printImageUsage();
    process.exit(1);
  }

  const provider = pickProvider(providers, providerName);
  if (!provider.configured) {
    console.error(`error: provider "${provider.name}" is not configured. ${provider.configHelp ?? ''}`);
    process.exit(1);
  }

  console.error(`Generating with ${provider.name}…`);
  const result = await provider.generate({
    prompt,
    width: Number.isFinite(width) ? width : undefined,
    height: Number.isFinite(height) ? height : undefined,
    nologo: true,
  });

  const outputPath = resolveImageOutputPath(outPath, result.contentType);
  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, result.bytes);

  console.log(`provider: ${result.provider}`);
  console.log(`model:    ${result.model}`);
  console.log(`type:     ${result.contentType}`);
  console.log(`output:   ${outputPath}`);
  console.log(`bytes:    ${result.bytes.length}`);
}

async function runTextMode(): Promise<void> {
  const { assistant, aais, discovery, sovereignXRouter } =
    await createFreeCodingAssistant({
      // Status should not block on Ollama cold-load warm-up.
      warmModels: !statusOnly,
    });

  console.error('AAIS flow:', aais.describeFlow().join(' → '));
  console.error(
    'Free agents:',
    discovery.available.map((a) => `${a.name}${a.models?.length ? ` [${a.models.join(', ')}]` : ''}`).join('; ') ||
      'none',
  );
  if (discovery.skipped.length > 0) {
    console.error(
      'Skipped:',
      discovery.skipped.map((s) => `${s.name} (${s.reason})`).join('; '),
    );
  }
  console.error(
    'SovereignX:',
    sovereignXRouter || assistant.getSovereignXRouter() ? 'ready (3b/7b when both present)' : 'not wrapped',
  );

  const imageProviders = createAvailableProviders();
  console.error(
    'Image (use --image):',
    imageProviders
      .filter((p) => p.configured)
      .map((p) => p.name)
      .join(', ') || 'none',
  );

  if (statusOnly) {
    const caps = aais.describeCapabilities?.() ?? [];
    console.log(
      JSON.stringify(
        {
          flow: aais.describeFlow(),
          capabilityCount: caps.length,
          available: discovery.available,
          skipped: discovery.skipped,
          imageProviders: imageProviders.map((p) => ({
            name: p.name,
            configured: p.configured,
            requiresApiKey: p.requiresApiKey,
          })),
        },
        null,
        2,
      ),
    );
    process.exit(0);
  }

  if (!prompt) {
    printTextUsage();
    process.exit(1);
  }

  if (modelPref && ['auto', 'qwen-3b', 'qwen-7b'].includes(modelPref)) {
    assistant.setModelPreference(modelPref);
    console.error('Model preference:', modelPref);
  }

  const identity = {
    actorId: process.env.USER ?? process.env.USERNAME ?? 'developer',
    role: 'developer',
  };

  const result = await assistant.nova(identity).runCommand(prompt);
  console.log(result.output.text);
}

function resolveImageOutputPath(out: string | undefined, contentType: string): string {
  if (out) {
    return isAbsolute(out) ? out : join(process.cwd(), out);
  }
  const extension = imageExtension(contentType);
  return join(process.cwd(), `aais-image-${Date.now()}.${extension}`);
}

function printTextUsage(): void {
  console.error('');
  console.error('Usage: pnpm aais [--status] [--model auto|qwen-3b|qwen-7b] "<prompt>"');
  console.error('       pnpm aais --image [--provider pollinations|gemini] [--out path] "<prompt>"');
  console.error('Free text backends: Ollama (local) and/or cloud keys:');
  console.error('  ollama serve && ollama pull qwen2.5-coder:3b && ollama pull qwen2.5-coder:7b');
  console.error('  set OPENROUTER_API_KEY=...   # model default openrouter/free');
  console.error('  set GROQ_API_KEY=...         # model default llama-3.3-70b-versatile');
  console.error('Free image: Pollinations (keyless) or Gemini (GEMINI_API_KEY / GOOGLE_API_KEY).');
}

function printImageUsage(): void {
  console.error('');
  console.error('Usage: pnpm aais --image [--provider pollinations|gemini] [--out path] [--width N] [--height N] "<prompt>"');
  console.error('       pnpm aais --image --status');
  console.error('Defaults: --provider pollinations (keyless). Gemini needs GEMINI_API_KEY or GOOGLE_API_KEY.');
}
