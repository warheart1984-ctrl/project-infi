import assert from "node:assert/strict";
import test from "node:test";
import { validateProviderSettingsForVeil } from "../server/lib/provider-settings-validation";

test("provider settings missing resolves to missing with no distortion", () => {
  const result = validateProviderSettingsForVeil(undefined);
  assert.equal(result.state, "missing");
  assert.equal(result.hasProviderSettings, false);
  assert.equal(result.parseResult.success, false);
  assert.deepEqual(result.distortions, []);
});

test("provider settings malformed resolves to invalid distortion", () => {
  const result = validateProviderSettingsForVeil({
    provider: "openai",
    // apiKey intentionally omitted to fail schema validation
  });
  assert.equal(result.state, "invalid");
  assert.equal(result.hasProviderSettings, true);
  assert.equal(result.parseResult.success, false);
  assert.deepEqual(result.distortions, ["provider-settings-invalid"]);
});

test("provider settings valid resolves without distortion", () => {
  const result = validateProviderSettingsForVeil({
    provider: "openai",
    apiKey: "test-key",
  });
  assert.equal(result.state, "valid");
  assert.equal(result.hasProviderSettings, true);
  assert.equal(result.parseResult.success, true);
  assert.deepEqual(result.distortions, []);
});
