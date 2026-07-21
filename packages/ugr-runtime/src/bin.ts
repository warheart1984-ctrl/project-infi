#!/usr/bin/env node
import { parseUgrRuntimeCliArgs, runUgrRuntimeCli, runUgrRuntimeServe } from './cli.js';

const argv = process.argv.slice(2);
const options = parseUgrRuntimeCliArgs(argv);

if (options.mode === 'serve') {
  const code = await runUgrRuntimeServe(argv);
  process.exit(code);
}

const code = await runUgrRuntimeCli(argv);
process.exit(code);
