#include "governance.h"
#include <iostream>
#include <fstream>
#include <filesystem>
#include <sstream>
#include <iomanip>

namespace llm_engine {

namespace {

std::string escape_json_string(const std::string& input) {
    std::string output;
    output.reserve(input.size() + 8);
    for (char ch : input) {
        switch (ch) {
            case '\\': output += "\\\\"; break;
            case '"': output += "\\\""; break;
            case '\n': output += "\\n"; break;
            case '\r': output += "\\r"; break;
            case '\t': output += "\\t"; break;
            default: output.push_back(ch); break;
        }
    }
    return output;
}

} // namespace

Governance::Governance(const GovernanceConfig& config)
    : config_(config),
      active_requests_(0),
      vram_used_mb_(0) {
    
    // Open log file
    log_file_.open(config_.log_path, std::ios::app);
    if (!log_file_.is_open()) {
        std::cerr << "Failed to open log file: " << config_.log_path << std::endl;
    }
}

bool Governance::validate_request(const std::string& prompt, int max_tokens, float temperature) {
    // Validate prompt length
    if (prompt.length() > static_cast<size_t>(config_.max_prompt_length)) {
        return false;
    }
    
    // Validate max_tokens range
    if (max_tokens < 1 || max_tokens > config_.max_tokens) {
        return false;
    }
    
    // Validate temperature range
    if (temperature < config_.min_temperature || temperature > config_.max_temperature) {
        return false;
    }
    
    return true;
}

bool Governance::can_accept_request() {
    return active_requests_.load() < config_.max_concurrent;
}

bool Governance::can_allocate_vram(int required_mb) {
    return (vram_used_mb_.load() + required_mb) <= config_.vram_budget_mb;
}

void Governance::increment_active_requests() {
    active_requests_.fetch_add(1);
}

void Governance::decrement_active_requests() {
    active_requests_.fetch_sub(1);
}

int Governance::get_active_requests() const {
    return active_requests_.load();
}

void Governance::allocate_vram(int mb) {
    vram_used_mb_.fetch_add(mb);
}

void Governance::free_vram(int mb) {
    vram_used_mb_.fetch_sub(mb);
}

int Governance::get_vram_used() const {
    return vram_used_mb_.load();
}

int Governance::get_cpu_temp() {
    // Try to read from Linux thermal zones
    for (int i = 0; i < 10; i++) {
        std::string path = "/sys/class/thermal/thermal_zone" + std::to_string(i) + "/temp";
        int temp = read_thermal_zone(path);
        if (temp > 0) {
            return temp / 1000; // Convert from millidegrees to degrees
        }
    }
    
    // Fallback: return a reasonable default or use platform-specific methods
    return 0;
}

bool Governance::is_thermal_throttled() {
    int temp = get_cpu_temp();
    return temp >= config_.thermal_throttle_c;
}

void Governance::log_request(const RequestLog& log) {
    std::lock_guard<std::mutex> lock(log_mutex_);
    
    if (log_file_.is_open()) {
        log_file_ << "{"
                  << "\"ts\":\"" << escape_json_string(log.ts) << "\","
                  << "\"node\":\"" << escape_json_string(log.node) << "\","
                  << "\"runtime_version\":\"" << escape_json_string(log.runtime_version) << "\","
                  << "\"backend\":\"" << escape_json_string(log.backend) << "\","
                  << "\"model\":\"" << escape_json_string(log.model) << "\","
                  << "\"evidence_receipt\":\"" << escape_json_string(log.evidence_receipt) << "\","
                  << "\"replay_id\":\"" << escape_json_string(log.replay_id) << "\","
                  << "\"proof_level\":\"" << escape_json_string(log.proof_level) << "\","
                  << "\"verification_status\":\"" << escape_json_string(log.verification_status) << "\","
                  << "\"governance_decision\":\"" << escape_json_string(log.governance_decision) << "\","
                  << "\"prompt_tokens\":" << log.prompt_tokens << ","
                  << "\"completion_tokens\":" << log.completion_tokens << ","
                  << "\"latency_ms\":" << log.latency_ms << ","
                  << "\"temperature\":" << log.temperature << ","
                  << "\"status\":\"" << escape_json_string(log.status) << "\","
                  << "\"error\":" << (log.error.empty() ? std::string("null") : std::string("\"") + escape_json_string(log.error) + "\"") << ","
                  << "\"cpu_temp_c\":" << log.cpu_temp_c << ","
                  << "\"vram_used_mb\":" << log.vram_used_mb << ","
                  << "\"fallback\":" << (log.fallback ? "true" : "false")
                  << "}" << std::endl;
        log_file_.flush();
    }
}

const GovernanceConfig& Governance::get_config() const {
    return config_;
}

std::string Governance::get_timestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
#ifdef _WIN32
    std::tm utc_time{};
    gmtime_s(&utc_time, &time_t);
    ss << std::put_time(&utc_time, "%Y-%m-%dT%H:%M:%SZ");
#else
    std::tm utc_time{};
    gmtime_r(&time_t, &utc_time);
    ss << std::put_time(&utc_time, "%Y-%m-%dT%H:%M:%SZ");
#endif
    return ss.str();
}

int Governance::read_thermal_zone(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        return -1;
    }
    
    int temp;
    file >> temp;
    return temp;
}

} // namespace llm_engine
