import { describe, expect, it } from 'vitest';

import { parseCliArgs, usageText } from './cliArgs.js';

describe('parseCliArgs', () => {
  it('parses a generate command with a positional input', () => {
    const args = parseCliArgs(['photo.png', '-p', 'watercolor version', '-m', 'sana', '--provider', 'pollinations', '-o', 'out.png', '--width', '512', '--height', '384', '--seed', '9']);
    expect(args.command).toBe('generate');
    if (args.command === 'generate') {
      expect(args.input).toBe('photo.png');
      expect(args.prompt).toBe('watercolor version');
      expect(args.model).toBe('sana');
      expect(args.provider).toBe('pollinations');
      expect(args.out).toBe('out.png');
      expect(args.width).toBe(512);
      expect(args.height).toBe(384);
      expect(args.seed).toBe(9);
    }
  });

  it('supports --url instead of a local file', () => {
    const args = parseCliArgs(['--url', 'https://example.com/photo.jpg', '-p', 'neon version']);
    if (args.command === 'generate') {
      expect(args.referenceUrl).toBe('https://example.com/photo.jpg');
      expect(args.input).toBeUndefined();
    }
  });

  it('parses --models', () => {
    expect(parseCliArgs(['--models']).command).toBe('models');
  });

  it('parses --server with a custom port', () => {
    const args = parseCliArgs(['--server', '--port', '8080']);
    expect(args.command).toBe('server');
    if (args.command === 'server') {
      expect(args.port).toBe(8080);
    }
  });

  it('parses --help', () => {
    expect(parseCliArgs(['--help']).command).toBe('help');
    expect(parseCliArgs(['-h']).command).toBe('help');
  });

  it('rejects unknown flags', () => {
    expect(() => parseCliArgs(['--bogus'])).toThrow(/Unknown option/);
  });

  it('rejects missing option values', () => {
    expect(() => parseCliArgs(['-p'])).toThrow(/Missing value/);
  });

  it('rejects non-integer numeric options', () => {
    expect(() => parseCliArgs(['--seed', 'abc'])).toThrow(/expects an integer/);
    expect(() => parseCliArgs(['--port', '999999'])).toThrow(/expects a number between/);
  });

  it('exposes usage text with the main commands', () => {
    const text = usageText();
    expect(text).toContain('image-studio');
    expect(text).toContain('--models');
    expect(text).toContain('--server');
  });
});
