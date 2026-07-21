import { cp, mkdir, readdir, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import webpack from 'webpack';

import prodConfig from '../build/webpack.prod.js';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const studioRoot = path.resolve(scriptDir, '..');
const distRoot = path.join(studioRoot, 'dist');
const publicRoot = path.join(studioRoot, 'public');

async function runWebpackBuild(): Promise<void> {
  const compiler = webpack(prodConfig);
  await new Promise<void>((resolve, reject) => {
    compiler.run((error, stats) => {
      compiler.close(() => undefined);
      if (error) {
        reject(error);
        return;
      }
      if (!stats) {
        reject(new Error('webpack returned no stats'));
        return;
      }
      if (stats.hasErrors()) {
        reject(new Error(stats.toString({ all: false, errors: true, warnings: true })));
        return;
      }
      resolve();
    });
  });
}

async function copyStaticAssets(sourceDir: string, targetDir: string): Promise<void> {
  await mkdir(targetDir, { recursive: true });
  for (const entry of await readdir(sourceDir, { withFileTypes: true })) {
    const source = path.join(sourceDir, entry.name);
    const target = path.join(targetDir, entry.name);
    if (entry.isDirectory()) {
      await copyStaticAssets(source, target);
      continue;
    }
    if (entry.isFile() && entry.name !== 'index.html') {
      await cp(source, target);
    }
  }
}

async function main(): Promise<void> {
  await rm(distRoot, { recursive: true, force: true });
  await runWebpackBuild();
  await copyStaticAssets(publicRoot, distRoot);
  console.log(`Nova Studio production build complete in ${distRoot}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
