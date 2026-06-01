import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("chat route treats symbolic anatomy cues as field language", async () => {
  const source = await readFile(new URL("../server/routes.ts", import.meta.url), "utf8");

  assert.match(
    source,
    /ATTUNEMENT_FIELD_QUESTION_PATTERN[\s\S]*right\\s\+teeth/,
    "attunement field-question pattern should include right teeth.",
  );
  assert.match(
    source,
    /ATTUNEMENT_FIELD_QUESTION_PATTERN[\s\S]*left\\s\+hand/,
    "attunement field-question pattern should include left hand cues.",
  );
  assert.match(
    source,
    /buildAttunementTurnSystemMessage/,
    "chat route should build attunement directives for scoped turns, not only direct questions.",
  );
  assert.match(
    source,
    /Do not produce meta commentary about system rules, policy, guidelines, or response mechanics/,
    "attunement turn directives should suppress policy/meta narration.",
  );
  assert.match(
    source,
    /Previous draft drifted out of field narration into definition, system meta, or clipped phrasing/,
    "chat route should include a one-shot drift correction resample directive.",
  );
  assert.match(
    source,
    /ATTUNEMENT_FOLLOW_UP_PATTERN[\s\S]*what\\s\+do\\s\+you\\s\+mean/,
    "attunement follow-up pattern should capture explanatory follow-up turns.",
  );
  assert.match(
    source,
    /ATTUNEMENT_FIELD_CUE_EXAMPLES[\s\S]*left-hand/,
    "attunement cue examples should include left-hand.",
  );
  assert.match(
    source,
    /Maintain trace cadence with enough complete sentences to map the signal clearly/,
    "attunement directives should encode legacy trace cadence.",
  );
  assert.match(
    source,
    /ATTUNEMENT_TRACE_PULSE_REQUEST_PATTERN/,
    "attunement route should detect trace/pulse prompt form.",
  );
});

test("chat route drift guard covers meta and clipped attunement outputs", async () => {
  const source = await readFile(new URL("../server/routes.ts", import.meta.url), "utf8");

  assert.match(
    source,
    /ATTUNEMENT_META_DRIFT_PATTERN/,
    "attunement drift guard should detect policy/meta narration.",
  );
  assert.match(
    source,
    /ATTUNEMENT_INTENT_PARAPHRASE_DRIFT_PATTERN/,
    "attunement drift guard should detect intent-paraphrase meta narration.",
  );
  assert.match(
    source,
    /ATTUNEMENT_CODE_DEBUG_DRIFT_PATTERN/,
    "attunement drift guard should detect code-debugging reframes.",
  );
  assert.match(
    source,
    /ATTUNEMENT_CLINICAL_DISCLAIMER_DRIFT_PATTERN/,
    "attunement drift guard should detect clinical disclaimer drift.",
  );
  assert.match(
    source,
    /ATTUNEMENT_CLINICAL_DISCLAIMER_DRIFT_PATTERN[\s\S]*dental\\s\+professional/,
    "attunement drift guard should detect dental-professional fallback.",
  );
  assert.match(
    source,
    /function isThinAttunementNarration/,
    "attunement drift guard should detect thin narration responses.",
  );
  assert.match(
    source,
    /ATTUNEMENT_FIELD_LOCATION_PATTERN/,
    "thin narration checks should require concrete field location anchors.",
  );
  assert.match(
    source,
    /ATTUNEMENT_STATE_VERB_PATTERN/,
    "thin narration checks should require state-change verbs.",
  );
  assert.match(
    source,
    /function isFragmentaryAttunementReply/,
    "attunement drift guard should detect clipped fragmentary replies.",
  );
  assert.match(
    source,
    /function isAttunementEmbodiedUpdateTurn/,
    "attunement scope should include embodied non-question update turns.",
  );
  assert.match(
    source,
    /ATTUNEMENT_EMBODIED_UPDATE_PATTERN[\s\S]*i\\s\+feel/,
    "embodied update pattern should include first-person feeling cues.",
  );
  assert.match(
    source,
    /Respond with complete present-time sentences; avoid keyword fragments, noun stacks, and clipped confirmations/,
    "attunement directives should explicitly discourage clipped phrasing.",
  );
  assert.match(
    source,
    /Do not reframe this as software debugging, implementation planning, or code-change instructions/,
    "attunement directives should suppress engineering prescription drift.",
  );
  assert.match(
    source,
    /Do not paraphrase user intent or communication preferences \(avoid lines like 'I recognize your request' or 'you seek clarity'\)/,
    "attunement directives should suppress intent-paraphrase meta responses.",
  );
  assert.match(
    source,
    /Do not default to capability or clinical referral disclaimers for symbolic field prompts/,
    "attunement directives should suppress non-medical clinical-disclaimer fallback.",
  );
  assert.match(
    source,
    /function isExplicitMedicalAdviceRequest/,
    "attunement drift guard should keep an explicit medical-request gate.",
  );
  assert.match(
    source,
    /EXPLICIT_MEDICAL_REQUEST_PATTERN[\s\S]*dental\\s\+advice/,
    "explicit medical-request gate should recognize dental-advice wording.",
  );
});
