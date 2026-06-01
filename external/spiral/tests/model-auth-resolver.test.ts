import assert from "node:assert/strict";
import { mkdtemp } from "fs/promises";
import os from "os";
import path from "path";
import test from "node:test";
import { upsertAuthProfile } from "../server/auth-profiles";
import { resolveExecutorAuth, resolveRuntimeAuth } from "../server/model-auth-resolver";

async function withTempAuthStore(
  run: (authProfilesPath: string) => Promise<void>,
): Promise<void> {
  const previousPath = process.env.SPIRAL_AUTH_PROFILES_PATH;
  const dir = await mkdtemp(path.join(os.tmpdir(), "spiral-auth-test-"));
  const authProfilesPath = path.join(dir, "auth-profiles.json");
  process.env.SPIRAL_AUTH_PROFILES_PATH = authProfilesPath;
  try {
    await run(authProfilesPath);
  } finally {
    if (previousPath === undefined) {
      delete process.env.SPIRAL_AUTH_PROFILES_PATH;
    } else {
      process.env.SPIRAL_AUTH_PROFILES_PATH = previousPath;
    }
  }
}

test("resolveRuntimeAuth rejects auth profiles deterministically", async () => {
  await assert.rejects(
    resolveRuntimeAuth({
      provider: "openai",
      authProfileId: "codex-oauth-default",
      fallbackInlineApiKey: "inline-key",
    }),
    /does not accept authProfileId/i,
  );
});

test("resolveRuntimeAuth requires inline API key", async () => {
  await assert.rejects(
    resolveRuntimeAuth({
      provider: "openai",
    }),
    /requires fallbackInlineApiKey/i,
  );
});

test("resolveRuntimeAuth builds provider headers from inline API key", async () => {
  const resolved = await resolveRuntimeAuth({
    provider: "anthropic",
    requestedModel: "claude-sonnet-4-20250514",
    fallbackInlineApiKey: "anthropic-inline",
  });
  assert.equal(resolved.source, "inline-api-key");
  assert.equal(resolved.headers["x-api-key"], "anthropic-inline");
});

test("resolveExecutorAuth requires oauth auth profile and rejects inline API key", async () => {
  await withTempAuthStore(async () => {
    await assert.rejects(
      resolveExecutorAuth({
        provider: "codex-local",
        fallbackInlineApiKey: "should-not-be-used",
      }),
      /does not accept fallbackInlineApiKey/i,
    );
  });
});

test("resolveExecutorAuth rejects missing profile, api-key profile, and expired oauth profile", async () => {
  await withTempAuthStore(async () => {
    await assert.rejects(
      resolveExecutorAuth({
        provider: "codex-local",
        authProfileId: "missing-profile",
      }),
      /not found/i,
    );

    await upsertAuthProfile({
      id: "api-key-profile",
      type: "api_key",
      provider: "openai",
      apiKey: "sk-test",
      createdAt: Date.now(),
      updatedAt: Date.now(),
    });
    await assert.rejects(
      resolveExecutorAuth({
        provider: "codex-local",
        authProfileId: "api-key-profile",
      }),
      /must be type oauth/i,
    );

    await upsertAuthProfile({
      id: "expired-oauth",
      type: "oauth",
      provider: "openai",
      accessToken: "expired-token",
      expiresAt: Date.now() - 1_000,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    });
    await assert.rejects(
      resolveExecutorAuth({
        provider: "codex-local",
        authProfileId: "expired-oauth",
      }),
      /expired/i,
    );
  });
});

test("resolveExecutorAuth accepts valid oauth auth profile", async () => {
  await withTempAuthStore(async () => {
    await upsertAuthProfile({
      id: "codex-oauth-default",
      type: "oauth",
      provider: "openai",
      accessToken: "oauth-token-1",
      expiresAt: Date.now() + 60_000,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    });

    const resolved = await resolveExecutorAuth({
      provider: "codex-local",
      requestedModel: "gpt-5-codex",
      authProfileId: "codex-oauth-default",
    });

    assert.equal(resolved.provider, "codex-local");
    assert.equal(resolved.profileIdUsed, "codex-oauth-default");
    assert.equal(resolved.source, "auth-profile-oauth");
    assert.equal(resolved.accessToken, "oauth-token-1");
  });
});
