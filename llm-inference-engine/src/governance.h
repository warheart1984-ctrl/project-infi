#pragma once

#include <string>
#include <atomic>
#include <mutex>
#include <fstream>
#include <chrono>
#include <nlohmann/json.hpp>

namespace llm_engine {

struct GovernanceConfig {
    int max_concurrent = 4;
    int vram_budget_mb = 3500;
    int thermal_throttle_c = 85;
    std::string log_path = "requests.jsonl";
    int max_prompt_length = 4096;
    int max_tokens = 512;
    float max_temperature = 2.0f;
    float min_temperature = 0.0f;
};

struct RequestLog {
    std::string ts;
    std::string node;
    std::string runtime_version;
    std::string backend;
    std::string model;
    std::string evidence_receipt;
    std::string replay_id;
    std::string proof_level;
    std::string verification_status;
    std::string governance_decision;
    int prompt_tokens = 0;
    int completion_tokens = 0;
    int latency_ms = 0;
    float temperature = 0.0f;
    std::string status;
    std::string error;
    int cpu_temp_c = 0;
    int vram_used_mb = 0;
    bool fallback = false;

    nlohmann::json to_json() const {
        nlohmann::json j;
        j["ts"] = ts;
        j["node"] = node;
        j["runtime_version"] = runtime_version;
        j["backend"] = backend;
        j["model"] = model;
        j["evidence_receipt"] = evidence_receipt;
        j["replay_id"] = replay_id;
        j["proof_level"] = proof_level;
        j["verification_status"] = verification_status;
        j["governance_decision"] = governance_decision;
        j["prompt_tokens"] = prompt_tokens;
        j["completion_tokens"] = completion_tokens;
        j["latency_ms"] = latency_ms;
        j["temperature"] = temperature;
        j["status"] = status;
        j["error"] = error.empty() ? nullptr : error;
        j["cpu_temp_c"] = cpu_temp_c;
        j["vram_used_mb"] = vram_used_mb;
        j["fallback"] = fallback;
        return j;
    }
};

class Governance {
public:
    explicit Governance(const GovernanceConfig& config);
    
    // Pre-flight checks
    bool validate_request(const std::string& prompt, int max_tokens, float temperature);
    bool can_accept_request();
    bool can_allocate_vram(int required_mb);
    
    // Concurrency management
    void increment_active_requests();
    void decrement_active_requests();
    int get_active_requests() const;
    
    // VRAM tracking
    void allocate_vram(int mb);
    void free_vram(int mb);
    int get_vram_used() const;
    
    // Thermal monitoring
    int get_cpu_temp();
    bool is_thermal_throttled();
    
    // Logging
    void log_request(const RequestLog& log);
    std::string get_timestamp();
    
    // Configuration
    const GovernanceConfig& get_config() const;
    
private:
    GovernanceConfig config_;
    std::atomic<int> active_requests_;
    std::atomic<int> vram_used_mb_;
    std::mutex log_mutex_;
    std::ofstream log_file_;
    
    int read_thermal_zone(const std::string& path);
};

} // namespace llm_engine
