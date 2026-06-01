import assert from "node:assert/strict";
import test from "node:test";
import {
  formatSelfEvaluationReport,
  isSelfEvaluationProfile,
  runSelfEvaluation,
} from "../server/self-evaluation";

test("isSelfEvaluationProfile accepts only known profiles", () => {
  assert.equal(isSelfEvaluationProfile("integrity"), true);
  assert.equal(isSelfEvaluationProfile("gates"), true);
  assert.equal(isSelfEvaluationProfile("contracts"), true);
  assert.equal(isSelfEvaluationProfile("all"), true);
  assert.equal(isSelfEvaluationProfile("unknown"), false);
});

test("runSelfEvaluation returns structured report for integrity profile", async () => {
  const report = await runSelfEvaluation("integrity");
  assert.equal(report.profile, "integrity");
  assert.ok(report.generatedAt.length > 0);
  assert.ok(report.summary.total >= 1);
  assert.equal(report.summary.total, report.checks.length);
  assert.equal(report.summary.passed + report.summary.failed, report.summary.total);
  const formatted = formatSelfEvaluationReport(report);
  assert.match(formatted, /Evaluation: self-inspection integrity/);
});
