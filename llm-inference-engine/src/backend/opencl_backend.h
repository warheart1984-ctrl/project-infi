#pragma once

#include "../executor_interface.h"
#include "../tensor_ops.h"
#include "../model_loader.h"
#include <CL/cl.h>
#include <memory>

namespace llm_engine {

#define CHECK_CL(err) \
    if (err != CL_SUCCESS) { \
        std::cerr << "OpenCL error: " << err << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }

class OpenCLBackend : public ILayerExecutor {
public:
    OpenCLBackend();
    ~OpenCLBackend();
    
    std::string name() const override { return "opencl"; }
    bool initialize();
    bool load_model(const std::string& model_path);
    
    Tensor forward(const Tensor& input);
    Tensor forward_layer(const Tensor& x, int layer_idx);
    
    std::string generate(const std::string& prompt, int max_tokens, float temperature);
    
    bool is_loaded() const { return model_loaded_; }
    int get_vram_usage() const { return vram_used_mb_; }
    
private:
    bool compile_kernels();
    bool upload_weights();
    bool allocate_buffers();
    
    // OpenCL objects
    cl_context context_;
    cl_command_queue queue_;
    cl_device_id device_;
    cl_program program_;
    
    // Kernels
    cl_kernel matmul_kernel_;
    cl_kernel layer_norm_kernel_;
    cl_kernel gelu_kernel_;
    cl_kernel softmax_kernel_;
    
    // Buffers
    cl_mem input_buffer_;
    cl_mem output_buffer_;
    cl_mem weights_buffer_;
    
    bool model_loaded_;
    int vram_used_mb_;
    
    // Model components
    std::unique_ptr<GGUFLoader> loader_;
    std::vector<Tensor> weights_;
    
    // Model hyperparameters
    int vocab_size_;
    int context_length_;
    int embedding_dim_;
    int num_layers_;
    int num_heads_;
    
    // Kernel source code
    const char* get_kernel_source();
};

} // namespace llm_engine
