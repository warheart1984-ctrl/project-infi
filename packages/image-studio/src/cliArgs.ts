export type CliCommand =
  | {
      command: 'generate';
      input?: string;
      prompt?: string;
      model?: string;
      provider?: string;
      out?: string;
      width?: number;
      height?: number;
      seed?: number;
      referenceUrl?: string;
    }
  | { command: 'models' }
  | { command: 'server'; port: number }
  | { command: 'help' };

const PORT_NUMBER = /^[0-9]{1,5}$/;
const INTEGER = /^-?[0-9]+$/;

export function parseCliArgs(argv: readonly string[]): CliCommand {
  let command: 'generate' | 'models' | 'server' | 'help' = 'generate';
  const positionals: string[] = [];
  let prompt: string | undefined;
  let model: string | undefined;
  let provider: string | undefined;
  let out: string | undefined;
  let width: number | undefined;
  let height: number | undefined;
  let seed: number | undefined;
  let referenceUrl: string | undefined;
  let port = 4317;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    switch (arg) {
      case '--models':
        command = 'models';
        break;
      case '--server':
        command = 'server';
        break;
      case '--help':
      case '-h':
        command = 'help';
        break;
      case '-p':
      case '--prompt':
        prompt = readValue(argv, index, arg);
        index += 1;
        break;
      case '-m':
      case '--model':
        model = readValue(argv, index, arg);
        index += 1;
        break;
      case '--provider':
        provider = readValue(argv, index, arg);
        index += 1;
        break;
      case '-o':
      case '--out':
        out = readValue(argv, index, arg);
        index += 1;
        break;
      case '--url':
        referenceUrl = readValue(argv, index, arg);
        index += 1;
        break;
      case '--port':
        port = readPort(argv, index);
        index += 1;
        break;
      case '--width':
        width = readInteger(argv, index, arg);
        index += 1;
        break;
      case '--height':
        height = readInteger(argv, index, arg);
        index += 1;
        break;
      case '--seed':
        seed = readInteger(argv, index, arg);
        index += 1;
        break;
      default:
        if (arg.startsWith('-')) {
          throw new Error(`Unknown option: ${arg}`);
        }
        positionals.push(arg);
        break;
    }
  }

  if (command === 'generate') {
    return {
      command,
      input: positionals[0],
      prompt,
      model,
      provider,
      out,
      width,
      height,
      seed,
      referenceUrl,
    };
  }
  if (command === 'server') {
    return { command, port };
  }
  return { command };
}

function readValue(argv: readonly string[], index: number, flag: string): string {
  const value = argv[index + 1];
  if (value === undefined || value.startsWith('--')) {
    throw new Error(`Missing value for ${flag}`);
  }
  return value;
}

function readInteger(argv: readonly string[], index: number, flag: string): number {
  const raw = readValue(argv, index, flag);
  if (!INTEGER.test(raw)) {
    throw new Error(`${flag} expects an integer, got "${raw}"`);
  }
  return Number.parseInt(raw, 10);
}

function readPort(argv: readonly string[], index: number): number {
  const raw = readValue(argv, index, '--port');
  if (!PORT_NUMBER.test(raw)) {
    throw new Error(`--port expects a number between 0 and 65535, got "${raw}"`);
  }
  const value = Number.parseInt(raw, 10);
  if (value > 65535) {
    throw new Error(`--port expects a number between 0 and 65535, got "${raw}"`);
  }
  return value;
}

export function usageText(): string {
  return [
    'image-studio — free cloud-hosted image-to-image studio',
    '',
    'Usage:',
    '  image-studio <input-image> -p "transform it into ..." [options]',
    '  image-studio --url <image-url> -p "..." [options]',
    '  image-studio --models',
    '  image-studio --server [--port 4317]',
    '',
    'Options:',
    '  -p, --prompt <text>   Required. Transformation instruction for the reference image.',
    '  -m, --model <name>    Model to use (default: sana for pollinations).',
    '  --provider <name>     pollinations (free, keyless) | cloudflare | huggingface.',
    '  -o, --out <path>      Output file path (default: image-studio-output-<timestamp>.<ext>).',
    '  --url <image-url>     Use a hosted image URL as the reference instead of a local file.',
    '  --width <px>          Output width (default: 1024).',
    '  --height <px>         Output height (default: 1024).',
    '  --seed <n>            Seed for reproducible output.',
    '  --models              List available free models and exit.',
    '  --server              Start the local web UI.',
    '  --port <n>            Web UI port (default: 4317).',
    '  -h, --help            Show this help.',
  ].join('\n');
}
