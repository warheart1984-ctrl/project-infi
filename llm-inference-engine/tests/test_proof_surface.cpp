#include "../src/http_server.h"
#include "../src/governance.h"
#include "../src/proof_surface.h"

#include <cassert>
#include <cstdio>
#include <fstream>
#include <iostream>

using namespace llm_engine;

namespace {

ProofSurfaceInput make_sample_input() {
    ProofSurfaceInput input;
    input.backend = "cpu";
    input.model = "unit-test-model";
    input.proof_level = kDefaultProofLevel;
    input.prompt = "Build the canonical proof surface.";
    input.max_tokens = 48;
    input.temperature = 0.15f;
    input.backend_available = true;
    input.verification_status = "verified";
    input.governance_decision = "allow";
    input.latency_ms = 7;
    input.tokens_generated = 21;
    input.tokens_per_second = 3000.0f;
    input.vram_used_mb = 0;
    input.cpu_temp_c = 42;
    input.fallback = false;
    return input;
}

void test_proof_receipt_is_deterministic() {
    std::cout << "Testing proof receipt determinism..." << std::endl;

    const ProofSurfaceInput input = make_sample_input();
    const ProofReceipt first = make_proof_receipt(input);
    const ProofReceipt second = make_proof_receipt(input);

    assert(first.runtime_version == kRuntimeVersion);
    assert(first.backend == "cpu");
    assert(first.model == "unit-test-model");
    assert(first.proof_level == kDefaultProofLevel);
    assert(first.evidence_receipt == second.evidence_receipt);
    assert(first.replay_id == second.replay_id);
    assert(first.verification_status == "verified");
    assert(first.governance_decision == "allow");
    assert(first.resource_usage["backend_available"] == true);
    assert(first.resource_usage["latency_ms"] == 7);
    assert(first.resource_usage["tokens_generated"] == 21);
    assert(first.resource_usage["fallback"] == false);

    const nlohmann::json json = first.to_json();
    assert(json["runtime_version"] == kRuntimeVersion);
    assert(json["backend"] == "cpu");
    assert(json["resource_usage"]["cpu_temp_c"] == 42);
    assert(json["resource_usage"]["tokens_per_second"] == 3000.0f);

    std::cout << "proof receipt determinism passed" << std::endl;
}

void test_response_metadata_contains_proof_fields() {
    std::cout << "Testing response metadata serialization..." << std::endl;

    InferenceResponse response;
    response.completion = "ok";
    response.backend_used = "cpu";
    response.latency_ms = 7;
    response.tokens_generated = 21;
    response.tokens_per_second = 3000.0f;
    response.vram_used_mb = 0;
    response.cpu_temp_c = 42;
    response.proof_receipt = make_proof_receipt(make_sample_input());

    const nlohmann::json json = response.to_json();
    assert(json["completion"] == "ok");
    assert(json["metadata"]["backend_used"] == "cpu");
    assert(json["metadata"]["runtime_version"] == kRuntimeVersion);
    assert(json["metadata"]["backend"] == "cpu");
    assert(json["metadata"]["model"] == "unit-test-model");
    assert(json["metadata"]["proof_level"] == kDefaultProofLevel);
    assert(json["metadata"]["evidence_receipt"].is_string());
    assert(json["metadata"]["replay_id"].is_string());
    assert(json["metadata"]["verification_status"] == "verified");
    assert(json["metadata"]["governance_decision"] == "allow");
    assert(json["metadata"]["resource_usage"]["backend_available"] == true);
    assert(json["metadata"]["resource_usage"]["latency_ms"] == 7);

    std::cout << "response metadata serialization passed" << std::endl;
}

void test_backend_gate_fails_closed() {
    std::cout << "Testing fail-closed backend gate..." << std::endl;

    GovernanceConfig config;
    config.log_path = "proof_surface_gate_test.jsonl";

    {
        HTTPServer server(config);

        InferenceRequest request;
        request.prompt = "Use the gated backend.";
        request.max_tokens = 16;
        request.temperature = 0.2f;
        request.backend = "opencl";

        const InferenceResponse response = server.handle_inference(request);

        assert(!response.error.empty());
        assert(response.error == "Requested backend not available");
        assert(response.backend_used == "opencl");
        assert(response.proof_receipt.verification_status == "rejected");
        assert(response.proof_receipt.governance_decision == "deny");
        assert(response.proof_receipt.resource_usage["backend_available"] == false);

        const nlohmann::json json = response.to_json();
        assert(json["metadata"]["verification_status"] == "rejected");
        assert(json["metadata"]["governance_decision"] == "deny");
        assert(json["metadata"]["resource_usage"]["backend_available"] == false);
    }

    std::remove(config.log_path.c_str());

    std::cout << "fail-closed backend gate passed" << std::endl;
}

void test_request_log_matches_response_ids() {
    std::cout << "Testing request log correlation..." << std::endl;

    GovernanceConfig config;
    config.log_path = "proof_surface_log_test.jsonl";

    {
        Governance governance(config);

        RequestLog log;
        log.ts = "2026-07-08T00:00:00Z";
        log.node = "test-node";
        log.runtime_version = kRuntimeVersion;
        log.backend = "cpu";
        log.model = "unit-test-model";
        log.evidence_receipt = "ev-0123456789abcdef";
        log.replay_id = "rp-fedcba9876543210";
        log.proof_level = kDefaultProofLevel;
        log.verification_status = "verified";
        log.governance_decision = "allow";
        log.prompt_tokens = 8;
        log.completion_tokens = 4;
        log.latency_ms = 2;
        log.temperature = 0.3f;
        log.status = "ok";
        log.error = "";
        log.cpu_temp_c = 40;
        log.vram_used_mb = 0;
        log.fallback = false;

        governance.log_request(log);
    }

    std::ifstream file(config.log_path);
    assert(file.is_open());

    std::string line;
    std::getline(file, line);
    assert(!line.empty());
    file.close();

    const nlohmann::json parsed = nlohmann::json::parse(line);
    assert(parsed["runtime_version"] == kRuntimeVersion);
    assert(parsed["backend"] == "cpu");
    assert(parsed["model"] == "unit-test-model");
    assert(parsed["evidence_receipt"] == "ev-0123456789abcdef");
    assert(parsed["replay_id"] == "rp-fedcba9876543210");
    assert(parsed["proof_level"] == kDefaultProofLevel);
    assert(parsed["verification_status"] == "verified");
    assert(parsed["governance_decision"] == "allow");

    std::remove(config.log_path.c_str());

    std::cout << "request log correlation passed" << std::endl;
}

} // namespace

int test_proof_surface_main() {
    std::cout << "Running proof surface tests" << std::endl;
    std::cout << "==========================" << std::endl;

    try {
        test_proof_receipt_is_deterministic();
        test_response_metadata_contains_proof_fields();
        test_backend_gate_fails_closed();
        test_request_log_matches_response_ids();

        std::cout << "\nproof surface tests passed" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "proof surface test failed: " << e.what() << std::endl;
        return 1;
    }
}
