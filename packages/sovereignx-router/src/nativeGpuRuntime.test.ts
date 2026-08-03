import { describe,expect,it } from 'vitest';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { collectLiveGpuTelemetry,createNativeRenderJob,dispatchNativeRenderJob,encodeNativeFrames,parseAmdAdlTelemetry,parseHardwareEncoders,parseNvidiaTelemetry,parseVulkanSummary,runtimeStatsFromTelemetry,SovereignXNativeRenderDaemon,validateNativeMeshContract } from './nativeGpuRuntime.js';

describe('native GPU runtime',()=>{
  it('validates the hashed Scene4D mesh contract before native dispatch',async()=>{
    const mesh=path.join(path.dirname(fileURLToPath(import.meta.url)),'..','meshes','clifford-torus.mesh.json');
    const contract=await validateNativeMeshContract(mesh);expect(contract).toMatchObject({id:'clifford-torus',vertexCount:1089,faceCount:2048});
  });
  it('parses live NVIDIA telemetry into router runtime stats',()=>{
    const devices=parseNvidiaTelemetry('0, GPU-1, RTX Test, 61, 75, 2048, 8192, 120, 240');
    expect(devices[0]?.utilization).toBe(.75);
    const runtime=runtimeStatsFromTelemetry({source:'nvidia-smi',trusted:true,observedAt:new Date().toISOString(),devices,errors:[]});
    expect(runtime.gpuTempC).toBe(61); expect(runtime.vramTotalBytes).toBe(8192*1024*1024);
  });
  it('accepts only bounded, explicitly trusted AMD ADL telemetry',()=>{
    const devices=parseAmdAdlTelemetry(JSON.stringify({source:'amd-adl',trusted:true,devices:[{index:0,uuid:'PCI-AMD-1',name:'Radeon',temperatureC:42,utilization:.6},{index:1,uuid:'bad',temperatureC:900,utilization:2}]}));
    expect(devices).toHaveLength(1); expect(devices[0]).toMatchObject({name:'Radeon',temperatureC:42,utilization:.6});
    expect(parseAmdAdlTelemetry(JSON.stringify({source:'amd-adl',trusted:false,devices:[{index:0,uuid:'x',temperatureC:40,utilization:.2}]}))).toEqual([]);
  });
  it('enumerates Vulkan physical devices',()=>{
    const adapters=parseVulkanSummary('\nGPU0:\n apiVersion = 1.3.280\n deviceType = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU\n deviceName = Radeon Test\n deviceUUID = abc-123\n');
    expect(adapters[0]).toMatchObject({id:'vulkan-abc-123',backend:'vulkan',deviceClass:'discrete-gpu',name:'Radeon Test'});
  });
  it('executes the native worker protocol and verifies its receipt',async()=>{
    const fixture=path.join(path.dirname(fileURLToPath(import.meta.url)),'test-fixtures','native-render-worker.mjs');
    const job=createNativeRenderJob({jobId:'job-1',sceneId:'scene',backend:'vulkan',adapterId:'gpu-1',scenePath:'scene.json',outputDir:'out',width:320,height:240,frames:3,fps:30,evidenceRefs:['evidence-1']});
    const receipt=await dispatchNativeRenderJob(job,{executable:process.execPath,args:[fixture],timeoutMs:10_000});
    expect(receipt.status).toBe('completed'); expect(receipt.deviceName).toBe('Test Vulkan Device'); expect(receipt.outputPaths).toHaveLength(3);
  });
  it('propagates cancellation to a running native worker',async()=>{
    const fixture=path.join(path.dirname(fileURLToPath(import.meta.url)),'test-fixtures','native-render-worker.mjs');
    const job={...createNativeRenderJob({jobId:'cancel-1',sceneId:'scene',backend:'vulkan',scenePath:'scene.json',outputDir:'out',width:32,height:32,frames:20,fps:30,evidenceRefs:[]}),testDelayMs:20};
    const controller=new AbortController(); setTimeout(()=>controller.abort(),50);
    await expect(dispatchNativeRenderJob(job,{executable:process.execPath,args:[fixture],signal:controller.signal,timeoutMs:10_000})).rejects.toThrow('cancelled by governance');
  });
  it('reuses one resident worker process across unrelated jobs',async()=>{
    const fixture=path.join(path.dirname(fileURLToPath(import.meta.url)),'test-fixtures','native-render-worker.mjs');
    const daemon=new SovereignXNativeRenderDaemon({executable:process.execPath,args:[fixture],timeoutMs:10_000}); const pid=daemon.processId;
    const make=(id:string)=>createNativeRenderJob({jobId:id,sceneId:id,backend:'vulkan',scenePath:'scene.json',outputDir:'out',width:32,height:32,frames:2,fps:30,evidenceRefs:[id]});
    const first=await daemon.dispatch(make('resident-1')); const second=await daemon.dispatch(make('resident-2')); await daemon.close();
    expect(daemon.processId).toBe(pid); expect(first.outputPaths).toHaveLength(2); expect(second.jobId).toBe('resident-2');
  });
  it('fails telemetry closed when the vendor source is unavailable',async()=>{
    const snapshot=await collectLiveGpuTelemetry((async()=>{throw new Error('sensor denied');}) as never);
    expect(snapshot).toMatchObject({source:'unavailable',trusted:false,devices:[]}); expect(snapshot.errors[0]).toContain('sensor denied');
    expect(runtimeStatsFromTelemetry(snapshot).gpuTempC).toBe(Number.POSITIVE_INFINITY);
  });
  it('negotiates vendor hardware encoders without assuming availability',()=>{
    expect(parseHardwareEncoders('V....D h264_amf AMD AMF H.264 encoder\nV....D hevc_nvenc NVIDIA NVENC hevc encoder')).toEqual(['h264_amf','hevc_nvenc']);
  });
  it('builds a bounded AMD AMF encode command from a native receipt',async()=>{
    const job=createNativeRenderJob({jobId:'encode-1',sceneId:'s',backend:'vulkan',scenePath:'s',outputDir:'out',width:32,height:32,frames:2,fps:24,encoding:{codec:'h264',hardwarePreferred:true},evidenceRefs:[]});
    const receipt={version:'1.0',jobId:'encode-1',status:'completed',backend:'vulkan',outputPaths:['out/vulkan-frame-000000.ppm','out/vulkan-frame-000001.ppm'],startedAt:'x',completedAt:'y',evidenceRefs:[],workerEvidenceHash:'x'} as const;
    let args:string[]=[];const encoded=await encodeNativeFrames(job,receipt,{runner:(async(_file,values)=>{args=values as string[];return {stdout:'',stderr:''};}) as never});
    expect(args).toContain('h264_amf');expect(args).toContain('24');expect(encoded.encodedPath).toContain('encode-1.mp4');
  });
});
