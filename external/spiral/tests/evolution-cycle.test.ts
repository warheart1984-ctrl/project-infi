import assert from "node:assert/strict";
import test from "node:test";
import {
  evolutionTriggerAllowsProposalApply,
  pulseAncillaryWorkAllowed,
} from "../server/evolution-cycle";

test("manual evolution cycles may cross the apply boundary", () => {
  assert.equal(evolutionTriggerAllowsProposalApply("manual"), true);
});

test("pulse evolution cycles remain execution-only until human promotion", () => {
  assert.equal(evolutionTriggerAllowsProposalApply("pulse"), false);
});

test("pulse ancillary work is blocked when background pulse is disabled", () => {
  assert.equal(
    pulseAncillaryWorkAllowed({
      backgroundPulseEnabled: false,
      mutationSealEnabled: false,
    }),
    false,
  );
});

test("pulse ancillary work is blocked when mutation seal is enabled", () => {
  assert.equal(
    pulseAncillaryWorkAllowed({
      backgroundPulseEnabled: true,
      mutationSealEnabled: true,
    }),
    false,
  );
});

test("pulse ancillary work remains allowed only when pulse is enabled and seal is open", () => {
  assert.equal(
    pulseAncillaryWorkAllowed({
      backgroundPulseEnabled: true,
      mutationSealEnabled: false,
    }),
    true,
  );
});
