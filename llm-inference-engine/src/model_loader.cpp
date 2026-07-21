#include "model_loader.h"

#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>

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

std::string type_name(std::uint32_t type_tag) {
    switch (type_tag) {
        case 0: return "u8";
        case 1: return "i8";
        case 2: return "u16";
        case 3: return "i16";
        case 4: return "u32";
        case 5: return "i32";
        case 6: return "f32";
        case 7: return "bool";
        case 8: return "string";
        case 9: return "array";
        default: return "unknown";
    }
}

std::size_t element_size_for_type(const std::string& type) {
    if (type == "f32") {
        return sizeof(float);
    }
    if (type == "f16") {
        return sizeof(std::uint16_t);
    }
    if (type == "u32" || type == "i32") {
        return sizeof(std::uint32_t);
    }
    return 0;
}

} // namespace

GGUFLoader::GGUFLoader(const std::string& model_path)
    : model_path_(model_path) {
}

bool GGUFLoader::load() {
    std::ifstream file(model_path_, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Failed to open model file: " << model_path_ << std::endl;
        return false;
    }

    const auto file_size = std::filesystem::file_size(model_path_);
    file_bytes_.resize(static_cast<std::size_t>(file_size));
    if (!file.read(reinterpret_cast<char*>(file_bytes_.data()), static_cast<std::streamsize>(file_bytes_.size()))) {
        std::cerr << "Failed to read model file: " << model_path_ << std::endl;
        return false;
    }

    cursor_ = file_bytes_.data();
    end_ = file_bytes_.data() + file_bytes_.size();

    if (!parse_gguf_header()) {
        return false;
    }
    if (!parse_gguf_tensors()) {
        return false;
    }

    config_.metadata = metadata_;
    config_.architecture = metadata_.count("general.architecture") ? metadata_.at("general.architecture") : "unknown";
    config_.tokenizer_model = metadata_.count("tokenizer.ggml.model") ? metadata_.at("tokenizer.ggml.model") : "";
    config_.vocab_size = get_vocab_size();
    config_.context_length = get_context_length();
    config_.embedding_dim = get_embedding_dim();
    config_.num_layers = get_num_layers();
    config_.num_heads = get_num_heads();
    return true;
}

bool GGUFLoader::parse_gguf_header() {
    char magic[4];
    std::memcpy(magic, cursor_, sizeof(magic));
    cursor_ += sizeof(magic);
    if (std::strncmp(magic, "GGUF", 4) != 0) {
        std::cerr << "Invalid GGUF magic number" << std::endl;
        return false;
    }

    const std::uint32_t version = read_u32();
    if (version != 2 && version != 3) {
        std::cerr << "Unsupported GGUF version: " << version << std::endl;
        return false;
    }

    const std::uint64_t tensor_count = read_u64();
    const std::uint64_t metadata_count = read_u64();

    for (std::uint64_t i = 0; i < metadata_count; ++i) {
        const std::string key = read_string();
        const std::uint32_t type_tag = read_u32();
        const std::string value = read_typed_value(type_tag);
        metadata_[key] = value;
    }

    metadata_["general.tensor_count"] = std::to_string(tensor_count);
    return true;
}

bool GGUFLoader::parse_gguf_tensors() {
    const auto tensor_count_it = metadata_.find("general.tensor_count");
    if (tensor_count_it == metadata_.end()) {
        std::cerr << "Tensor count missing from metadata" << std::endl;
        return false;
    }

    const std::uint64_t tensor_count = std::stoull(tensor_count_it->second);
    std::vector<TensorDescriptor> descriptors;
    descriptors.reserve(static_cast<std::size_t>(tensor_count));

    for (std::uint64_t i = 0; i < tensor_count; ++i) {
        TensorDescriptor descriptor;
        descriptor.name = read_string();

        const std::uint32_t num_dims = read_u32();
        descriptor.shape.reserve(num_dims);
        descriptor.element_count = 1;
        for (std::uint32_t j = 0; j < num_dims; ++j) {
            const std::uint64_t dim = read_u64();
            descriptor.shape.push_back(static_cast<std::size_t>(dim));
            descriptor.element_count *= static_cast<std::size_t>(dim);
        }

        const std::uint32_t type_tag = read_u32();
        descriptor.type = type_name(type_tag);
        descriptor.offset = read_u64();
        descriptor.byte_size = descriptor.element_count * element_size_for_type(descriptor.type);
        descriptors.push_back(descriptor);
    }

    data_section_offset_ = static_cast<std::uint64_t>(cursor_ - file_bytes_.data());

    for (const auto& descriptor : descriptors) {
        WeightTensor tensor;
        tensor.name = descriptor.name;
        tensor.type = descriptor.type;
        tensor.offset = descriptor.offset;
        tensor.element_count = descriptor.element_count;
        tensor.byte_size = descriptor.byte_size;
        tensor.shape.reserve(descriptor.shape.size());
        for (std::size_t dim : descriptor.shape) {
            tensor.shape.push_back(static_cast<int>(dim));
        }

        if (!parse_tensor_data(tensor)) {
            std::cerr << "Failed to load tensor: " << tensor.name << std::endl;
            return false;
        }

        tensors_[tensor.name] = std::move(tensor);
    }

    return true;
}

bool GGUFLoader::parse_tensor_data(WeightTensor& tensor) {
    if (tensor.type != "f32") {
        std::cerr << "Quantized tensor type not yet implemented: " << tensor.type << std::endl;
        return false;
    }

    const std::size_t start = static_cast<std::size_t>(data_section_offset_ + tensor.offset);
    const std::size_t byte_count = tensor.element_count * sizeof(float);
    if (start + byte_count > file_bytes_.size()) {
        std::cerr << "Tensor exceeds file bounds: " << tensor.name << std::endl;
        return false;
    }

    tensor.data = reinterpret_cast<const float*>(file_bytes_.data() + start);
    tensor.memory_mapped = true;
    return true;
}

const TensorRegistry& GGUFLoader::get_tensors() const {
    return tensors_;
}

const ModelConfig& GGUFLoader::get_model_config() const {
    return config_;
}

const std::unordered_map<std::string, std::string>& GGUFLoader::get_metadata() const {
    return metadata_;
}

int GGUFLoader::get_vocab_size() const {
    return extract_int("tokenizer.ggml.tokens", {
        "tokenizer.ggml.vocab_size",
        "llama.vocab_size",
        "general.vocab_size",
    }, 0);
}

int GGUFLoader::get_context_length() const {
    return extract_int("llama.context_length", {
        "llama.n_ctx_train",
        "context_length",
        "general.context_length",
    }, 0);
}

int GGUFLoader::get_embedding_dim() const {
    return extract_int("llama.embedding_length", {
        "embedding_length",
        "llama.n_embd",
        "general.embedding_length",
    }, 0);
}

int GGUFLoader::get_num_layers() const {
    return extract_int("llama.block_count", {
        "num_layers",
        "general.block_count",
        "llama.n_layer",
    }, 0);
}

int GGUFLoader::get_num_heads() const {
    return extract_int("llama.attention.head_count", {
        "num_heads",
        "general.head_count",
        "llama.n_head",
    }, 0);
}

const std::string& GGUFLoader::get_architecture() const {
    static const std::string empty;
    const auto it = metadata_.find("general.architecture");
    return it == metadata_.end() ? empty : it->second;
}

bool GGUFLoader::has_tensor(const std::string& name) const {
    return tensors_.find(name) != tensors_.end();
}

std::uint32_t GGUFLoader::read_u32() {
    if (remaining() < sizeof(std::uint32_t)) {
        throw std::runtime_error("Unexpected end of GGUF stream");
    }
    std::uint32_t value = 0;
    std::memcpy(&value, cursor_, sizeof(value));
    cursor_ += sizeof(value);
    return value;
}

std::uint64_t GGUFLoader::read_u64() {
    if (remaining() < sizeof(std::uint64_t)) {
        throw std::runtime_error("Unexpected end of GGUF stream");
    }
    std::uint64_t value = 0;
    std::memcpy(&value, cursor_, sizeof(value));
    cursor_ += sizeof(value);
    return value;
}

std::string GGUFLoader::read_string() {
    const std::uint64_t length = read_u64();
    if (remaining() < length) {
        throw std::runtime_error("Unexpected end of GGUF string");
    }
    std::string value(reinterpret_cast<const char*>(cursor_), reinterpret_cast<const char*>(cursor_ + length));
    cursor_ += length;
    return value;
}

std::vector<float> GGUFLoader::read_f32_array(std::size_t count) {
    if (remaining() < count * sizeof(float)) {
        throw std::runtime_error("Unexpected end of GGUF float array");
    }
    std::vector<float> values(count);
    std::memcpy(values.data(), cursor_, count * sizeof(float));
    cursor_ += count * sizeof(float);
    return values;
}

std::string GGUFLoader::read_typed_value(std::uint32_t type_tag) {
    switch (type_tag) {
        case 0:
            return std::to_string(static_cast<unsigned int>(*cursor_++));
        case 1:
            return std::to_string(static_cast<int>(static_cast<std::int8_t>(*cursor_++)));
        case 2: {
            const std::uint16_t value = read_pod<std::uint16_t>();
            return std::to_string(value);
        }
        case 3: {
            const std::int16_t value = read_pod<std::int16_t>();
            return std::to_string(value);
        }
        case 4:
            return std::to_string(read_u32());
        case 5: {
            const std::int32_t value = read_pod<std::int32_t>();
            return std::to_string(value);
        }
        case 6: {
            const float value = read_pod<float>();
            std::ostringstream stream;
            stream << value;
            return stream.str();
        }
        case 7:
            return (*cursor_++ != 0) ? "true" : "false";
        case 8:
            return read_string();
        case 9: {
            const std::uint32_t element_type = read_u32();
            const std::uint64_t count = read_u64();
            std::vector<std::string> values;
            values.reserve(static_cast<std::size_t>(count));
            for (std::uint64_t i = 0; i < count; ++i) {
                values.push_back(read_typed_value(element_type));
            }
            std::ostringstream stream;
            stream << "[";
            for (std::size_t i = 0; i < values.size(); ++i) {
                if (i > 0) {
                    stream << ", ";
                }
                stream << values[i];
            }
            stream << "]";
            return stream.str();
        }
        default:
            return "";
    }
}

void GGUFLoader::rewind(std::size_t bytes) {
    if (bytes > static_cast<std::size_t>(cursor_ - file_bytes_.data())) {
        throw std::runtime_error("Cannot rewind before start of GGUF buffer");
    }
    cursor_ -= bytes;
}

std::size_t GGUFLoader::remaining() const {
    return static_cast<std::size_t>(end_ - cursor_);
}

int GGUFLoader::extract_int(const std::string& primary, const std::vector<std::string>& fallbacks, int default_value) const {
    const auto lookup = [&](const std::string& key) -> int {
        const auto it = metadata_.find(key);
        if (it == metadata_.end()) {
            return default_value;
        }
        try {
            return std::stoi(trim_copy(it->second));
        } catch (...) {
            return default_value;
        }
    };

    const int primary_value = lookup(primary);
    if (primary_value != default_value) {
        return primary_value;
    }
    for (const auto& key : fallbacks) {
        const int value = lookup(key);
        if (value != default_value) {
            return value;
        }
    }

    if (primary == "tokenizer.ggml.tokens") {
        const auto tensor_it = tensors_.find("token_embd.weight");
        if (tensor_it != tensors_.end() && !tensor_it->second.shape.empty()) {
            return tensor_it->second.shape.front();
        }
    }

    return default_value;
}

} // namespace llm_engine
