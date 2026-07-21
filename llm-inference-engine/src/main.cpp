#include "http_server.h"
#include "governance.h"
#include <iostream>
#include <string>
#include <csignal>
#include <memory>
#include <cmath>
#include <chrono>
#include <thread>

using namespace llm_engine;

std::unique_ptr<HTTPServer> g_server;
bool g_running = true;

void signal_handler(int signal) {
    std::cout << "\nReceived signal " << signal << ", shutting down..." << std::endl;
    g_running = false;
    if (g_server) {
        g_server->stop();
    }
}

void print_usage(const char* program_name) {
    std::cout << "Usage: " << program_name << " [options]\n";
    std::cout << "Options:\n";
    std::cout << "  --model <path>       Path to GGUF model file (required)\n";
    std::cout << "  --port <port>        HTTP server port (default: 8080)\n";
    std::cout << "  --backend <name>     Default backend: cpu, opencl, vulkan (default: cpu)\n";
    std::cout << "  --max-concurrent <n> Maximum concurrent requests (default: 4)\n";
    std::cout << "  --vram-budget <mb>   VRAM budget in MB (default: 3500)\n";
    std::cout << "  --thermal-throttle <c> Thermal throttle threshold in C (default: 85)\n";
    std::cout << "  --log-path <path>    Path to request log file (default: requests.jsonl)\n";
    std::cout << "  --selftest           Run self-test and exit\n";
    std::cout << "  --help               Show this help message\n";
}

int run_selftest() {
    std::cout << "Running self-test..." << std::endl;
    
    // Test tensor operations
    std::cout << "Testing tensor operations..." << std::endl;
    
    Tensor a({4, 4});
    Tensor b({4, 4});
    
    // Fill with known values
    for (int i = 0; i < 16; i++) {
        a.data()[i] = 1.0f;
        b.data()[i] = 2.0f;
    }
    
    Tensor c = add(a, b);
    bool add_correct = true;
    for (int i = 0; i < 16; i++) {
        if (std::abs(c.data()[i] - 3.0f) > 1e-5) {
            add_correct = false;
            break;
        }
    }
    
    if (add_correct) {
        std::cout << "✓ Tensor add operation correct" << std::endl;
    } else {
        std::cout << "✗ Tensor add operation failed" << std::endl;
        return 1;
    }
    
    // Test matrix multiplication
    Tensor m1({2, 2});
    Tensor m2({2, 2});
    
    m1.data()[0] = 1.0f; m1.data()[1] = 2.0f;
    m1.data()[2] = 3.0f; m1.data()[3] = 4.0f;
    
    m2.data()[0] = 5.0f; m2.data()[1] = 6.0f;
    m2.data()[2] = 7.0f; m2.data()[3] = 8.0f;
    
    Tensor result = matmul(m1, m2);
    
    // Expected: [[19, 22], [43, 50]]
    if (std::abs(result.data()[0] - 19.0f) < 1e-5 &&
        std::abs(result.data()[1] - 22.0f) < 1e-5 &&
        std::abs(result.data()[2] - 43.0f) < 1e-5 &&
        std::abs(result.data()[3] - 50.0f) < 1e-5) {
        std::cout << "✓ Matrix multiplication correct" << std::endl;
    } else {
        std::cout << "✗ Matrix multiplication failed" << std::endl;
        return 1;
    }
    
    // Test layer norm
    Tensor x({1, 4});
    x.data()[0] = 1.0f; x.data()[1] = 2.0f;
    x.data()[2] = 3.0f; x.data()[3] = 4.0f;
    
    Tensor gamma({4});
    Tensor beta({4});
    gamma.fill(1.0f);
    beta.fill(0.0f);
    
    Tensor ln = layer_norm(x, gamma, beta);
    std::cout << "✓ Layer norm executed" << std::endl;
    
    // Test softmax
    Tensor s({1, 4});
    s.data()[0] = 1.0f; s.data()[1] = 2.0f;
    s.data()[2] = 3.0f; s.data()[3] = 4.0f;
    
    Tensor sm = softmax(s);
    float sum = 0.0f;
    for (int i = 0; i < 4; i++) {
        sum += sm.data()[i];
    }
    
    if (std::abs(sum - 1.0f) < 1e-5) {
        std::cout << "✓ Softmax correct" << std::endl;
    } else {
        std::cout << "✗ Softmax failed" << std::endl;
        return 1;
    }
    
    std::cout << "\n✓ Self-test passed" << std::endl;
    return 0;
}

int main(int argc, char* argv[]) {
    // Set up signal handlers
    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);
    
    // Parse command line arguments
    std::string model_path;
    int port = 8080;
    std::string default_backend = "cpu";
    int max_concurrent = 4;
    int vram_budget = 3500;
    int thermal_throttle = 85;
    std::string log_path = "requests.jsonl";
    bool run_selftest_flag = false;
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        
        if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        } else if (arg == "--selftest") {
            run_selftest_flag = true;
        } else if (i + 1 < argc) {
            if (arg == "--model") {
                model_path = argv[++i];
            } else if (arg == "--port") {
                port = std::stoi(argv[++i]);
            } else if (arg == "--backend") {
                default_backend = argv[++i];
            } else if (arg == "--max-concurrent") {
                max_concurrent = std::stoi(argv[++i]);
            } else if (arg == "--vram-budget") {
                vram_budget = std::stoi(argv[++i]);
            } else if (arg == "--thermal-throttle") {
                thermal_throttle = std::stoi(argv[++i]);
            } else if (arg == "--log-path") {
                log_path = argv[++i];
            }
        }
    }
    
    // Run self-test if requested
    if (run_selftest_flag) {
        return run_selftest();
    }
    
    // Check if model path is provided
    if (model_path.empty()) {
        std::cerr << "Error: --model is required" << std::endl;
        print_usage(argv[0]);
        return 1;
    }
    
    // Configure governance
    GovernanceConfig config;
    config.max_concurrent = max_concurrent;
    config.vram_budget_mb = vram_budget;
    config.thermal_throttle_c = thermal_throttle;
    config.log_path = log_path;
    
    // Create and initialize server
    g_server = std::make_unique<HTTPServer>(config);
    
    std::cout << "LLM Inference Engine v1.0.0" << std::endl;
    std::cout << "=========================" << std::endl;
    std::cout << "Model: " << model_path << std::endl;
    std::cout << "Port: " << port << std::endl;
    std::cout << "Default backend: " << default_backend << std::endl;
    std::cout << "Max concurrent: " << max_concurrent << std::endl;
    std::cout << "VRAM budget: " << vram_budget << " MB" << std::endl;
    std::cout << "Thermal throttle: " << thermal_throttle << " C" << std::endl;
    std::cout << "Log path: " << log_path << std::endl;
    std::cout << std::endl;
    
    // Load model
    std::cout << "Loading model..." << std::endl;
    if (!g_server->load_model(model_path)) {
        std::cerr << "Failed to load model" << std::endl;
        return 1;
    }
    
    // Start server
    if (!g_server->start(port)) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }
    
    std::cout << "\nServer ready. Press Ctrl+C to stop." << std::endl;
    
    // Main loop
    while (g_running) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    
    std::cout << "Server stopped." << std::endl;
    return 0;
}
