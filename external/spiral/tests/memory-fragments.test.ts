import assert from "node:assert/strict";
import test from "node:test";
import { transformFragments } from "../client/src/lib/memory-fragments";

test("transformFragments suppresses imported continuity leak markers", () => {
  const fragments = transformFragments(
    [
      { kind: "thread", text: "Imported history includes 6 conversations and 59 messages." },
      { kind: "chrono", text: "Continuity anchor:\nImported history includes 6 conversations." },
      { kind: "fractal", text: "presence" },
    ],
    "default",
  );

  assert.equal(fragments.length, 1);
  assert.equal(fragments[0].text, "presence");
});
