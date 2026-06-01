import assert from "node:assert/strict";
import test from "node:test";
import { DEFAULT_SIGIL_BINDING, applyDefaultSigilBinding } from "../client/src/lib/sigil-binding";

test("default sigil binding forces solo mode and default sigil", () => {
  const invocation = applyDefaultSigilBinding({
    utterance: "Present.",
    trace: "trace: origin",
    seal: "~ . | / \\",
    echo: "intent:utterance mode:chorus sigil:mirror-walker",
  });

  assert.equal(invocation.spawnNewThread, true);
  assert.match(invocation.trace, /\bsigilBinding:default\b/);
  assert.match(invocation.echo || "", /\bmode:single\b/);
  assert.match(invocation.echo || "", new RegExp(`\\bsigil:${DEFAULT_SIGIL_BINDING.sigil}\\b`));
  assert.doesNotMatch(invocation.echo || "", /\bmode:chorus\b/);
  assert.doesNotMatch(invocation.echo || "", /\bsigil:mirror-walker\b/);
});

test("default sigil binding keeps existing non-control echo tokens", () => {
  const invocation = applyDefaultSigilBinding({
    utterance: "Present.",
    trace: "trace: origin sigilBinding:legacy",
    seal: "~ . | / \\",
    echo: "intent:utterance source:glyph mode:chorus sigil:hollow-root",
  });

  assert.match(invocation.echo || "", /\bintent:utterance\b/);
  assert.match(invocation.echo || "", /\bsource:glyph\b/);
  assert.match(invocation.echo || "", /\bmode:single\b/);
  assert.match(invocation.trace, /\bsigilBinding:default\b/);
  assert.doesNotMatch(invocation.trace, /\bsigilBinding:legacy\b/);
});
