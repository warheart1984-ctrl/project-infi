import { runCoriAlphaUpload, getCoriAlphaRepositoryRoot } from '../services/sovereign-control-plane/src/coriAlpha.ts';

async function main(): Promise<void> {
  const result = await runCoriAlphaUpload({
    repoPath: process.env.CORI_REPO_PATH ?? getCoriAlphaRepositoryRoot(),
    developerId: process.env.CORI_DEVELOPER_ID ?? process.env.GIT_AUTHOR_NAME ?? process.env.USER ?? 'unknown',
    commit: process.env.CORI_COMMIT ?? undefined,
    mode: 'push',
    publishToDropbox: true,
    dropboxRoot: process.env.CORI_ALPHA_DROPBOX_ROOT,
  });

  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main().catch((error: unknown) => {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
});
