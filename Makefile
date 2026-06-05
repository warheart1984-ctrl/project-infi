.PHONY: run worker test governance-check rootfs iso-tree rootfs-forge iso-tree-forge forge-installer forge-shippable-gate forge-platform-gate forge-dashboard forge-nightly-evolution forge-nightly-build installer-smoke installer-integration sign-artifacts verify-artifacts ugr-cloud-gate ugr-ingestion-gate ugr-platform-gate ugr-graph-index-gate ugr-embryo-gate ugr-causal-graph-gate ugr-llm-provider-gate ugr-cogos-write-path-gate ugr-graph-backend-gate ugr-trust-bundle-gate ugr-operator-console-gate ugr-mission-gate forge-clean forge-rocky forge-rocky-fallback fetch-rocky-substrate ai-factory-build ai-factory-gate synthetic-mind-gate repo-hygiene-gate lab-init lab-gate mechanic-gate slingshot-gate lineage-gate temporal-replay-gate triangulation-gate narrative-gate recipe-module-gate imagine-generator-gate human-voice-extraction-gate alt3-gate ssp-gate genome-gate alt4-gate promotion-scan recipe-module-prototype-gate imagine-generator-prototype-gate human-voice-extraction-prototype-gate narrative-trust-pack-prototype-gate forensic-triangulation-prototype-gate cisiv-operator-lineage-console-prototype-gate recipe-module-mutation-gate narrative-trust-pack-mutation-gate platform-gate platform-smoke platform-up

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

ugr-discovery-gate:
	pytest tests/test_ugr_subsystem_discovery.py -q

ugr-rewards-gate:
	pytest tests/test_ugr_operator_rewards.py tests/test_ugr_subsystem_discovery.py -q

ugr-mission-gate:
	python3 wolf-cog-os/scripts/validate-ugr-mission-manifest.py --mode fail
	pytest tests/test_ugr_mission_demo.py tests/test_ugr_tenant_isolation.py tests/test_ugr_cost_routing.py tests/test_ugr_marketplace.py tests/test_ugr_cloud_invariants.py tests/test_ugr_cloud_invariants_v2.py tests/test_ugr_execution_policy.py tests/test_ugr_cloud_forge_tenant_binding.py tests/test_ugr_cloud_forge_observed.py tests/test_ugr_cloud_forge_governance.py tests/test_ugr_federation_v17_acceptance.py tests/test_ugr_federation_v18_acceptance.py tests/test_ugr_federation_v19_acceptance.py tests/test_ugr_federation_forge_peer_rail.py tests/test_ugr_subsystem_discovery.py -q

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

temporal-replay-gate:
	python3 .github/scripts/check-temporal-replay-governance.py

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

naming-gate:
	python3 tools/naming_protocol_lint.py

naming-genome-gate:
	python3 tools/governance/check_naming_genome.py --snapshot

naming-genome-gate-strict:
	python3 tools/governance/check_naming_genome.py --snapshot --strict

linguistic-diff:
	python3 tools/linguistic_diff.py --gene $(GENE)

translate-mythic:
	python3 tools/mythic_engineering_translator.py --mythic "$(MYTHIC)"

linguistic-mutation-gate:
	python3 tools/governance/check_linguistic_mutation_gate.py

linguistic-drift-gate:
	python3 tools/linguistic_drift_predictor.py --json -o governance/linguistic_drift_report.v1.json

linguistic-lineage-viz:
	python3 tools/linguistic_lineage_viz.py $(if $(GENE),--gene $(GENE),) $(if $(OUTPUT),-o $(OUTPUT),) $(if $(CASCADE_FROM),--cascade-from $(CASCADE_FROM),)

meta-linguistic-gate:
	python3 -m src.governance_organs.linguistic_governance_engine --gate

linguistic-remediation-gate:
	python3 tools/governance/check_linguistic_remediation_gate.py

linguistic-cascade-report:
	python3 tools/linguistic_cascade_report.py --gene $(GENE)

generate-linguistic-remediations:
	python3 tools/governance/generate_linguistic_remediations.py --min-band medium

linguistic-governance-cycle:
	python3 tools/governance/run_linguistic_governance_cycle.py

linguistic-governance-cycle-gate:
	python3 tools/governance/check_linguistic_governance_cycle_gate.py

linguistic-governance-cycle-fast:
	python3 tools/governance/run_linguistic_governance_cycle.py --skip-gates

linguistic-predictive-cycle:
	python3 tools/governance/run_linguistic_predictive_cycle.py

linguistic-predictive-cycle-fast:
	python3 tools/governance/run_linguistic_predictive_cycle.py --skip-drift-refresh

linguistic-drift-forecast:
	python3 tools/linguistic_drift_forecast.py -o governance/linguistic_drift_forecast.v1.json

linguistic-predictive-gate:
	python3 tools/governance/check_linguistic_predictive_gate.py

linguistic-calibration-cycle:
	python3 tools/governance/run_linguistic_calibration_cycle.py

linguistic-calibration-gate:
	python3 tools/governance/check_linguistic_calibration_gate.py

linguistic-governance-queue:
	python3 tools/linguistic_governance_queue.py -o governance/linguistic_governance_queue.v1.json

linguistic-full-governance-cycle:
	python3 tools/governance/run_linguistic_full_governance_cycle.py

linguistic-full-governance-cycle-fast:
	python3 tools/governance/run_linguistic_full_governance_cycle.py --skip-gates --skip-drift-refresh

linguistic-work-order-sync:
	python3 tools/governance/linguistic_work_order.py --sync-from-queue

linguistic-work-order-gate:
	python3 tools/governance/check_linguistic_work_order_gate.py

linguistic-governance-attestation:
	python3 tools/governance/run_linguistic_attestation.py

linguistic-attestation-gate:
	python3 tools/governance/check_linguistic_attestation_gate.py

linguistic-full-cycle-gate:
	python3 tools/governance/check_linguistic_full_cycle_gate.py

linguistic-governance-day:
	python3 tools/governance/run_linguistic_governance_day.py

linguistic-governance-day-fast:
	python3 tools/governance/run_linguistic_governance_day.py --fast

linguistic-governance-stack-gate:
	python3 tools/governance/check_linguistic_governance_stack_gate.py

safety-envelope-gate:
	python3 .github/scripts/check-safety-envelope-governance.py

operator-profile-gate:
	python3 .github/scripts/check-operator-profile-governance.py

capability-bridge-gate:
	python3 .github/scripts/check-capability-bridge-governance.py

memory-board-gate:
	python3 .github/scripts/check-memory-board-governance.py

coding-organs-gate:
	python3 .github/scripts/check-subsystem-mvp-integration-governance.py

otem-execution-substrate-gate:
	python3 .github/scripts/check-subsystem-mvp-integration-governance.py

aris-standalone-gate:
	python3 .github/scripts/check-subsystem-mvp-integration-governance.py

media-processor-gate:
	python3 .github/scripts/check-subsystem-mvp-integration-governance.py

dreamspace-organ-gate:
	python3 .github/scripts/check-subsystem-mvp-integration-governance.py

subsystem-mvp-gate:
	python3 .github/scripts/check-subsystem-mvp-integration-governance.py

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

meta-law-gate:
	python3 tools/governance/check_meta_law.py

collaboration-charter-gate:
	python3 tools/governance/check_collaboration_charter.py

constitutional-substrate-gate: meta-law-gate collaboration-charter-gate

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

document-vision-organ-gate:
	python3 .github/scripts/check-document-vision-organ-governance.py

ui-vision-organ-gate:
	python3 .github/scripts/check-ui-vision-organ-governance.py

perception-gateway-organ-gate:
	python3 .github/scripts/check-perception-gateway-organ-governance.py

spatial-reasoning-organ-gate:
	python3 .github/scripts/check-spatial-reasoning-organ-governance.py

mystic-engine-organ-gate:
	python3 .github/scripts/check-mystic-engine-organ-governance.py

perception-lane-organ-gate:
	python3 .github/scripts/check-perception-lane-organ-governance.py

route-choice-organ-gate:
	python3 .github/scripts/check-route-choice-organ-governance.py

specialist-route-organ-gate:
	python3 .github/scripts/check-specialist-route-organ-governance.py

provider-route-organ-gate:
	python3 .github/scripts/check-provider-route-organ-governance.py

alt14-gate: document-vision-organ-gate ui-vision-organ-gate perception-gateway-organ-gate spatial-reasoning-organ-gate mystic-engine-organ-gate perception-lane-organ-gate route-choice-organ-gate specialist-route-organ-gate provider-route-organ-gate genome-gate

alt14-1-gate: alt14-gate alt13-1-gate
	python3 -m pytest tests/test_document_vision_organ.py tests/test_ui_vision_organ.py tests/test_perception_gateway_organ.py tests/test_spatial_reasoning_organ.py tests/test_mystic_engine_organ.py tests/test_perception_lane_organ.py tests/test_route_choice_organ.py tests/test_specialist_route_organ.py tests/test_provider_route_organ.py tests/test_operator_cognition_coherence_fabric.py -q

alt14-closure-gate:
	python3 tools/governance/check_alt14_closure.py

alt14-2-gate: alt14-1-gate alt14-closure-gate

alt14-governed-gate:
	python3 tools/governance/check_alt14_governed_eligibility.py

reasoning-executive-organ-gate:
	python3 .github/scripts/check-reasoning-executive-organ-governance.py

attention-organ-gate:
	python3 .github/scripts/check-attention-organ-governance.py

coherence-projection-organ-gate:
	python3 .github/scripts/check-coherence-projection-organ-governance.py

deliberation-organ-gate:
	python3 .github/scripts/check-deliberation-organ-governance.py

planning-organ-gate:
	python3 .github/scripts/check-planning-organ-governance.py

cortex-arcs-organ-gate:
	python3 .github/scripts/check-cortex-arcs-organ-governance.py

cognitive-execution-organ-gate:
	python3 .github/scripts/check-cognitive-execution-organ-governance.py

speaking-runtime-organ-gate:
	python3 .github/scripts/check-speaking-runtime-organ-governance.py

nova-face-organ-gate:
	python3 .github/scripts/check-nova-face-organ-governance.py

alt15-gate: reasoning-executive-organ-gate attention-organ-gate coherence-projection-organ-gate deliberation-organ-gate planning-organ-gate cortex-arcs-organ-gate cognitive-execution-organ-gate speaking-runtime-organ-gate nova-face-organ-gate genome-gate

alt15-1-gate: alt15-gate alt14-1-gate
	python3 -m pytest tests/test_reasoning_executive_organ.py tests/test_attention_organ.py tests/test_coherence_projection_organ.py tests/test_deliberation_organ.py tests/test_planning_organ.py tests/test_cortex_arcs_organ.py tests/test_cognitive_execution_organ.py tests/test_speaking_runtime_organ.py tests/test_nova_face_organ.py tests/test_operator_cognition_coherence_fabric.py -q

alt15-closure-gate:
	python3 tools/governance/check_alt15_closure.py

alt15-2-gate: alt15-1-gate alt15-closure-gate

alt15-governed-gate:
	python3 tools/governance/check_alt15_governed_eligibility.py

ai-factory-organ-gate:
	python3 .github/scripts/check-ai-factory-organ-governance.py

cogos-runtime-bridge-organ-gate:
	python3 .github/scripts/check-cogos-runtime-bridge-organ-governance.py

wolf-rehydration-organ-gate:
	python3 .github/scripts/check-wolf-rehydration-organ-governance.py

forge-contractor-organ-gate:
	python3 .github/scripts/check-forge-contractor-organ-governance.py

forge-eval-organ-gate:
	python3 .github/scripts/check-forge-eval-organ-governance.py

evolve-engine-organ-gate:
	python3 .github/scripts/check-evolve-engine-organ-governance.py

slingshot-organ-gate:
	python3 .github/scripts/check-slingshot-organ-governance.py

operator-workbench-organ-gate:
	python3 .github/scripts/check-operator-workbench-organ-governance.py

workflow-shell-organ-gate:
	python3 .github/scripts/check-workflow-shell-organ-governance.py

alt16-gate: ai-factory-organ-gate cogos-runtime-bridge-organ-gate wolf-rehydration-organ-gate forge-contractor-organ-gate forge-eval-organ-gate evolve-engine-organ-gate slingshot-organ-gate operator-workbench-organ-gate workflow-shell-organ-gate genome-gate

alt16-1-gate: alt16-gate alt15-1-gate
	python3 -m pytest tests/test_ai_factory_organ.py tests/test_cogos_runtime_bridge_organ.py tests/test_wolf_rehydration_organ.py tests/test_forge_contractor_organ.py tests/test_forge_eval_organ.py tests/test_evolve_engine_organ.py tests/test_slingshot_organ.py tests/test_operator_workbench_organ.py tests/test_workflow_shell_organ.py tests/test_operator_cognition_coherence_fabric.py -q

alt16-closure-gate:
	python3 tools/governance/check_alt16_closure.py

alt16-2-gate: alt16-1-gate alt16-closure-gate

alt16-governed-gate:
	python3 tools/governance/check_alt16_governed_eligibility.py

jarvis-protocol-organ-gate:
	python3 .github/scripts/check-jarvis-protocol-organ-governance.py

reasoning-contract-organ-gate:
	python3 .github/scripts/check-reasoning-contract-organ-governance.py

jarvis-reasoning-lane-organ-gate:
	python3 .github/scripts/check-jarvis-reasoning-lane-organ-governance.py

conversation-memory-organ-gate:
	python3 .github/scripts/check-conversation-memory-organ-governance.py

continuity-substrate-organ-gate:
	python3 .github/scripts/check-continuity-substrate-organ-governance.py

jarvis-operator-organ-gate:
	python3 .github/scripts/check-jarvis-operator-organ-governance.py

anti-drift-organ-gate:
	python3 .github/scripts/check-anti-drift-organ-governance.py

prompt-assembly-organ-gate:
	python3 .github/scripts/check-prompt-assembly-organ-governance.py

output-integrity-organ-gate:
	python3 .github/scripts/check-output-integrity-organ-governance.py

alt17-gate: jarvis-protocol-organ-gate reasoning-contract-organ-gate jarvis-reasoning-lane-organ-gate conversation-memory-organ-gate continuity-substrate-organ-gate jarvis-operator-organ-gate anti-drift-organ-gate prompt-assembly-organ-gate output-integrity-organ-gate genome-gate

alt17-1-gate: alt17-gate alt16-1-gate
	python3 -m pytest tests/test_jarvis_protocol_organ.py tests/test_reasoning_contract_organ.py tests/test_jarvis_reasoning_lane_organ.py tests/test_conversation_memory_organ.py tests/test_continuity_substrate_organ.py tests/test_jarvis_operator_organ.py tests/test_anti_drift_organ.py tests/test_prompt_assembly_organ.py tests/test_output_integrity_organ.py tests/test_operator_cognition_coherence_fabric.py -q

alt17-closure-gate:
	python3 tools/governance/check_alt17_closure.py

alt17-2-gate: alt17-1-gate alt17-closure-gate

alt17-governed-gate:
	python3 tools/governance/check_alt17_governed_eligibility.py

project-infi-state-machine-organ-gate:
	python3 .github/scripts/check-project-infi-state-machine-organ-governance.py

project-infi-law-organ-gate:
	python3 .github/scripts/check-project-infi-law-organ-governance.py

run-ledger-binding-organ-gate:
	python3 .github/scripts/check-run-ledger-binding-organ-governance.py

chat-turn-governance-organ-gate:
	python3 .github/scripts/check-chat-turn-governance-organ-governance.py

aais-ul-substrate-organ-gate:
	python3 .github/scripts/check-aais-ul-substrate-organ-governance.py

aris-integration-organ-gate:
	python3 .github/scripts/check-aris-integration-organ-governance.py

governance-layer-organ-gate:
	python3 .github/scripts/check-governance-layer-organ-governance.py

security-protocol-organ-gate:
	python3 .github/scripts/check-security-protocol-organ-governance.py

system-guard-organ-gate:
	python3 .github/scripts/check-system-guard-organ-governance.py

alt18-gate: project-infi-state-machine-organ-gate project-infi-law-organ-gate run-ledger-binding-organ-gate chat-turn-governance-organ-gate aais-ul-substrate-organ-gate aris-integration-organ-gate governance-layer-organ-gate security-protocol-organ-gate system-guard-organ-gate genome-gate

alt18-1-gate: alt18-gate alt17-1-gate

alt18-closure-gate:
	python3 tools/governance/check_alt18_closure.py

alt18-2-gate: alt18-1-gate alt18-closure-gate

alt18-governed-gate:
	python3 tools/governance/check_alt18_governed_eligibility.py

launcher-organ-gate:
	python3 .github/scripts/check-launcher-organ-governance.py

aais-doctor-organ-gate:
	python3 .github/scripts/check-aais-doctor-organ-governance.py

workflow-runtime-organ-gate:
	python3 .github/scripts/check-workflow-runtime-organ-governance.py

jarvis-console-surface-organ-gate:
	python3 .github/scripts/check-jarvis-console-surface-organ-governance.py

memory-bank-surface-organ-gate:
	python3 .github/scripts/check-memory-bank-surface-organ-governance.py

dashboard-surface-organ-gate:
	python3 .github/scripts/check-dashboard-surface-organ-governance.py

nova-landing-surface-organ-gate:
	python3 .github/scripts/check-nova-landing-surface-organ-governance.py

aais-composed-runtime-organ-gate:
	python3 .github/scripts/check-aais-composed-runtime-organ-governance.py

api-gateway-organ-gate:
	python3 .github/scripts/check-api-gateway-organ-governance.py

alt19-gate: launcher-organ-gate aais-doctor-organ-gate workflow-runtime-organ-gate jarvis-console-surface-organ-gate memory-bank-surface-organ-gate dashboard-surface-organ-gate nova-landing-surface-organ-gate aais-composed-runtime-organ-gate api-gateway-organ-gate genome-gate

alt19-1-gate: alt19-gate alt18-1-gate

alt19-closure-gate:
	python3 tools/governance/check_alt19_closure.py

alt19-2-gate: alt19-1-gate alt19-closure-gate

alt19-governed-gate:
	python3 tools/governance/check_alt19_governed_eligibility.py

memory-smith-organ-gate:
	python3 .github/scripts/check-memory-smith-organ-governance.py

operator-workspace-organ-gate:
	python3 .github/scripts/check-operator-workspace-organ-governance.py

jarvis-runs-organ-gate:
	python3 .github/scripts/check-jarvis-runs-organ-governance.py

state-hygiene-organ-gate:
	python3 .github/scripts/check-state-hygiene-organ-governance.py

blueprint-posture-organ-gate:
	python3 .github/scripts/check-blueprint-posture-organ-governance.py

workflow-interfaces-organ-gate:
	python3 .github/scripts/check-workflow-interfaces-organ-governance.py

platform-console-interfaces-organ-gate:
	python3 .github/scripts/check-platform-console-interfaces-organ-governance.py

operator-console-interface-organ-gate:
	python3 .github/scripts/check-operator-console-interface-organ-governance.py

nova-workspace-interface-organ-gate:
	python3 .github/scripts/check-nova-workspace-interface-organ-governance.py

alt20-gate: memory-smith-organ-gate operator-workspace-organ-gate jarvis-runs-organ-gate state-hygiene-organ-gate blueprint-posture-organ-gate workflow-interfaces-organ-gate platform-console-interfaces-organ-gate operator-console-interface-organ-gate nova-workspace-interface-organ-gate genome-gate

alt20-1-gate: alt20-gate alt19-1-gate

alt20-closure-gate:
	python3 tools/governance/check_alt20_closure.py

alt20-2-gate: alt20-1-gate alt20-closure-gate

alt20-governed-gate:
	python3 tools/governance/check_alt20_governed_eligibility.py

creative-core-runtime-organ-gate:
	python3 .github/scripts/check-creative-core-runtime-organ-governance.py

v9-core-organ-gate:
	python3 .github/scripts/check-v9-core-organ-governance.py

v9-runtime-organ-gate:
	python3 .github/scripts/check-v9-runtime-organ-governance.py

v10-core-organ-gate:
	python3 .github/scripts/check-v10-core-organ-governance.py

v10-runtime-organ-gate:
	python3 .github/scripts/check-v10-runtime-organ-governance.py

v10-action-engine-organ-gate:
	python3 .github/scripts/check-v10-action-engine-organ-governance.py

creative-capability-bridge-organ-gate:
	python3 .github/scripts/check-creative-capability-bridge-organ-governance.py

creative-operator-handoff-organ-gate:
	python3 .github/scripts/check-creative-operator-handoff-organ-governance.py

creative-console-interface-organ-gate:
	python3 .github/scripts/check-creative-console-interface-organ-governance.py

alt21-gate: creative-core-runtime-organ-gate v9-core-organ-gate v9-runtime-organ-gate v10-core-organ-gate v10-runtime-organ-gate v10-action-engine-organ-gate creative-capability-bridge-organ-gate creative-operator-handoff-organ-gate creative-console-interface-organ-gate genome-gate

alt21-1-gate: alt21-gate alt20-1-gate

alt21-closure-gate:
	python3 tools/governance/check_alt21_closure.py

alt21-2-gate: alt21-1-gate alt21-closure-gate

alt21-governed-gate:
	python3 tools/governance/check_alt21_governed_eligibility.py

naming-protocol-organ-gate:
	python3 .github/scripts/check-naming-protocol-organ-governance.py

naming-genome-organ-gate:
	python3 .github/scripts/check-naming-genome-organ-governance.py

linguistic-mutation-organ-gate:
	python3 .github/scripts/check-linguistic-mutation-organ-governance.py

mythic-engineering-translator-organ-gate:
	python3 .github/scripts/check-mythic-engineering-translator-organ-governance.py

linguistic-drift-predictor-organ-gate:
	python3 .github/scripts/check-linguistic-drift-predictor-organ-governance.py

linguistic-lineage-viz-organ-gate:
	python3 .github/scripts/check-linguistic-lineage-viz-organ-governance.py

linguistic-remediation-organ-gate:
	python3 .github/scripts/check-linguistic-remediation-organ-governance.py

linguistic-cascade-organ-gate:
	python3 .github/scripts/check-linguistic-cascade-organ-governance.py

meta-linguistic-governance-organ-gate:
	python3 .github/scripts/check-meta-linguistic-governance-organ-governance.py

alt22-gate: naming-protocol-organ-gate naming-genome-organ-gate linguistic-mutation-organ-gate mythic-engineering-translator-organ-gate linguistic-drift-predictor-organ-gate linguistic-lineage-viz-organ-gate linguistic-remediation-organ-gate linguistic-cascade-organ-gate meta-linguistic-governance-organ-gate genome-gate

alt22-1-gate: alt22-gate alt21-1-gate

alt22-closure-gate:
	python3 tools/governance/check_alt22_closure.py

alt22-2-gate: alt22-1-gate alt22-closure-gate

alt22-governed-gate:
	python3 tools/governance/check_alt22_governed_eligibility.py

linguistic-drift-forecast-organ-gate:
	python3 .github/scripts/check-linguistic-drift-forecast-organ-governance.py

linguistic-preemptive-remediation-organ-gate:
	python3 .github/scripts/check-linguistic-preemptive-remediation-organ-governance.py

linguistic-predictive-governance-organ-gate:
	python3 .github/scripts/check-linguistic-predictive-governance-organ-governance.py

linguistic-predictive-cycle-history-organ-gate:
	python3 .github/scripts/check-linguistic-predictive-cycle-history-organ-governance.py

linguistic-governance-cycle-organ-gate:
	python3 .github/scripts/check-linguistic-governance-cycle-organ-governance.py

linguistic-governance-cycle-history-organ-gate:
	python3 .github/scripts/check-linguistic-governance-cycle-history-organ-governance.py

linguistic-forecast-consumption-organ-gate:
	python3 .github/scripts/check-linguistic-forecast-consumption-organ-governance.py

linguistic-cycle-optimization-organ-gate:
	python3 .github/scripts/check-linguistic-cycle-optimization-organ-governance.py

linguistic-closed-loop-fabric-organ-gate:
	python3 .github/scripts/check-linguistic-closed-loop-fabric-organ-governance.py

alt23-gate: linguistic-drift-forecast-organ-gate linguistic-preemptive-remediation-organ-gate linguistic-predictive-governance-organ-gate linguistic-predictive-cycle-history-organ-gate linguistic-governance-cycle-organ-gate linguistic-governance-cycle-history-organ-gate linguistic-forecast-consumption-organ-gate linguistic-cycle-optimization-organ-gate linguistic-closed-loop-fabric-organ-gate genome-gate

linguistic-forecast-calibration-organ-gate:
	python3 .github/scripts/check-linguistic-forecast-calibration-organ-governance.py

linguistic-governance-queue-organ-gate:
	python3 .github/scripts/check-linguistic-governance-queue-organ-governance.py

linguistic-full-governance-cycle-organ-gate:
	python3 .github/scripts/check-linguistic-full-governance-cycle-organ-governance.py

linguistic-governance-attestation-organ-gate:
	python3 .github/scripts/check-linguistic-governance-attestation-organ-governance.py

alt24-gate: linguistic-forecast-calibration-organ-gate linguistic-governance-queue-organ-gate linguistic-full-governance-cycle-organ-gate linguistic-governance-attestation-organ-gate genome-gate

alt24-1-gate: alt24-gate alt23-1-gate

alt24-closure-gate:
	python3 tools/governance/check_alt24_closure.py

alt24-2-gate: alt24-1-gate alt24-closure-gate

alt24-governed-gate:
	python3 tools/governance/check_alt24_governed_eligibility.py

linguistic-forecast-archive-organ-gate:
	python3 .github/scripts/check-linguistic-forecast-archive-organ-governance.py

linguistic-drift-report-organ-gate:
	python3 .github/scripts/check-linguistic-drift-report-organ-governance.py

linguistic-governance-work-order-organ-gate:
	python3 .github/scripts/check-linguistic-governance-work-order-organ-governance.py

linguistic-governance-cadence-organ-gate:
	python3 .github/scripts/check-linguistic-governance-cadence-organ-governance.py

linguistic-forecast-calibration-report-organ-gate:
	python3 .github/scripts/check-linguistic-forecast-calibration-report-organ-governance.py

linguistic-full-governance-cycle-history-organ-gate:
	python3 .github/scripts/check-linguistic-full-governance-cycle-history-organ-governance.py

meta-linguistic-registry-organ-gate:
	python3 .github/scripts/check-meta-linguistic-registry-organ-governance.py

linguistic-subsystem-promotion-organ-gate:
	python3 .github/scripts/check-linguistic-subsystem-promotion-organ-governance.py

linguistic-governed-lifecycle-fabric-organ-gate:
	python3 .github/scripts/check-linguistic-governed-lifecycle-fabric-organ-governance.py

alt25-gate: linguistic-forecast-archive-organ-gate linguistic-drift-report-organ-gate linguistic-governance-work-order-organ-gate linguistic-governance-cadence-organ-gate linguistic-forecast-calibration-report-organ-gate linguistic-full-governance-cycle-history-organ-gate meta-linguistic-registry-organ-gate linguistic-subsystem-promotion-organ-gate linguistic-governed-lifecycle-fabric-organ-gate genome-gate

alt25-1-gate: alt25-gate alt24-2-gate

alt25-closure-gate:
	python3 tools/governance/check_alt25_closure.py

alt25-2-gate: alt25-1-gate alt25-closure-gate

alt25-governed-gate:
	python3 tools/governance/check_alt25_governed_eligibility.py

linguistic-governance-day-organ-gate:
	python3 .github/scripts/check-linguistic-governance-day-organ-governance.py

linguistic-work-order-history-organ-gate:
	python3 .github/scripts/check-linguistic-work-order-history-organ-governance.py

linguistic-attestation-history-organ-gate:
	python3 .github/scripts/check-linguistic-attestation-history-organ-governance.py

alt26-gate: linguistic-governance-day-organ-gate linguistic-work-order-history-organ-gate linguistic-attestation-history-organ-gate genome-gate

alt26-1-gate: alt26-gate alt25-2-gate

alt26-closure-gate:
	python3 tools/governance/check_alt26_closure.py

alt26-2-gate: alt26-1-gate alt26-closure-gate

alt26-governed-gate:
	python3 tools/governance/check_alt26_governed_eligibility.py

alt27-gate: lineage-gate triangulation-gate narrative-gate barebones-gate ul-lineage-console-organ-gate recipe-module-organ-gate imagine-generator-organ-gate human-voice-extraction-organ-gate narrative-trust-pack-organ-gate genome-gate

alt27-1-gate: alt27-gate alt26-2-gate

alt27-closure-gate:
	python3 tools/governance/check_alt27_closure.py

alt27-2-gate: alt27-1-gate alt27-closure-gate

alt27-governed-gate:
	python3 tools/governance/check_alt27_governed_eligibility.py

story-forge-launcher-organ-gate:
	python3 .github/scripts/check-story-forge-launcher-organ-governance.py

movie-renderer-lane-organ-gate:
	python3 .github/scripts/check-movie-renderer-lane-organ-governance.py

text-game-to-video-organ-gate:
	python3 .github/scripts/check-text-game-to-video-organ-governance.py

game-front-door-organ-gate:
	python3 .github/scripts/check-game-front-door-organ-governance.py

text-to-3d-world-lane-organ-gate:
	python3 .github/scripts/check-text-to-3d-world-lane-organ-governance.py

world-pack-lane-organ-gate:
	python3 .github/scripts/check-world-pack-lane-organ-governance.py

alt28-gate: story-forge-launcher-organ-gate movie-renderer-lane-organ-gate text-game-to-video-organ-gate game-front-door-organ-gate text-to-3d-world-lane-organ-gate world-pack-lane-organ-gate genome-gate

alt28-1-gate: alt28-gate alt27-2-gate

alt28-closure-gate:
	python3 tools/governance/check_alt28_closure.py

alt28-2-gate: alt28-1-gate alt28-closure-gate

alt28-governed-gate:
	python3 tools/governance/check_alt28_governed_eligibility.py

media-processor-bridge-organ-gate:
	python3 .github/scripts/check-media-processor-bridge-organ-gate-governance.py

alt29-gate: alt28-governed-gate media-processor-bridge-organ-gate genome-gate

alt29-1-gate: alt29-gate alt28-2-gate

alt29-closure-gate:
	python3 tools/governance/check_alt29_closure.py

alt29-2-gate: alt29-1-gate alt29-closure-gate

alt29-governed-gate:
	python3 tools/governance/check_alt29_governed_eligibility.py

alt30-governed-gate:
	python3 tools/governance/check_alt30_governed_eligibility.py

v1.26.1-gate: alt30-governed-gate otem-execution-substrate-gate

alt23-1-gate: alt23-gate alt22-1-gate

alt23-closure-gate:
	python3 tools/governance/check_alt23_closure.py

alt23-2-gate: alt23-1-gate alt23-closure-gate

alt23-governed-gate:
	python3 tools/governance/check_alt23_governed_eligibility.py

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
