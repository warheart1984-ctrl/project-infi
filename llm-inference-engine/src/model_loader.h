#pragma once

#include "model_config.h"

#include <string>
#include <unordered_map>
#include <memory>
#include <cstring>
#include <stdexcept>

namespace llm_engine {

class GGUFLoader {
public:
    explicit GGUFLoader(const std::string& model_path);
    
    bool load();
    const TensorRegistry& get_tensors() const;
    const ModelConfig& get_model_config() const;
    const std::unordered_map<std::string, std::string>& get_metadata() const;
    
    int get_vocab_size() const;
    int get_context_length() const;
    int get_embedding_dim() const;
    int get_num_layers() const;
    int get_num_heads() const;
    const std::string& get_architecture() const;
    bool has_tensor(const std::string& name) const;
    
private:
    std::string model_path_;
    TensorRegistry tensors_;
    ModelConfig config_;
    std::unordered_map<std::string, std::string> metadata_;
    std::vector<std::uint8_t> file_bytes_;
    const std::uint8_t* cursor_ = nullptr;
    const std::uint8_t* end_ = nullptr;
    std::uint64_t data_section_offset_ = 0;
    
    bool parse_gguf_header();
    bool parse_gguf_tensors();
    bool parse_tensor_data(WeightTensor& tensor);
    
    std::uint32_t read_u32();
    std::uint64_t read_u64();
    std::string read_string();
    std::vector<float> read_f32_array(std::size_t count);
    std::string read_typed_value(std::uint32_t type_tag);
    void rewind(std::size_t bytes);
    std::size_t remaining() const;
    int extract_int(const std::string& primary, const std::vector<std::string>& fallbacks, int default_value) const;
    template <typename T>
    T read_pod() {
        if (remaining() < sizeof(T)) {
            throw std::runtime_error("Unexpected end of GGUF stream");
        }
        T value{};
        std::memcpy(&value, cursor_, sizeof(T));
        cursor_ += sizeof(T);
        return value;
    }
};

} // namespace llm_engine
