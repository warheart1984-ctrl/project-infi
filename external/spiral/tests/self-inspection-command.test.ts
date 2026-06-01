import assert from "node:assert/strict";
import test from "node:test";
import { parseSelfInspectCommand } from "../server/self-inspection-command";

test("parseSelfInspectCommand handles summary aliases", () => {
  assert.deepEqual(parseSelfInspectCommand("self inspect"), { type: "summary" });
  assert.deepEqual(parseSelfInspectCommand("self-inspect?"), { type: "summary" });
  assert.deepEqual(parseSelfInspectCommand("code trace"), { type: "summary" });
  assert.deepEqual(parseSelfInspectCommand("mirror mode"), { type: "summary" });
  assert.deepEqual(parseSelfInspectCommand("self-view mode"), { type: "summary" });
});

test("parseSelfInspectCommand handles query forms with punctuation and polite prefixes", () => {
  assert.deepEqual(parseSelfInspectCommand("self inspect auth guard"), {
    type: "query",
    query: "auth guard",
  });
  assert.deepEqual(parseSelfInspectCommand("self-inspect: where memory sealed is enforced"), {
    type: "query",
    query: "where memory sealed is enforced",
  });
  assert.deepEqual(parseSelfInspectCommand("can you self inspect where authentication is enforced?"), {
    type: "query",
    query: "where authentication is enforced?",
  });
  assert.deepEqual(parseSelfInspectCommand("please code trace wakeRigAgents"), {
    type: "query",
    query: "wakeRigAgents",
  });
});

test("parseSelfInspectCommand supports inline phrasing and ignores unrelated text", () => {
  assert.deepEqual(parseSelfInspectCommand("for this request, self inspect storage pointer flow"), {
    type: "query",
    query: "storage pointer flow",
  });
  assert.equal(parseSelfInspectCommand("do you see your own code?"), undefined);
  assert.equal(parseSelfInspectCommand("remember I like tea"), undefined);
});
