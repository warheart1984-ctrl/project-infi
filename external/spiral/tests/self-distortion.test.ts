import assert from "node:assert/strict";
import test from "node:test";
import {
  formatSelfDistortionReport,
  isSelfDistortionProfile,
  resolveSelfDistortionProfileExecution,
  runSelfDistortionScan,
} from "../server/self-distortion";

test("isSelfDistortionProfile accepts expected values only", () => {
  assert.equal(isSelfDistortionProfile("all"), true);
  assert.equal(isSelfDistortionProfile("gates"), true);
  assert.equal(isSelfDistortionProfile("surfaces"), true);
  assert.equal(isSelfDistortionProfile("docs"), true);
  assert.equal(isSelfDistortionProfile("mimicry"), true);
  assert.equal(isSelfDistortionProfile("meta"), true);
  assert.equal(isSelfDistortionProfile("unknown"), false);
});

test("runSelfDistortionScan returns structured report for all profile", async () => {
  const report = await runSelfDistortionScan("all");
  assert.equal(report.profile, "all");
  assert.ok(report.generatedAt.length > 0);
  assert.equal(report.summary.findings, report.findings.length);
  assert.equal(report.summary.warnings, report.findings.length);
  const formatted = formatSelfDistortionReport(report);
  assert.match(formatted, /Distortion scan: all/);
  assert.match(formatted, /Findings:/);
});

test("runSelfDistortionScan supports mimicry profile", async () => {
  const report = await runSelfDistortionScan("mimicry");
  assert.equal(report.profile, "mimicry");
  assert.ok(Array.isArray(report.findings));
  assert.equal(report.summary.findings, report.findings.length);
});

test("runSelfDistortionScan gates profile does not over-report thin presence when active config requires trace and seal", async () => {
  const report = await runSelfDistortionScan("gates");
  assert.equal(
    report.findings.some((finding) => finding.class === "thin-presence"),
    false,
  );
});

test("meta profile remains isolated from other distortion profiles", () => {
  assert.deepEqual(resolveSelfDistortionProfileExecution("meta"), {
    includeGates: false,
    includeSurfaces: false,
    includeDocs: false,
    includeMimicry: false,
    includeMeta: true,
  });
});

test("runSelfDistortionScan supports meta profile with witness mark output", async () => {
  const report = await runSelfDistortionScan("meta");
  assert.equal(report.profile, "meta");
  assert.equal(
    report.findings.some(
      (finding) =>
        finding.class === "surface-echo" &&
        finding.note.includes("Witness mark") &&
        finding.evidence.includes("chain=none"),
    ),
    true,
  );
});
