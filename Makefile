.PHONY: run worker test governance-check rootfs iso-tree rootfs-forge iso-tree-forge forge-installer forge-shippable-gate forge-platform-gate forge-dashboard forge-nightly-evolution forge-nightly-build installer-smoke installer-integration sign-artifacts verify-artifacts ugr-cloud-gate ugr-ingestion-gate ugr-platform-gate ugr-graph-index-gate ugr-embryo-gate ugr-causal-graph-gate ugr-llm-provider-gate ugr-cogos-write-path-gate ugr-graph-backend-gate ugr-trust-bundle-gate ugr-operator-console-gate forge-clean forge-rocky forge-rocky-fallback fetch-rocky-substrate ai-factory-build ai-factory-gate synthetic-mind-gate repo-hygiene-gate lab-init lab-gate mechanic-gate slingshot-gate lineage-gate triangulation-gate narrative-gate recipe-module-gate imagine-generator-gate human-voice-extraction-gate alt3-gate ssp-gate genome-gate alt4-gate promotion-scan recipe-module-prototype-gate imagine-generator-prototype-gate human-voice-extraction-prototype-gate narrative-trust-pack-prototype-gate forensic-triangulation-prototype-gate cisiv-operator-lineage-console-prototype-gate recipe-module-mutation-gate narrative-trust-pack-mutation-gate platform-gate platform-smoke platform-up

REPO_HYGIENE_MODE ?= fail

FORGE_PROFILE ?= $(COGOS_FORGE_PROFILE)
FORGE_PROFILE_ARG := $(if $(strip $(FORGE_PROFILE)),--profile $(FORGE_PROFILE),)

run:
	uvicorn app.main:app --reload

worker:
	celery -A app.celery_app.celery worker --loglevel=info

test:
	pytest -q

governance-check:
	python3 .github/scripts/validate-governance-ledger.py

rootfs:
	sudo -E bash wolf-cog-os/scripts/build-rootfs.sh $(FORGE_PROFILE_ARG)

iso-tree:
	COGOS_BUILD_FROM_TREE=1 bash wolf-cog-os/scripts/build.sh $(FORGE_PROFILE_ARG) "$${ISO:-}"

rootfs-forge:
	sudo -E bash wolf-cog-os/scripts/build-rootfs.sh --profile "$${COGOS_FORGE_PROFILE:-forge-selfhosted}"

iso-tree-forge:
	COGOS_BUILD_FROM_TREE=1 bash wolf-cog-os/scripts/build.sh --profile "$${COGOS_FORGE_PROFILE:-forge-selfhosted}" "$${ISO:-}"

forge-installer:
	bash wolf-cog-os/scripts/build-forge-installer.sh "$${ISO:-}"

forge-shippable-gate:
	python3 .github/scripts/check-forge-shippable-gate.py --mode fail

forge-platform-gate:
	python3 .github/scripts/check-forge-platform-gate.py --mode fail

forge-dashboard:
	python3 wolf-cog-os/scripts/forge-platform-dashboard.py $(FORGE_DASHBOARD_ARGS)

forge-nightly-evolution:
	bash wolf-cog-os/scripts/test/forge-nightly-evolution.sh --dry-run

forge-nightly-build:
	bash wolf-cog-os/scripts/test/forge-nightly-evolution.sh --build

forge-run-pipeline:
	bash wolf-cog-os/scripts/run-forge-pipeline.sh $(PIPELINE)

forge-rocky-fallback:
	bash wolf-cog-os/scripts/test/forge-build-with-rocky-fallback.sh

forge-clean:
	bash wolf-cog-os/scripts/test/forge-clean-work.sh

forge-rocky:
	bash wolf-cog-os/scripts/test/forge-build-rocky.sh

fetch-rocky-substrate:
	bash wolf-cog-os/scripts/test/fetch-rocky-substrate.sh $(ROCKY_ISO)

installer-smoke:
	bash wolf-cog-os/scripts/cogos-installer.sh --smoke $(INSTALLER_ARGS)

installer-integration:
	python3 wolf-cog-os/scripts/test/installer-matrix.py

sign-artifacts:
	bash .github/scripts/sign-artifacts.sh "$(ARTIFACT_DIR)"

verify-artifacts:
	bash .github/scripts/verify-artifacts.sh "$(ARTIFACT_DIR)"

ugr-cloud-gate:
	python3 wolf-cog-os/scripts/validate-ugr-cloud-manifest.py --mode fail
	pytest tests/test_ugr_cloud.py -q

ugr-ingestion-gate:
	python3 wolf-cog-os/scripts/validate-ugr-ingestion-manifest.py --mode fail
	pytest tests/test_ugr_ingestion.py -q

ugr-platform-gate:
	python3 wolf-cog-os/scripts/validate-ugr-platform-manifest.py --mode fail
	pytest tests/test_ugr_platform.py -q

ugr-graph-index-gate:
	python3 wolf-cog-os/scripts/validate-ugr-graph-index-manifest.py --mode fail
	pytest tests/test_ugr_graph_index.py -q

ugr-embryo-gate:
	python3 wolf-cog-os/scripts/validate-ugr-embryo-manifest.py --mode fail
	pytest tests/test_ugr_embryo.py -q

ugr-causal-graph-gate:
	python3 wolf-cog-os/scripts/validate-ugr-causal-graph-manifest.py --mode fail
	pytest tests/test_ugr_causal_graph.py -q

ugr-llm-provider-gate:
	python3 wolf-cog-os/scripts/validate-ugr-llm-provider-manifest.py --mode fail
	pytest tests/test_ugr_governed_llm_executor.py tests/test_ugr_llm_lane.py -q

ugr-cogos-write-path-gate:
	python3 wolf-cog-os/scripts/validate-ugr-cogos-write-path-manifest.py --mode fail
	pytest tests/test_ugr_cogos_pattern_bridge.py tests/test_unified_pattern_ledger.py -q

ugr-graph-backend-gate:
	python3 wolf-cog-os/scripts/validate-ugr-graph-backend-manifest.py --mode fail
	pytest tests/test_ugr_graph_backend.py tests/test_ugr_graph_index.py -q

ugr-trust-bundle-gate:
	python3 wolf-cog-os/scripts/validate-ugr-trust-bundle-manifest.py --mode fail
	pytest tests/test_ugr_trust_bundle_organ.py -q
	python3 tools/proof/run_ugr_trust_bundle.py --mode fail

ugr-operator-console-gate:
	python3 wolf-cog-os/scripts/validate-ugr-operator-console-manifest.py --mode fail
	pytest tests/test_ugr_operator_console.py -q

SPEC ?= factory/specs/nova-default.yaml

ai-factory-build:
	python3 -m ai_factory build --spec $(SPEC)

ai-factory-gate:
	python3 .github/scripts/check-ai-factory-governance.py

repo-hygiene-gate:
	python3 .github/scripts/check-repo-hygiene.py --mode $(REPO_HYGIENE_MODE) --output ci-artifacts/repo-hygiene-report.json

synthetic-mind-gate:
	python3 scripts/cogos/build_synthetic_mind_bundle.py
	python3 .github/scripts/check-canonical-lane-sync.py --mode $(REPO_HYGIENE_MODE)
	python3 wolf-cog-os/scripts/validate-substrate-invariants.py --mode fail
	python3 -m pytest tests/test_synthetic_mind_bundle.py tests/test_synthetic_mind_platform.py tests/test_spark_pipeline.py tests/test_coherence_projection.py -q

LAB_SPEC ?= lab/specs/default.yaml
LAB_PROJECT ?= nova-ai-factory

lab-init:
	python3 -m lab init --spec $(LAB_SPEC) --source .

lab-gate:
	python3 .github/scripts/check-lab-governance.py

mechanic-gate:
	python3 .github/scripts/check-mechanic-governance.py

slingshot-gate:
	python3 .github/scripts/check-slingshot-governance.py

lineage-gate:
	python3 .github/scripts/check-lineage-governance.py

triangulation-gate:
	python3 .github/scripts/check-triangulation-governance.py

narrative-gate:
	python3 .github/scripts/check-narrative-governance.py

recipe-module-gate:
	python3 .github/scripts/check-recipe-module-governance.py

imagine-generator-gate:
	python3 .github/scripts/check-imagine-generator-governance.py

human-voice-extraction-gate:
	python3 .github/scripts/check-human-voice-extraction-governance.py

alt3-gate: recipe-module-gate imagine-generator-gate human-voice-extraction-gate

ssp-gate:
	python3 tools/governance/check_ssp_completeness.py

genome-gate:
	python3 tools/governance/check_subsystem_genome.py

safety-envelope-gate:
	python3 .github/scripts/check-safety-envelope-governance.py

operator-profile-gate:
	python3 .github/scripts/check-operator-profile-governance.py

capability-bridge-gate:
	python3 .github/scripts/check-capability-bridge-governance.py

memory-board-gate:
	python3 .github/scripts/check-memory-board-governance.py

governed-pipeline-gate:
	python3 .github/scripts/check-governed-pipeline-governance.py

barebones-gate: genome-gate capability-bridge-gate memory-board-gate governed-pipeline-gate

barebones-promote-governed:
	python3 tools/governance/barebones_promote_governed.py

reflection-runtime-gate:
	python3 .github/scripts/check-reflection-runtime-governance.py

memory-runtime-gate:
	python3 .github/scripts/check-memory-runtime-governance.py

alt5-gate: safety-envelope-gate operator-profile-gate reflection-runtime-gate memory-runtime-gate genome-gate

adaptive-lane-gate:
	python3 .github/scripts/check-adaptive-lane-governance.py

alt6-gate: adaptive-lane-gate tier5-gate genome-gate

alt6-governed-gate:
	python3 tools/governance/check_alt6_governed_eligibility.py
	python3 .github/scripts/check-adaptive-lane-governance.py
	python3 tools/governance/check_adaptive_governance.py
	python3 tools/governance/check_subsystem_genome.py

tier5-gate:
	python3 tools/governance/check_adaptive_governance.py

alt4-gate:
	python3 tools/governance/alt4_gate.py

alt4-gate-strict:
	python3 tools/governance/alt4_gate.py --strict

promotion-scan:
	python3 -m src.governance_organs.promotion_engine --scan-all

promotion-apply:
	python3 -m src.governance_organs.promotion_engine --scan-all --apply

retirement-scan:
	python3 -m src.governance_organs.retirement_engine --scan-all

retirement-apply:
	python3 -m src.governance_organs.retirement_engine --gene $(GENE) --apply --step $(or $(STEP),6)

recipe-module-prototype-gate:
	python3 tools/governance/prototype_gate_stub.py recipe_module

imagine-generator-prototype-gate:
	python3 tools/governance/prototype_gate_stub.py imagine_generator

human-voice-extraction-prototype-gate:
	python3 tools/governance/prototype_gate_stub.py human_voice_extraction

narrative-trust-pack-prototype-gate:
	python3 tools/governance/prototype_gate_stub.py narrative_trust_pack

forensic-triangulation-prototype-gate:
	python3 tools/governance/prototype_gate_stub.py forensic_triangulation

cisiv-operator-lineage-console-prototype-gate:
	python3 tools/governance/prototype_gate_stub.py cisiv_operator_lineage_console

recipe-module-mutation-gate:
	python3 tools/governance/mutation_gate.py recipe_module MP-PLACEHOLDER

narrative-trust-pack-mutation-gate:
	python3 tools/governance/check_narrative_trust_pack_mutation.py

adaptive-lane-mutation-gate:
	python3 tools/governance/check_adaptive_lane_mutation.py

coherence-fabric-gate:
	python3 .github/scripts/check-coherence-fabric-governance.py

coherence-fabric-mutation-gate:
	python3 tools/governance/check_coherence_fabric_mutation.py

alt7-gate: coherence-fabric-gate alt6-governed-gate genome-gate

alt7-governed-gate:
	python3 tools/governance/check_alt7_governed_eligibility.py
	python3 .github/scripts/check-coherence-fabric-governance.py
	python3 -m pytest tests/test_coherence_fabric_bridge.py tests/test_alt7_governed_eligibility.py -q

alt7-1-gate: coherence-fabric-mutation-gate alt7-governed-gate genome-gate
	python3 -m pytest tests/test_coherence_fabric_pipeline.py tests/test_governance_coherence_projection.py -q

operator-profile-mutation-gate:
	python3 tools/governance/check_operator_profile_mutation.py

alt7-2-gate: alt7-1-gate operator-profile-mutation-gate
	python3 -m pytest tests/test_coherence_fabric_chat_block.py tests/test_coherence_fabric_pipeline.py tests/test_operator_cognition_coherence_fabric.py tests/test_operator_profile_organ_mutation_MP_OPO_001.py -q

continuity-witness-gate:
	python3 .github/scripts/check-continuity-witness-governance.py

narrative-continuity-gate:
	python3 .github/scripts/check-narrative-continuity-governance.py

intent-agency-gate:
	python3 .github/scripts/check-intent-agency-governance.py

alt8-gate: continuity-witness-gate narrative-continuity-gate intent-agency-gate genome-gate

alt8-1-gate: alt8-gate alt7-2-gate
	python3 -m pytest tests/test_operator_cognition_coherence_fabric.py tests/test_narrative_continuity_organ.py tests/test_intent_agency_organ.py tests/test_continuity_witness_organ.py -q

safety-envelope-mutation-gate:
	python3 tools/governance/check_safety_envelope_mutation.py

alt8-2-gate: alt8-1-gate safety-envelope-mutation-gate
	python3 -m pytest tests/test_safety_envelope_organ_mutation_MP_SE_001.py -q

alt8-governed-gate:
	python3 tools/governance/check_alt8_governed_eligibility.py

phase-gate-organ-gate:
	python3 .github/scripts/check-phase-gate-organ-governance.py

realtime-predictor-organ-gate:
	python3 .github/scripts/check-realtime-predictor-organ-governance.py

invariant-engine-organ-gate:
	python3 .github/scripts/check-invariant-engine-organ-governance.py

alt9-gate: phase-gate-organ-gate realtime-predictor-organ-gate invariant-engine-organ-gate genome-gate

alt9-1-gate: alt9-gate alt8-1-gate
	python3 -m pytest tests/test_operator_cognition_coherence_fabric.py tests/test_phase_gate_organ.py tests/test_realtime_event_cause_predictor_organ.py tests/test_invariant_engine_organ.py -q

immune-substrate-gate:
	python3 tools/governance/check_immune_substrate.py

alt9-2-gate: alt9-1-gate immune-substrate-gate

alt9-governed-gate:
	python3 tools/governance/check_alt9_governed_eligibility.py

verification-gate-organ-gate:
	python3 .github/scripts/check-verification-gate-organ-governance.py

memory-path-governance-organ-gate:
	python3 .github/scripts/check-memory-path-governance-organ-governance.py

knowledge-authority-organ-gate:
	python3 .github/scripts/check-knowledge-authority-organ-governance.py

scorpion-bridge-organ-gate:
	python3 .github/scripts/check-scorpion-bridge-organ-governance.py

mechanic-handoff-organ-gate:
	python3 .github/scripts/check-mechanic-handoff-organ-governance.py

forensic-triangulation-organ-gate:
	python3 .github/scripts/check-forensic-triangulation-organ-governance.py

immune-observe-organ-gate:
	python3 .github/scripts/check-immune-observe-organ-governance.py

policy-gate-organ-gate:
	python3 .github/scripts/check-policy-gate-organ-governance.py

predictor-immune-bridge-organ-gate:
	python3 .github/scripts/check-predictor-immune-bridge-organ-governance.py

alt10-gate: verification-gate-organ-gate memory-path-governance-organ-gate knowledge-authority-organ-gate scorpion-bridge-organ-gate mechanic-handoff-organ-gate forensic-triangulation-organ-gate immune-observe-organ-gate policy-gate-organ-gate predictor-immune-bridge-organ-gate genome-gate

alt10-1-gate: alt10-gate alt9-1-gate
	python3 -m pytest tests/test_verification_gate_organ.py tests/test_memory_path_governance_organ.py tests/test_knowledge_authority_organ.py tests/test_scorpion_bridge_organ.py tests/test_mechanic_handoff_organ.py tests/test_forensic_triangulation_organ.py tests/test_immune_observe_organ.py tests/test_policy_gate_organ.py tests/test_predictor_immune_bridge_organ.py tests/test_operator_cognition_coherence_fabric.py -q

immune-observe-closure-gate:
	python3 tools/governance/check_immune_observe_closure.py

alt10-2-gate: alt10-1-gate immune-observe-closure-gate

alt10-governed-gate:
	python3 tools/governance/check_alt10_governed_eligibility.py

cognitive-bridge-organ-gate:
	python3 .github/scripts/check-cognitive-bridge-organ-governance.py

governed-event-chain-organ-gate:
	python3 .github/scripts/check-governed-event-chain-organ-governance.py

tracing-spine-organ-gate:
	python3 .github/scripts/check-tracing-spine-organ-governance.py

mission-board-organ-gate:
	python3 .github/scripts/check-mission-board-organ-governance.py

aris-boundary-organ-gate:
	python3 .github/scripts/check-aris-boundary-organ-governance.py

capability-module-organ-gate:
	python3 .github/scripts/check-capability-module-organ-governance.py

patchforge-organ-gate:
	python3 .github/scripts/check-patchforge-organ-governance.py

change-scope-organ-gate:
	python3 .github/scripts/check-change-scope-organ-governance.py

patch-verification-organ-gate:
	python3 .github/scripts/check-patch-verification-organ-governance.py

alt11-gate: cognitive-bridge-organ-gate governed-event-chain-organ-gate tracing-spine-organ-gate mission-board-organ-gate aris-boundary-organ-gate capability-module-organ-gate patchforge-organ-gate change-scope-organ-gate patch-verification-organ-gate genome-gate

alt11-1-gate: alt11-gate alt10-1-gate
	python3 -m pytest tests/test_cognitive_bridge_organ.py tests/test_governed_event_chain_organ.py tests/test_tracing_spine_organ.py tests/test_mission_board_organ.py tests/test_aris_boundary_organ.py tests/test_capability_module_organ.py tests/test_patchforge_organ.py tests/test_change_scope_organ.py tests/test_patch_verification_organ.py tests/test_operator_cognition_coherence_fabric.py -q

alt11-closure-gate:
	python3 tools/governance/check_alt11_closure.py

alt11-2-gate: alt11-1-gate alt11-closure-gate

alt11-governed-gate:
	python3 tools/governance/check_alt11_governed_eligibility.py

otem-bounded-organ-gate:
	python3 .github/scripts/check-otem-bounded-organ-governance.py

direct-challenge-organ-gate:
	python3 .github/scripts/check-direct-challenge-organ-governance.py

orchestration-spine-organ-gate:
	python3 .github/scripts/check-orchestration-spine-organ-governance.py

operator-health-sentinel-organ-gate:
	python3 .github/scripts/check-operator-health-sentinel-organ-governance.py

governed-realtime-lane-organ-gate:
	python3 .github/scripts/check-governed-realtime-lane-organ-governance.py

v8-runtime-organ-gate:
	python3 .github/scripts/check-v8-runtime-organ-governance.py

patch-apply-organ-gate:
	python3 .github/scripts/check-patch-apply-organ-governance.py

patch-execution-preview-organ-gate:
	python3 .github/scripts/check-patch-execution-preview-organ-governance.py

run-ledger-organ-gate:
	python3 .github/scripts/check-run-ledger-organ-governance.py

alt12-gate: otem-bounded-organ-gate direct-challenge-organ-gate orchestration-spine-organ-gate operator-health-sentinel-organ-gate governed-realtime-lane-organ-gate v8-runtime-organ-gate patch-apply-organ-gate patch-execution-preview-organ-gate run-ledger-organ-gate genome-gate

alt12-1-gate: alt12-gate alt11-1-gate
	python3 -m pytest tests/test_otem_bounded_organ.py tests/test_direct_challenge_organ.py tests/test_orchestration_spine_organ.py tests/test_operator_health_sentinel_organ.py tests/test_governed_realtime_lane_organ.py tests/test_v8_runtime_organ.py tests/test_patch_apply_organ.py tests/test_patch_execution_preview_organ.py tests/test_run_ledger_organ.py tests/test_operator_cognition_coherence_fabric.py -q

alt12-closure-gate:
	python3 tools/governance/check_alt12_closure.py

alt12-2-gate: alt12-1-gate alt12-closure-gate

alt12-governed-gate:
	python3 tools/governance/check_alt12_governed_eligibility.py

ul-lineage-console-organ-gate:
	python3 .github/scripts/check-ul-lineage-console-organ-governance.py

module-governance-organ-gate:
	python3 .github/scripts/check-module-governance-organ-governance.py

recipe-module-organ-gate:
	python3 .github/scripts/check-recipe-module-organ-governance.py

imagine-generator-organ-gate:
	python3 .github/scripts/check-imagine-generator-organ-governance.py

story-forge-lane-organ-gate:
	python3 .github/scripts/check-story-forge-lane-organ-governance.py

beatbox-lane-organ-gate:
	python3 .github/scripts/check-beatbox-lane-organ-governance.py

speakers-lane-organ-gate:
	python3 .github/scripts/check-speakers-lane-organ-governance.py

human-voice-extraction-organ-gate:
	python3 .github/scripts/check-human-voice-extraction-organ-governance.py

narrative-trust-pack-organ-gate:
	python3 .github/scripts/check-narrative-trust-pack-organ-governance.py

alt13-gate: ul-lineage-console-organ-gate module-governance-organ-gate recipe-module-organ-gate imagine-generator-organ-gate story-forge-lane-organ-gate beatbox-lane-organ-gate speakers-lane-organ-gate human-voice-extraction-organ-gate narrative-trust-pack-organ-gate genome-gate

alt13-1-gate: alt13-gate alt12-1-gate
	python3 -m pytest tests/test_ul_lineage_console_organ.py tests/test_module_governance_organ.py tests/test_recipe_module_organ.py tests/test_imagine_generator_organ.py tests/test_story_forge_lane_organ.py tests/test_beatbox_lane_organ.py tests/test_speakers_lane_organ.py tests/test_human_voice_extraction_organ.py tests/test_narrative_trust_pack_organ.py tests/test_operator_cognition_coherence_fabric.py -q

alt13-closure-gate:
	python3 tools/governance/check_alt13_closure.py

alt13-2-gate: alt13-1-gate alt13-closure-gate

alt13-governed-gate:
	python3 tools/governance/check_alt13_governed_eligibility.py

platform-gate:
	python3 .github/scripts/check-platform-governance.py

platform-smoke:
	python3 -m pytest tests/test_platform_schemas.py tests/test_platform_api_smoke.py -q

platform-v1-1-gate:
	python3 .github/scripts/check-platform-v1-1-governance.py

platform-v1-1-smoke:
	python3 -m pytest tests/test_platform_schemas.py tests/test_platform_api_smoke.py tests/test_platform_v11.py tests/test_platform_onboarding.py tests/test_platform_graph.py -q

platform-billing-export:
	python3 -m platform billing export --org $(or $(ORG),acme) --month $(or $(MONTH),2026-05)

platform-proof-run:
	python3 -m platform replay --manifest docs/proof/platform/cross_machine/REPLAY_MANIFEST.template.json

platform-v8-v14-gate:
	python3 .github/scripts/check-platform-v8-v14-governance.py

platform-v8-v14-smoke:
	python3 -m pytest tests/test_platform_v814.py tests/test_platform_schemas.py tests/test_platform_api_smoke.py -q

platform-v15-gate:
	python3 .github/scripts/check-platform-mesh-governance.py

platform-v16-smoke:
	python3 -m pytest tests/test_platform_v1520.py -q -k "mesh or handoff"

platform-v17-gate:
	python3 .github/scripts/check-platform-marketplace-governance.py

platform-v18-smoke:
	python3 -m pytest tests/test_platform_v1520.py -q -k marketplace

platform-v19-gate:
	python3 .github/scripts/check-platform-proof-federation-governance.py

platform-v20-smoke:
	python3 -m pytest tests/test_platform_v1520.py -q -k attestation

platform-v3-gate:
	python3 .github/scripts/check-platform-v3-governance.py

platform-v3-smoke:
	python3 -m pytest tests/test_platform_v1520.py tests/test_platform_v814.py -q

platform-v21-gate:
	python3 .github/scripts/check-platform-mesh-v2-governance.py

platform-v22-smoke:
	python3 -m pytest tests/test_platform_v2130.py -q -k "mesh or handoff"

platform-v23-gate:
	python3 .github/scripts/check-platform-marketplace-v2-governance.py

platform-v24-smoke:
	python3 -m pytest tests/test_platform_v2130.py -q -k marketplace

platform-v25-gate:
	python3 .github/scripts/check-platform-proof-v2-governance.py

platform-v28-smoke:
	python3 -m pytest tests/test_platform_v2130.py -q -k proof
	python3 -m platform replay --manifest docs/proof/platform/cross_machine/REPLAY_MANIFEST.v2.template.json

platform-v29-gate:
	python3 .github/scripts/check-platform-sovereign-governance.py

platform-v30-smoke:
	python3 -m pytest tests/test_platform_v2130.py -q -k sovereign

platform-v4-gate:
	python3 .github/scripts/check-platform-v4-governance.py

platform-v4-smoke:
	python3 -m pytest tests/test_platform_v1520.py tests/test_platform_v2130.py tests/test_platform_schemas.py -q

platform-v31-gate:
	python3 .github/scripts/check-platform-events-governance.py

platform-v32-smoke:
	python3 -m pytest tests/test_platform_v3140.py -q -k webhook

platform-v33-gate:
	python3 .github/scripts/check-platform-marketplace-v3-governance.py

platform-v34-smoke:
	python3 -m pytest tests/test_platform_v3140.py -q -k marketplace

platform-v35-gate:
	python3 .github/scripts/check-platform-proof-v3-governance.py

platform-v36-smoke:
	python3 -m pytest tests/test_platform_v3140.py -q -k proof

platform-v37-gate:
	python3 .github/scripts/check-platform-mesh-v3-governance.py

platform-v38-smoke:
	python3 -m pytest tests/test_platform_v3140.py -q -k mesh

platform-v39-gate:
	python3 .github/scripts/check-platform-sovereign-v2-governance.py

platform-v40-smoke:
	python3 -m pytest tests/test_platform_v3140.py -q -k sovereign

platform-v5-gate:
	python3 .github/scripts/check-platform-v5-governance.py

platform-v5-smoke:
	python3 -m pytest tests/test_platform_v1520.py tests/test_platform_v2130.py tests/test_platform_v3140.py tests/test_platform_schemas.py -q

platform-v41-gate:
	python3 .github/scripts/check-platform-mesh-v4-governance.py

platform-v42-smoke:
	python3 -m pytest tests/test_platform_v4150.py -q -k routing

platform-v43-gate:
	python3 .github/scripts/check-platform-proof-network-governance.py

platform-v44-smoke:
	python3 -m pytest tests/test_platform_v4150.py -q -k witness

platform-v45-gate:
	python3 .github/scripts/check-platform-exchange-governance.py

platform-v46-smoke:
	python3 -m pytest tests/test_platform_v4150.py -q -k exchange

platform-v47-gate:
	python3 .github/scripts/check-platform-ledger-v2-governance.py

platform-v48-smoke:
	python3 -m pytest tests/test_platform_v4150.py -q -k ledger

platform-v49-gate:
	python3 .github/scripts/check-platform-sovereign-runtime-governance.py

platform-v50-smoke:
	python3 -m pytest tests/test_platform_v4150.py -q -k sovereign

platform-v6-gate:
	python3 .github/scripts/check-platform-v6-governance.py

platform-v6-smoke:
	python3 -m pytest tests/test_platform_v1520.py tests/test_platform_v2130.py tests/test_platform_v3140.py tests/test_platform_v4150.py tests/test_platform_schemas.py -q

stack-platform-gate: platform-gate platform-v1-1-gate platform-v8-v14-gate platform-v6-gate platform-v6-smoke

ugr-ledger-bridge-gate:
	python3 .github/scripts/check-ugr-ledger-bridge-governance.py

pilot-compose-smoke:
	python3 scripts/pilot_compose_smoke.py --local

stack-pilot-gate: platform-v6-gate platform-v6-smoke ugr-ledger-bridge-gate pilot-compose-smoke
	python3 -m pytest tests/test_ugr_ledger_bridge.py tests/test_infinity_pilot_stack_smoke.py -q

pilot-up:
	cd deploy/pilot && docker compose up --build

platform-up:
	cd deploy/platform && docker compose up --build

wolf-rehydration-gate:
	python3 .github/scripts/check-wolf-rehydration.py

stage2-fidelity-gate:
	python3 .github/scripts/check-stage2-fidelity.py

ai-factory-deploy-wolf:
	python3 -m ai_factory deploy --build-id $(or $(BUILD_ID),nova-default) --wolf --repo-root .

stack-closure-gate: wolf-rehydration-gate stage2-fidelity-gate ai-factory-gate lab-gate
	python3 -m pytest tests/test_wolf_rehydration_harness.py tests/test_stage2_fidelity_metrics.py tests/test_memory_governance_membrane.py tests/test_ai_factory_wolf_deploy.py tests/test_lab_forge_bridge.py tests/test_nova_formal_spec.py tests/test_narrative_continuity_proof.py tests/test_intent_agency_evidence.py tests/test_ai_factory.py tests/test_lab.py -q
	python3 .github/scripts/check-nova-cortex-governance.py
	python3 .github/scripts/check-nova-narrative-continuity.py
	python3 .github/scripts/check-nova-intent-agency.py
