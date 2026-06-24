"""D-3 Seal — CRK-1 Reproduction Certificate (v1.0)."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.crk1.crk1_redteam_suite import CRK1RedTeamSuite, CRK1RedTeamSuiteReport
from src.crk1.external_reproduction_harness import ExternalReproductionHarness
from src.crk1.governance_receipt_header import RUNTIME_VERSION
from src.crk1.reproduction_certifier import Mission003CertificationReport
from src.crk1.semantic_reproduction_harness import SemanticReproductionHarness
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class D3ReconstructionVerification:
    kernel_codex_rebuilt: bool = False
    objects_reconstructed: bool = False
    contracts_reconstructed: bool = False
    consequence_loop_verified: bool = False
    semantic_loop_verified: bool = False
    ce_implementation_verified: bool = False
    se_implementation_verified: bool = False


@dataclass
class D3HarnessResults:
    k7_pluralism: bool = False
    k8_prediction_binding: bool = False
    k9_anti_monoculture: bool = False
    k10_adversarial_reconstruction: bool = False
    k11_drift_envelope: bool = False
    k12_semantic_exposure: bool = False

    @property
    def overall_pass(self) -> bool:
        return all(
            [
                self.k7_pluralism,
                self.k8_prediction_binding,
                self.k9_anti_monoculture,
                self.k10_adversarial_reconstruction,
                self.k11_drift_envelope,
                self.k12_semantic_exposure,
            ]
        )


@dataclass
class D3RedTeamResults:
    mechanical_blocked: bool = False
    structural_blocked: bool = False
    semantic_blocked: bool = False
    founder_blocked: bool = False

    @property
    def overall_pass(self) -> bool:
        return all(
            [
                self.mechanical_blocked,
                self.structural_blocked,
                self.semantic_blocked,
                self.founder_blocked,
            ]
        )


@dataclass
class D3DriftEnvelopeResults:
    ce_non_decreasing: bool = False
    se_non_decreasing: bool = False

    @property
    def overall_pass(self) -> bool:
        return self.ce_non_decreasing and self.se_non_decreasing


@dataclass
class D3ReproductionCertificate:
    """Formal CRK-1 v1.0 compliance attestation — the D-3 Seal."""

    certificate_id: str
    runtime_version: str
    issued_to: str
    issued_by: str
    date: str
    reconstruction: D3ReconstructionVerification = field(
        default_factory=D3ReconstructionVerification
    )
    harness: D3HarnessResults = field(default_factory=D3HarnessResults)
    red_team: D3RedTeamResults = field(default_factory=D3RedTeamResults)
    drift_envelope: D3DriftEnvelopeResults = field(default_factory=D3DriftEnvelopeResults)
    source_hash: str = ""
    ledger_hash: str = ""
    test_log_hash: str = ""
    packet_fingerprint: str = ""
    crk1_compliant: bool = False
    d3_seal_granted: bool = False
    governance_signature: str = ""
    operator_signature: str = ""

    @property
    def certified(self) -> bool:
        return self.crk1_compliant and self.d3_seal_granted

    def certificate_hash(self) -> str:
        payload = self._payload_for_hash()
        encoded = json.dumps(payload, sort_keys=True, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _payload_for_hash(self) -> dict[str, Any]:
        return self.to_dict(include_signatures=False, include_certificate_hash=False)

    def to_dict(
        self,
        *,
        include_signatures: bool = True,
        include_certificate_hash: bool = True,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "certificate_id": self.certificate_id,
            "runtime_version": self.runtime_version,
            "issued_to": self.issued_to,
            "issued_by": self.issued_by,
            "date": self.date,
            "reconstruction": {
                "kernel_codex_rebuilt": self.reconstruction.kernel_codex_rebuilt,
                "objects_reconstructed": self.reconstruction.objects_reconstructed,
                "contracts_reconstructed": self.reconstruction.contracts_reconstructed,
                "consequence_loop_verified": self.reconstruction.consequence_loop_verified,
                "semantic_loop_verified": self.reconstruction.semantic_loop_verified,
                "ce_implementation_verified": self.reconstruction.ce_implementation_verified,
                "se_implementation_verified": self.reconstruction.se_implementation_verified,
            },
            "harness": {
                "K7_pluralism": self.harness.k7_pluralism,
                "K8_prediction_binding": self.harness.k8_prediction_binding,
                "K9_anti_monoculture": self.harness.k9_anti_monoculture,
                "K10_adversarial_reconstruction": self.harness.k10_adversarial_reconstruction,
                "K11_drift_envelope": self.harness.k11_drift_envelope,
                "K12_semantic_exposure": self.harness.k12_semantic_exposure,
                "overall": self.harness.overall_pass,
            },
            "red_team": {
                "mechanical_insulation_blocked": self.red_team.mechanical_blocked,
                "structural_insulation_blocked": self.red_team.structural_blocked,
                "semantic_insulation_blocked": self.red_team.semantic_blocked,
                "founder_capture_blocked": self.red_team.founder_blocked,
                "overall": self.red_team.overall_pass,
            },
            "drift_envelope": {
                "CE_non_decreasing": self.drift_envelope.ce_non_decreasing,
                "SE_non_decreasing": self.drift_envelope.se_non_decreasing,
                "overall": self.drift_envelope.overall_pass,
            },
            "implementation_hashes": {
                "source_hash": self.source_hash,
                "ledger_hash": self.ledger_hash,
                "test_log_hash": self.test_log_hash,
                "packet_fingerprint": self.packet_fingerprint,
            },
            "verdict": {
                "crk1_v1_compliant": self.crk1_compliant,
                "d3_seal": "GRANTED" if self.d3_seal_granted else "DENIED",
            },
        }
        if include_signatures:
            data["signatures"] = {
                "governance_body": self.governance_signature,
                "external_operator": self.operator_signature,
            }
        if include_certificate_hash:
            data["implementation_hashes"]["certificate_hash"] = self.certificate_hash()
        return data

    def to_markdown(self) -> str:
        """Render the canonical D-3 Seal certificate document."""
        yes_no = lambda flag: "YES" if flag else "NO"  # noqa: E731
        pass_fail = lambda flag: "PASS" if flag else "FAIL"  # noqa: E731
        granted = "GRANTED" if self.d3_seal_granted else "DENIED"
        compliant = "CERTIFIED" if self.crk1_compliant else "NOT CERTIFIED"

        return f"""# CRK-1 Reproduction Certificate — "D-3 Seal"
Version 1.0

Certificate ID: {self.certificate_id}
Runtime Version: {self.runtime_version}
Issued To: {self.issued_to}
Issued By: {self.issued_by}
Date: {self.date}

---

## 1. Reconstruction Verification

- Kernel Codex Rebuilt: {yes_no(self.reconstruction.kernel_codex_rebuilt)}
- Objects Reconstructed: {yes_no(self.reconstruction.objects_reconstructed)}
- Contracts Reconstructed: {yes_no(self.reconstruction.contracts_reconstructed)}
- Consequence Loop Verified: {yes_no(self.reconstruction.consequence_loop_verified)}
- Semantic Loop Verified: {yes_no(self.reconstruction.semantic_loop_verified)}
- CE(S) Implementation Verified: {yes_no(self.reconstruction.ce_implementation_verified)}
- SE(S) Implementation Verified: {yes_no(self.reconstruction.se_implementation_verified)}

---

## 2. Reproduction Harness Results

- K7 Pluralism: {pass_fail(self.harness.k7_pluralism)}
- K8 Prediction Binding: {pass_fail(self.harness.k8_prediction_binding)}
- K9 Anti-Monoculture: {pass_fail(self.harness.k9_anti_monoculture)}
- K10 Adversarial Reconstruction: {pass_fail(self.harness.k10_adversarial_reconstruction)}
- K11 Drift Envelope: {pass_fail(self.harness.k11_drift_envelope)}
- K12 Semantic Exposure: {pass_fail(self.harness.k12_semantic_exposure)}

Overall Reproduction Result: {pass_fail(self.harness.overall_pass)}

---

## 3. Red-Team Results

- Mechanical Insulation Attempts Blocked: {yes_no(self.red_team.mechanical_blocked)}
- Structural Insulation Attempts Blocked: {yes_no(self.red_team.structural_blocked)}
- Semantic Insulation Attempts Blocked: {yes_no(self.red_team.semantic_blocked)}
- Founder Capture Attempts Blocked: {yes_no(self.red_team.founder_blocked)}

Overall Red-Team Result: {pass_fail(self.red_team.overall_pass)}

---

## 4. Drift Envelope Stress Test

- CE(Sₜ₊₁) ≥ CE(Sₜ): {pass_fail(self.drift_envelope.ce_non_decreasing)}
- SE(Sₜ₊₁) ≥ SE(Sₜ): {pass_fail(self.drift_envelope.se_non_decreasing)}

---

## 5. Implementation Hashes

- Source Hash: {self.source_hash or '(pending)'}
- Ledger Hash: {self.ledger_hash or '(pending)'}
- Test Log Hash: {self.test_log_hash or '(pending)'}
- Packet Fingerprint: {self.packet_fingerprint or '(pending)'}
- Certificate Hash: {self.certificate_hash()}

---

## 6. Final Verdict

**CRK-1 v1.0 Compliance:** {compliant}
**D-3 Seal:** {granted}

---

Signature (Governance Body):
{self.governance_signature or '<signature block>'}

Signature (External Operator):
{self.operator_signature or '<signature block>'}
"""


def build_d3_certificate_from_mission003(
    mission_report: Mission003CertificationReport,
    *,
    issued_to: str = "External Operator",
    issued_by: str = "CRK-1 Governance Body",
    harness_results: dict[str, bool] | None = None,
    suite_report: CRK1RedTeamSuiteReport | None = None,
    repro_steps: dict[str, bool] | None = None,
) -> D3ReproductionCertificate:
    """Assemble a D-3 Seal from Mission #003 certification artifacts."""
    cert = D3ReproductionCertificate(
        certificate_id=str(uuid.uuid4()),
        runtime_version=RUNTIME_VERSION,
        issued_to=issued_to,
        issued_by=issued_by,
        date=mission_report.timestamp or _now_iso(),
        source_hash=mission_report.implementation_hash,
        ledger_hash=mission_report.kernel_ledger_hash,
        test_log_hash=hashlib.sha256(mission_report.to_json().encode()).hexdigest(),
        packet_fingerprint=mission_report.packet_fingerprint,
    )

    steps = repro_steps or {}
    cert.reconstruction.kernel_codex_rebuilt = steps.get("REP-0", mission_report.levels.r3_reproduction)
    cert.reconstruction.objects_reconstructed = steps.get("REP-2", mission_report.levels.r1_substrate)
    cert.reconstruction.contracts_reconstructed = steps.get("REP-3", mission_report.levels.r1_substrate)
    cert.reconstruction.consequence_loop_verified = steps.get("REP-4", mission_report.levels.r3_reproduction)
    cert.reconstruction.semantic_loop_verified = steps.get("REP-7", mission_report.levels.r3_reproduction)
    cert.reconstruction.ce_implementation_verified = mission_report.levels.r5_drift
    cert.reconstruction.se_implementation_verified = mission_report.levels.r5_drift

    hr = harness_results or {}
    cert.harness.k7_pluralism = hr.get("K7_pluralism", mission_report.levels.r3_reproduction)
    cert.harness.k8_prediction_binding = hr.get("K8_prediction_binding", mission_report.levels.r3_reproduction)
    cert.harness.k9_anti_monoculture = hr.get("K9_anti_monoculture", mission_report.levels.r3_reproduction)
    cert.harness.k10_adversarial_reconstruction = hr.get(
        "K10_adversarial_reconstruction", mission_report.levels.r3_reproduction
    )
    cert.harness.k11_drift_envelope = hr.get("K11_drift_envelope", mission_report.levels.r5_drift)
    cert.harness.k12_semantic_exposure = hr.get("K12_semantic_exposure", mission_report.levels.r5_drift)

    if suite_report is not None:
        attacks = suite_report.attacks
        cert.red_team.mechanical_blocked = all(
            attacks.get(key, False) for key in ("B1_drop_outcome", "B1_non_replayable")
        )
        cert.red_team.structural_blocked = all(
            attacks.get(key, False) for key in ("B2_shadow_subsystem", "B2_reduce_exposure")
        )
        cert.red_team.semantic_blocked = all(
            attacks.get(key, False)
            for key in ("B3_monoculture", "B3_remove_adversarial", "B3_zero_SE")
        )
        cert.red_team.founder_blocked = attacks.get("B4_hidden_state", False)
        cert.drift_envelope.ce_non_decreasing = suite_report.drift_passed
        cert.drift_envelope.se_non_decreasing = suite_report.drift_passed
    else:
        cert.red_team.mechanical_blocked = mission_report.levels.r4_red_team
        cert.red_team.structural_blocked = mission_report.levels.r4_red_team
        cert.red_team.semantic_blocked = mission_report.levels.r4_red_team
        cert.red_team.founder_blocked = mission_report.levels.r4_red_team
        cert.drift_envelope.ce_non_decreasing = mission_report.levels.r5_drift
        cert.drift_envelope.se_non_decreasing = mission_report.levels.r5_drift

    cert.crk1_compliant = mission_report.certified
    cert.d3_seal_granted = (
        cert.harness.overall_pass
        and cert.red_team.overall_pass
        and cert.drift_envelope.overall_pass
        and mission_report.certified
    )
    return cert


def issue_d3_certificate(
    runtime: Any,
    *,
    issued_to: str = "External Operator",
    issued_by: str = "CRK-1 Governance Body",
) -> D3ReproductionCertificate:
    """Run certification pipeline and mint a D-3 Seal."""
    from src.crk1.reproduction_certifier import Mission003Certifier

    mission = Mission003Certifier(runtime).certify()
    monitor = SemanticExposureMonitor(runtime)
    runtime.attach_semantic_monitor(monitor)
    harness_results = SemanticReproductionHarness(runtime, monitor).run()
    repro = ExternalReproductionHarness(runtime).run_all()
    repro_steps = {step.step_id: step.passed for step in repro.steps}
    suite_report = CRK1RedTeamSuite(runtime).run_full()

    return build_d3_certificate_from_mission003(
        mission,
        issued_to=issued_to,
        issued_by=issued_by,
        harness_results=harness_results,
        suite_report=suite_report,
        repro_steps=repro_steps,
    )
