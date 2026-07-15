#pragma once

#include <cstddef>
#include <cstdint>

extern "C" {

typedef std::int32_t cl_int;
typedef std::uint32_t cl_uint;
typedef std::uint64_t cl_bitfield;
typedef cl_bitfield cl_device_type;
typedef cl_bitfield cl_mem_flags;
typedef cl_bitfield cl_command_queue_properties;
typedef std::size_t cl_bool;

struct _cl_platform_id;
struct _cl_device_id;
struct _cl_context;
struct _cl_command_queue;
struct _cl_program;
struct _cl_kernel;
struct _cl_mem;

typedef _cl_platform_id* cl_platform_id;
typedef _cl_device_id* cl_device_id;
typedef _cl_context* cl_context;
typedef _cl_command_queue* cl_command_queue;
typedef _cl_program* cl_program;
typedef _cl_kernel* cl_kernel;
typedef _cl_mem* cl_mem;

typedef std::intptr_t cl_platform_info;
typedef std::intptr_t cl_device_info;
typedef std::intptr_t cl_program_build_info;

typedef std::uintptr_t cl_context_properties;

typedef struct _cl_context {
    int reserved;
} _cl_context;

typedef struct _cl_command_queue {
    int reserved;
} _cl_command_queue;

typedef struct _cl_program {
    int reserved;
} _cl_program;

typedef struct _cl_kernel {
    int reserved;
} _cl_kernel;

typedef struct _cl_mem {
    void* storage;
    std::size_t size;
} _cl_mem;

typedef struct _cl_platform_id {
    int reserved;
} _cl_platform_id;

typedef struct _cl_device_id {
    int reserved;
} _cl_device_id;

#define CL_SUCCESS 0
#define CL_DEVICE_NOT_FOUND -1
#define CL_PLATFORM_NOT_FOUND_KHR -1001

#define CL_DEVICE_TYPE_CPU (1ULL << 1)
#define CL_DEVICE_TYPE_GPU (1ULL << 2)

#define CL_MEM_READ_ONLY (1ULL << 0)
#define CL_MEM_READ_WRITE (1ULL << 1)

#define CL_TRUE 1

#define CL_PROGRAM_BUILD_LOG 0x1183

static inline cl_int clGetPlatformIDs(cl_uint, cl_platform_id*, cl_uint* num_platforms) {
    if (num_platforms != nullptr) {
        *num_platforms = 0;
    }
    return CL_PLATFORM_NOT_FOUND_KHR;
}

static inline cl_int clGetDeviceIDs(cl_platform_id, cl_device_type, cl_uint, cl_device_id*, cl_uint* num_devices) {
    if (num_devices != nullptr) {
        *num_devices = 0;
    }
    return CL_DEVICE_NOT_FOUND;
}

static inline cl_context clCreateContext(const cl_context_properties*, cl_uint, const cl_device_id*, void*, void*, cl_int* errcode_ret) {
    if (errcode_ret != nullptr) {
        *errcode_ret = CL_PLATFORM_NOT_FOUND_KHR;
    }
    return nullptr;
}

static inline cl_command_queue clCreateCommandQueue(cl_context, cl_device_id, cl_command_queue_properties, cl_int* errcode_ret) {
    if (errcode_ret != nullptr) {
        *errcode_ret = CL_PLATFORM_NOT_FOUND_KHR;
    }
    return nullptr;
}

static inline cl_program clCreateProgramWithSource(cl_context, cl_uint, const char**, const std::size_t*, cl_int* errcode_ret) {
    if (errcode_ret != nullptr) {
        *errcode_ret = CL_PLATFORM_NOT_FOUND_KHR;
    }
    return nullptr;
}

static inline cl_int clBuildProgram(cl_program, cl_uint, const cl_device_id*, const char*, void*, void*) {
    return CL_PLATFORM_NOT_FOUND_KHR;
}

static inline cl_kernel clCreateKernel(cl_program, const char*, cl_int* errcode_ret) {
    if (errcode_ret != nullptr) {
        *errcode_ret = CL_PLATFORM_NOT_FOUND_KHR;
    }
    return nullptr;
}

static inline cl_int clGetProgramBuildInfo(cl_program, cl_device_id, cl_program_build_info, std::size_t, void*, std::size_t*) {
    return CL_PLATFORM_NOT_FOUND_KHR;
}

static inline cl_mem clCreateBuffer(cl_context, cl_mem_flags, std::size_t, void*, cl_int* errcode_ret) {
    if (errcode_ret != nullptr) {
        *errcode_ret = CL_PLATFORM_NOT_FOUND_KHR;
    }
    return nullptr;
}

static inline cl_int clEnqueueWriteBuffer(cl_command_queue, cl_mem, cl_bool, std::size_t, std::size_t, const void*, cl_uint, const void*, void*) {
    return CL_PLATFORM_NOT_FOUND_KHR;
}

static inline cl_int clEnqueueReadBuffer(cl_command_queue, cl_mem, cl_bool, std::size_t, std::size_t, void*, cl_uint, const void*, void*) {
    return CL_PLATFORM_NOT_FOUND_KHR;
}

static inline cl_int clReleaseKernel(cl_kernel) {
    return CL_SUCCESS;
}

static inline cl_int clReleaseProgram(cl_program) {
    return CL_SUCCESS;
}

static inline cl_int clReleaseCommandQueue(cl_command_queue) {
    return CL_SUCCESS;
}

static inline cl_int clReleaseContext(cl_context) {
    return CL_SUCCESS;
}

static inline cl_int clReleaseMemObject(cl_mem) {
    return CL_SUCCESS;
}

} // extern "C"
