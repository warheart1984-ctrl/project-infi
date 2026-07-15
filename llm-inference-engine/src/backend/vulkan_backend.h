#pragma once

#include "../executor_interface.h"
#include "../tensor_ops.h"
#include "../model_loader.h"
#include <vulkan/vulkan.h>
#include <memory>

namespace llm_engine {

#define CHECK_VK(result) \
    if (result != VK_SUCCESS) { \
        std::cerr << "Vulkan error: " << result << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
        return false; \
    }

class VulkanBackend : public ILayerExecutor {
public:
    VulkanBackend();
    ~VulkanBackend();
    
    std::string name() const override { return "vulkan"; }
    bool initialize();
    bool load_model(const std::string& model_path);
    
    Tensor forward(const Tensor& input);
    Tensor forward_layer(const Tensor& x, int layer_idx);
    
    std::string generate(const std::string& prompt, int max_tokens, float temperature);
    
    bool is_loaded() const { return model_loaded_; }
    int get_vram_usage() const { return vram_used_mb_; }
    
private:
    bool create_instance();
    bool select_physical_device();
    bool create_logical_device();
    bool create_command_pool();
    bool create_descriptor_pool();
    bool create_pipeline_layout();
    bool create_compute_pipeline();
    bool allocate_buffers();
    bool upload_weights();
    
    // Vulkan objects
    VkInstance instance_;
    VkPhysicalDevice physical_device_;
    VkDevice device_;
    VkQueue compute_queue_;
    VkCommandPool command_pool_;
    VkDescriptorPool descriptor_pool_;
    VkPipelineLayout pipeline_layout_;
    VkPipeline compute_pipeline_;
    
    // Buffers
    VkBuffer input_buffer_;
    VkDeviceMemory input_memory_;
    VkBuffer output_buffer_;
    VkDeviceMemory output_memory_;
    VkBuffer weights_buffer_;
    VkDeviceMemory weights_memory_;
    
    uint32_t compute_queue_family_index_;
    
    bool model_loaded_;
    int vram_used_mb_;
    
    // Model components
    std::unique_ptr<GGUFLoader> loader_;
    
    // Model hyperparameters
    int vocab_size_;
    int context_length_;
    int embedding_dim_;
    int num_layers_;
    int num_heads_;
    
    uint32_t find_memory_type(uint32_t type_filter, VkMemoryPropertyFlags properties);
};

} // namespace llm_engine
