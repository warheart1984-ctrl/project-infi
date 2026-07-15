#pragma once

#include "proof_surface.h"
#include "governance.h"
#include "backend/cpu_backend.h"
#include "backend/opencl_backend.h"
#include "backend/vulkan_backend.h"
#include <string>
#include <memory>
#include <functional>
#include <map>
#include <thread>
#include <atomic>
#include <cstdint>

namespace llm_engine {

struct InferenceRequest {
    std::string prompt;
    int max_tokens = 0;
    float temperature = 0.0f;
    std::string backend = "cpu"; // "cpu", "opencl", "vulkan"
};

struct InferenceResponse {
    std::string completion;
    std::string backend_used = "cpu";
    std::string model;
    int latency_ms = 0;
    int tokens_generated = 0;
    float tokens_per_second = 0.0f;
    std::string error;
    int vram_used_mb = 0;
    int cpu_temp_c = 0;
    bool fallback = false;
    ProofReceipt proof_receipt;
    
    nlohmann::json to_json() const {
        nlohmann::json j;
        j["completion"] = completion;
        nlohmann::json metadata = {
            {"backend_used", backend_used},
            {"latency_ms", latency_ms},
            {"tokens_generated", tokens_generated},
            {"tokens_per_second", tokens_per_second},
            {"vram_used_mb", vram_used_mb},
            {"cpu_temp_c", cpu_temp_c},
            {"fallback", fallback}
        };
        const nlohmann::json proof = proof_receipt.to_json();
        for (const auto& item : proof.items()) {
            metadata[item.key()] = item.value();
        }
        j["metadata"] = metadata;
        if (!error.empty()) {
            j["error"] = error;
        }
        return j;
    }
};

class HTTPServer {
public:
    HTTPServer(const GovernanceConfig& config);
    
    bool start(int port = 8080);
    void stop();
    
    bool load_model(const std::string& model_path);
    
    // HTTP endpoints
    InferenceResponse handle_inference(const InferenceRequest& request);
    nlohmann::json handle_health();
    nlohmann::json handle_backends();
    
private:
    struct HttpRequest {
        std::string method;
        std::string target;
        std::string version;
        std::map<std::string, std::string> headers;
        std::string body;
    };

    std::unique_ptr<Governance> governance_;
    std::unique_ptr<CPUBackend> cpu_backend_;
    std::unique_ptr<OpenCLBackend> opencl_backend_;
    std::unique_ptr<VulkanBackend> vulkan_backend_;
    
    std::string current_backend_;
    std::string current_model_;
    bool model_loaded_;
    int port_ = 8080;
    std::atomic<bool> running_;
    std::thread server_thread_;
#ifdef _WIN32
    std::intptr_t listen_socket_;
#else
    int listen_socket_;
#endif

    bool select_backend(const std::string& preferred);
    bool is_backend_available(const std::string& backend) const;
    InferenceResponse run_inference(const InferenceRequest& request);
    ProofReceipt build_proof_receipt(const InferenceRequest& request, const InferenceResponse& response) const;
    void finalize_response(const InferenceRequest& request, InferenceResponse& response, int latency_ms);
    void log_request(const InferenceRequest& request, const InferenceResponse& response, 
                     const std::string& backend, int latency_ms);
    void serve_loop();
    void handle_client(std::intptr_t client_socket);
    std::string dispatch_request(const HttpRequest& request, int& status_code, std::string& content_type);
    HttpRequest parse_request(const std::string& raw_request) const;
    InferenceRequest parse_inference_request(const nlohmann::json& body) const;
    std::string make_json_response(int status_code, const nlohmann::json& body) const;
    std::string make_text_response(int status_code, const std::string& body, const std::string& content_type) const;
    static std::string route_backend_from_target(const std::string& target);
};

} // namespace llm_engine
