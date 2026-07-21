#pragma once

#include <cstddef>
#include <cstdint>

typedef std::int32_t VkResult;
typedef std::uint64_t VkDeviceSize;
typedef std::uint32_t VkFlags;
typedef std::uint32_t VkBool32;

typedef void* VkInstance;
typedef void* VkPhysicalDevice;
typedef void* VkDevice;
typedef void* VkQueue;
typedef void* VkCommandPool;
typedef void* VkDescriptorPool;
typedef void* VkPipelineLayout;
typedef void* VkPipeline;
typedef void* VkBuffer;
typedef void* VkDeviceMemory;
typedef void* VkShaderModule;
typedef void* VkCommandBuffer;

typedef VkFlags VkStructureType;
typedef VkFlags VkQueueFlags;
typedef VkFlags VkBufferUsageFlags;
typedef VkFlags VkSharingMode;
typedef VkFlags VkDescriptorType;
typedef VkFlags VkMemoryPropertyFlags;
typedef VkFlags VkCommandPoolCreateFlags;
typedef VkFlags VkPipelineCreateFlags;
typedef VkFlags VkShaderStageFlags;

static constexpr std::nullptr_t VK_NULL_HANDLE = nullptr;
static constexpr VkResult VK_SUCCESS = 0;
static constexpr VkResult VK_ERROR_INITIALIZATION_FAILED = -3;
static constexpr VkResult VK_ERROR_FEATURE_NOT_PRESENT = -8;

static constexpr VkStructureType VK_STRUCTURE_TYPE_APPLICATION_INFO = 0;
static constexpr VkStructureType VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO = 1;
static constexpr VkStructureType VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO = 2;
static constexpr VkStructureType VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO = 3;
static constexpr VkStructureType VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO = 4;
static constexpr VkStructureType VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO = 5;
static constexpr VkStructureType VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO = 6;
static constexpr VkStructureType VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO = 7;
static constexpr VkStructureType VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO = 8;
static constexpr VkStructureType VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO = 9;
static constexpr VkStructureType VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO = 10;
static constexpr VkStructureType VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO = 11;

static constexpr std::uint32_t VK_QUEUE_COMPUTE_BIT = 0x00000002u;
static constexpr std::uint32_t VK_DESCRIPTOR_TYPE_STORAGE_BUFFER = 7u;
static constexpr std::uint32_t VK_BUFFER_USAGE_STORAGE_BUFFER_BIT = 0x00000020u;
static constexpr std::uint32_t VK_BUFFER_USAGE_TRANSFER_DST_BIT = 0x00000002u;
static constexpr std::uint32_t VK_SHARING_MODE_EXCLUSIVE = 0u;
static constexpr std::uint32_t VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT = 0x00000002u;
static constexpr std::uint32_t VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT = 0x00000001u;
static constexpr std::uint32_t VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT = 0x00000002u;
static constexpr std::uint32_t VK_MEMORY_PROPERTY_HOST_COHERENT_BIT = 0x00000004u;
static constexpr std::uint32_t VK_SHADER_STAGE_COMPUTE_BIT = 0x00000020u;

static constexpr std::uint32_t VK_PHYSICAL_DEVICE_TYPE_OTHER = 0u;
static constexpr std::uint32_t VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU = 1u;
static constexpr std::uint32_t VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU = 2u;

static constexpr std::uint32_t VK_API_VERSION_1_0 = 1u;

#define VK_MAKE_VERSION(major, minor, patch) (((major) << 22) | ((minor) << 12) | (patch))

typedef struct VkApplicationInfo {
    VkStructureType sType;
    const void* pNext;
    const char* pApplicationName;
    std::uint32_t applicationVersion;
    const char* pEngineName;
    std::uint32_t engineVersion;
    std::uint32_t apiVersion;
} VkApplicationInfo;

typedef struct VkInstanceCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkFlags flags;
    const VkApplicationInfo* pApplicationInfo;
    std::uint32_t enabledLayerCount;
    const char* const* ppEnabledLayerNames;
    std::uint32_t enabledExtensionCount;
    const char* const* ppEnabledExtensionNames;
} VkInstanceCreateInfo;

typedef struct VkPhysicalDeviceProperties {
    std::uint32_t deviceType;
    char deviceName[256];
} VkPhysicalDeviceProperties;

typedef struct VkQueueFamilyProperties {
    VkQueueFlags queueFlags;
} VkQueueFamilyProperties;

typedef struct VkDeviceQueueCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkFlags flags;
    std::uint32_t queueFamilyIndex;
    std::uint32_t queueCount;
    const float* pQueuePriorities;
} VkDeviceQueueCreateInfo;

typedef struct VkDeviceCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkFlags flags;
    std::uint32_t queueCreateInfoCount;
    const VkDeviceQueueCreateInfo* pQueueCreateInfos;
    std::uint32_t enabledLayerCount;
    const char* const* ppEnabledLayerNames;
    std::uint32_t enabledExtensionCount;
    const char* const* ppEnabledExtensionNames;
    const void* pEnabledFeatures;
} VkDeviceCreateInfo;

typedef struct VkCommandPoolCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkCommandPoolCreateFlags flags;
    std::uint32_t queueFamilyIndex;
} VkCommandPoolCreateInfo;

typedef struct VkDescriptorPoolSize {
    VkDescriptorType type;
    std::uint32_t descriptorCount;
} VkDescriptorPoolSize;

typedef struct VkDescriptorPoolCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkFlags flags;
    std::uint32_t maxSets;
    std::uint32_t poolSizeCount;
    const VkDescriptorPoolSize* pPoolSizes;
} VkDescriptorPoolCreateInfo;

typedef struct VkPipelineLayoutCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkFlags flags;
} VkPipelineLayoutCreateInfo;

typedef struct VkShaderModuleCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkFlags flags;
    std::size_t codeSize;
    const std::uint32_t* pCode;
} VkShaderModuleCreateInfo;

typedef struct VkPipelineShaderStageCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkFlags flags;
    VkShaderStageFlags stage;
    VkShaderModule module;
    const char* pName;
} VkPipelineShaderStageCreateInfo;

typedef struct VkComputePipelineCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkPipelineCreateFlags flags;
    VkPipelineShaderStageCreateInfo stage;
    VkPipelineLayout layout;
    VkPipeline basePipelineHandle;
    std::int32_t basePipelineIndex;
} VkComputePipelineCreateInfo;

typedef struct VkBufferCreateInfo {
    VkStructureType sType;
    const void* pNext;
    VkFlags flags;
    VkDeviceSize size;
    VkBufferUsageFlags usage;
    VkSharingMode sharingMode;
    std::uint32_t queueFamilyIndexCount;
    const std::uint32_t* pQueueFamilyIndices;
} VkBufferCreateInfo;

typedef struct VkMemoryRequirements {
    VkDeviceSize size;
    std::uint32_t memoryTypeBits;
} VkMemoryRequirements;

typedef struct VkMemoryAllocateInfo {
    VkStructureType sType;
    const void* pNext;
    VkDeviceSize allocationSize;
    std::uint32_t memoryTypeIndex;
} VkMemoryAllocateInfo;

typedef struct VkPhysicalDeviceMemoryProperties {
    std::uint32_t memoryTypeCount;
    struct {
        VkMemoryPropertyFlags propertyFlags;
    } memoryTypes[16];
} VkPhysicalDeviceMemoryProperties;

static inline VkResult vkCreateInstance(const VkInstanceCreateInfo*, const void*, VkInstance*) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkDestroyInstance(VkInstance, const void*) {}

static inline VkResult vkEnumeratePhysicalDevices(VkInstance, std::uint32_t* deviceCount, VkPhysicalDevice*) {
    if (deviceCount != nullptr) {
        *deviceCount = 0;
    }
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkGetPhysicalDeviceProperties(VkPhysicalDevice, VkPhysicalDeviceProperties* properties) {
    if (properties != nullptr) {
        properties->deviceType = VK_PHYSICAL_DEVICE_TYPE_OTHER;
        properties->deviceName[0] = '\0';
    }
}

static inline void vkGetPhysicalDeviceQueueFamilyProperties(VkPhysicalDevice, std::uint32_t* count, VkQueueFamilyProperties* properties) {
    if (count != nullptr) {
        *count = 0;
    }
    if (properties != nullptr) {
        properties[0].queueFlags = 0;
    }
}

static inline VkResult vkCreateDevice(VkPhysicalDevice, const VkDeviceCreateInfo*, const void*, VkDevice*) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkDestroyDevice(VkDevice, const void*) {}

static inline void vkGetDeviceQueue(VkDevice, std::uint32_t, std::uint32_t, VkQueue*) {}

static inline VkResult vkCreateCommandPool(VkDevice, const VkCommandPoolCreateInfo*, const void*, VkCommandPool*) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkDestroyCommandPool(VkDevice, VkCommandPool, const void*) {}

static inline VkResult vkCreateDescriptorPool(VkDevice, const VkDescriptorPoolCreateInfo*, const void*, VkDescriptorPool*) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkDestroyDescriptorPool(VkDevice, VkDescriptorPool, const void*) {}

static inline VkResult vkCreatePipelineLayout(VkDevice, const VkPipelineLayoutCreateInfo*, const void*, VkPipelineLayout*) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkDestroyPipelineLayout(VkDevice, VkPipelineLayout, const void*) {}

static inline VkResult vkCreateShaderModule(VkDevice, const VkShaderModuleCreateInfo*, const void*, VkShaderModule*) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkDestroyShaderModule(VkDevice, VkShaderModule, const void*) {}

static inline VkResult vkCreateComputePipelines(VkDevice, VkPipeline, std::uint32_t, const VkComputePipelineCreateInfo*, const void*, VkPipeline*) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkDestroyPipeline(VkDevice, VkPipeline, const void*) {}

static inline VkResult vkCreateBuffer(VkDevice, const VkBufferCreateInfo*, const void*, VkBuffer*) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkDestroyBuffer(VkDevice, VkBuffer, const void*) {}

static inline void vkGetBufferMemoryRequirements(VkDevice, VkBuffer, VkMemoryRequirements* requirements) {
    if (requirements != nullptr) {
        requirements->size = 0;
        requirements->memoryTypeBits = 0;
    }
}

static inline VkResult vkAllocateMemory(VkDevice, const VkMemoryAllocateInfo*, const void*, VkDeviceMemory*) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkFreeMemory(VkDevice, VkDeviceMemory, const void*) {}

static inline VkResult vkBindBufferMemory(VkDevice, VkBuffer, VkDeviceMemory, VkDeviceSize) {
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline VkResult vkMapMemory(VkDevice, VkDeviceMemory, VkDeviceSize, VkDeviceSize, VkFlags, void** data) {
    if (data != nullptr) {
        *data = nullptr;
    }
    return VK_ERROR_INITIALIZATION_FAILED;
}

static inline void vkUnmapMemory(VkDevice, VkDeviceMemory) {}

static inline void vkGetPhysicalDeviceMemoryProperties(VkPhysicalDevice, VkPhysicalDeviceMemoryProperties* properties) {
    if (properties != nullptr) {
        properties->memoryTypeCount = 0;
    }
}
