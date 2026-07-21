#pragma once

#include <string>

#include <nlohmann/json.hpp>

namespace llm_engine {

inline constexpr const char* kRuntimeVersion = "1.0.0";
inline constexpr const char* kDefaultProofLevel = "P3";

struct ProofSurfaceInput {
    std::string backend;
    std::string model;
    std::string proof_level = kDefaultProofLevel;
    std::string prompt;
    int max_tokens = 0;
    float temperature = 0.0f;
    bool backend_available = false;
    std::string verification_status = "rejected";
    std::string governance_decision = "deny";
    int latency_ms = 0;
    int tokens_generated = 0;
    float tokens_per_second = 0.0f;
    int vram_used_mb = 0;
    int cpu_temp_c = 0;
    bool fallback = false;
};

struct ProofReceipt {
    std::string runtime_version;
    std::string backend;
    std::string model;
    std::string proof_level;
    std::string evidence_receipt;
    std::string replay_id;
    std::string verification_status;
    std::string governance_decision;
    nlohmann::json resource_usage;

    nlohmann::json to_json() const;
};

ProofReceipt make_proof_receipt(const ProofSurfaceInput& input);

} // namespace llm_engine
