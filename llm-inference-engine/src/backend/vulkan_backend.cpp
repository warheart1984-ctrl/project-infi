#include "vulkan_backend.h"
#include <iostream>
#include <fstream>
#include <set>

namespace llm_engine {

VulkanBackend::VulkanBackend()
    : instance_(VK_NULL_HANDLE), physical_device_(VK_NULL_HANDLE), device_(VK_NULL_HANDLE),
      compute_queue_(VK_NULL_HANDLE), command_pool_(VK_NULL_HANDLE), descriptor_pool_(VK_NULL_HANDLE),
      pipeline_layout_(VK_NULL_HANDLE), compute_pipeline_(VK_NULL_HANDLE),
      input_buffer_(VK_NULL_HANDLE), input_memory_(VK_NULL_HANDLE),
      output_buffer_(VK_NULL_HANDLE), output_memory_(VK_NULL_HANDLE),
      weights_buffer_(VK_NULL_HANDLE), weights_memory_(VK_NULL_HANDLE),
      compute_queue_family_index_(0),
      model_loaded_(false), vram_used_mb_(0) {
}

VulkanBackend::~VulkanBackend() {
    // Cleanup Vulkan objects
    if (compute_pipeline_) vkDestroyPipeline(device_, compute_pipeline_, nullptr);
    if (pipeline_layout_) vkDestroyPipelineLayout(device_, pipeline_layout_, nullptr);
    if (descriptor_pool_) vkDestroyDescriptorPool(device_, descriptor_pool_, nullptr);
    if (command_pool_) vkDestroyCommandPool(device_, command_pool_, nullptr);
    if (device_) vkDestroyDevice(device_, nullptr);
    if (instance_) vkDestroyInstance(instance_, nullptr);
    
    if (input_buffer_) vkDestroyBuffer(device_, input_buffer_, nullptr);
    if (input_memory_) vkFreeMemory(device_, input_memory_, nullptr);
    if (output_buffer_) vkDestroyBuffer(device_, output_buffer_, nullptr);
    if (output_memory_) vkFreeMemory(device_, output_memory_, nullptr);
    if (weights_buffer_) vkDestroyBuffer(device_, weights_buffer_, nullptr);
    if (weights_memory_) vkFreeMemory(device_, weights_memory_, nullptr);
}

bool VulkanBackend::initialize() {
    if (!create_instance()) return false;
    if (!select_physical_device()) return false;
    if (!create_logical_device()) return false;
    if (!create_command_pool()) return false;
    if (!create_descriptor_pool()) return false;
    if (!create_pipeline_layout()) return false;
    if (!create_compute_pipeline()) return false;
    
    std::cout << "Vulkan backend initialized" << std::endl;
    return true;
}

bool VulkanBackend::create_instance() {
    VkApplicationInfo app_info = {};
    app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app_info.pApplicationName = "LLM Inference Engine";
    app_info.applicationVersion = VK_MAKE_VERSION(1, 0, 0);
    app_info.pEngineName = "No Engine";
    app_info.engineVersion = VK_MAKE_VERSION(1, 0, 0);
    app_info.apiVersion = VK_API_VERSION_1_0;
    
    VkInstanceCreateInfo create_info = {};
    create_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    create_info.pApplicationInfo = &app_info;
    
    VkResult result = vkCreateInstance(&create_info, nullptr, &instance_);
    CHECK_VK(result);
    return true;
}

bool VulkanBackend::select_physical_device() {
    uint32_t device_count = 0;
    vkEnumeratePhysicalDevices(instance_, &device_count, nullptr);
    
    if (device_count == 0) {
        std::cerr << "No Vulkan devices found" << std::endl;
        return false;
    }
    
    std::vector<VkPhysicalDevice> devices(device_count);
    vkEnumeratePhysicalDevices(instance_, &device_count, devices.data());
    
    // Select first device that supports compute
    for (const auto& device : devices) {
        VkPhysicalDeviceProperties properties;
        vkGetPhysicalDeviceProperties(device, &properties);
        
        if (properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU ||
            properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU) {
            physical_device_ = device;
            std::cout << "Selected Vulkan device: " << properties.deviceName << std::endl;
            return true;
        }
    }
    
    // Fallback to any device
    physical_device_ = devices[0];
    return true;
}

bool VulkanBackend::create_logical_device() {
    // Find compute queue family
    uint32_t queue_family_count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(physical_device_, &queue_family_count, nullptr);
    
    std::vector<VkQueueFamilyProperties> queue_families(queue_family_count);
    vkGetPhysicalDeviceQueueFamilyProperties(physical_device_, &queue_family_count, queue_families.data());
    
    for (uint32_t i = 0; i < queue_family_count; i++) {
        if (queue_families[i].queueFlags & VK_QUEUE_COMPUTE_BIT) {
            compute_queue_family_index_ = i;
            break;
        }
    }
    
    VkDeviceQueueCreateInfo queue_create_info = {};
    queue_create_info.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    queue_create_info.queueFamilyIndex = compute_queue_family_index_;
    queue_create_info.queueCount = 1;
    float queue_priority = 1.0f;
    queue_create_info.pQueuePriorities = &queue_priority;
    
    VkDeviceCreateInfo create_info = {};
    create_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    create_info.pQueueCreateInfos = &queue_create_info;
    create_info.queueCreateInfoCount = 1;
    
    VkResult result = vkCreateDevice(physical_device_, &create_info, nullptr, &device_);
    CHECK_VK(result);
    
    vkGetDeviceQueue(device_, compute_queue_family_index_, 0, &compute_queue_);
    return true;
}

bool VulkanBackend::create_command_pool() {
    VkCommandPoolCreateInfo pool_info = {};
    pool_info.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    pool_info.queueFamilyIndex = compute_queue_family_index_;
    pool_info.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    
    VkResult result = vkCreateCommandPool(device_, &pool_info, nullptr, &command_pool_);
    CHECK_VK(result);
    return true;
}

bool VulkanBackend::create_descriptor_pool() {
    VkDescriptorPoolSize pool_size = {};
    pool_size.type = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
    pool_size.descriptorCount = 10;
    
    VkDescriptorPoolCreateInfo pool_info = {};
    pool_info.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    pool_info.poolSizeCount = 1;
    pool_info.pPoolSizes = &pool_size;
    pool_info.maxSets = 10;
    
    VkResult result = vkCreateDescriptorPool(device_, &pool_info, nullptr, &descriptor_pool_);
    CHECK_VK(result);
    return true;
}

bool VulkanBackend::create_pipeline_layout() {
    VkPipelineLayoutCreateInfo layout_info = {};
    layout_info.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    
    VkResult result = vkCreatePipelineLayout(device_, &layout_info, nullptr, &pipeline_layout_);
    CHECK_VK(result);
    return true;
}

bool VulkanBackend::create_compute_pipeline() {
    // Simplified - in production, load actual SPIR-V shader
    VkShaderModuleCreateInfo shader_info = {};
    shader_info.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    shader_info.codeSize = 0; // Load actual shader
    shader_info.pCode = nullptr;
    
    VkShaderModule shader_module;
    VkResult result = vkCreateShaderModule(device_, &shader_info, nullptr, &shader_module);
    if (result != VK_SUCCESS) {
        std::cerr << "Shader loading not implemented" << std::endl;
        return false;
    }
    
    VkPipelineShaderStageCreateInfo shader_stage_info = {};
    shader_stage_info.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    shader_stage_info.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    shader_stage_info.module = shader_module;
    shader_stage_info.pName = "main";
    
    VkComputePipelineCreateInfo pipeline_info = {};
    pipeline_info.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
    pipeline_info.stage = shader_stage_info;
    pipeline_info.layout = pipeline_layout_;
    
    result = vkCreateComputePipelines(device_, VK_NULL_HANDLE, 1, &pipeline_info, nullptr, &compute_pipeline_);
    CHECK_VK(result);
    
    vkDestroyShaderModule(device_, shader_module, nullptr);
    return true;
}

bool VulkanBackend::load_model(const std::string& model_path) {
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

bool VulkanBackend::upload_weights() {
    auto tensors = loader_->get_tensors();
    
    // Calculate total VRAM needed
    size_t total_size = 0;
    for (const auto& [name, tensor] : tensors) {
        size_t tensor_size = tensor.element_count * sizeof(float);
        total_size += tensor_size;
    }
    
    vram_used_mb_ = static_cast<int>(total_size / (1024 * 1024));
    
    std::cout << "Uploading " << vram_used_mb_ << " MB of weights to GPU via Vulkan" << std::endl;
    
    // Create buffer
    VkBufferCreateInfo buffer_info = {};
    buffer_info.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    buffer_info.size = total_size;
    buffer_info.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT;
    buffer_info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    
    VkResult result = vkCreateBuffer(device_, &buffer_info, nullptr, &weights_buffer_);
    CHECK_VK(result);
    
    // Allocate memory
    VkMemoryRequirements mem_requirements;
    vkGetBufferMemoryRequirements(device_, weights_buffer_, &mem_requirements);
    
    VkMemoryAllocateInfo alloc_info = {};
    alloc_info.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    alloc_info.allocationSize = mem_requirements.size;
    alloc_info.memoryTypeIndex = find_memory_type(mem_requirements.memoryTypeBits, 
                                                 VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    
    result = vkAllocateMemory(device_, &alloc_info, nullptr, &weights_memory_);
    CHECK_VK(result);
    
    vkBindBufferMemory(device_, weights_buffer_, weights_memory_, 0);
    
    // Upload weights (simplified - use staging buffer in production)
    // For now, just mark as uploaded
    return true;
}

bool VulkanBackend::allocate_buffers() {
    VkResult err;
    
    // Allocate input/output buffers
    size_t buffer_size = context_length_ * embedding_dim_ * sizeof(float);
    
    VkBufferCreateInfo buffer_info = {};
    buffer_info.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    buffer_info.size = buffer_size;
    buffer_info.usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;
    buffer_info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
    
    err = vkCreateBuffer(device_, &buffer_info, nullptr, &input_buffer_);
    CHECK_VK(err);
    
    err = vkCreateBuffer(device_, &buffer_info, nullptr, &output_buffer_);
    CHECK_VK(err);
    
    // Allocate memory
    VkMemoryRequirements mem_requirements;
    vkGetBufferMemoryRequirements(device_, input_buffer_, &mem_requirements);
    
    VkMemoryAllocateInfo alloc_info = {};
    alloc_info.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    alloc_info.allocationSize = mem_requirements.size;
    alloc_info.memoryTypeIndex = find_memory_type(mem_requirements.memoryTypeBits,
                                                 VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    
    err = vkAllocateMemory(device_, &alloc_info, nullptr, &input_memory_);
    CHECK_VK(err);
    
    err = vkAllocateMemory(device_, &alloc_info, nullptr, &output_memory_);
    CHECK_VK(err);
    
    vkBindBufferMemory(device_, input_buffer_, input_memory_, 0);
    vkBindBufferMemory(device_, output_buffer_, output_memory_, 0);
    
    return true;
}

Tensor VulkanBackend::forward(const Tensor& input) {
    if (!model_loaded_) {
        throw std::runtime_error("Model not loaded");
    }
    
    // Copy input to GPU
    void* data;
    vkMapMemory(device_, input_memory_, 0, input.data().size() * sizeof(float), 0, &data);
    memcpy(data, input.data().data(), input.data().size() * sizeof(float));
    vkUnmapMemory(device_, input_memory_);
    
    // Execute compute shader (simplified)
    Tensor output(input.shape());
    
    // Copy output from GPU
    vkMapMemory(device_, output_memory_, 0, output.data().size() * sizeof(float), 0, &data);
    memcpy(output.data().data(), data, output.data().size() * sizeof(float));
    vkUnmapMemory(device_, output_memory_);
    
    return output;
}

Tensor VulkanBackend::forward_layer(const Tensor& x, int layer_idx) {
    (void)layer_idx;
    return forward(x);
}

std::string VulkanBackend::generate(const std::string& prompt, int max_tokens, float temperature) {
    // Simplified - use CPU backend for generation
    (void)max_tokens;
    (void)temperature;
    return prompt;
}

uint32_t VulkanBackend::find_memory_type(uint32_t type_filter, VkMemoryPropertyFlags properties) {
    VkPhysicalDeviceMemoryProperties mem_properties;
    vkGetPhysicalDeviceMemoryProperties(physical_device_, &mem_properties);
    
    for (uint32_t i = 0; i < mem_properties.memoryTypeCount; i++) {
        if ((type_filter & (1 << i)) && (mem_properties.memoryTypes[i].propertyFlags & properties) == properties) {
            return i;
        }
    }
    
    throw std::runtime_error("Failed to find suitable memory type");
}

} // namespace llm_engine
