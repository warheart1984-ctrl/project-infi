#include "../src/http_server.h"
#include "../src/governance.h"
#include <iostream>
#include <cassert>
#include <thread>
#include <chrono>

using namespace llm_engine;

extern int test_proof_surface_main();

void test_server_startup() {
    std::cout << "Testing server startup..." << std::endl;
    
    GovernanceConfig config;
    config.max_concurrent = 4;
    config.vram_budget_mb = 3500;
    config.thermal_throttle_c = 85;
    config.log_path = "test_requests.jsonl";
    
    HTTPServer server(config);
    
    // Test health endpoint
    auto health = server.handle_health();
    
    assert(health["status"] == "ok");
    assert(health["model_loaded"] == false);
    assert(health["backends"]["cpu"] == false);
    assert(health["backends"]["opencl"] == false);
    assert(health["backends"]["vulkan"] == false);
    
    std::cout << "✓ Server startup test passed" << std::endl;
}

void test_governance_validation() {
    std::cout << "Testing governance validation..." << std::endl;
    
    GovernanceConfig config;
    config.max_prompt_length = 4096;
    config.max_tokens = 512;
    config.max_temperature = 2.0f;
    config.min_temperature = 0.0f;
    
    Governance governance(config);
    
    // Valid request
    assert(governance.validate_request("Hello", 100, 0.7f) == true);
    
    // Invalid prompt length
    std::string long_prompt(5000, 'a');
    assert(governance.validate_request(long_prompt, 100, 0.7f) == false);
    
    // Invalid max_tokens
    assert(governance.validate_request("Hello", 1000, 0.7f) == false);
    assert(governance.validate_request("Hello", 0, 0.7f) == false);
    
    // Invalid temperature
    assert(governance.validate_request("Hello", 100, 3.0f) == false);
    assert(governance.validate_request("Hello", 100, -0.5f) == false);
    
    std::cout << "✓ Governance validation test passed" << std::endl;
}

void test_concurrency_control() {
    std::cout << "Testing concurrency control..." << std::endl;
    
    GovernanceConfig config;
    config.max_concurrent = 2;
    
    Governance governance(config);
    
    assert(governance.can_accept_request() == true);
    
    governance.increment_active_requests();
    assert(governance.get_active_requests() == 1);
    assert(governance.can_accept_request() == true);
    
    governance.increment_active_requests();
    assert(governance.get_active_requests() == 2);
    assert(governance.can_accept_request() == false);
    
    governance.decrement_active_requests();
    assert(governance.get_active_requests() == 1);
    assert(governance.can_accept_request() == true);
    
    governance.decrement_active_requests();
    assert(governance.get_active_requests() == 0);
    
    std::cout << "✓ Concurrency control test passed" << std::endl;
}

void test_vram_tracking() {
    std::cout << "Testing VRAM tracking..." << std::endl;
    
    GovernanceConfig config;
    config.vram_budget_mb = 3500;
    
    Governance governance(config);
    
    assert(governance.can_allocate_vram(1000) == true);
    assert(governance.can_allocate_vram(4000) == false);
    
    governance.allocate_vram(1000);
    assert(governance.get_vram_used() == 1000);
    assert(governance.can_allocate_vram(2000) == true);
    assert(governance.can_allocate_vram(3000) == false);
    
    governance.allocate_vram(2000);
    assert(governance.get_vram_used() == 3000);
    
    governance.free_vram(1000);
    assert(governance.get_vram_used() == 2000);
    assert(governance.can_allocate_vram(1500) == true);
    
    std::cout << "✓ VRAM tracking test passed" << std::endl;
}

void test_request_logging() {
    std::cout << "Testing request logging..." << std::endl;
    
    GovernanceConfig config;
    config.log_path = "test_requests.jsonl";
    
    Governance governance(config);
    
    RequestLog log;
    log.ts = "2026-07-06T16:28:00Z";
    log.node = "test-node";
    log.backend = "cpu";
    log.prompt_tokens = 12;
    log.completion_tokens = 47;
    log.latency_ms = 891;
    log.temperature = 0.7f;
    log.status = "ok";
    log.error = "";
    log.cpu_temp_c = 71;
    log.vram_used_mb = 3241;
    log.fallback = false;
    
    governance.log_request(log);
    
    // Verify log file was created and contains entry
    std::ifstream file(config.log_path);
    assert(file.is_open());
    
    std::string line;
    std::getline(file, line);
    assert(!line.empty());
    
    file.close();
    
    // Clean up
    std::remove(config.log_path.c_str());
    
    std::cout << "✓ Request logging test passed" << std::endl;
}

void test_inference_request_validation() {
    std::cout << "Testing inference request validation..." << std::endl;
    
    GovernanceConfig config;
    HTTPServer server(config);
    
    InferenceRequest valid_request;
    valid_request.prompt = "Hello world";
    valid_request.max_tokens = 50;
    valid_request.temperature = 0.7f;
    valid_request.backend = "cpu";
    
    InferenceResponse response = server.handle_inference(valid_request);
    
    // Should fail because model not loaded
    assert(!response.error.empty());
    
    std::cout << "✓ Inference request validation test passed" << std::endl;
}

void test_backends_endpoint() {
    std::cout << "Testing backends endpoint..." << std::endl;
    
    GovernanceConfig config;
    HTTPServer server(config);
    
    auto backends = server.handle_backends();
    
    assert(backends["cpu"]["available"] == true);
    assert(backends["cpu"]["loaded"] == false);
    assert(backends["cpu"]["vram_mb"] == 0);
    
    assert(backends.contains("opencl"));
    assert(backends.contains("vulkan"));
    
    assert(backends["current"] == "cpu");
    
    std::cout << "✓ Backends endpoint test passed" << std::endl;
}

void test_proof_surface_contract() {
    std::cout << "Testing proof surface contract..." << std::endl;

    GovernanceConfig config;
    HTTPServer server(config);

    InferenceRequest request;
    request.prompt = "proof";
    request.max_tokens = 8;
    request.temperature = 0.2f;
    request.backend = "cpu";

    const auto response = server.handle_inference(request).to_json();

    assert(response.contains("metadata"));
    assert(response["metadata"].contains("runtime_version"));
    assert(response["metadata"].contains("backend"));
    assert(response["metadata"].contains("model"));
    assert(response["metadata"].contains("proof_level"));
    assert(response["metadata"].contains("evidence_receipt"));
    assert(response["metadata"].contains("replay_id"));
    assert(response["metadata"].contains("verification_status"));
    assert(response["metadata"].contains("governance_decision"));
    assert(response["metadata"].contains("resource_usage"));

    std::cout << "âœ“ Proof surface contract test passed" << std::endl;
}

void test_thermal_monitoring() {
    std::cout << "Testing thermal monitoring..." << std::endl;
    
    GovernanceConfig config;
    config.thermal_throttle_c = 85;
    
    Governance governance(config);
    
    int temp = governance.get_cpu_temp();
    // Should return a valid temperature or 0 if not available
    assert(temp >= 0);
    
    bool throttled = governance.is_thermal_throttled();
    // Should be false unless system is actually overheating
    // Just verify it doesn't crash
    (void)throttled;
    
    std::cout << "✓ Thermal monitoring test passed" << std::endl;
}

void test_over_limit_rejection() {
    std::cout << "Testing over-limit rejection..." << std::endl;
    
    GovernanceConfig config;
    config.max_tokens = 512;
    config.max_prompt_length = 4096;
    
    Governance governance(config);
    
    // Test max_tokens over limit
    assert(governance.validate_request("Hello", 1000, 0.7f) == false);
    
    // Test prompt over limit
    std::string long_prompt(5000, 'a');
    assert(governance.validate_request(long_prompt, 100, 0.7f) == false);
    
    std::cout << "✓ Over-limit rejection test passed" << std::endl;
}

void test_concurrent_requests() {
    std::cout << "Testing concurrent requests..." << std::endl;
    
    GovernanceConfig config;
    config.max_concurrent = 2;
    
    Governance governance(config);
    
    assert(governance.can_accept_request() == true);
    governance.increment_active_requests();
    
    assert(governance.can_accept_request() == true);
    governance.increment_active_requests();
    
    assert(governance.can_accept_request() == false);
    
    // Simulate request completion
    governance.decrement_active_requests();
    assert(governance.can_accept_request() == true);
    
    governance.decrement_active_requests();
    
    std::cout << "✓ Concurrent requests test passed" << std::endl;
}

int test_integration_main() {
    std::cout << "Running Tier 3 Integration Tests" << std::endl;
    std::cout << "===================================" << std::endl;
    
    try {
        test_server_startup();
        test_governance_validation();
        test_concurrency_control();
        test_vram_tracking();
        test_request_logging();
        test_inference_request_validation();
        test_backends_endpoint();
        test_proof_surface_main();
        test_proof_surface_contract();
        test_thermal_monitoring();
        test_over_limit_rejection();
        test_concurrent_requests();
        
        std::cout << "\n✓ All Tier 3 integration tests passed" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "✗ Test failed: " << e.what() << std::endl;
        return 1;
    }
}
