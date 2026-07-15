#include <iostream>
#include <string>

// External test functions
extern int test_tensor_ops_main();
extern int test_backend_comparison_main(int argc, char* argv[]);
extern int test_integration_main();

void print_usage(const char* program_name) {
    std::cout << "Usage: " << program_name << " [options]\n";
    std::cout << "Options:\n";
    std::cout << "  --unit               Run Tier 1 unit tests\n";
    std::cout << "  --backend-comparison Run Tier 2 backend comparison tests\n";
    std::cout << "  --integration        Run Tier 3 integration tests\n";
    std::cout << "  --model <path>       Model path for backend comparison tests\n";
    std::cout << "  --all                Run all tests\n";
    std::cout << "  --help               Show this help message\n";
}

int main(int argc, char* argv[]) {
    bool run_unit = false;
    bool run_backend_comparison = false;
    bool run_integration = false;
    std::string model_path;
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        
        if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        } else if (arg == "--unit") {
            run_unit = true;
        } else if (arg == "--backend-comparison") {
            run_backend_comparison = true;
        } else if (arg == "--integration") {
            run_integration = true;
        } else if (arg == "--all") {
            run_unit = true;
            run_backend_comparison = true;
            run_integration = true;
        } else if (arg == "--model" && i + 1 < argc) {
            model_path = argv[++i];
        }
    }
    
    // If no specific test requested, run all
    if (!run_unit && !run_backend_comparison && !run_integration) {
        run_unit = true;
        run_backend_comparison = true;
        run_integration = true;
    }
    
    int total_failures = 0;
    
    if (run_unit) {
        std::cout << "\n========================================" << std::endl;
        std::cout << "Running Tier 1 Unit Tests" << std::endl;
        std::cout << "========================================" << std::endl;
        
        int result = test_tensor_ops_main();
        if (result != 0) {
            total_failures++;
            std::cerr << "Tier 1 unit tests FAILED" << std::endl;
        } else {
            std::cout << "Tier 1 unit tests PASSED" << std::endl;
        }
    }
    
    if (run_backend_comparison) {
        std::cout << "\n========================================" << std::endl;
        std::cout << "Running Tier 2 Backend Comparison Tests" << std::endl;
        std::cout << "========================================" << std::endl;
        
        if (model_path.empty()) {
            std::cerr << "Warning: No model path provided, skipping backend comparison tests" << std::endl;
            std::cerr << "Use --model <path> to run these tests" << std::endl;
        } else {
            int result = test_backend_comparison_main(2, const_cast<char**>(new char*[2]{argv[0], const_cast<char*>(model_path.c_str())}));
            if (result != 0) {
                total_failures++;
                std::cerr << "Tier 2 backend comparison tests FAILED" << std::endl;
            } else {
                std::cout << "Tier 2 backend comparison tests PASSED" << std::endl;
            }
        }
    }
    
    if (run_integration) {
        std::cout << "\n========================================" << std::endl;
        std::cout << "Running Tier 3 Integration Tests" << std::endl;
        std::cout << "========================================" << std::endl;
        
        int result = test_integration_main();
        if (result != 0) {
            total_failures++;
            std::cerr << "Tier 3 integration tests FAILED" << std::endl;
        } else {
            std::cout << "Tier 3 integration tests PASSED" << std::endl;
        }
    }
    
    std::cout << "\n========================================" << std::endl;
    std::cout << "Test Summary" << std::endl;
    std::cout << "========================================" << std::endl;
    
    if (total_failures == 0) {
        std::cout << "✓ All tests PASSED" << std::endl;
        return 0;
    } else {
        std::cout << "✗ " << total_failures << " test suite(s) FAILED" << std::endl;
        return 1;
    }
}
