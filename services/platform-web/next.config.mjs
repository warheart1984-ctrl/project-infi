import path from 'node:path';
import { fileURLToPath } from 'node:url';

const appDir = path.dirname(fileURLToPath(import.meta.url));
const workspaceRoot = path.resolve(appDir, '../..');

/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingRoot: workspaceRoot,
  transpilePackages: ['@aaes-os/platform-sdk', '@aaes-os/sovereignx-router'],
  webpack(config) {
    config.resolve ??= {};
    config.resolve.alias ??= {};
    config.resolve.alias['@aaes-os/sovereignx-router'] = path.resolve(workspaceRoot, 'packages/sovereignx-router/src/pricing.ts');
    return config;
  },
  async rewrites() {
    const apiUrl = process.env.PLATFORM_API_URL ?? 'http://localhost:4100';
    return [
      {
        source: '/api/platform/:path*',
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
