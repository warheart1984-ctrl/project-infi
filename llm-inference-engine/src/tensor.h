#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <memory>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace llm_engine {

class Tensor {
public:
    Tensor() = default;
    explicit Tensor(const std::vector<int>& shape);
    Tensor(const std::vector<int>& shape, const std::vector<float>& data);
    Tensor(const std::vector<int>& shape, const float* data, std::size_t count);

    const std::vector<int>& shape() const { return shape_; }
    const std::vector<float>& data() const { return data_; }
    std::vector<float>& data() { return data_; }

    int size() const { return static_cast<int>(data_.size()); }
    int ndim() const { return static_cast<int>(shape_.size()); }

    void reshape(const std::vector<int>& new_shape);
    void fill(float value);

    static Tensor zeros(const std::vector<int>& shape);
    static Tensor ones(const std::vector<int>& shape);
    static Tensor randn(const std::vector<int>& shape);

private:
    std::vector<int> shape_;
    std::vector<float> data_;
};

Tensor add(const Tensor& a, const Tensor& b);
Tensor sub(const Tensor& a, const Tensor& b);
Tensor mul(const Tensor& a, const Tensor& b);
Tensor div(const Tensor& a, const Tensor& b);

Tensor matmul(const Tensor& a, const Tensor& b);
Tensor transpose(const Tensor& a);

Tensor softmax(const Tensor& a, int dim = -1);
Tensor layer_norm(const Tensor& a, const Tensor& gamma, const Tensor& beta, float eps = 1e-5f);

Tensor embedding_lookup(const Tensor& weights, const Tensor& indices);

Tensor gelu(const Tensor& a);
Tensor relu(const Tensor& a);
Tensor sigmoid(const Tensor& a);

Tensor concat(const std::vector<Tensor>& tensors, int dim = 0);

Tensor scaled_dot_product_attention(
    const Tensor& q, const Tensor& k, const Tensor& v,
    const Tensor& mask = Tensor()
);

Tensor multi_head_attention(
    const Tensor& x, const Tensor& wq, const Tensor& wk, const Tensor& wv, const Tensor& wo,
    int num_heads
);

Tensor mlp(const Tensor& x, const Tensor& w1, const Tensor& w2, const Tensor& b1, const Tensor& b2);

float sum(const Tensor& a);
float mean(const Tensor& a);
float max(const Tensor& a);

Tensor slice(const Tensor& a, int dim, int start, int end);

} // namespace llm_engine
