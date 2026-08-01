import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';

import { bufferToDataUrl } from './detectImageType.js';
import { createAvailableProviders, pickProvider } from './providers/registry.js';
import type { ImageProvider } from './providers/types.js';
import { describeImageStudioCapability, imageStudioProvenance } from './runtime.js';

const MAX_BODY_BYTES = 16 * 1024 * 1024;
const DATA_URL_PREFIX = /^data:image\/(png|jpeg|jpg|gif|webp);base64,/;

export interface StudioServerOptions {
  port?: number;
  host?: string;
  providers?: ImageProvider[];
}

export function startStudioServer(options: StudioServerOptions = {}): Promise<void> {
  const port = options.port ?? 4317;
  const host = options.host ?? '127.0.0.1';
  const providers = options.providers ?? createAvailableProviders();

  const server = createServer((req, res) => {
    void handleRequest(req, res, providers).catch((error: unknown) => {
      const message = error instanceof Error ? error.message : String(error);
      sendJson(res, 500, { ok: false, error: message });
    });
  });

  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, host, () => {
      console.log(`image-studio web UI: http://${host}:${port}`);
      for (const provider of providers) {
        const state = provider.configured ? 'configured' : `needs setup (${provider.configHelp ?? 'see docs'})`;
        console.log(`provider: ${provider.name} [${state}]`);
      }
      console.log('Anonymous Pollinations tier: ~1 request per 15s, watermarked.');
      resolve();
    });
  });
}

async function handleRequest(
  req: IncomingMessage,
  res: ServerResponse,
  providers: readonly ImageProvider[],
): Promise<void> {
  const url = new URL(req.url ?? '/', 'http://localhost');

  if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(buildHtmlPage());
    return;
  }

  if (req.method === 'GET' && url.pathname === '/api/models') {
    const listed = await Promise.all(
      providers.map(async (provider) => ({
        name: provider.name,
        requiresApiKey: provider.requiresApiKey,
        configured: provider.configured,
        configHelp: provider.configHelp,
        models: await provider.listModels(),
      })),
    );
    sendJson(res, 200, { ok: true, providers: listed });
    return;
  }

  if (req.method === 'POST' && url.pathname === '/api/generate') {
    const body = await readJsonBody(req);
    const prompt = typeof body.prompt === 'string' ? body.prompt.trim() : '';
    if (!prompt) {
      sendJson(res, 400, { ok: false, error: 'prompt is required' });
      return;
    }
    const imageDataUrl = typeof body.imageDataUrl === 'string' ? body.imageDataUrl : '';
    if (!DATA_URL_PREFIX.test(imageDataUrl)) {
      sendJson(res, 400, { ok: false, error: 'imageDataUrl must be a base64 data:image/... URL' });
      return;
    }

    let provider: ImageProvider;
    try {
      provider = pickProvider(providers, typeof body.provider === 'string' ? body.provider : undefined);
    } catch (error) {
      sendJson(res, 400, { ok: false, error: error instanceof Error ? error.message : String(error) });
      return;
    }
    if (!provider.configured) {
      sendJson(res, 400, {
        ok: false,
        error: `Provider "${provider.name}" is not configured. ${provider.configHelp ?? ''}`,
      });
      return;
    }

    const provenance = imageStudioProvenance(prompt);
    const capability = describeImageStudioCapability();

    const result = await provider.generate({
      prompt,
      model: typeof body.model === 'string' && body.model.trim() ? body.model.trim() : undefined,
      width: positiveInteger(body.width),
      height: positiveInteger(body.height),
      seed: integer(body.seed),
      nologo: true,
      referenceImage: { kind: 'dataUrl', dataUrl: imageDataUrl },
    });

    sendJson(res, 200, {
      ok: true,
      provider: result.provider,
      model: result.model,
      contentType: result.contentType,
      dataUrl: bufferToDataUrl(result.bytes, result.contentType),
      capability: { name: capability.name, id: capability.id, summary: capability.summary },
      provenance,
    });
    return;
  }

  sendJson(res, 404, { ok: false, error: 'not found' });
}

function sendJson(res: ServerResponse, status: number, payload: unknown): void {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(payload));
}

async function readJsonBody(req: IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of req) {
    const buffer = chunk as Buffer;
    size += buffer.length;
    if (size > MAX_BODY_BYTES) {
      throw new Error('request body too large');
    }
    chunks.push(buffer);
  }
  const raw = Buffer.concat(chunks).toString('utf8');
  if (!raw.trim()) {
    return {};
  }
  try {
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    throw new Error('invalid JSON body');
  }
}

function positiveInteger(value: unknown): number | undefined {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) {
    return undefined;
  }
  return Math.floor(value);
}

function integer(value: unknown): number | undefined {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return undefined;
  }
  return Math.floor(value);
}

export function buildHtmlPage(): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>image-studio — free image-to-image</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; max-width: 760px; margin: 0 auto; padding: 24px; }
  label { display: block; margin-top: 14px; font-weight: 600; }
  input, textarea, select { width: 100%; box-sizing: border-box; padding: 8px; margin-top: 4px; }
  textarea { min-height: 72px; }
  .row { display: flex; gap: 12px; }
  .row > div { flex: 1; }
  button { margin-top: 18px; padding: 10px 22px; font-size: 1rem; }
  #status { margin-top: 14px; white-space: pre-wrap; font-family: monospace; font-size: 0.85rem; }
  #result { margin-top: 18px; display: none; }
  #result img { max-width: 100%; border-radius: 8px; }
  a { margin-top: 8px; display: inline-block; }
  #drop { border: 2px dashed #888; padding: 22px; text-align: center; border-radius: 10px; margin-top: 8px; cursor: pointer; }
  #drop.over { background: #222; }
</style>
</head>
<body>
<h1>image-studio</h1>
<p>Free image-to-image. <strong>Pollinations</strong> works with no API key (anonymous: ~1 req/15s, watermarked). <strong>HF Space</strong> uses a keyless community ZeroGPU Space (rate-limited). <strong>Cloudflare</strong> and <strong>Hugging Face</strong> use their free tiers once you set tokens.</p>

<label for="file">1. Reference image</label>
<div id="drop">Click or drop an image here</div>
<input type="file" id="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden>
<div id="fileName" style="margin-top:6px;font-size:0.85rem;"></div>

<label for="prompt">2. Transform it into&hellip;</label>
<textarea id="prompt" placeholder="e.g. a watercolor painting, cyberpunk neon, in the style of a renaissance oil painting"></textarea>

<div class="row">
  <div>
    <label for="provider">3. Provider</label>
    <select id="provider"></select>
  </div>
  <div>
    <label for="model">4. Model</label>
    <select id="model"></select>
  </div>
</div>

<div class="row">
  <div>
    <label for="width">Width</label>
    <input type="number" id="width" value="1024" min="64" max="2048">
  </div>
  <div>
    <label for="height">Height</label>
    <input type="number" id="height" value="1024" min="64" max="2048">
  </div>
  <div>
    <label for="seed">Seed (optional)</label>
    <input type="number" id="seed" placeholder="random">
  </div>
</div>

<button id="go">Generate</button>
<div id="status"></div>
<div id="result">
  <img id="out" alt="generated image">
  <br><a id="download" download="image-studio-output.png">Download</a>
</div>

<script>
  let currentDataUrl = null;
  let modelsByProvider = {};

  const file = document.getElementById('file');
  const drop = document.getElementById('drop');
  const fileName = document.getElementById('fileName');
  const prompt = document.getElementById('prompt');
  const provider = document.getElementById('provider');
  const model = document.getElementById('model');
  const width = document.getElementById('width');
  const height = document.getElementById('height');
  const seed = document.getElementById('seed');
  const go = document.getElementById('go');
  const status = document.getElementById('status');
  const result = document.getElementById('result');
  const out = document.getElementById('out');
  const download = document.getElementById('download');

  async function loadProviders() {
    const res = await fetch('/api/models');
    const data = await res.json();
    const list = data.providers || [];
    modelsByProvider = {};
    provider.innerHTML = '';
    let firstConfigured = null;
    for (const entry of list) {
      modelsByProvider[entry.name] = entry.models || [];
      if (!firstConfigured && entry.configured) firstConfigured = entry.name;
      const label = entry.configured ? entry.name : entry.name + ' (needs setup)';
      const opt = document.createElement('option');
      opt.value = entry.name;
      opt.textContent = label;
      provider.appendChild(opt);
    }
    provider.value = firstConfigured || (list[0] ? list[0].name : 'pollinations');
    fillModels();
  }

  function fillModels() {
    const name = provider.value;
    const models = modelsByProvider[name] || ['sana'];
    model.innerHTML = models.map((m) => '<option value="' + m + '">' + m + '</option>').join('');
  }

  provider.addEventListener('change', fillModels);

  function readAsDataUrl(file) {
    const reader = new FileReader();
    reader.onload = () => { currentDataUrl = reader.result; };
    reader.readAsDataURL(file);
  }

  drop.addEventListener('click', () => file.click());
  drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('over'); });
  drop.addEventListener('dragleave', () => drop.classList.remove('over'));
  drop.addEventListener('drop', (e) => {
    e.preventDefault();
    drop.classList.remove('over');
    if (e.dataTransfer.files[0]) { file.files = e.dataTransfer.files; readAsDataUrl(e.dataTransfer.files[0]); fileName.textContent = e.dataTransfer.files[0].name; }
  });
  file.addEventListener('change', () => {
    if (file.files[0]) { readAsDataUrl(file.files[0]); fileName.textContent = file.files[0].name; }
  });

  go.addEventListener('click', async () => {
    status.textContent = 'generating... (free tiers may take 15-60s)';
    result.style.display = 'none';
    const body = {
      provider: provider.value,
      prompt: prompt.value,
      model: model.value,
      width: parseInt(width.value, 10),
      height: parseInt(height.value, 10),
      seed: seed.value === '' ? undefined : parseInt(seed.value, 10),
      imageDataUrl: currentDataUrl,
    };
    if (!body.prompt) { status.textContent = 'enter a prompt first.'; return; }
    if (!body.imageDataUrl) { status.textContent = 'choose a reference image first.'; return; }
    try {
      const res = await fetch('/api/generate', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
      const data = await res.json();
      if (!data.ok) { status.textContent = 'error: ' + data.error; return; }
      out.src = data.dataUrl;
      download.href = data.dataUrl;
      const ext = data.contentType === 'image/png' ? 'png' : data.contentType === 'image/jpeg' ? 'jpg' : data.contentType === 'image/gif' ? 'gif' : 'png';
      download.setAttribute('download', 'image-studio-output-' + Date.now() + '.' + ext);
      result.style.display = 'block';
      status.textContent = 'done. provider=' + data.provider + ' model=' + data.model + ' capability=' + data.capability.name;
    } catch (err) {
      status.textContent = 'error: ' + err;
    }
  });

  loadProviders();
</script>
</body>
</html>`;
}
