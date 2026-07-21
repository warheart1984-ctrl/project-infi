#include "tensor_ops.h"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <random>

namespace llm_engine {

Tensor::Tensor(const std::vector<int>& shape) : shape_(shape) {
    int total_size = 1;
    for (int dim : shape_) {
        total_size *= dim;
    }
    data_.resize(total_size, 0.0f);
}

Tensor::Tensor(const std::vector<int>& shape, const std::vector<float>& data)
    : shape_(shape), data_(data) {
}

Tensor::Tensor(const std::vector<int>& shape, const float* data, std::size_t count)
    : shape_(shape) {
    if (data == nullptr || count == 0) {
        return;
    }
    data_.assign(data, data + count);
}

void Tensor::reshape(const std::vector<int>& new_shape) {
    int total_size = 1;
    for (int dim : new_shape) {
        total_size *= dim;
    }
    if (total_size != static_cast<int>(data_.size())) {
        throw std::runtime_error("Reshape would change total size");
    }
    shape_ = new_shape;
}

void Tensor::fill(float value) {
    std::fill(data_.begin(), data_.end(), value);
}

Tensor Tensor::zeros(const std::vector<int>& shape) {
    Tensor tensor(shape);
    tensor.fill(0.0f);
    return tensor;
}

Tensor Tensor::ones(const std::vector<int>& shape) {
    Tensor tensor(shape);
    tensor.fill(1.0f);
    return tensor;
}

Tensor Tensor::randn(const std::vector<int>& shape) {
    Tensor tensor(shape);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    
    for (auto& val : tensor.data()) {
        val = dist(gen);
    }
    return tensor;
}

Tensor add(const Tensor& a, const Tensor& b) {
    if (a.shape() != b.shape()) {
        throw std::runtime_error("Shape mismatch in add");
    }
    
    Tensor result(a.shape());
    for (size_t i = 0; i < a.data().size(); i++) {
        result.data()[i] = a.data()[i] + b.data()[i];
    }
    return result;
}

Tensor sub(const Tensor& a, const Tensor& b) {
    if (a.shape() != b.shape()) {
        throw std::runtime_error("Shape mismatch in sub");
    }
    
    Tensor result(a.shape());
    for (size_t i = 0; i < a.data().size(); i++) {
        result.data()[i] = a.data()[i] - b.data()[i];
    }
    return result;
}

Tensor mul(const Tensor& a, const Tensor& b) {
    if (a.shape() != b.shape()) {
        throw std::runtime_error("Shape mismatch in mul");
    }
    
    Tensor result(a.shape());
    for (size_t i = 0; i < a.data().size(); i++) {
        result.data()[i] = a.data()[i] * b.data()[i];
    }
    return result;
}

Tensor div(const Tensor& a, const Tensor& b) {
    if (a.shape() != b.shape()) {
        throw std::runtime_error("Shape mismatch in div");
    }
    
    Tensor result(a.shape());
    for (size_t i = 0; i < a.data().size(); i++) {
        result.data()[i] = a.data()[i] / b.data()[i];
    }
    return result;
}

Tensor matmul(const Tensor& a, const Tensor& b) {
    // Simple 2D matrix multiplication
    if (a.ndim() != 2 || b.ndim() != 2) {
        throw std::runtime_error("matmul requires 2D tensors");
    }
    
    int m = a.shape()[0];
    int k = a.shape()[1];
    int n = b.shape()[1];
    
    if (k != b.shape()[0]) {
        throw std::runtime_error("Inner dimensions must match in matmul");
    }
    
    Tensor result({m, n});
    result.fill(0.0f);
    
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            for (int p = 0; p < k; p++) {
                result.data()[i * n + j] += a.data()[i * k + p] * b.data()[p * n + j];
            }
        }
    }
    
    return result;
}

Tensor transpose(const Tensor& a) {
    if (a.ndim() != 2) {
        throw std::runtime_error("transpose requires 2D tensor");
    }
    
    int m = a.shape()[0];
    int n = a.shape()[1];
    
    Tensor result({n, m});
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            result.data()[j * m + i] = a.data()[i * n + j];
        }
    }
    
    return result;
}

Tensor softmax(const Tensor& a, int dim) {
    Tensor result(a.shape());
    
    if (dim == -1 || dim == a.ndim() - 1) {
        // Softmax along last dimension
        int outer_size = 1;
        int inner_size = a.shape().back();
        for (size_t i = 0; i < a.shape().size() - 1; i++) {
            outer_size *= a.shape()[i];
        }
        
        for (int i = 0; i < outer_size; i++) {
            // Find max for numerical stability
            float max_val = a.data()[i * inner_size];
            for (int j = 1; j < inner_size; j++) {
                max_val = std::max(max_val, a.data()[i * inner_size + j]);
            }
            
            // Compute exp and sum
            float sum = 0.0f;
            for (int j = 0; j < inner_size; j++) {
                result.data()[i * inner_size + j] = std::exp(a.data()[i * inner_size + j] - max_val);
                sum += result.data()[i * inner_size + j];
            }
            
            // Normalize
            for (int j = 0; j < inner_size; j++) {
                result.data()[i * inner_size + j] /= sum;
            }
        }
    }
    
    return result;
}

Tensor layer_norm(const Tensor& a, const Tensor& gamma, const Tensor& beta, float eps) {
    Tensor result(a.shape());
    
    int outer_size = 1;
    int inner_size = a.shape().back();
    for (size_t i = 0; i < a.shape().size() - 1; i++) {
        outer_size *= a.shape()[i];
    }
    
    for (int i = 0; i < outer_size; i++) {
        // Compute mean
        float mean = 0.0f;
        for (int j = 0; j < inner_size; j++) {
            mean += a.data()[i * inner_size + j];
        }
        mean /= inner_size;
        
        // Compute variance
        float variance = 0.0f;
        for (int j = 0; j < inner_size; j++) {
            float diff = a.data()[i * inner_size + j] - mean;
            variance += diff * diff;
        }
        variance /= inner_size;
        
        // Normalize and apply gamma/beta
        float std_dev = std::sqrt(variance + eps);
        for (int j = 0; j < inner_size; j++) {
            result.data()[i * inner_size + j] = 
                gamma.data()[j] * (a.data()[i * inner_size + j] - mean) / std_dev + beta.data()[j];
        }
    }
    
    return result;
}

Tensor embedding_lookup(const Tensor& weights, const Tensor& indices) {
    // weights: [vocab_size, embedding_dim]
    // indices: [seq_len]
    // result: [seq_len, embedding_dim]
    
    int vocab_size = weights.shape()[0];
    int embedding_dim = weights.shape()[1];
    int seq_len = indices.size();
    
    Tensor result({seq_len, embedding_dim});
    
    for (int i = 0; i < seq_len; i++) {
        int idx = static_cast<int>(indices.data()[i]);
        if (idx < 0 || idx >= vocab_size) {
            throw std::runtime_error("Index out of bounds in embedding lookup");
        }
        
        for (int j = 0; j < embedding_dim; j++) {
            result.data()[i * embedding_dim + j] = weights.data()[idx * embedding_dim + j];
        }
    }
    
    return result;
}

Tensor gelu(const Tensor& a) {
    Tensor result(a.shape());
    
    // GELU approximation: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
    const float sqrt_2_over_pi = std::sqrt(2.0f / 3.14159265358979323846f);
    
    for (size_t i = 0; i < a.data().size(); i++) {
        float x = a.data()[i];
        float tanh_arg = sqrt_2_over_pi * (x + 0.044715f * x * x * x);
        result.data()[i] = 0.5f * x * (1.0f + std::tanh(tanh_arg));
    }
    
    return result;
}

Tensor relu(const Tensor& a) {
    Tensor result(a.shape());
    
    for (size_t i = 0; i < a.data().size(); i++) {
        result.data()[i] = std::max(0.0f, a.data()[i]);
    }
    
    return result;
}

Tensor sigmoid(const Tensor& a) {
    Tensor result(a.shape());
    
    for (size_t i = 0; i < a.data().size(); i++) {
        result.data()[i] = 1.0f / (1.0f + std::exp(-a.data()[i]));
    }
    
    return result;
}

Tensor concat(const std::vector<Tensor>& tensors, int dim) {
    if (tensors.empty()) {
        throw std::runtime_error("Cannot concat empty tensor list");
    }
    
    // Verify all tensors have same shape except for concat dimension
    for (size_t i = 1; i < tensors.size(); i++) {
        if (tensors[i].ndim() != tensors[0].ndim()) {
            throw std::runtime_error("All tensors must have same number of dimensions");
        }
        for (int d = 0; d < tensors[0].ndim(); d++) {
            if (d != dim && tensors[i].shape()[d] != tensors[0].shape()[d]) {
                throw std::runtime_error("Shape mismatch in concat");
            }
        }
    }
    
    // Calculate output shape
    std::vector<int> out_shape = tensors[0].shape();
    out_shape[dim] = 0;
    for (const auto& tensor : tensors) {
        out_shape[dim] += tensor.shape()[dim];
    }
    
    Tensor result(out_shape);
    
    // Copy data
    int offset = 0;
    for (const auto& tensor : tensors) {
        // Simple implementation for dim = 0
        if (dim == 0) {
            std::copy(tensor.data().begin(), tensor.data().end(), 
                     result.data().begin() + offset);
            offset += tensor.size();
        }
    }
    
    return result;
}

float sum(const Tensor& a) {
    return std::accumulate(a.data().begin(), a.data().end(), 0.0f);
}

float mean(const Tensor& a) {
    return sum(a) / a.size();
}

float max(const Tensor& a) {
    return *std::max_element(a.data().begin(), a.data().end());
}

Tensor slice(const Tensor& a, int dim, int start, int end) {
    // Simple implementation for dim = 0
    if (dim != 0) {
        throw std::runtime_error("slice only implemented for dim=0");
    }
    
    std::vector<int> new_shape = a.shape();
    new_shape[dim] = end - start;
    
    Tensor result(new_shape);
    
    int element_size = 1;
    for (size_t i = 1; i < a.shape().size(); i++) {
        element_size *= a.shape()[i];
    }
    
    std::copy(a.data().begin() + start * element_size,
             a.data().begin() + end * element_size,
             result.data().begin());
    
    return result;
}

Tensor scaled_dot_product_attention(
    const Tensor& q, const Tensor& k, const Tensor& v,
    const Tensor& mask
) {
    // q, k, v: [batch, heads, seq_len, head_dim]
    // Compute QK^T
    Tensor kt = transpose(k);
    Tensor scores = matmul(q, kt);
    
    // Scale
    float scale = 1.0f / std::sqrt(static_cast<float>(q.shape().back()));
    for (auto& val : scores.data()) {
        val *= scale;
    }
    
    // Apply mask if provided
    if (mask.size() > 0) {
        scores = add(scores, mask);
    }
    
    // Softmax
    Tensor attn_weights = softmax(scores, -1);
    
    // Apply to values
    Tensor output = matmul(attn_weights, v);
    
    return output;
}

Tensor multi_head_attention(
    const Tensor& x, const Tensor& wq, const Tensor& wk, const Tensor& wv, const Tensor& wo,
    int num_heads
) {
    // x: [batch, seq_len, d_model]
    // wq, wk, wv: [d_model, d_model]
    // wo: [d_model, d_model]
    // num_heads: number of attention heads
    
    int d_model = x.shape()[2];
    (void)d_model;
    (void)num_heads;
    
    // Project to Q, K, V
    Tensor q = matmul(x, wq);
    Tensor k = matmul(x, wk);
    Tensor v = matmul(x, wv);
    
    // Reshape for multi-head
    // This is simplified - proper implementation would reshape and transpose
    
    // Apply attention
    Tensor attn_output = scaled_dot_product_attention(q, k, v);
    
    // Project back
    Tensor output = matmul(attn_output, wo);
    
    return output;
}

Tensor mlp(const Tensor& x, const Tensor& w1, const Tensor& w2, const Tensor& b1, const Tensor& b2) {
    // x: [batch, seq_len, d_model]
    // w1: [d_model, d_ff]
    // w2: [d_ff, d_model]
    // b1: [d_ff]
    // b2: [d_model]
    
    // First projection
    Tensor hidden = matmul(x, w1);
    
    // Add bias (broadcast)
    for (int i = 0; i < hidden.shape()[0]; i++) {
        for (int j = 0; j < hidden.shape()[1]; j++) {
            for (int k = 0; k < b1.size(); k++) {
                hidden.data()[i * hidden.shape()[1] * hidden.shape()[2] + j * hidden.shape()[2] + k] += b1.data()[k];
            }
        }
    }
    
    // GELU activation
    hidden = gelu(hidden);
    
    // Second projection
    Tensor output = matmul(hidden, w2);
    
    // Add bias
    for (int i = 0; i < output.shape()[0]; i++) {
        for (int j = 0; j < output.shape()[1]; j++) {
            for (int k = 0; k < b2.size(); k++) {
                output.data()[i * output.shape()[1] * output.shape()[2] + j * output.shape()[2] + k] += b2.data()[k];
            }
        }
    }
    
    return output;
}

} // namespace llm_engine
