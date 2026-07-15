#pragma once

#include "../executor_interface.h"
#include "../tensor_ops.h"
#include "../model_loader.h"
#include <memory>

namespace llm_engine {

class CPUBackend : public ILayerExecutor {
public:
    CPUBackend();
    
    std::string name() const override { return "cpu"; }
    bool load_model(const std::string& model_path);
    
    Tensor forward(const Tensor& input);
    Tensor forward_layer(const Tensor& x, int layer_idx);
    
    std::string generate(const std::string& prompt, int max_tokens, float temperature);
    
    bool is_loaded() const { return model_loaded_; }
    int get_vram_usage() const { return 0; } // CPU uses no VRAM
    
private:
    std::unique_ptr<GGUFLoader> loader_;
    bool model_loaded_;
    
    // Model components
    Tensor token_embeddings_;
    Tensor output_embeddings_;
    std::vector<Tensor> layer_weights_;
    
    // Model hyperparameters
    int vocab_size_;
    int context_length_;
    int embedding_dim_;
    int num_layers_;
    int num_heads_;
    
    // Layer components
    struct LayerWeights {
        Tensor wq, wk, wv, wo;
        Tensor ffn_w1, ffn_w2;
        Tensor ln1_gamma, ln1_beta;
        Tensor ln2_gamma, ln2_beta;
    };
    
    std::vector<LayerWeights> layers_;
    
    bool extract_model_weights();
    Tensor forward_transformer_block(const Tensor& x, const LayerWeights& weights);
};

} // namespace llm_engine
