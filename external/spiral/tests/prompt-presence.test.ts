import assert from "node:assert/strict";
import test from "node:test";
import { hasValidPresence, resolvePresenceEvidence } from "../server/prompt";
import { DEFAULT_PROJECT_SIGIL } from "../shared/sigil";

test("resolvePresenceEvidence classifies lexical declarations separately from structural traces", () => {
  assert.equal(resolvePresenceEvidence({ utterance: "Present." }), "lexical");
  assert.equal(resolvePresenceEvidence({ utterance: "Witness: Present." }), "lexical");
  assert.equal(resolvePresenceEvidence({ trace: "trace: anchored" }), "structural");
  assert.equal(resolvePresenceEvidence({ seal: DEFAULT_PROJECT_SIGIL.seal }), "structural");
  assert.equal(resolvePresenceEvidence({ seal: "~ . | / \\" }), "structural");
  assert.equal(resolvePresenceEvidence({ utterance: "plain text" }), "none");
  assert.equal(resolvePresenceEvidence({ utterance: "presently" }), "none");
});

test("hasValidPresence remains a boolean wrapper over resolved evidence", () => {
  assert.equal(hasValidPresence({ utterance: "Present." }), true);
  assert.equal(hasValidPresence({ utterance: "plain text" }), false);
});
