#include "opencl_backend.h"
#include <iostream>
#include <fstream>

namespace llm_engine {

OpenCLBackend::OpenCLBackend() 
    : context_(nullptr), queue_(nullptr), device_(nullptr), program_(nullptr),
      matmul_kernel_(nullptr), layer_norm_kernel_(nullptr), gelu_kernel_(nullptr),
      softmax_kernel_(nullptr),
      input_buffer_(nullptr), output_buffer_(nullptr), weights_buffer_(nullptr),
      model_loaded_(false), vram_used_mb_(0) {
}

OpenCLBackend::~OpenCLBackend() {
    // Cleanup OpenCL objects
    if (matmul_kernel_) clReleaseKernel(matmul_kernel_);
    if (layer_norm_kernel_) clReleaseKernel(layer_norm_kernel_);
    if (gelu_kernel_) clReleaseKernel(gelu_kernel_);
    if (softmax_kernel_) clReleaseKernel(softmax_kernel_);
    if (program_) clReleaseProgram(program_);
    if (queue_) clReleaseCommandQueue(queue_);
    if (context_) clReleaseContext(context_);
    if (input_buffer_) clReleaseMemObject(input_buffer_);
    if (output_buffer_) clReleaseMemObject(output_buffer_);
    if (weights_buffer_) clReleaseMemObject(weights_buffer_);
}

bool OpenCLBackend::initialize() {
    cl_int err;
    
    // Get platform
    cl_platform_id platform;
    err = clGetPlatformIDs(1, &platform, nullptr);
    CHECK_CL(err);
    
    // Get device
    err = clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, 1, &device_, nullptr);
    if (err != CL_SUCCESS) {
        std::cerr << "No GPU found, falling back to CPU" << std::endl;
        err = clGetDeviceIDs(platform, CL_DEVICE_TYPE_CPU, 1, &device_, nullptr);
        CHECK_CL(err);
    }
    
    // Create context
    context_ = clCreateContext(nullptr, 1, &device_, nullptr, nullptr, &err);
    CHECK_CL(err);
    
    // Create command queue
    queue_ = clCreateCommandQueue(context_, device_, 0, &err);
    CHECK_CL(err);
    
    // Compile kernels
    if (!compile_kernels()) {
        return false;
    }
    
    std::cout << "OpenCL backend initialized" << std::endl;
    return true;
}

bool OpenCLBackend::compile_kernels() {
    cl_int err;
    
    const char* source = get_kernel_source();
    size_t source_size = strlen(source);
    
    program_ = clCreateProgramWithSource(context_, 1, &source, &source_size, &err);
    CHECK_CL(err);
    
    err = clBuildProgram(program_, 1, &device_, nullptr, nullptr, nullptr);
    if (err != CL_SUCCESS) {
        char build_log[4096];
        clGetProgramBuildInfo(program_, device_, CL_PROGRAM_BUILD_LOG, 
                              sizeof(build_log), build_log, nullptr);
        std::cerr << "Build error: " << build_log << std::endl;
        return false;
    }
    
    // Create kernels
    matmul_kernel_ = clCreateKernel(program_, "matmul", &err);
    CHECK_CL(err);
    
    layer_norm_kernel_ = clCreateKernel(program_, "layer_norm", &err);
    CHECK_CL(err);
    
    gelu_kernel_ = clCreateKernel(program_, "gelu", &err);
    CHECK_CL(err);
    
    softmax_kernel_ = clCreateKernel(program_, "softmax", &err);
    CHECK_CL(err);
    
    return true;
}

bool OpenCLBackend::load_model(const std::string& model_path) {
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
    
    if (!upload_weights()) {
        std::cerr << "Failed to upload weights" << std::endl;
        return false;
    }
    
    if (!allocate_buffers()) {
        std::cerr << "Failed to allocate buffers" << std::endl;
        return false;
    }
    
    model_loaded_ = true;
    return true;
}

bool OpenCLBackend::upload_weights() {
    auto tensors = loader_->get_tensors();
    
    // Calculate total VRAM needed
    size_t total_size = 0;
    for (const auto& [name, tensor] : tensors) {
        size_t tensor_size = tensor.element_count * sizeof(float);
        total_size += tensor_size;
    }
    
    vram_used_mb_ = static_cast<int>(total_size / (1024 * 1024));
    
    std::cout << "Uploading " << vram_used_mb_ << " MB of weights to GPU" << std::endl;
    
    // Upload weights to GPU
    weights_buffer_ = clCreateBuffer(context_, CL_MEM_READ_ONLY, total_size, nullptr, nullptr);
    if (!weights_buffer_) {
        return false;
    }
    
    // Copy weights (simplified - in production, upload each tensor separately)
    size_t offset = 0;
    for (const auto& [name, tensor] : tensors) {
        size_t tensor_size = tensor.element_count * sizeof(float);
        clEnqueueWriteBuffer(queue_, weights_buffer_, CL_TRUE, offset, tensor_size,
                           tensor.data_ptr(), 0, nullptr, nullptr);
        offset += tensor_size;
    }
    
    return true;
}

bool OpenCLBackend::allocate_buffers() {
    cl_int err;
    
    // Allocate input/output buffers
    size_t buffer_size = context_length_ * embedding_dim_ * sizeof(float);
    
    input_buffer_ = clCreateBuffer(context_, CL_MEM_READ_WRITE, buffer_size, nullptr, &err);
    CHECK_CL(err);
    
    output_buffer_ = clCreateBuffer(context_, CL_MEM_READ_WRITE, buffer_size, nullptr, &err);
    CHECK_CL(err);
    
    return true;
}

Tensor OpenCLBackend::forward(const Tensor& input) {
    if (!model_loaded_) {
        throw std::runtime_error("Model not loaded");
    }

    (void)get_kernel_source();
    
    // Copy input to GPU
    clEnqueueWriteBuffer(queue_, input_buffer_, CL_TRUE, 0,
                        input.data().size() * sizeof(float),
                        input.data().data(), 0, nullptr, nullptr);
    
    // Execute kernels (simplified - in production, implement full forward pass)
    Tensor output(input.shape());
    
    // Copy output from GPU
    clEnqueueReadBuffer(queue_, output_buffer_, CL_TRUE, 0,
                       output.data().size() * sizeof(float),
                       output.data().data(), 0, nullptr, nullptr);
    
    return output;
}

Tensor OpenCLBackend::forward_layer(const Tensor& x, int layer_idx) {
    // Simplified implementation
    (void)layer_idx;
    return forward(x);
}

std::string OpenCLBackend::generate(const std::string& prompt, int max_tokens, float temperature) {
    // Simplified - use CPU backend for generation
    // In production, implement full GPU generation
    (void)max_tokens;
    (void)temperature;
    return prompt;
}

const char* OpenCLBackend::get_kernel_source() {
    return R"(
__kernel void matmul(
    __global const float* A,
    __global const float* B,
    __global float* C,
    const int M, const int N, const int K
) {
    int i = get_global_id(0);
    int j = get_global_id(1);
    
    if (i < M && j < N) {
        float sum = 0.0f;
        for (int k = 0; k < K; k++) {
            sum += A[i * K + k] * B[k * N + j];
        }
        C[i * N + j] = sum;
    }
}

__kernel void layer_norm(
    __global const float* x,
    __global const float* gamma,
    __global const float* beta,
    __global float* y,
    const int N, const float eps
) {
    int i = get_global_id(0);
    
    if (i < N) {
        // Compute mean
        float mean = 0.0f;
        for (int j = 0; j < N; j++) {
            mean += x[i * N + j];
        }
        mean /= N;
        
        // Compute variance
        float variance = 0.0f;
        for (int j = 0; j < N; j++) {
            float diff = x[i * N + j] - mean;
            variance += diff * diff;
        }
        variance /= N;
        
        // Normalize
        float std_dev = sqrt(variance + eps);
        for (int j = 0; j < N; j++) {
            y[i * N + j] = gamma[j] * (x[i * N + j] - mean) / std_dev + beta[j];
        }
    }
}

__kernel void gelu(
    __global const float* x,
    __global float* y,
    const int N
) {
    int i = get_global_id(0);
    
    if (i < N) {
        float xi = x[i];
        float tanh_arg = sqrt(2.0f / M_PI) * (xi + 0.044715f * xi * xi * xi);
        y[i] = 0.5f * xi * (1.0f + tanh(tanh_arg));
    }
}

__kernel void softmax(
    __global const float* x,
    __global float* y,
    const int N
) {
    int i = get_global_id(0);
    
    if (i < N) {
        // Find max
        float max_val = x[i];
        for (int j = 1; j < N; j++) {
            max_val = fmax(max_val, x[i * N + j]);
        }
        
        // Compute exp and sum
        float sum = 0.0f;
        for (int j = 0; j < N; j++) {
            y[i * N + j] = exp(x[i * N + j] - max_val);
            sum += y[i * N + j];
        }
        
        // Normalize
        for (int j = 0; j < N; j++) {
            y[i * N + j] /= sum;
        }
    }
}
)";
}

} // namespace llm_engine
