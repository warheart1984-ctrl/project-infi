#include "../src/backend/cpu_backend.h"
#include "../src/backend/opencl_backend.h"
#include "../src/backend/vulkan_backend.h"
#include <iostream>
#include <cmath>
#include <cassert>
#include <fstream>

using namespace llm_engine;

void compare_backends(const std::string& model_path) {
    std::cout << "Comparing backends with model: " << model_path << std::endl;
    
    // Initialize CPU backend
    CPUBackend cpu_backend;
    if (!cpu_backend.load_model(model_path)) {
        std::cerr << "Failed to load model on CPU backend" << std::endl;
        return;
    }
    
    // Initialize OpenCL backend
    OpenCLBackend opencl_backend;
    bool opencl_available = false;
    try {
        if (opencl_backend.initialize() && opencl_backend.load_model(model_path)) {
            opencl_available = true;
            std::cout << "OpenCL backend available" << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "OpenCL backend not available: " << e.what() << std::endl;
    }
    
    // Initialize Vulkan backend
    VulkanBackend vulkan_backend;
    bool vulkan_available = false;
    try {
        if (vulkan_backend.initialize() && vulkan_backend.load_model(model_path)) {
            vulkan_available = true;
            std::cout << "Vulkan backend available" << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "Vulkan backend not available: " << e.what() << std::endl;
    }
    
    // Create test input
    std::vector<float> test_data(128);
    for (int i = 0; i < 128; i++) {
        test_data[i] = static_cast<float>(i) / 128.0f;
    }
    
    Tensor input({1, 128}, test_data);
    
    // Run on CPU
    std::cout << "Running CPU backend..." << std::endl;
    Tensor cpu_output = cpu_backend.forward(input);
    
    // Compare with OpenCL
    if (opencl_available) {
        std::cout << "Running OpenCL backend..." << std::endl;
        Tensor opencl_output = opencl_backend.forward(input);
        
        // Compare outputs
        float max_diff = 0.0f;
        int first_diff_idx = -1;
        
        for (size_t i = 0; i < cpu_output.data().size(); i++) {
            float diff = std::abs(cpu_output.data()[i] - opencl_output.data()[i]);
            if (diff > max_diff) {
                max_diff = diff;
                first_diff_idx = static_cast<int>(i);
            }
        }
        
        std::cout << "OpenCL vs CPU max difference: " << max_diff << std::endl;
        
        if (max_diff > 1e-3) {
            std::cerr << "✗ OpenCL output differs from CPU by more than 1e-3" << std::endl;
            std::cerr << "  First differing index: " << first_diff_idx << std::endl;
            std::cerr << "  CPU value: " << cpu_output.data()[first_diff_idx] << std::endl;
            std::cerr << "  OpenCL value: " << opencl_output.data()[first_diff_idx] << std::endl;
        } else {
            std::cout << "✓ OpenCL output matches CPU within tolerance" << std::endl;
        }
    }
    
    // Compare with Vulkan
    if (vulkan_available) {
        std::cout << "Running Vulkan backend..." << std::endl;
        Tensor vulkan_output = vulkan_backend.forward(input);
        
        // Compare outputs
        float max_diff = 0.0f;
        int first_diff_idx = -1;
        
        for (size_t i = 0; i < cpu_output.data().size(); i++) {
            float diff = std::abs(cpu_output.data()[i] - vulkan_output.data()[i]);
            if (diff > max_diff) {
                max_diff = diff;
                first_diff_idx = static_cast<int>(i);
            }
        }
        
        std::cout << "Vulkan vs CPU max difference: " << max_diff << std::endl;
        
        if (max_diff > 1e-3) {
            std::cerr << "✗ Vulkan output differs from CPU by more than 1e-3" << std::endl;
            std::cerr << "  First differing index: " << first_diff_idx << std::endl;
            std::cerr << "  CPU value: " << cpu_output.data()[first_diff_idx] << std::endl;
            std::cerr << "  Vulkan value: " << vulkan_output.data()[first_diff_idx] << std::endl;
        } else {
            std::cout << "✓ Vulkan output matches CPU within tolerance" << std::endl;
        }
    }
    
    // Test layer-by-layer comparison
    std::cout << "\nTesting layer-by-layer comparison..." << std::endl;
    
    for (int layer = 0; layer < 3; layer++) {  // Test first 3 layers
        std::cout << "Layer " << layer << ":" << std::endl;
        
        Tensor cpu_layer_out = cpu_backend.forward_layer(input, layer);
        
        if (opencl_available) {
            Tensor opencl_layer_out = opencl_backend.forward_layer(input, layer);
            
            float max_diff = 0.0f;
            for (size_t i = 0; i < cpu_layer_out.data().size(); i++) {
                float diff = std::abs(cpu_layer_out.data()[i] - opencl_layer_out.data()[i]);
                max_diff = std::max(max_diff, diff);
            }
            
            std::cout << "  OpenCL max diff: " << max_diff << std::endl;
            
            if (max_diff > 1e-3) {
                std::cerr << "  ✗ Layer " << layer << " exceeds tolerance" << std::endl;
            } else {
                std::cout << "  ✓ Layer " << layer << " within tolerance" << std::endl;
            }
        }
        
        if (vulkan_available) {
            Tensor vulkan_layer_out = vulkan_backend.forward_layer(input, layer);
            
            float max_diff = 0.0f;
            for (size_t i = 0; i < cpu_layer_out.data().size(); i++) {
                float diff = std::abs(cpu_layer_out.data()[i] - vulkan_layer_out.data()[i]);
                max_diff = std::max(max_diff, diff);
            }
            
            std::cout << "  Vulkan max diff: " << max_diff << std::endl;
            
            if (max_diff > 1e-3) {
                std::cerr << "  ✗ Layer " << layer << " exceeds tolerance" << std::endl;
            } else {
                std::cout << "  ✓ Layer " << layer << " within tolerance" << std::endl;
            }
        }
    }
}

int test_backend_comparison_main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <model_path>" << std::endl;
        return 1;
    }
    
    std::string model_path = argv[1];
    
    std::cout << "Running Tier 2 Backend Comparison Tests" << std::endl;
    std::cout << "========================================" << std::endl;
    
    try {
        compare_backends(model_path);
        
        std::cout << "\n✓ Tier 2 tests completed" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "✗ Test failed: " << e.what() << std::endl;
        return 1;
    }
}
