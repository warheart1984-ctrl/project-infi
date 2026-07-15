#pragma once

#include "tensor.h"

#include <string>

namespace llm_engine {

class ILayerExecutor {
public:
    virtual ~ILayerExecutor() = default;

    virtual std::string name() const = 0;
    virtual bool load_model(const std::string& model_path) = 0;
    virtual bool is_loaded() const = 0;
    virtual int get_vram_usage() const = 0;
    virtual Tensor forward(const Tensor& input) = 0;
    virtual Tensor forward_layer(const Tensor& x, int layer_idx) = 0;
    virtual std::string generate(const std::string& prompt, int max_tokens, float temperature) = 0;
};

} // namespace llm_engine
