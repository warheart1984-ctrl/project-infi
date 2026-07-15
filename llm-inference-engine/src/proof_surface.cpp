#include "proof_surface.h"

#include <cstdint>
#include <iomanip>
#include <sstream>

namespace llm_engine {

namespace {

std::string normalize_or_default(const std::string& value, const std::string& fallback) {
    return value.empty() ? fallback : value;
}

std::uint64_t fnv1a64(const std::string& value) {
    constexpr std::uint64_t kOffset = 14695981039346656037ull;
    constexpr std::uint64_t kPrime = 1099511628211ull;
    std::uint64_t hash = kOffset;
    for (unsigned char ch : value) {
        hash ^= static_cast<std::uint64_t>(ch);
        hash *= kPrime;
    }
    return hash;
}

std::string to_hex(std::uint64_t value) {
    std::ostringstream stream;
    stream << std::hex << std::nouppercase << std::setfill('0') << std::setw(16) << value;
    return stream.str();
}

std::string canonical_material(const ProofSurfaceInput& input) {
    std::ostringstream stream;
    stream << kRuntimeVersion << '|'
           << normalize_or_default(input.backend, "cpu") << '|'
           << normalize_or_default(input.model, "llm-engine-local") << '|'
           << normalize_or_default(input.proof_level, kDefaultProofLevel) << '|'
           << input.max_tokens << '|'
           << std::fixed << std::setprecision(6) << input.temperature << '|'
           << input.prompt;
    return stream.str();
}

} // namespace

nlohmann::json ProofReceipt::to_json() const {
    nlohmann::json j;
    j["runtime_version"] = runtime_version;
    j["backend"] = backend;
    j["model"] = model;
    j["proof_level"] = proof_level;
    j["evidence_receipt"] = evidence_receipt;
    j["replay_id"] = replay_id;
    j["verification_status"] = verification_status;
    j["governance_decision"] = governance_decision;
    j["resource_usage"] = resource_usage;
    return j;
}

ProofReceipt make_proof_receipt(const ProofSurfaceInput& input) {
    ProofReceipt receipt;
    receipt.runtime_version = kRuntimeVersion;
    receipt.backend = normalize_or_default(input.backend, "cpu");
    receipt.model = normalize_or_default(input.model, "llm-engine-local");
    receipt.proof_level = normalize_or_default(input.proof_level, kDefaultProofLevel);
    receipt.verification_status = normalize_or_default(input.verification_status, "rejected");
    receipt.governance_decision = normalize_or_default(input.governance_decision, "deny");

    const std::string material = canonical_material(input);
    receipt.evidence_receipt = std::string("ev-") + to_hex(fnv1a64(material + "|evidence"));
    receipt.replay_id = std::string("rp-") + to_hex(fnv1a64(material + "|replay"));

    receipt.resource_usage = nlohmann::json::object();
    receipt.resource_usage["backend_available"] = input.backend_available;
    receipt.resource_usage["latency_ms"] = input.latency_ms;
    receipt.resource_usage["tokens_generated"] = input.tokens_generated;
    receipt.resource_usage["tokens_per_second"] = input.tokens_per_second;
    receipt.resource_usage["vram_used_mb"] = input.vram_used_mb;
    receipt.resource_usage["cpu_temp_c"] = input.cpu_temp_c;
    receipt.resource_usage["fallback"] = input.fallback;
    return receipt;
}

} // namespace llm_engine
