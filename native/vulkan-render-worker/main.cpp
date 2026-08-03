#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <vulkan/vulkan.h>

#include "../../llm-inference-engine/src/nlohmann/json.hpp"
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using json = nlohmann::json;

static std::string now_iso() {
  const auto now = std::chrono::system_clock::now();
  const auto time = std::chrono::system_clock::to_time_t(now);
  std::tm tm{};
  gmtime_s(&tm, &time);
  std::ostringstream out;
  out << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
  return out.str();
}

static std::string sha256(const std::string &value) {
  BCRYPT_ALG_HANDLE alg = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  DWORD size = 0, written = 0, object_size = 0, hash_size = 0;
  if (BCryptOpenAlgorithmProvider(&alg, BCRYPT_SHA256_ALGORITHM, nullptr, 0) <
      0)
    throw std::runtime_error("BCrypt SHA-256 unavailable");
  BCryptGetProperty(alg, BCRYPT_OBJECT_LENGTH,
                    reinterpret_cast<PUCHAR>(&object_size), sizeof(object_size),
                    &written, 0);
  BCryptGetProperty(alg, BCRYPT_HASH_LENGTH,
                    reinterpret_cast<PUCHAR>(&hash_size), sizeof(hash_size),
                    &written, 0);
  std::vector<UCHAR> object(object_size), digest(hash_size);
  if (BCryptCreateHash(alg, &hash, object.data(), object_size, nullptr, 0, 0) <
          0 ||
      BCryptHashData(hash,
                     reinterpret_cast<PUCHAR>(const_cast<char *>(value.data())),
                     static_cast<ULONG>(value.size()), 0) < 0 ||
      BCryptFinishHash(hash, digest.data(), hash_size, 0) < 0)
    throw std::runtime_error("SHA-256 failed");
  BCryptDestroyHash(hash);
  BCryptCloseAlgorithmProvider(alg, 0);
  std::ostringstream out;
  for (auto byte : digest)
    out << std::hex << std::setw(2) << std::setfill('0')
        << static_cast<int>(byte);
  return out.str();
}

static uint32_t memory_type(VkPhysicalDevice physical, uint32_t bits,
                            VkMemoryPropertyFlags flags) {
  VkPhysicalDeviceMemoryProperties props{};
  vkGetPhysicalDeviceMemoryProperties(physical, &props);
  for (uint32_t i = 0; i < props.memoryTypeCount; i++)
    if ((bits & (1u << i)) &&
        (props.memoryTypes[i].propertyFlags & flags) == flags)
      return i;
  throw std::runtime_error("no compatible Vulkan memory type");
}

static std::vector<uint32_t> load_spirv(const std::string &path) {
  std::ifstream file(path, std::ios::binary | std::ios::ate);
  if (!file)
    throw std::runtime_error("compute shader not found");
  const auto size = static_cast<size_t>(file.tellg());
  std::vector<uint32_t> code((size + 3) / 4);
  file.seekg(0);
  file.read(reinterpret_cast<char *>(code.data()), size);
  return code;
}
struct PushParams {
  uint32_t width, height;
  float time;
  uint32_t pass, vertex_count, face_count;
};
struct BufferResource { VkBuffer buffer{}; VkDeviceMemory memory{}; VkDeviceSize size{}; };
struct MeshVertex { float x,y,z,w; };
struct MeshFace { uint32_t x,y,z,pad; };
struct SharedFrameHeader { uint32_t magic,version,width,height,stride,frame_index,active_slot,slot_bytes; };

int main(int argc, char **argv) {
  std::string job_path, receipt_path;
  bool daemon = false;
  for (int i = 1; i < argc; ++i) {
    const std::string key = argv[i];
    if (key == "--daemon") daemon = true;
    else if (key == "--job" && i + 1 < argc) job_path = argv[++i];
    else if (key == "--receipt" && i + 1 < argc) receipt_path = argv[++i];
  }
  auto read_daemon_command = [&]() {
    std::string line;
    if (!std::getline(std::cin, line)) return false;
    const auto command = json::parse(line);
    job_path = command.at("jobPath").get<std::string>();
    receipt_path = command.at("receiptPath").get<std::string>();
    return true;
  };
  if (daemon && job_path.empty() && !read_daemon_command()) return 0;
  if (job_path.empty() || receipt_path.empty()) {
    std::cerr << "usage: --job file --receipt file | --daemon\n";
    return 2;
  }
  auto started = now_iso();
  try {
    std::ifstream input(job_path);
    json job;
    input >> job;
    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.pApplicationName = "SovereignX Vulkan Worker";
    app.apiVersion = VK_API_VERSION_1_1;
    VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    ici.pApplicationInfo = &app;
    VkInstance instance{};
    if (vkCreateInstance(&ici, nullptr, &instance) != VK_SUCCESS)
      throw std::runtime_error("vkCreateInstance failed");
    uint32_t count = 0;
    vkEnumeratePhysicalDevices(instance, &count, nullptr);
    if (!count)
      throw std::runtime_error("no Vulkan physical device");
    std::vector<VkPhysicalDevice> devices(count);
    vkEnumeratePhysicalDevices(instance, &count, devices.data());
    VkPhysicalDevice physical = devices[0];
    VkPhysicalDeviceProperties properties{};
    vkGetPhysicalDeviceProperties(physical, &properties);
    uint32_t family_count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(physical, &family_count, nullptr);
    std::vector<VkQueueFamilyProperties> families(family_count);
    vkGetPhysicalDeviceQueueFamilyProperties(physical, &family_count,
                                             families.data());
    uint32_t family = UINT32_MAX;
    for (uint32_t i = 0; i < family_count; i++)
      if (families[i].queueFlags & VK_QUEUE_COMPUTE_BIT) {
        family = i;
        break;
      }
    if (family == UINT32_MAX)
      throw std::runtime_error("no Vulkan compute queue");
    float priority = 1;
    VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    qci.queueFamilyIndex = family;
    qci.queueCount = 1;
    qci.pQueuePriorities = &priority;
    VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    dci.queueCreateInfoCount = 1;
    dci.pQueueCreateInfos = &qci;
    VkDevice device{};
    if (vkCreateDevice(physical, &dci, nullptr, &device) != VK_SUCCESS)
      throw std::runtime_error("vkCreateDevice failed");
    constexpr uint32_t max_width=7680,max_height=4320,max_vertices=262144,max_faces=524288;
    const VkDeviceSize buffer_size=static_cast<VkDeviceSize>(max_width)*max_height*4;
    auto create_buffer=[&](VkDeviceSize size){BufferResource out{};out.size=size;VkBufferCreateInfo info{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};info.size=size;info.usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;info.sharingMode=VK_SHARING_MODE_EXCLUSIVE;if(vkCreateBuffer(device,&info,nullptr,&out.buffer)!=VK_SUCCESS)throw std::runtime_error("storage buffer creation failed");VkMemoryRequirements req{};vkGetBufferMemoryRequirements(device,out.buffer,&req);VkMemoryAllocateInfo alloc{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};alloc.allocationSize=req.size;alloc.memoryTypeIndex=memory_type(physical,req.memoryTypeBits,VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);if(vkAllocateMemory(device,&alloc,nullptr,&out.memory)!=VK_SUCCESS)throw std::runtime_error("storage memory allocation failed");vkBindBufferMemory(device,out.buffer,out.memory,0);return out;};
    auto pixel_buffer=create_buffer(buffer_size),depth_buffer=create_buffer(buffer_size);
    auto vertex_buffer=create_buffer(static_cast<VkDeviceSize>(max_vertices)*sizeof(MeshVertex));
    auto face_buffer=create_buffer(static_cast<VkDeviceSize>(max_faces)*sizeof(MeshFace));
    VkDescriptorSetLayoutBinding bindings[4]{};
    for(uint32_t i=0;i<4;i++){bindings[i].binding=i;bindings[i].descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;bindings[i].descriptorCount=1;bindings[i].stageFlags=VK_SHADER_STAGE_COMPUTE_BIT;}
    VkDescriptorSetLayoutCreateInfo lci{
        VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    lci.bindingCount = 4;
    lci.pBindings = bindings;
    VkDescriptorSetLayout set_layout{};
    vkCreateDescriptorSetLayout(device, &lci, nullptr, &set_layout);
    VkPushConstantRange range{VK_SHADER_STAGE_COMPUTE_BIT, 0,
                              sizeof(PushParams)};
    VkPipelineLayoutCreateInfo plci{
        VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    plci.setLayoutCount = 1;
    plci.pSetLayouts = &set_layout;
    plci.pushConstantRangeCount = 1;
    plci.pPushConstantRanges = &range;
    VkPipelineLayout pipeline_layout{};
    vkCreatePipelineLayout(device, &plci, nullptr, &pipeline_layout);
    const auto code = load_spirv(SOVEREIGNX_SHADER_PATH);
    VkShaderModuleCreateInfo smci{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
    smci.codeSize = code.size() * 4;
    smci.pCode = code.data();
    VkShaderModule shader{};
    vkCreateShaderModule(device, &smci, nullptr, &shader);
    VkPipelineShaderStageCreateInfo stage{
        VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};
    stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    stage.module = shader;
    stage.pName = "main";
    VkComputePipelineCreateInfo cpci{
        VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
    cpci.stage = stage;
    cpci.layout = pipeline_layout;
    VkPipeline pipeline{};
    if (vkCreateComputePipelines(device, VK_NULL_HANDLE, 1, &cpci, nullptr,
                                 &pipeline) != VK_SUCCESS)
      throw std::runtime_error("compute pipeline creation failed");
    VkDescriptorPoolSize pool_size{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 4};
    VkDescriptorPoolCreateInfo dpci{
        VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    dpci.maxSets = 1;
    dpci.poolSizeCount = 1;
    dpci.pPoolSizes = &pool_size;
    VkDescriptorPool descriptor_pool{};
    vkCreateDescriptorPool(device, &dpci, nullptr, &descriptor_pool);
    VkDescriptorSetAllocateInfo dsai{
        VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
    dsai.descriptorPool = descriptor_pool;
    dsai.descriptorSetCount = 1;
    dsai.pSetLayouts = &set_layout;
    VkDescriptorSet descriptor{};
    vkAllocateDescriptorSets(device, &dsai, &descriptor);
    BufferResource resources[4]={pixel_buffer,depth_buffer,vertex_buffer,face_buffer};VkDescriptorBufferInfo infos[4]{};VkWriteDescriptorSet writes[4]{};
    for(uint32_t i=0;i<4;i++){infos[i]={resources[i].buffer,0,resources[i].size};writes[i]={VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};writes[i].dstSet=descriptor;writes[i].dstBinding=i;writes[i].descriptorCount=1;writes[i].descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;writes[i].pBufferInfo=&infos[i];}
    vkUpdateDescriptorSets(device,4,writes,0,nullptr);
    VkCommandPoolCreateInfo pci{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    pci.queueFamilyIndex = family;
    pci.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    VkCommandPool pool{};
    vkCreateCommandPool(device, &pci, nullptr, &pool);
    VkCommandBufferAllocateInfo cai{
        VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    cai.commandPool = pool;
    cai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cai.commandBufferCount = 1;
    VkCommandBuffer command{};
    vkAllocateCommandBuffers(device, &cai, &command);
    VkQueue queue{};
    vkGetDeviceQueue(device, family, 0, &queue);
    while (true) {
    const uint32_t width = job.value("width", 640u), height = job.value("height", 480u);
    if (!width || !height || width > max_width || height > max_height)
      throw std::runtime_error("frame dimensions exceed resident worker limits");
    std::string surface_id = job.value("surfaceId", "clifford-torus");
    json mesh_contract;
    if (job.contains("meshPath") && !job["meshPath"].get<std::string>().empty()) {
      std::ifstream mesh_input(job["meshPath"].get<std::string>());
      mesh_input >> mesh_contract;
      if (mesh_contract.value("contractVersion", "") != "1.0" || mesh_contract.value("source", "") != "4d-renderer" ||
          !mesh_contract.contains("vertices") || !mesh_contract.contains("faces") ||
          mesh_contract["vertices"].size() != mesh_contract.value("vertexCount", 0u) || mesh_contract["faces"].size() != mesh_contract.value("faceCount", 0u))
        throw std::runtime_error("invalid Scene4D native mesh contract");
      surface_id = mesh_contract.value("id", surface_id);
    }
    if (mesh_contract.is_null()) throw std::runtime_error("meshPath is required for native triangle rasterization");
    std::vector<MeshVertex> mesh_vertices;std::vector<MeshFace> mesh_faces;
    if(mesh_contract["vertices"].size()>max_vertices||mesh_contract["faces"].size()>max_faces)throw std::runtime_error("Scene4D mesh exceeds resident GPU buffer capacity");
    for(const auto& v:mesh_contract["vertices"])mesh_vertices.push_back({v["x"].get<float>(),v["y"].get<float>(),v["z"].get<float>(),v["w"].get<float>()});
    for(const auto& f:mesh_contract["faces"])mesh_faces.push_back({f[0].get<uint32_t>(),f[1].get<uint32_t>(),f[2].get<uint32_t>(),0});
    void* upload=nullptr;vkMapMemory(device,vertex_buffer.memory,0,mesh_vertices.size()*sizeof(MeshVertex),0,&upload);std::memcpy(upload,mesh_vertices.data(),mesh_vertices.size()*sizeof(MeshVertex));vkUnmapMemory(device,vertex_buffer.memory);
    vkMapMemory(device,face_buffer.memory,0,mesh_faces.size()*sizeof(MeshFace),0,&upload);std::memcpy(upload,mesh_faces.data(),mesh_faces.size()*sizeof(MeshFace));vkUnmapMemory(device,face_buffer.memory);
    std::filesystem::create_directories(job["outputDir"].get<std::string>());
    json artifacts = json::array();
    const uint32_t frames = job.value("frames", 1u);
    const float fps = static_cast<float>(job.value("fps", 30u));
    const std::string cancel_path = job.value("cancellationPath", "");
    bool cancelled = false;
    for (uint32_t frame_index = 0; frame_index < frames; ++frame_index) {
      if (!cancel_path.empty() && std::filesystem::exists(cancel_path)) {
        if (daemon) { cancelled = true; break; }
        throw std::runtime_error("render cancelled by governance");
      }
      vkResetCommandBuffer(command, 0);
      PushParams params{width,height,job.value("time",0.0f)+frame_index/fps,0u,static_cast<uint32_t>(mesh_vertices.size()),static_cast<uint32_t>(mesh_faces.size())};
      VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
      vkBeginCommandBuffer(command, &begin);
      vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_COMPUTE, pipeline);
      vkCmdBindDescriptorSets(command, VK_PIPELINE_BIND_POINT_COMPUTE,
                              pipeline_layout, 0, 1, &descriptor, 0, nullptr);
      vkCmdPushConstants(command, pipeline_layout, VK_SHADER_STAGE_COMPUTE_BIT,
                         0, sizeof(params), &params);
      vkCmdDispatch(command,(width*height+63)/64,1,1);
      VkMemoryBarrier barrier{VK_STRUCTURE_TYPE_MEMORY_BARRIER};barrier.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;barrier.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;
      vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&barrier,0,nullptr,0,nullptr);
      params.pass=1u;vkCmdPushConstants(command,pipeline_layout,VK_SHADER_STAGE_COMPUTE_BIT,0,sizeof(params),&params);
      vkCmdDispatch(command,(params.face_count+63)/64,1,1);
      vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&barrier,0,nullptr,0,nullptr);
      params.pass=2u;vkCmdPushConstants(command,pipeline_layout,VK_SHADER_STAGE_COMPUTE_BIT,0,sizeof(params),&params);
      vkCmdDispatch(command,(params.face_count+63)/64,1,1);
      vkEndCommandBuffer(command);
      VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
      submit.commandBufferCount = 1;
      submit.pCommandBuffers = &command;
      vkQueueSubmit(queue, 1, &submit, VK_NULL_HANDLE);
      vkQueueWaitIdle(queue);
      void *mapped = nullptr;
      vkMapMemory(device, pixel_buffer.memory, 0, buffer_size, 0, &mapped);
      const auto *pixels = static_cast<const uint32_t *>(mapped);
      uint64_t checksum = 0;
      for (size_t i = 0; i < static_cast<size_t>(width) * height; i++) checksum += pixels[i];
      if (!checksum) throw std::runtime_error("Vulkan frame checksum is zero");
      std::ostringstream name;
      name << "vulkan-frame-" << std::setw(6) << std::setfill('0') << frame_index << ".ppm";
      const auto artifact = (std::filesystem::path(job["outputDir"].get<std::string>()) / name.str()).string();
      std::ofstream frame(artifact, std::ios::binary);
      frame << "P6\n" << width << " " << height << "\n255\n";
      for (size_t i = 0; i < static_cast<size_t>(width) * height; i++) {
        const uint32_t p = pixels[i];
        const char rgb[3] = {static_cast<char>(p & 255), static_cast<char>((p >> 8) & 255), static_cast<char>((p >> 16) & 255)};
        frame.write(rgb, 3);
      }
      frame.close();
      const std::string shared_path=job.value("sharedFramePath","");
      if(!shared_path.empty()){
        const uint32_t slot_bytes=width*height*4,slot=frame_index%2;const uint64_t total=sizeof(SharedFrameHeader)+uint64_t(slot_bytes)*2;
        if(!std::filesystem::exists(shared_path)){std::filesystem::create_directories(std::filesystem::path(shared_path).parent_path());std::ofstream create(shared_path,std::ios::binary);create.seekp(static_cast<std::streamoff>(total-1));create.put(0);}
        std::fstream shared(shared_path,std::ios::binary|std::ios::in|std::ios::out);shared.seekp(sizeof(SharedFrameHeader)+uint64_t(slot)*slot_bytes);shared.write(static_cast<const char*>(mapped),slot_bytes);shared.flush();
        SharedFrameHeader header{0x58524653u,1u,width,height,width*4,frame_index,slot,slot_bytes};shared.seekp(0);shared.write(reinterpret_cast<const char*>(&header),sizeof(header));shared.flush();
      }
      vkUnmapMemory(device, pixel_buffer.memory);
      artifacts.push_back(artifact);
      if (daemon) std::cout << json({{"event","frame"},{"jobId",job["jobId"]},{"frameIndex",frame_index},{"outputPath",artifact},{"sharedFramePath",shared_path}}).dump() << std::endl;
    }
    json receipt = {{"version", "1.0"},
                    {"jobId", job["jobId"]},
                    {"status", cancelled ? "failed" : "completed"},
                    {"backend", job["backend"]},
                    {"adapterId", job.value("adapterId", "")},
                    {"deviceName", properties.deviceName},
                    {"outputPaths", artifacts},
                    {"startedAt", started},
                    {"completedAt", now_iso()},
                    {"evidenceRefs", job["evidenceRefs"]}};
    if (cancelled) receipt["error"] = "render cancelled by governance";
    if (!mesh_contract.is_null()) {
      receipt["meshContract"] = {{"id", mesh_contract["id"]}, {"vertexCount", mesh_contract["vertexCount"]},
                                 {"faceCount", mesh_contract["faceCount"]}, {"contentHash", mesh_contract["contentHash"]}};
    }
    json evidence = {{"adapterId", receipt["adapterId"]},
                     {"backend", receipt["backend"]},
                     {"evidenceRefs", receipt["evidenceRefs"]},
                     {"jobId", receipt["jobId"]},
                     {"outputPaths", receipt["outputPaths"]}};
    receipt["workerEvidenceHash"] = sha256(evidence.dump());
    std::ofstream output(receipt_path);
    output << receipt.dump(2);
    output.close();
    if (!daemon) break;
    std::cout << json({{"event","receipt"},{"jobId",job["jobId"]},{"receiptPath",receipt_path}}).dump() << std::endl;
    if (!read_daemon_command()) break;
    std::ifstream next_input(job_path);
    next_input >> job;
    started = now_iso();
    }
    vkDeviceWaitIdle(device);
    vkDestroyDescriptorPool(device, descriptor_pool, nullptr);
    vkDestroyPipeline(device, pipeline, nullptr);
    vkDestroyShaderModule(device, shader, nullptr);
    vkDestroyPipelineLayout(device, pipeline_layout, nullptr);
    vkDestroyDescriptorSetLayout(device, set_layout, nullptr);
    vkDestroyCommandPool(device, pool, nullptr);
    for(auto& resource:resources){vkDestroyBuffer(device,resource.buffer,nullptr);vkFreeMemory(device,resource.memory,nullptr);}
    vkDestroyDevice(device, nullptr);
    vkDestroyInstance(instance, nullptr);
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << "\n";
    return 1;
  }
}
