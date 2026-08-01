#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join } from 'node:path';

import { parseCliArgs, usageText } from './cliArgs.js';
import { bufferToDataUrl, detectImageType, imageExtension } from './detectImageType.js';
import { createAvailableProviders, pickProvider } from './providers/registry.js';
import { describeImageStudioCapability, imageStudioProvenance } from './runtime.js';

async function main(): Promise<void> {
  const args = parseCliArgs(process.argv.slice(2));

  if (args.command === 'help') {
    console.log(usageText());
    return;
  }

  if (args.command === 'models') {
    const providers = createAvailableProviders();
    for (const provider of providers) {
      const models = await provider.listModels();
      const state = provider.configured ? 'configured' : `needs setup (${provider.configHelp ?? 'see docs'})`;
      console.log(`${provider.name} [${state}]`);
      for (const model of models) {
        console.log(`  ${model}`);
      }
    }
    return;
  }

  if (args.command === 'server') {
    const { startStudioServer } = await import('./server.js');
    await startStudioServer({ port: args.port });
    return;
  }

  const { prompt, model, provider: providerName, out, width, height, seed, input, referenceUrl } = args;
  if (!prompt) {
    console.error('error: --prompt is required');
    console.error(usageText());
    process.exitCode = 2;
    return;
  }
  if (!input && !referenceUrl) {
    console.error('error: provide an input image file or --url <image-url>');
    console.error(usageText());
    process.exitCode = 2;
    return;
  }

  const provider = pickProvider(createAvailableProviders(), providerName);
  if (!provider.configured) {
    console.error(`error: provider "${provider.name}" is not configured. ${provider.configHelp ?? ''}`);
    process.exitCode = 2;
    return;
  }

  const referenceImage = referenceUrl
    ? { kind: 'url' as const, url: referenceUrl }
    : toDataUrlReference(input as string);

  const capability = describeImageStudioCapability();
  const provenance = imageStudioProvenance(prompt);

  const result = await provider.generate({
    prompt,
    model,
    width,
    height,
    seed,
    nologo: true,
    referenceImage,
  });

  const outputPath = resolveOutputPath(out, result.contentType);
  mkdirSync(dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, result.bytes);

  console.log(`provider:  ${result.provider} (${result.model})`);
  console.log(`capability: ${capability.name}`);
  console.log(`output:    ${outputPath}`);
  console.log(`provenance: ${provenance.routingHint?.preferredModel ?? 'n/a'}`);
  console.log(`preview:   ${bufferToDataUrl(result.bytes, result.contentType).slice(0, 80)}...`);
}

function toDataUrlReference(filePath: string): { kind: 'dataUrl'; dataUrl: string } {
  const bytes = readFileSync(filePath);
  const contentType = detectImageType(bytes) ?? 'application/octet-stream';
  return { kind: 'dataUrl', dataUrl: bufferToDataUrl(bytes, contentType) };
}

function resolveOutputPath(out: string | undefined, contentType: string): string {
  if (out) {
    return out;
  }
  const extension = imageExtension(contentType);
  const filePath = `image-studio-output-${Date.now()}.${extension}`;
  return isAbsolute(filePath) ? filePath : join(process.cwd(), filePath);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`error: ${message}`);
  process.exitCode = 1;
});
