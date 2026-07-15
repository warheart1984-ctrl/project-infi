#include "http_server.h"

#include <chrono>
#include <thread>
#include <iostream>
#include <sstream>
#include <algorithm>
#include <cctype>
#include <vector>
#include <cstring>
#include <ctime>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "Ws2_32.lib")
using socket_handle_t = SOCKET;
static constexpr socket_handle_t INVALID_SOCKET_HANDLE = INVALID_SOCKET;
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
using socket_handle_t = int;
static constexpr socket_handle_t INVALID_SOCKET_HANDLE = -1;
#endif

namespace llm_engine {

namespace {

std::string trim_copy(const std::string& value) {
    const auto begin = value.find_first_not_of(" \t\r\n");
    if (begin == std::string::npos) {
        return "";
    }
    const auto end = value.find_last_not_of(" \t\r\n");
    return value.substr(begin, end - begin + 1);
}

std::string to_lower_copy(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return value;
}

std::vector<std::string> split_lines(const std::string& body) {
    std::vector<std::string> lines;
    std::istringstream stream(body);
    std::string line;
    while (std::getline(stream, line)) {
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }
        lines.push_back(line);
    }
    return lines;
}

bool send_all(socket_handle_t socket_fd, const std::string& payload) {
    const char* data = payload.data();
    std::size_t remaining = payload.size();
    while (remaining > 0) {
#ifdef _WIN32
        const int sent = ::send(socket_fd, data, static_cast<int>(remaining), 0);
#else
        const ssize_t sent = ::send(socket_fd, data, remaining, 0);
#endif
        if (sent <= 0) {
            return false;
        }
        data += sent;
        remaining -= static_cast<std::size_t>(sent);
    }
    return true;
}

std::string reason_phrase(int status_code) {
    switch (status_code) {
        case 200: return "OK";
        case 400: return "Bad Request";
        case 404: return "Not Found";
        case 405: return "Method Not Allowed";
        case 429: return "Too Many Requests";
        case 500: return "Internal Server Error";
        default: return "OK";
    }
}

} // namespace

HTTPServer::HTTPServer(const GovernanceConfig& config)
    : governance_(std::make_unique<Governance>(config)),
      model_loaded_(false),
      running_(false),
      listen_socket_(INVALID_SOCKET_HANDLE),
      current_backend_("cpu"),
      current_model_("llm-engine-local") {
    cpu_backend_ = std::make_unique<CPUBackend>();
    opencl_backend_ = std::make_unique<OpenCLBackend>();
    vulkan_backend_ = std::make_unique<VulkanBackend>();

    try {
        if (opencl_backend_->initialize()) {
            std::cout << "OpenCL backend available" << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "OpenCL backend initialization failed: " << e.what() << std::endl;
    }

    try {
        if (vulkan_backend_->initialize()) {
            std::cout << "Vulkan backend available" << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "Vulkan backend initialization failed: " << e.what() << std::endl;
    }
}

bool HTTPServer::load_model(const std::string& model_path) {
    current_model_ = model_path.empty() ? std::string("llm-engine-local") : model_path;
    if (!cpu_backend_->load_model(model_path)) {
        std::cerr << "Failed to load model on CPU backend" << std::endl;
        return false;
    }

    if (opencl_backend_->is_loaded() || opencl_backend_->initialize()) {
        try {
            if (opencl_backend_->load_model(model_path)) {
                std::cout << "Model loaded on OpenCL backend" << std::endl;
            }
        } catch (const std::exception& e) {
            std::cerr << "OpenCL model load failed: " << e.what() << std::endl;
        }
    }

    if (vulkan_backend_->is_loaded() || vulkan_backend_->initialize()) {
        try {
            if (vulkan_backend_->load_model(model_path)) {
                std::cout << "Model loaded on Vulkan backend" << std::endl;
            }
        } catch (const std::exception& e) {
            std::cerr << "Vulkan model load failed: " << e.what() << std::endl;
        }
    }

    model_loaded_ = true;
    return true;
}

bool HTTPServer::start(int port) {
    if (running_.load()) {
        return true;
    }

    port_ = port;

#ifdef _WIN32
    WSADATA wsa_data;
    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
        std::cerr << "Failed to initialize WinSock" << std::endl;
        return false;
    }
#endif

    listen_socket_ = static_cast<std::intptr_t>(::socket(AF_INET, SOCK_STREAM, 0));
    if (listen_socket_ == INVALID_SOCKET_HANDLE) {
        std::cerr << "Failed to create server socket" << std::endl;
        return false;
    }

    int reuse = 1;
    (void)setsockopt(static_cast<socket_handle_t>(listen_socket_), SOL_SOCKET, SO_REUSEADDR,
                     reinterpret_cast<const char*>(&reuse), sizeof(reuse));

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(static_cast<uint16_t>(port_));

    if (bind(static_cast<socket_handle_t>(listen_socket_), reinterpret_cast<sockaddr*>(&address), sizeof(address)) < 0) {
        std::cerr << "Failed to bind server socket to port " << port_ << std::endl;
        stop();
        return false;
    }

    if (listen(static_cast<socket_handle_t>(listen_socket_), 16) < 0) {
        std::cerr << "Failed to listen on port " << port_ << std::endl;
        stop();
        return false;
    }

    running_.store(true);
    server_thread_ = std::thread(&HTTPServer::serve_loop, this);
    std::cout << "HTTP server listening on 0.0.0.0:" << port_ << std::endl;
    return true;
}

void HTTPServer::stop() {
    if (!running_.exchange(false)) {
        return;
    }

    socket_handle_t socket_fd = static_cast<socket_handle_t>(listen_socket_);
    listen_socket_ = INVALID_SOCKET_HANDLE;
    if (socket_fd != INVALID_SOCKET_HANDLE) {
#ifdef _WIN32
        ::closesocket(socket_fd);
        WSACleanup();
#else
        ::shutdown(socket_fd, SHUT_RDWR);
        ::close(socket_fd);
#endif
    }

    if (server_thread_.joinable()) {
        server_thread_.join();
    }

    std::cout << "HTTP server stopped" << std::endl;
}

bool HTTPServer::select_backend(const std::string& preferred) {
    const std::string backend = to_lower_copy(trim_copy(preferred));
    if (backend == "opencl") {
        if (!opencl_backend_->is_loaded()) {
            return false;
        }
        current_backend_ = "opencl";
        return true;
    }
    if (backend == "vulkan") {
        if (!vulkan_backend_->is_loaded()) {
            return false;
        }
        current_backend_ = "vulkan";
        return true;
    }
    if (backend != "cpu" && !backend.empty()) {
        return false;
    }
    current_backend_ = "cpu";
    return true;
}

bool HTTPServer::is_backend_available(const std::string& backend) const {
    const std::string normalized = to_lower_copy(trim_copy(backend));
    if (normalized.empty() || normalized == "cpu") {
        return true;
    }
    if (normalized == "opencl") {
        return opencl_backend_->is_loaded();
    }
    if (normalized == "vulkan") {
        return vulkan_backend_->is_loaded();
    }
    return false;
}

ProofReceipt HTTPServer::build_proof_receipt(const InferenceRequest& request, const InferenceResponse& response) const {
    ProofSurfaceInput input;
    input.backend = response.backend_used;
    input.model = current_model_;
    input.prompt = request.prompt;
    input.max_tokens = request.max_tokens;
    input.temperature = request.temperature;
    input.backend_available = is_backend_available(response.backend_used);
    input.verification_status = response.error.empty() ? "verified" : "rejected";
    input.governance_decision = response.error.empty() ? "allow" : "deny";
    input.latency_ms = response.latency_ms;
    input.tokens_generated = response.tokens_generated;
    input.tokens_per_second = response.tokens_per_second;
    input.vram_used_mb = response.vram_used_mb;
    input.cpu_temp_c = response.cpu_temp_c;
    input.fallback = response.fallback;
    return make_proof_receipt(input);
}

InferenceResponse HTTPServer::handle_inference(const InferenceRequest& request) {
    const auto start_time = std::chrono::high_resolution_clock::now();

    InferenceResponse response;
    response.backend_used = route_backend_from_target(request.backend);
    response.model = current_model_;

    if (!governance_->validate_request(request.prompt, request.max_tokens, request.temperature)) {
        response.error = "Request validation failed";
        finalize_response(request, response, 0);
        return response;
    }

    if (!governance_->can_accept_request()) {
        response.error = "Server at capacity (max_concurrent reached)";
        finalize_response(request, response, 0);
        return response;
    }

    if (governance_->is_thermal_throttled()) {
        std::cout << "Thermal throttling active" << std::endl;
    }

    if (!select_backend(request.backend)) {
        response.error = "Requested backend not available";
        finalize_response(request, response, 0);
        return response;
    }

    governance_->increment_active_requests();
    try {
        response = run_inference(request);
    } catch (const std::exception& e) {
        response.error = std::string("Inference failed: ") + e.what();
        if (current_backend_ != "cpu") {
            std::cout << "GPU backend failed, falling back to CPU" << std::endl;
            current_backend_ = "cpu";
            response.backend_used = "cpu";
            response.model = current_model_;
            try {
                response = run_inference(request);
                response.fallback = true;
            } catch (const std::exception& e2) {
                response.error = std::string("CPU fallback also failed: ") + e2.what();
            }
        }
    }
    governance_->decrement_active_requests();

    const auto end_time = std::chrono::high_resolution_clock::now();
    const int latency_ms = static_cast<int>(std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count());
    finalize_response(request, response, latency_ms);
    return response;
}

InferenceResponse HTTPServer::run_inference(const InferenceRequest& request) {
    InferenceResponse response;
    response.backend_used = current_backend_;
    response.model = current_model_;

    if (current_backend_ == "cpu") {
        response.completion = cpu_backend_->generate(request.prompt, request.max_tokens, request.temperature);
        response.vram_used_mb = cpu_backend_->get_vram_usage();
    } else if (current_backend_ == "opencl") {
        response.completion = opencl_backend_->generate(request.prompt, request.max_tokens, request.temperature);
        response.vram_used_mb = opencl_backend_->get_vram_usage();
    } else if (current_backend_ == "vulkan") {
        response.completion = vulkan_backend_->generate(request.prompt, request.max_tokens, request.temperature);
        response.vram_used_mb = vulkan_backend_->get_vram_usage();
    } else {
        throw std::runtime_error("unknown backend selected");
    }

    response.tokens_generated = static_cast<int>(response.completion.length());
    response.tokens_per_second = 0.0f;
    response.cpu_temp_c = governance_->get_cpu_temp();
    return response;
}

void HTTPServer::finalize_response(const InferenceRequest& request, InferenceResponse& response, int latency_ms) {
    response.latency_ms = latency_ms;
    if (response.latency_ms > 0 && response.tokens_generated > 0) {
        response.tokens_per_second = response.tokens_generated / (response.latency_ms / 1000.0f);
    }
    response.proof_receipt = build_proof_receipt(request, response);
    log_request(request, response, response.proof_receipt.backend, response.latency_ms);
}

void HTTPServer::log_request(const InferenceRequest& request, const InferenceResponse& response,
                             const std::string& backend, int latency_ms) {
    RequestLog log;
    log.ts = governance_->get_timestamp();
    log.node = "llm-engine-node-001";
    log.runtime_version = response.proof_receipt.runtime_version;
    log.backend = backend;
    log.model = response.proof_receipt.model;
    log.evidence_receipt = response.proof_receipt.evidence_receipt;
    log.replay_id = response.proof_receipt.replay_id;
    log.proof_level = response.proof_receipt.proof_level;
    log.verification_status = response.proof_receipt.verification_status;
    log.governance_decision = response.proof_receipt.governance_decision;
    log.prompt_tokens = static_cast<int>(request.prompt.length());
    log.completion_tokens = response.tokens_generated;
    log.latency_ms = latency_ms;
    log.temperature = request.temperature;
    log.status = response.error.empty() ? "ok" : "error";
    log.error = response.error;
    log.cpu_temp_c = response.cpu_temp_c;
    log.vram_used_mb = response.vram_used_mb;
    log.fallback = response.fallback || (backend != request.backend);
    governance_->log_request(log);
}

nlohmann::json HTTPServer::handle_health() {
    nlohmann::json response;
    response["status"] = "ok";
    response["model_loaded"] = model_loaded_;
    response["backend"] = current_backend_;
    response["model"] = current_model_;
    response["runtime_version"] = kRuntimeVersion;
    response["backends"] = {
        {"cpu", cpu_backend_->is_loaded()},
        {"opencl", opencl_backend_->is_loaded()},
        {"vulkan", vulkan_backend_->is_loaded()}
    };
    response["vram_used_mb"] = governance_->get_vram_used();
    response["active_requests"] = governance_->get_active_requests();
    response["thermal_throttled"] = governance_->is_thermal_throttled();
    return response;
}

nlohmann::json HTTPServer::handle_backends() {
    nlohmann::json response;
    response["runtime_version"] = kRuntimeVersion;
    response["model"] = current_model_;
    response["cpu"] = {
        {"available", true},
        {"loaded", cpu_backend_->is_loaded()},
        {"vram_mb", 0}
    };
    response["opencl"] = {
        {"available", opencl_backend_->is_loaded()},
        {"loaded", opencl_backend_->is_loaded()},
        {"vram_mb", opencl_backend_->get_vram_usage()}
    };
    response["vulkan"] = {
        {"available", vulkan_backend_->is_loaded()},
        {"loaded", vulkan_backend_->is_loaded()},
        {"vram_mb", vulkan_backend_->get_vram_usage()}
    };
    response["current"] = current_backend_;
    return response;
}

void HTTPServer::serve_loop() {
    while (running_.load()) {
        sockaddr_in client_address{};
        socklen_t client_size = sizeof(client_address);
        socket_handle_t client = static_cast<socket_handle_t>(
            accept(static_cast<socket_handle_t>(listen_socket_), reinterpret_cast<sockaddr*>(&client_address), &client_size)
        );
        if (!running_.load()) {
            break;
        }
        if (client == INVALID_SOCKET_HANDLE) {
            continue;
        }
        std::thread(&HTTPServer::handle_client, this, static_cast<std::intptr_t>(client)).detach();
    }
}

void HTTPServer::handle_client(std::intptr_t client_socket) {
    socket_handle_t socket_fd = static_cast<socket_handle_t>(client_socket);
    std::string raw_request;
    char buffer[4096];

    while (true) {
#ifdef _WIN32
        const int received = ::recv(socket_fd, buffer, static_cast<int>(sizeof(buffer)), 0);
#else
        const ssize_t received = ::recv(socket_fd, buffer, sizeof(buffer), 0);
#endif
        if (received <= 0) {
            break;
        }
        raw_request.append(buffer, static_cast<std::size_t>(received));
        if (raw_request.find("\r\n\r\n") != std::string::npos) {
            break;
        }
    }

    if (raw_request.empty()) {
#ifdef _WIN32
        ::closesocket(socket_fd);
#else
        ::close(socket_fd);
#endif
        return;
    }

    HttpRequest request = parse_request(raw_request);
    const std::size_t header_end = raw_request.find("\r\n\r\n");
    const auto content_length_it = request.headers.find("content-length");
    if (content_length_it != request.headers.end() && header_end != std::string::npos) {
        const std::size_t expected = static_cast<std::size_t>(std::stoul(content_length_it->second));
        std::size_t already_have = raw_request.size() - (header_end + 4);
        while (already_have < expected) {
#ifdef _WIN32
            const int received = ::recv(socket_fd, buffer, static_cast<int>(sizeof(buffer)), 0);
#else
            const ssize_t received = ::recv(socket_fd, buffer, sizeof(buffer), 0);
#endif
            if (received <= 0) {
                break;
            }
            raw_request.append(buffer, static_cast<std::size_t>(received));
            already_have += static_cast<std::size_t>(received);
        }
        request = parse_request(raw_request);
    }

    int status_code = 200;
    std::string content_type = "application/json";
    std::string response_body = dispatch_request(request, status_code, content_type);
    const std::string response = make_text_response(status_code, response_body, content_type);
    (void)send_all(socket_fd, response);

#ifdef _WIN32
    ::closesocket(socket_fd);
#else
    ::close(socket_fd);
#endif
}

std::string HTTPServer::dispatch_request(const HttpRequest& request, int& status_code, std::string& content_type) {
    try {
        if (request.method == "GET" && request.target == "/health") {
            status_code = 200;
            content_type = "application/json";
            return handle_health().dump();
        }
        if (request.method == "GET" && request.target == "/backends") {
            status_code = 200;
            content_type = "application/json";
            return handle_backends().dump();
        }
        if (request.method == "GET" && request.target == "/v1/models") {
            status_code = 200;
            content_type = "application/json";
            nlohmann::json body = {
                {"object", "list"},
                {"data", nlohmann::json::array({
                    {{"id", "llm-engine-local"}, {"object", "model"}, {"created", 0}, {"owned_by", "llm-engine"}}
                })}
            };
            return body.dump();
        }
        if (request.method == "POST" && request.target == "/v1/generate") {
            const auto body = nlohmann::json::parse(request.body.empty() ? "{}" : request.body);
            const InferenceRequest inference = parse_inference_request(body);
            const InferenceResponse response = handle_inference(inference);
            status_code = response.error.empty() ? 200 : 500;
            content_type = "application/json";
            return response.to_json().dump();
        }
        if (request.method == "POST" && request.target == "/v1/chat/completions") {
            const auto body = nlohmann::json::parse(request.body.empty() ? "{}" : request.body);
            const InferenceRequest inference = parse_inference_request(body);
            const InferenceResponse response = handle_inference(inference);
            const std::string created = governance_->get_timestamp();
            const nlohmann::json response_json = response.to_json();
            nlohmann::json payload = {
                {"id", std::string("chatcmpl-") + created},
                {"object", "chat.completion"},
                {"created", static_cast<int>(std::time(nullptr))},
                {"model", response.model.empty() ? body.value("model", std::string("llm-engine-local")) : response.model},
                {"backend_used", response.backend_used}
            };
            payload["metadata"] = response_json["metadata"];
            payload["choices"] = nlohmann::json::array({
                {
                    {"index", 0},
                    {"message", {
                        {"role", "assistant"},
                        {"content", response.completion}
                    }},
                    {"finish_reason", response.error.empty() ? "stop" : "error"}
                }
            });
            payload["usage"] = {
                {"prompt_tokens", static_cast<int>(inference.prompt.length())},
                {"completion_tokens", response.tokens_generated},
                {"total_tokens", static_cast<int>(inference.prompt.length()) + response.tokens_generated}
            };
            payload["latency_ms"] = response.latency_ms;
            payload["fallback"] = response.fallback;
            if (!response.error.empty()) {
                payload["error"] = response.error;
            }
            status_code = response.error.empty() ? 200 : 500;
            content_type = "application/json";
            return payload.dump();
        }

        status_code = request.method == "GET" || request.method == "POST" ? 404 : 405;
        content_type = "application/json";
        return nlohmann::json({{"error", "endpoint not found"}}).dump();
    } catch (const std::exception& e) {
        status_code = 500;
        content_type = "application/json";
        return nlohmann::json({{"error", e.what()}}).dump();
    }
}

HTTPServer::HttpRequest HTTPServer::parse_request(const std::string& raw_request) const {
    HttpRequest request;
    const std::size_t header_end = raw_request.find("\r\n\r\n");
    const std::string header_block = raw_request.substr(0, header_end);
    request.body = header_end == std::string::npos ? "" : raw_request.substr(header_end + 4);

    const auto lines = split_lines(header_block);
    if (lines.empty()) {
        return request;
    }

    {
        std::istringstream request_line(lines[0]);
        request_line >> request.method >> request.target >> request.version;
    }

    for (std::size_t i = 1; i < lines.size(); ++i) {
        const auto separator = lines[i].find(':');
        if (separator == std::string::npos) {
            continue;
        }
        const std::string key = to_lower_copy(trim_copy(lines[i].substr(0, separator)));
        const std::string value = trim_copy(lines[i].substr(separator + 1));
        request.headers[key] = value;
    }

    const auto content_length = request.headers.find("content-length");
    if (content_length != request.headers.end()) {
        const std::size_t expected = static_cast<std::size_t>(std::stoul(content_length->second));
        if (request.body.size() > expected) {
            request.body.resize(expected);
        }
    }

    return request;
}

InferenceRequest HTTPServer::parse_inference_request(const nlohmann::json& body) const {
    InferenceRequest request;
    if (body.contains("prompt")) {
        if (body["prompt"].is_string()) {
            request.prompt = body["prompt"].get<std::string>();
        } else if (body["prompt"].is_array()) {
            for (const auto& entry : body["prompt"]) {
                if (entry.is_string()) {
                    request.prompt += entry.get<std::string>();
                    request.prompt.push_back('\n');
                }
            }
        } else {
            request.prompt = body["prompt"].dump();
        }
    } else if (body.contains("messages") && body["messages"].is_array()) {
        for (const auto& message : body["messages"]) {
            if (message.contains("content")) {
                if (!request.prompt.empty()) {
                    request.prompt.push_back('\n');
                }
                request.prompt += message["content"].is_string() ? message["content"].get<std::string>() : message["content"].dump();
            }
        }
    }

    request.max_tokens = body.value("max_tokens", body.value("num_predict", 256));
    request.temperature = body.value("temperature", 0.2f);
    request.backend = route_backend_from_target(body.value("backend", body.value("model_backend", std::string("cpu"))));
    if (request.prompt.empty()) {
        request.prompt = body.value("input", std::string{});
    }
    return request;
}

std::string HTTPServer::make_json_response(int status_code, const nlohmann::json& body) const {
    return make_text_response(status_code, body.dump(), "application/json");
}

std::string HTTPServer::make_text_response(int status_code, const std::string& body, const std::string& content_type) const {
    std::ostringstream response;
    response << "HTTP/1.1 " << status_code << ' ' << reason_phrase(status_code) << "\r\n";
    response << "Content-Type: " << content_type << "\r\n";
    response << "Content-Length: " << body.size() << "\r\n";
    response << "Connection: close\r\n\r\n";
    response << body;
    return response.str();
}

std::string HTTPServer::route_backend_from_target(const std::string& target) {
    const std::string backend = to_lower_copy(trim_copy(target));
    if (backend == "opencl" || backend == "vulkan") {
        return backend;
    }
    return "cpu";
}

} // namespace llm_engine
