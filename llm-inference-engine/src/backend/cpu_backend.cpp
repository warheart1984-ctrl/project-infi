#include "cpu_backend.h"
#include <iostream>
#include <random>

namespace llm_engine {

CPUBackend::CPUBackend() : model_loaded_(false) {
}

bool CPUBackend::load_model(const std::string& model_path) {
    loader_ = std::make_unique<GGUFLoader>(model_path);
    
    if (!loader_->load()) {
        std::cerr << "Failed to load model" << std::endl;
        return false;
    }
    
    const auto& config = loader_->get_model_config();
    vocab_size_ = config.vocab_size;
    context_length_ = config.context_length;
    embedding_dim_ = config.embedding_dim;
    num_layers_ = config.num_layers;
    num_heads_ = config.num_heads;
    
    std::cout << "Model loaded: " << model_path << std::endl;
    std::cout << "Vocab size: " << vocab_size_ << std::endl;
    std::cout << "Context length: " << context_length_ << std::endl;
    std::cout << "Embedding dim: " << embedding_dim_ << std::endl;
    std::cout << "Num layers: " << num_layers_ << std::endl;
    std::cout << "Num heads: " << num_heads_ << std::endl;
    
    if (!extract_model_weights()) {
        std::cerr << "Failed to extract model weights" << std::endl;
        return false;
    }
    
    model_loaded_ = true;
    return true;
}

bool CPUBackend::extract_model_weights() {
    auto tensors = loader_->get_tensors();
    layers_.clear();
    
    // Extract token embeddings
    auto tok_emb_it = tensors.find("token_embd.weight");
    if (tok_emb_it != tensors.end()) {
        token_embeddings_ = Tensor(tok_emb_it->second.shape, tok_emb_it->second.data_ptr(), tok_emb_it->second.element_count);
    }
    
    // Extract output embeddings
    auto out_emb_it = tensors.find("output.weight");
    if (out_emb_it != tensors.end()) {
        output_embeddings_ = Tensor(out_emb_it->second.shape, out_emb_it->second.data_ptr(), out_emb_it->second.element_count);
    }
    
    // Extract layer weights
    for (int i = 0; i < num_layers_; i++) {
        LayerWeights layer;
        
        // Attention weights
        std::string wq_name = "blk." + std::to_string(i) + ".attn_q.weight";
        std::string wk_name = "blk." + std::to_string(i) + ".attn_k.weight";
        std::string wv_name = "blk." + std::to_string(i) + ".attn_v.weight";
        std::string wo_name = "blk." + std::to_string(i) + ".attn_output.weight";
        
        auto wq_it = tensors.find(wq_name);
        auto wk_it = tensors.find(wk_name);
        auto wv_it = tensors.find(wv_name);
        auto wo_it = tensors.find(wo_name);
        
        if (wq_it != tensors.end()) layer.wq = Tensor(wq_it->second.shape, wq_it->second.data_ptr(), wq_it->second.element_count);
        if (wk_it != tensors.end()) layer.wk = Tensor(wk_it->second.shape, wk_it->second.data_ptr(), wk_it->second.element_count);
        if (wv_it != tensors.end()) layer.wv = Tensor(wv_it->second.shape, wv_it->second.data_ptr(), wv_it->second.element_count);
        if (wo_it != tensors.end()) layer.wo = Tensor(wo_it->second.shape, wo_it->second.data_ptr(), wo_it->second.element_count);
        
        // FFN weights
        std::string ffn_w1_name = "blk." + std::to_string(i) + ".ffn_gate.weight";
        std::string ffn_w2_name = "blk." + std::to_string(i) + ".ffn_down.weight";
        
        auto ffn_w1_it = tensors.find(ffn_w1_name);
        auto ffn_w2_it = tensors.find(ffn_w2_name);
        
        if (ffn_w1_it != tensors.end()) layer.ffn_w1 = Tensor(ffn_w1_it->second.shape, ffn_w1_it->second.data_ptr(), ffn_w1_it->second.element_count);
        if (ffn_w2_it != tensors.end()) layer.ffn_w2 = Tensor(ffn_w2_it->second.shape, ffn_w2_it->second.data_ptr(), ffn_w2_it->second.element_count);
        
        // Layer norm weights
        std::string ln1_gamma_name = "blk." + std::to_string(i) + ".attn_norm.weight";
        std::string ln1_beta_name = "blk." + std::to_string(i) + ".attn_norm.bias";
        std::string ln2_gamma_name = "blk." + std::to_string(i) + ".ffn_norm.weight";
        std::string ln2_beta_name = "blk." + std::to_string(i) + ".ffn_norm.bias";
        
        auto ln1_gamma_it = tensors.find(ln1_gamma_name);
        auto ln1_beta_it = tensors.find(ln1_beta_name);
        auto ln2_gamma_it = tensors.find(ln2_gamma_name);
        auto ln2_beta_it = tensors.find(ln2_beta_name);
        
        if (ln1_gamma_it != tensors.end()) layer.ln1_gamma = Tensor(ln1_gamma_it->second.shape, ln1_gamma_it->second.data_ptr(), ln1_gamma_it->second.element_count);
        if (ln1_beta_it != tensors.end()) layer.ln1_beta = Tensor(ln1_beta_it->second.shape, ln1_beta_it->second.data_ptr(), ln1_beta_it->second.element_count);
        if (ln2_gamma_it != tensors.end()) layer.ln2_gamma = Tensor(ln2_gamma_it->second.shape, ln2_gamma_it->second.data_ptr(), ln2_gamma_it->second.element_count);
        if (ln2_beta_it != tensors.end()) layer.ln2_beta = Tensor(ln2_beta_it->second.shape, ln2_beta_it->second.data_ptr(), ln2_beta_it->second.element_count);
        
        layers_.push_back(layer);
    }
    
    return true;
}

Tensor CPUBackend::forward_transformer_block(const Tensor& x, const LayerWeights& weights) {
    // Layer norm 1
    Tensor ln1_out = layer_norm(x, weights.ln1_gamma, weights.ln1_beta);
    
    // Self-attention
    Tensor attn_out = multi_head_attention(ln1_out, weights.wq, weights.wk, weights.wv, weights.wo, num_heads_);
    
    // Residual connection
    Tensor residual1 = add(x, attn_out);
    
    // Layer norm 2
    Tensor ln2_out = layer_norm(residual1, weights.ln2_gamma, weights.ln2_beta);
    
    // FFN
    Tensor ffn_out = mlp(ln2_out, weights.ffn_w1, weights.ffn_w2, 
                        Tensor({weights.ffn_w1.shape()[1]}), Tensor({weights.ffn_w2.shape()[1]}));
    
    // Residual connection
    Tensor residual2 = add(residual1, ffn_out);
    
    return residual2;
}

Tensor CPUBackend::forward(const Tensor& input) {
    if (!model_loaded_) {
        throw std::runtime_error("Model not loaded");
    }
    
    Tensor x = input;
    
    // Embedding lookup
    x = embedding_lookup(token_embeddings_, x);
    
    // Forward through all layers
    for (int i = 0; i < num_layers_; i++) {
        x = forward_layer(x, i);
    }
    
    // Final layer norm
    Tensor final_ln = layer_norm(x, layers_.back().ln2_gamma, layers_.back().ln2_beta);
    
    // Project to vocabulary
    Tensor logits = matmul(final_ln, transpose(output_embeddings_));
    
    return logits;
}

Tensor CPUBackend::forward_layer(const Tensor& x, int layer_idx) {
    if (layer_idx < 0 || layer_idx >= num_layers_) {
        throw std::runtime_error("Invalid layer index");
    }
    
    return forward_transformer_block(x, layers_[layer_idx]);
}

std::string CPUBackend::generate(const std::string& prompt, int max_tokens, float temperature) {
    if (!model_loaded_) {
        throw std::runtime_error("Model not loaded");
    }
    
    // Simple tokenization (in production, use proper tokenizer)
    std::vector<float> prompt_tokens;
    for (char c : prompt) {
        prompt_tokens.push_back(static_cast<float>(static_cast<unsigned char>(c)));
    }
    
    Tensor input({1, static_cast<int>(prompt_tokens.size())}, prompt_tokens);
    
    std::string result = prompt;
    
    for (int i = 0; i < max_tokens; i++) {
        // Forward pass
        Tensor logits = forward(input);
        
        // Sample from distribution
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        
        // Get last token logits
        int vocab_size = logits.shape()[1];
        std::vector<float> probs(vocab_size);
        
        // Apply temperature and softmax
        for (int j = 0; j < vocab_size; j++) {
            probs[j] = logits.data()[logits.size() - vocab_size + j] / temperature;
        }
        
        // Simple sampling (in production, use proper sampling)
        int next_token = 0;
        float max_prob = probs[0];
        for (int j = 1; j < vocab_size; j++) {
            if (probs[j] > max_prob) {
                max_prob = probs[j];
                next_token = j;
            }
        }
        
        // Append token to result
        result += static_cast<char>(next_token);
        
        // Update input for next iteration
        // (simplified - in production, use proper KV cache)
    }
    
    return result;
}

} // namespace llm_engine
