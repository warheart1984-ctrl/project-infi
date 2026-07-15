import path from 'node:path';
import { fileURLToPath } from 'node:url';
import webpack from 'webpack';
import WebpackDevServer from 'webpack-dev-server';

import devConfig from '../build/webpack.dev.js';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const studioRoot = path.resolve(scriptDir, '..');

async function main(): Promise<void> {
  const compiler = webpack(devConfig);
  const server = new WebpackDevServer(devConfig.devServer ?? {}, compiler);
  await server.start();
  process.on('SIGINT', async () => {
    await server.stop();
    process.exit(0);
  });
  process.on('SIGTERM', async () => {
    await server.stop();
    process.exit(0);
  });
  console.log(`Nova Studio development server running from ${studioRoot}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
