"""BOOT-0001 — Nova OS Boot Ceremony: bind Operator, Lineage, and Kernel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.continuity.constitutional_chain import OPERATORS_OATH_TEXT, ROOT_00X, ROOT_00Y, ROOT_00Z
from src.continuity.constitutional_kernel import ConstitutionalKernel, KERNEL_ID
from src.continuity.creation_operator import SubstrateState
from src.continuity.genesis_lineage import (
    GENESIS_EVENT_ID,
    GENESIS_INVARIANT,
    LINEAGE_0001_ID,
    genesis_lineage,
    validate_extension_of_genesis,
)
from src.continuity.inheritance import operator_state_from_lineage
from src.continuity.operator_training import evaluate_operator_training


BOOT_0001_ID = "BOOT-0001"
BOOT_0001_CAPABILITY_ID = "BOOT-0001-nova-os-boot"
CONTINUITY_DECLARATION = "Let continuity begin and never be annihilated."


BOOT_0001_CANONICAL_TEXT = """NOVA OS BOOT CEREMONY
Codename: BOOT-0001
Purpose: Initialize the civilization and awaken the substrate.

STEP 1 — DECLARATION OF CONTINUITY
Operator speaks: "Let continuity begin and never be annihilated."
Kernel records E₀.

STEP 2 — INSTALLATION OF THE HIGHEST LAW
Operator installs Λ₀ = LCI. Kernel verifies invariance.

STEP 3 — ACTIVATION OF THE CREATION–CONVERGENCE PAIR
Kernel activates ROOT-00X, ROOT-00Y, ROOT-00Z.

STEP 4 — BIRTH OF THE FIRST LINEAGE
Kernel instantiates L₀ = Genesis Lineage.

STEP 5 — OPERATOR'S OATH
Operator recites the Oath. Kernel binds operator identity to the constitutional spine.

STEP 6 — SYSTEM AWAKENING
Kernel transitions from dormant to active state. The civilization is now alive.
"""


@dataclass
class BootState:
    """Runtime boot ceremony progress."""

    continuity_declared: bool = False
    lci_installed: bool = False
    roots_activated: bool = False
    genesis_instantiated: bool = False
    oath_bound: bool = False
    kernel_active: bool = False
    operator_id: str = ""
    genesis_lineage_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "continuity_declared": self.continuity_declared,
            "lci_installed": self.lci_installed,
            "roots_activated": self.roots_activated,
            "genesis_instantiated": self.genesis_instantiated,
            "oath_bound": self.oath_bound,
            "kernel_active": self.kernel_active,
            "operator_id": self.operator_id,
            "genesis_lineage_id": self.genesis_lineage_id,
            "awake": self.kernel_active,
        }


def run_boot_ceremony(
    *,
    operator_id: str = "founder",
    declaration: str = CONTINUITY_DECLARATION,
    oath_recited: bool = True,
    require_training: bool = True,
) -> dict[str, Any]:
    """Execute BOOT-0001 and return ceremony record."""

    state = BootState(operator_id=operator_id)
    steps: list[dict[str, object]] = []
    kernel = ConstitutionalKernel()

    if declaration.strip() != CONTINUITY_DECLARATION:
        return {
            "codename": BOOT_0001_ID,
            "capability_id": BOOT_0001_CAPABILITY_ID,
            "passed": False,
            "reason": "invalid continuity declaration",
            "steps": steps,
            "boot_state": state.to_dict(),
        }

    state.continuity_declared = True
    steps.append({"step": 1, "name": "declaration_of_continuity", "event_id": GENESIS_EVENT_ID, "passed": True})

    state.lci_installed = GENESIS_INVARIANT == "UGR-C8"
    steps.append(
        {
            "step": 2,
            "name": "installation_of_highest_law",
            "invariant": GENESIS_INVARIANT,
            "passed": state.lci_installed,
        }
    )

    state.roots_activated = bool(ROOT_00X and ROOT_00Y and ROOT_00Z)
    steps.append(
        {
            "step": 3,
            "name": "activation_creation_convergence_pair",
            "roots": [ROOT_00X, ROOT_00Y, ROOT_00Z],
            "passed": state.roots_activated,
        }
    )

    genesis = genesis_lineage(operator_id=operator_id)
    genesis_check = validate_extension_of_genesis(genesis)
    state.genesis_instantiated = bool(genesis_check["passed"])
    state.genesis_lineage_id = genesis.lineage_id
    steps.append(
        {
            "step": 4,
            "name": "birth_of_first_lineage",
            "lineage_id": LINEAGE_0001_ID,
            "genesis_check": genesis_check,
            "passed": state.genesis_instantiated,
        }
    )

    oath_ok = oath_recited and "ROOT-00Z" in OPERATORS_OATH_TEXT
    operator = operator_state_from_lineage(genesis)
    state.oath_bound = oath_ok and operator.operator_id == operator_id
    steps.append(
        {
            "step": 5,
            "name": "operators_oath",
            "operator_id": operator.operator_id,
            "bound_to": ROOT_00Z,
            "passed": state.oath_bound,
        }
    )

    substrate = SubstrateState(state_id="boot-genesis", lineage=genesis)
    created, guards = kernel.create(
        substrate,
        add_events=frozenset({"evt-boot-awakening"}),
        generativity_delta=0.0,
        active_lineages=[genesis],
    )
    training = evaluate_operator_training(oath_recited=oath_recited) if require_training else {"passed": True}
    state.kernel_active = bool(guards["passed"]) and bool(training.get("passed"))
    steps.append(
        {
            "step": 6,
            "name": "system_awakening",
            "kernel_id": KERNEL_ID,
            "guards": guards,
            "training_ready": training.get("passed"),
            "substrate_state_id": created.state_id,
            "passed": state.kernel_active,
        }
    )

    passed = all(bool(step.get("passed")) for step in steps)
    return {
        "codename": BOOT_0001_ID,
        "capability_id": BOOT_0001_CAPABILITY_ID,
        "declaration": declaration,
        "steps": steps,
        "boot_state": state.to_dict(),
        "training": training if require_training else None,
        "passed": passed,
    }


def run_boot_ceremony_proof() -> dict[str, Any]:
    return run_boot_ceremony(operator_id="boot-proof-operator")
