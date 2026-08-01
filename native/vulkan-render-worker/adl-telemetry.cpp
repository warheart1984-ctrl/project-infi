#define NOMINMAX
#include <windows.h>
#include "../../llm-inference-engine/src/nlohmann/json.hpp"
#include <cstdlib>
#include <iostream>
#include <set>
#include <vector>

using json = nlohmann::json;
constexpr int ADL_OK = 0;
constexpr int ADL_MAX_PATH = 256;

struct AdapterInfo {
  int iSize, iAdapterIndex; char strUDID[ADL_MAX_PATH];
  int iBusNumber, iDeviceNumber, iFunctionNumber, iVendorID;
  char strAdapterName[ADL_MAX_PATH], strDisplayName[ADL_MAX_PATH];
  int iPresent, iExist; char strDriverPath[ADL_MAX_PATH], strDriverPathExt[ADL_MAX_PATH], strPNPString[ADL_MAX_PATH];
  int iOSDisplayIndex;
};
struct ADLTemperature { int iSize, iTemperature; };
struct ADLPMActivity {
  int iSize, iEngineClock, iMemoryClock, iVddc, iActivityPercent;
  int iCurrentPerformanceLevel, iCurrentBusSpeed, iCurrentBusLanes, iMaximumBusLanes, iReserved;
};

static void* __stdcall adl_alloc(int bytes) { return std::malloc(static_cast<size_t>(bytes)); }
template<typename T> static T symbol(HMODULE module, const char* name) {
  auto value = reinterpret_cast<T>(GetProcAddress(module, name));
  if (!value) throw std::runtime_error(std::string("ADL export unavailable: ") + name);
  return value;
}

int main() {
  HMODULE module = LoadLibraryW(L"atiadlxx.dll");
  if (!module) { std::cerr << "AMD ADL library unavailable\n"; return 2; }
  using Create = int(__stdcall*)(void*(__stdcall*)(int), int);
  using Destroy = int(__stdcall*)();
  using Count = int(__stdcall*)(int*);
  using Info = int(__stdcall*)(AdapterInfo*, int);
  using Temperature = int(__stdcall*)(int, int, ADLTemperature*);
  using Activity = int(__stdcall*)(int, ADLPMActivity*);
  try {
    const auto create=symbol<Create>(module,"ADL_Main_Control_Create");
    const auto destroy=symbol<Destroy>(module,"ADL_Main_Control_Destroy");
    const auto count_fn=symbol<Count>(module,"ADL_Adapter_NumberOfAdapters_Get");
    const auto info_fn=symbol<Info>(module,"ADL_Adapter_AdapterInfo_Get");
    const auto temp_fn=symbol<Temperature>(module,"ADL_Overdrive5_Temperature_Get");
    const auto activity_fn=symbol<Activity>(module,"ADL_Overdrive5_CurrentActivity_Get");
    if (create(adl_alloc, 1) != ADL_OK) throw std::runtime_error("ADL initialization failed");
    int count=0; if(count_fn(&count)!=ADL_OK || count<=0) throw std::runtime_error("ADL returned no adapters");
    std::vector<AdapterInfo> adapters(static_cast<size_t>(count));
    for(auto& adapter:adapters) adapter.iSize=sizeof(AdapterInfo);
    if(info_fn(adapters.data(), static_cast<int>(adapters.size()*sizeof(AdapterInfo)))!=ADL_OK) throw std::runtime_error("ADL adapter query failed");
    json devices=json::array();
    std::set<std::string> physical_devices;
    for(const auto& adapter:adapters) {
      if(!adapter.iPresent || (adapter.iVendorID!=1002 && adapter.iVendorID!=0x1002)) continue;
      const auto physical_key=std::to_string(adapter.iBusNumber)+":"+std::to_string(adapter.iDeviceNumber)+":"+std::to_string(adapter.iFunctionNumber);
      if(!physical_devices.insert(physical_key).second) continue;
      ADLTemperature temperature{sizeof(ADLTemperature),0}; ADLPMActivity activity{}; activity.iSize=sizeof(ADLPMActivity);
      const bool has_temp=temp_fn(adapter.iAdapterIndex,0,&temperature)==ADL_OK;
      const bool has_activity=activity_fn(adapter.iAdapterIndex,&activity)==ADL_OK;
      if(!has_temp || !has_activity || temperature.iTemperature<0 || temperature.iTemperature>150000 || activity.iActivityPercent<0 || activity.iActivityPercent>100) continue;
      devices.push_back({{"index",adapter.iAdapterIndex},{"uuid",adapter.strUDID},{"name",adapter.strAdapterName},{"temperatureC",temperature.iTemperature/1000.0},{"utilization",activity.iActivityPercent/100.0},{"coreClockMhz",activity.iEngineClock/100.0},{"memoryClockMhz",activity.iMemoryClock/100.0},{"voltageV",activity.iVddc/1000.0}});
    }
    destroy(); FreeLibrary(module);
    if(devices.empty()) { std::cerr << "ADL returned no fully validated AMD sensors\n"; return 3; }
    std::cout << json({{"version","1.0"},{"source","amd-adl"},{"trusted",true},{"devices",devices}}).dump();
    return 0;
  } catch(const std::exception& error) { std::cerr << error.what() << '\n'; FreeLibrary(module); return 1; }
}
