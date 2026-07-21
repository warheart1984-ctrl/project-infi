#include "../src/tensor_ops.h"
#include <iostream>
#include <cmath>
#include <cassert>

using namespace llm_engine;

void test_tensor_add() {
    std::cout << "Testing tensor add..." << std::endl;
    
    Tensor a({4, 4});
    Tensor b({4, 4});
    
    for (int i = 0; i < 16; i++) {
        a.data()[i] = 1.0f;
        b.data()[i] = 2.0f;
    }
    
    Tensor c = add(a, b);
    
    for (int i = 0; i < 16; i++) {
        assert(std::abs(c.data()[i] - 3.0f) < 1e-5);
    }
    
    std::cout << "✓ Tensor add passed" << std::endl;
}

void test_tensor_sub() {
    std::cout << "Testing tensor sub..." << std::endl;
    
    Tensor a({4, 4});
    Tensor b({4, 4});
    
    for (int i = 0; i < 16; i++) {
        a.data()[i] = 5.0f;
        b.data()[i] = 2.0f;
    }
    
    Tensor c = sub(a, b);
    
    for (int i = 0; i < 16; i++) {
        assert(std::abs(c.data()[i] - 3.0f) < 1e-5);
    }
    
    std::cout << "✓ Tensor sub passed" << std::endl;
}

void test_tensor_mul() {
    std::cout << "Testing tensor mul..." << std::endl;
    
    Tensor a({4, 4});
    Tensor b({4, 4});
    
    for (int i = 0; i < 16; i++) {
        a.data()[i] = 3.0f;
        b.data()[i] = 4.0f;
    }
    
    Tensor c = mul(a, b);
    
    for (int i = 0; i < 16; i++) {
        assert(std::abs(c.data()[i] - 12.0f) < 1e-5);
    }
    
    std::cout << "✓ Tensor mul passed" << std::endl;
}

void test_tensor_div() {
    std::cout << "Testing tensor div..." << std::endl;
    
    Tensor a({4, 4});
    Tensor b({4, 4});
    
    for (int i = 0; i < 16; i++) {
        a.data()[i] = 12.0f;
        b.data()[i] = 3.0f;
    }
    
    Tensor c = div(a, b);
    
    for (int i = 0; i < 16; i++) {
        assert(std::abs(c.data()[i] - 4.0f) < 1e-5);
    }
    
    std::cout << "✓ Tensor div passed" << std::endl;
}

void test_matmul_2x2() {
    std::cout << "Testing 2x2 matrix multiplication..." << std::endl;
    
    Tensor a({2, 2});
    Tensor b({2, 2});
    
    a.data()[0] = 1.0f; a.data()[1] = 2.0f;
    a.data()[2] = 3.0f; a.data()[3] = 4.0f;
    
    b.data()[0] = 5.0f; b.data()[1] = 6.0f;
    b.data()[2] = 7.0f; b.data()[3] = 8.0f;
    
    Tensor result = matmul(a, b);
    
    // Expected: [[19, 22], [43, 50]]
    assert(std::abs(result.data()[0] - 19.0f) < 1e-5);
    assert(std::abs(result.data()[1] - 22.0f) < 1e-5);
    assert(std::abs(result.data()[2] - 43.0f) < 1e-5);
    assert(std::abs(result.data()[3] - 50.0f) < 1e-5);
    
    std::cout << "✓ 2x2 matmul passed" << std::endl;
}

void test_matmul_4x4() {
    std::cout << "Testing 4x4 matrix multiplication..." << std::endl;
    
    Tensor a({4, 4});
    Tensor b({4, 4});
    
    // Identity matrices
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            a.data()[i * 4 + j] = (i == j) ? 1.0f : 0.0f;
            b.data()[i * 4 + j] = (i == j) ? 2.0f : 0.0f;
        }
    }
    
    Tensor result = matmul(a, b);
    
    // Should equal b
    for (int i = 0; i < 16; i++) {
        assert(std::abs(result.data()[i] - b.data()[i]) < 1e-5);
    }
    
    std::cout << "✓ 4x4 matmul passed" << std::endl;
}

void test_transpose() {
    std::cout << "Testing transpose..." << std::endl;
    
    Tensor a({2, 3});
    a.data()[0] = 1.0f; a.data()[1] = 2.0f; a.data()[2] = 3.0f;
    a.data()[3] = 4.0f; a.data()[4] = 5.0f; a.data()[5] = 6.0f;
    
    Tensor result = transpose(a);
    
    assert(result.shape()[0] == 3);
    assert(result.shape()[1] == 2);
    
    assert(std::abs(result.data()[0] - 1.0f) < 1e-5);
    assert(std::abs(result.data()[1] - 4.0f) < 1e-5);
    assert(std::abs(result.data()[2] - 2.0f) < 1e-5);
    assert(std::abs(result.data()[3] - 5.0f) < 1e-5);
    assert(std::abs(result.data()[4] - 3.0f) < 1e-5);
    assert(std::abs(result.data()[5] - 6.0f) < 1e-5);
    
    std::cout << "✓ Transpose passed" << std::endl;
}

void test_softmax() {
    std::cout << "Testing softmax..." << std::endl;
    
    Tensor x({1, 4});
    x.data()[0] = 1.0f; x.data()[1] = 2.0f;
    x.data()[2] = 3.0f; x.data()[3] = 4.0f;
    
    Tensor result = softmax(x);
    
    // Check that sum is 1.0
    float sum = 0.0f;
    for (int i = 0; i < 4; i++) {
        sum += result.data()[i];
    }
    assert(std::abs(sum - 1.0f) < 1e-5);
    
    // Check that values are in [0, 1]
    for (int i = 0; i < 4; i++) {
        assert(result.data()[i] >= 0.0f);
        assert(result.data()[i] <= 1.0f);
    }
    
    // Check monotonicity (higher input -> higher output)
    for (int i = 0; i < 3; i++) {
        assert(result.data()[i] < result.data()[i + 1]);
    }
    
    std::cout << "✓ Softmax passed" << std::endl;
}

void test_layer_norm() {
    std::cout << "Testing layer norm..." << std::endl;
    
    Tensor x({1, 4});
    x.data()[0] = 1.0f; x.data()[1] = 2.0f;
    x.data()[2] = 3.0f; x.data()[3] = 4.0f;
    
    Tensor gamma({4});
    Tensor beta({4});
    gamma.fill(1.0f);
    beta.fill(0.0f);
    
    Tensor result = layer_norm(x, gamma, beta);
    
    // Check that mean is approximately 0
    float mean = 0.0f;
    for (int i = 0; i < 4; i++) {
        mean += result.data()[i];
    }
    mean /= 4.0f;
    assert(std::abs(mean) < 1e-3);
    
    // Check that variance is approximately 1
    float variance = 0.0f;
    for (int i = 0; i < 4; i++) {
        float diff = result.data()[i] - mean;
        variance += diff * diff;
    }
    variance /= 4.0f;
    assert(std::abs(std::sqrt(variance) - 1.0f) < 1e-3);
    
    std::cout << "✓ Layer norm passed" << std::endl;
}

void test_gelu() {
    std::cout << "Testing GELU..." << std::endl;
    
    Tensor x({1, 4});
    x.data()[0] = 0.0f; x.data()[1] = 1.0f;
    x.data()[2] = -1.0f; x.data()[3] = 2.0f;
    
    Tensor result = gelu(x);
    
    // GELU(0) should be approximately 0
    assert(std::abs(result.data()[0]) < 1e-3);
    
    // GELU should be positive for positive inputs
    assert(result.data()[1] > 0.0f);
    assert(result.data()[3] > 0.0f);
    
    // GELU should be negative for negative inputs
    assert(result.data()[2] < 0.0f);
    
    std::cout << "✓ GELU passed" << std::endl;
}

void test_relu() {
    std::cout << "Testing ReLU..." << std::endl;
    
    Tensor x({1, 4});
    x.data()[0] = -2.0f; x.data()[1] = -1.0f;
    x.data()[2] = 0.0f; x.data()[3] = 3.0f;
    
    Tensor result = relu(x);
    
    assert(std::abs(result.data()[0]) < 1e-5);
    assert(std::abs(result.data()[1]) < 1e-5);
    assert(std::abs(result.data()[2]) < 1e-5);
    assert(std::abs(result.data()[3] - 3.0f) < 1e-5);
    
    std::cout << "✓ ReLU passed" << std::endl;
}

void test_sigmoid() {
    std::cout << "Testing sigmoid..." << std::endl;
    
    Tensor x({1, 4});
    x.data()[0] = -10.0f; x.data()[1] = 0.0f;
    x.data()[2] = 10.0f; x.data()[3] = 1.0f;
    
    Tensor result = sigmoid(x);
    
    // sigmoid(-inf) -> 0
    assert(result.data()[0] < 1e-3);
    
    // sigmoid(0) -> 0.5
    assert(std::abs(result.data()[1] - 0.5f) < 1e-3);
    
    // sigmoid(inf) -> 1
    assert(result.data()[2] > 0.999f);
    
    // sigmoid(1) should be > 0.5
    assert(result.data()[3] > 0.5f);
    
    std::cout << "✓ Sigmoid passed" << std::endl;
}

void test_embedding_lookup() {
    std::cout << "Testing embedding lookup..." << std::endl;
    
    Tensor weights({5, 3});
    for (int i = 0; i < 15; i++) {
        weights.data()[i] = static_cast<float>(i);
    }
    
    Tensor indices({3});
    indices.data()[0] = 0.0f;
    indices.data()[1] = 2.0f;
    indices.data()[2] = 4.0f;
    
    Tensor result = embedding_lookup(weights, indices);
    
    assert(result.shape()[0] == 3);
    assert(result.shape()[1] == 3);
    
    // Check first embedding (index 0)
    assert(std::abs(result.data()[0] - 0.0f) < 1e-5);
    assert(std::abs(result.data()[1] - 1.0f) < 1e-5);
    assert(std::abs(result.data()[2] - 2.0f) < 1e-5);
    
    // Check second embedding (index 2)
    assert(std::abs(result.data()[3] - 6.0f) < 1e-5);
    assert(std::abs(result.data()[4] - 7.0f) < 1e-5);
    assert(std::abs(result.data()[5] - 8.0f) < 1e-5);
    
    // Check third embedding (index 4)
    assert(std::abs(result.data()[6] - 12.0f) < 1e-5);
    assert(std::abs(result.data()[7] - 13.0f) < 1e-5);
    assert(std::abs(result.data()[8] - 14.0f) < 1e-5);
    
    std::cout << "✓ Embedding lookup passed" << std::endl;
}

void test_special_cases() {
    std::cout << "Testing special cases..." << std::endl;
    
    // Test zero-length sequence
    Tensor zero({0, 4});
    Tensor zero_result = add(zero, zero);
    assert(zero_result.size() == 0);
    
    // Test single-token sequence
    Tensor single({1, 1});
    single.data()[0] = 5.0f;
    Tensor single_result = mul(single, single);
    assert(std::abs(single_result.data()[0] - 25.0f) < 1e-5);
    
    // Test all-zero weights
    Tensor zeros({4, 4});
    zeros.fill(0.0f);
    Tensor zeros_result = matmul(zeros, zeros);
    for (int i = 0; i < 16; i++) {
        assert(std::abs(zeros_result.data()[i]) < 1e-5);
    }
    
    // Test identity weights
    Tensor identity({4, 4});
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            identity.data()[i * 4 + j] = (i == j) ? 1.0f : 0.0f;
        }
    }
    Tensor identity_result = matmul(identity, identity);
    for (int i = 0; i < 16; i++) {
        assert(std::abs(identity_result.data()[i] - identity.data()[i]) < 1e-5);
    }
    
    std::cout << "✓ Special cases passed" << std::endl;
}

int test_tensor_ops_main() {
    std::cout << "Running Tier 1 Unit Tests" << std::endl;
    std::cout << "=========================" << std::endl;
    
    try {
        test_tensor_add();
        test_tensor_sub();
        test_tensor_mul();
        test_tensor_div();
        test_matmul_2x2();
        test_matmul_4x4();
        test_transpose();
        test_softmax();
        test_layer_norm();
        test_gelu();
        test_relu();
        test_sigmoid();
        test_embedding_lookup();
        test_special_cases();
        
        std::cout << "\n✓ All Tier 1 unit tests passed" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "✗ Test failed: " << e.what() << std::endl;
        return 1;
    }
}
