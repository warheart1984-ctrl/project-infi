#!/usr/bin/env python3
"""Add children to parent genomes for a wave."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--wave", choices=["alt17", "alt18", "alt19", "alt20"], required=True
    )
    args = parser.parse_args()
    if args.wave == "alt17":
        genes = {
            "jarvis_protocol_organ": ["operator_cognition_coherence_fabric", "capability_service_bridge", "governed_direct_pipeline"],
            "reasoning_contract_organ": ["jarvis_protocol_organ", "reasoning_executive_organ"],
            "jarvis_reasoning_lane_organ": ["jarvis_protocol_organ", "reasoning_contract_organ"],
            "conversation_memory_organ": ["jarvis_memory_board", "jarvis_protocol_organ"],
            "continuity_substrate_organ": ["conversation_memory_organ", "continuity_witness_organ"],
            "jarvis_operator_organ": ["jarvis_protocol_organ", "safety_envelope_organ", "workflow_shell_organ"],
            "anti_drift_organ": ["safety_envelope_organ", "jarvis_operator_organ"],
            "prompt_assembly_organ": ["anti_drift_organ", "conversation_memory_organ"],
            "output_integrity_organ": ["prompt_assembly_organ", "anti_drift_organ"],
        }
    elif args.wave == "alt18":
        genes = {
            "project_infi_state_machine_organ": ["operator_cognition_coherence_fabric", "ul_lineage_console_organ"],
            "project_infi_law_organ": ["project_infi_state_machine_organ", "run_ledger_organ"],
            "run_ledger_binding_organ": ["project_infi_law_organ", "run_ledger_organ"],
            "chat_turn_governance_organ": ["project_infi_law_organ", "jarvis_operator_organ"],
            "aais_ul_substrate_organ": ["chat_turn_governance_organ", "cisiv_operator_lineage_console"],
            "aris_integration_organ": ["project_infi_law_organ", "cognitive_bridge_organ"],
            "governance_layer_organ": ["project_infi_law_organ", "immune_observe_organ"],
            "security_protocol_organ": ["governance_layer_organ", "policy_gate_organ"],
            "system_guard_organ": ["governance_layer_organ", "security_protocol_organ"],
        }
    elif args.wave == "alt20":
        genes = {
            "memory_smith_organ": [
                "jarvis_memory_board",
                "memory_path_governance_organ",
            ],
            "operator_workspace_organ": [
                "capability_service_bridge",
                "jarvis_operator_organ",
            ],
            "jarvis_runs_organ": ["run_ledger_organ", "run_ledger_binding_organ"],
            "state_hygiene_organ": [
                "governance_layer_organ",
                "jarvis_operator_organ",
            ],
            "blueprint_posture_organ": [
                "project_infi_law_organ",
                "aais_ul_substrate_organ",
            ],
            "workflow_interfaces_organ": [
                "workflow_shell_organ",
                "workflow_runtime_organ",
            ],
            "platform_console_interfaces_organ": ["api_gateway_organ"],
            "operator_console_interface_organ": ["jarvis_console_surface_organ"],
            "nova_workspace_interface_organ": [
                "nova_landing_surface_organ",
                "nova_face_organ",
            ],
        }
    else:
        genes = {
            "launcher_organ": ["workflow_shell_organ", "capability_service_bridge"],
            "aais_doctor_organ": ["launcher_organ"],
            "workflow_runtime_organ": ["workflow_shell_organ", "launcher_organ"],
            "jarvis_console_surface_organ": ["jarvis_operator_organ", "api_gateway_organ"],
            "memory_bank_surface_organ": ["jarvis_memory_board", "jarvis_console_surface_organ"],
            "dashboard_surface_organ": ["governance_layer_organ", "jarvis_console_surface_organ"],
            "nova_landing_surface_organ": ["nova_face_organ", "jarvis_console_surface_organ"],
            "aais_composed_runtime_organ": ["jarvis_operator_organ", "governance_layer_organ"],
            "api_gateway_organ": ["jarvis_operator_organ", "capability_service_bridge"],
        }
    gdir = ROOT / "governance/subsystem_genomes"
    for child, parents in genes.items():
        for parent in parents:
            p = gdir / f"{parent}.genome.v1.json"
            if not p.is_file():
                print("missing parent", parent)
                continue
            data = json.loads(p.read_text(encoding="utf-8"))
            ch = data.setdefault("lineage", {}).setdefault("children", [])
            if child not in ch:
                ch.append(child)
                ch.sort()
            p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"lineage ok for {args.wave}")


if __name__ == "__main__":
    main()
