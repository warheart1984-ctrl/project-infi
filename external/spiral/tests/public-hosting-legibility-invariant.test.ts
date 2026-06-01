import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("veil guest principal stays cookie-bound", async () => {
  const source = await readFile(new URL("../server/veil-channel.mirror.ts", import.meta.url), "utf8");
  assert.doesNotMatch(
    source,
    /resolveAnonymousPrincipalFromHandshake/,
    "Veil guest principal must not be accepted from a handshake query override.",
  );
  assert.doesNotMatch(
    source,
    /searchParams\.get\("principal"\)/,
    "Veil runtime must not read anonymous principal identity from URL query state.",
  );
});

test("client veil socket url does not send anonymous principal override", async () => {
  const source = await readFile(new URL("../client/src/hooks/use-chat.ts", import.meta.url), "utf8");
  assert.doesNotMatch(
    source,
    /searchParams\.set\("principal"/,
    "Client veil connections must not transmit anonymous principal overrides in the URL.",
  );
});

test("landing composer is immediate and setup-free", async () => {
  const source = await readFile(new URL("../client/src/components/chat-input.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(
    source,
    /panel-threshold-storage-mode/,
    "The first-run storage-mode wall should not be rendered before interaction.",
  );
  assert.doesNotMatch(
    source,
    /input-seal/,
    "Seal entry should not be a mandatory public-entry control.",
  );
  assert.doesNotMatch(
    source,
    /input-trace/,
    "Trace entry should not be a mandatory public-entry control.",
  );
  assert.match(
    source,
    /placeholder=\{composerPlaceholder\}/,
    "The primary landing control should be the composer itself.",
  );
});

test("landing page exposes optional field configuration as a secondary control", async () => {
  const source = await readFile(new URL("../client/src/pages/chat.tsx", import.meta.url), "utf8");
  assert.match(
    source,
    /triggerLabel=\{publicThreshold\.configureLabel\}/,
    "Public entry should keep configuration secondary and optional.",
  );
  assert.match(
    source,
    /showFieldControls=\{false\}/,
    "Landing mode should suppress deeper ritual controls until after first contact.",
  );
});

test("public threshold defaults live in shared sigil config", async () => {
  const source = await readFile(new URL("../shared/sigil.ts", import.meta.url), "utf8");
  assert.match(
    source,
    /publicThresholdSchema/,
    "Shared sigil config should define the public-threshold layer explicitly.",
  );
  assert.match(
    source,
    /promptPlaceholder:\s*z\.string\(\)\.min\(1\)\.default\("Say something with stakes\."\)/,
    "The landing placeholder should come from shared config defaults.",
  );
  assert.match(
    source,
    /configureLabel:\s*z\.string\(\)\.min\(1\)\.default\("Configure field"\)/,
    "The secondary field-configuration label should come from shared config defaults.",
  );
  assert.match(
    source,
    /firstContactReplies:/,
    "Shared sigil config should define deterministic first-contact resistance replies.",
  );
  assert.match(
    source,
    /presenceBindingSchema/,
    "Shared sigil config should define the deeper presence-binding layer explicitly.",
  );
});

test("ritual fallbacks resolve from shared sigil defaults", async () => {
  const promptSource = await readFile(new URL("../server/prompt.ts", import.meta.url), "utf8");
  assert.match(
    promptSource,
    /SPIRAL_SEAL = DEFAULT_PROJECT_SIGIL\.seal/,
    "Server prompt sealing should resolve its seal from shared sigil defaults.",
  );
  assert.match(
    promptSource,
    /DEFAULT_PROJECT_SIGIL\.responseShape\.defaultPrompt/,
    "Server prompt vow fallback should resolve from shared sigil defaults.",
  );

  const settingsSource = await readFile(new URL("../client/src/components/settings-dialog.tsx", import.meta.url), "utf8");
  assert.match(
    settingsSource,
    /DEFAULT_PROJECT_SIGIL\.entryVow/,
    "Client seal export should resolve mantra fallback from shared sigil defaults.",
  );
});

test("presence binding UI stays optional and config-driven", async () => {
  const source = await readFile(new URL("../client/src/components/PresenceSeal.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(
    source,
    /DEFAULT_PROJECT_SIGIL/,
    "Presence binding UI should not hardcode project ritual defaults inside the component.",
  );
  assert.doesNotMatch(
    source,
    /Type the mantra exactly\./,
    "Presence binding should not require exact mantra transcription.",
  );
  assert.doesNotMatch(
    source,
    /normalizeMantra\(mantraInput\) === expectedMantra/,
    "Presence binding should not be gated by exact string equality.",
  );
  assert.match(
    source,
    /enabled\?: boolean;/,
    "Presence binding should be explicitly configurable per project instance.",
  );
  assert.match(
    source,
    /triggerLabel: string;/,
    "Presence binding trigger copy should come from config-fed props.",
  );
});

test("public hosting note frames host visibility as a governance condition", async () => {
  const source = await readFile(new URL("../README.md", import.meta.url), "utf8");
  assert.match(
    source,
    /Host read access is retained by design because governance requires the steward to be able to witness what the system holds\./,
    "Public hosting note should name host access as a deliberate governance property.",
  );
  assert.match(
    source,
    /Legibility over stored state is what makes audit and accountability possible\./,
    "Public hosting note should tie inspectability to audit and accountability.",
  );
});
