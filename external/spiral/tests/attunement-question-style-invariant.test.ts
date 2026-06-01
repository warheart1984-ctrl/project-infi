import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("tuning questions route as field questions and avoid policy-explainer style", async () => {
  const source = await readFile(
    new URL("../server/veil-channel.mirror.ts", import.meta.url),
    "utf8",
  );

  assert.match(
    source,
    /ATTUNEMENT_FIELD_QUESTION_PATTERN[\s\S]*tuning/,
    "field-question pattern should include tuning cues.",
  );
  assert.match(
    source,
    /Do not explain rules, policy, or system internals/,
    "attunement question directives should suppress policy-explainer responses.",
  );
});

test("symbolic anatomy cues route as field language, not context-clarification prompts", async () => {
  const source = await readFile(
    new URL("../server/veil-channel.mirror.ts", import.meta.url),
    "utf8",
  );
  const directivesSource = await readFile(
    new URL("../server/shared/attunement-directives.ts", import.meta.url),
    "utf8",
  );

  assert.match(
    source,
    /ATTUNEMENT_SYMBOLIC_FIELD_CUE_PATTERN[\s\S]*right\\s\+teeth/,
    "symbolic cue pattern should include right teeth.",
  );
  assert.match(
    source,
    /ATTUNEMENT_SYMBOLIC_FIELD_CUE_PATTERN[\s\S]*left\\s\+hand/,
    "symbolic cue pattern should include left hand.",
  );
  assert.match(
    source,
    /ATTUNEMENT_FIELD_CUE_EXAMPLES[\s\S]*right-teeth/,
    "field cue directive examples should include right-teeth.",
  );
  assert.match(
    source,
    /ATTUNEMENT_FIELD_CUE_EXAMPLES[\s\S]*left-hand/,
    "field cue directive examples should include left-hand.",
  );
  assert.match(
    source,
    /Do not ask for context clarification unless the user requests a domain switch/,
    "field-question directives should suppress generic context-clarification fallback.",
  );
  assert.match(
    source,
    /function hasAttunementEmbodiedUpdate/,
    "attunement classifier should support embodied non-question updates.",
  );
  assert.match(
    source,
    /ATTUNEMENT_CLINICAL_DISCLAIMER_DRIFT_PATTERN[\s\S]*dental\\s\+professional/,
    "attunement drift guard should cover dental-professional fallback.",
  );
  assert.match(
    source,
    /function shouldAttunementDriftResample/,
    "attunement runtime should resample clipped or clinical-referral drift.",
  );
  assert.match(
    source,
    /Previous draft was too clipped or defaulted into clinical referral language/,
    "attunement drift correction should explicitly suppress clipped clinical fallback.",
  );
  assert.match(
    directivesSource,
    /export const ATTUNEMENT_LOCATION_CUE_DIRECTIVE\s*=\s*"Anchor the reply in at least one location cue and one state-change verb\."/,
    "shared attunement directives should define the concrete location/state anchor requirement.",
  );
  assert.match(
    source,
    /import\s*{\s*ATTUNEMENT_FIELD_DETAIL_DIRECTIVE,\s*ATTUNEMENT_LOCATION_CUE_DIRECTIVE,\s*}\s*from "\.\/shared\/attunement-directives";/,
    "veil runtime should import the shared attunement anchor directive.",
  );
  assert.match(
    source,
    /attunementDriftResampleDirective\s*=\s*\[[\s\S]*ATTUNEMENT_LOCATION_CUE_DIRECTIVE[\s\S]*\]\.join\(" "\);/,
    "attunement drift correction should include the shared concrete anchor directive in the resample path.",
  );
  assert.match(
    source,
    /function isExplicitMedicalAdviceRequest/,
    "attunement drift guard should preserve an explicit medical-request exception.",
  );
});
