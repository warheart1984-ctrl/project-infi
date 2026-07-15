#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace llm_engine {

struct ModelConfig {
    std::string architecture;
    std::string tokenizer_model;
    int vocab_size = 0;
    int context_length = 0;
    int embedding_dim = 0;
    int num_layers = 0;
    int num_heads = 0;
    std::unordered_map<std::string, std::string> metadata;
};

struct TensorDescriptor {
    std::string name;
    std::vector<std::size_t> shape;
    std::string type;
    std::uint64_t offset = 0;
    std::size_t element_count = 0;
    std::size_t byte_size = 0;
};

struct WeightTensor {
    std::string name;
    std::vector<int> shape;
    std::string type;
    const float* data = nullptr;
    std::size_t element_count = 0;
    std::size_t byte_size = 0;
    std::uint64_t offset = 0;
    bool memory_mapped = false;
    std::vector<float> owned_data;

    const float* data_ptr() const {
        return data ? data : owned_data.data();
    }
};

using TensorRegistry = std::unordered_map<std::string, WeightTensor>;

} // namespace llm_engine
