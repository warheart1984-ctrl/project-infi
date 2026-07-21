import { spawnSync } from 'node:child_process';

import { runCoriAlphaUpload, getCoriAlphaRepositoryRoot } from '../services/sovereign-control-plane/src/coriAlpha.ts';

function getReleaseTag(repoPath: string): string | null {
  const result = spawnSync('git', ['-C', repoPath, 'describe', '--tags', '--exact-match', 'HEAD'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'],
  });
  if (result.status === 0 && typeof result.stdout === 'string') {
    const tag = result.stdout.trim();
    if (tag.length > 0) {
      return tag;
    }
  }
  return process.env.CORI_TAG ?? process.env.GITHUB_REF_NAME ?? null;
}

async function main(): Promise<void> {
  const repoPath = process.env.CORI_REPO_PATH ?? getCoriAlphaRepositoryRoot();
  const tag = getReleaseTag(repoPath);
  const result = await runCoriAlphaUpload({
    repoPath,
    developerId: process.env.CORI_DEVELOPER_ID ?? process.env.GIT_AUTHOR_NAME ?? process.env.USER ?? 'unknown',
    commit: process.env.CORI_COMMIT ?? undefined,
    tag,
    mode: 'tag',
    publishToDropbox: true,
    dropboxRoot: process.env.CORI_ALPHA_DROPBOX_ROOT,
  });

  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main().catch((error: unknown) => {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
});
