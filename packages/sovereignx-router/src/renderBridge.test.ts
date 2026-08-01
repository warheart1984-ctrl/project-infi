import { describe, expect, it } from 'vitest';
import { registerSovereignXRenderIntent, routeSovereignXRender } from './renderBridge.js';
import { SovereignXRouter } from './SovereignXRouter.js';
import type { GovernanceLimits, RuntimeStats } from './types.js';

const limits: GovernanceLimits = { maxGpuJobs:2,maxCpuJobs:8,maxConcurrentJobs:4,maxGpuTempC:80,maxVramBytes:8e9,maxTokensPerAgentPerMin:1000,maxFlopsPerAgentPerMin:1e12 };
const runtime: RuntimeStats = { activeGpuJobs:0,activeCpuJobs:0,gpuUtil:0.2,cpuUtil:0.1,gpuTempC:60,vramUsedBytes:1e9,vramTotalBytes:16e9 };
const request = { id:'render-1',agentId:'renderer',intentId:'intent-4d-render',sceneId:'scene-1',width:1920,height:1080,frames:120,estimatedFlops:1e9,preferredBackends:['webgpu','vulkan'] as const };
const adapters = [
  { id:'canvas-main',backend:'canvas' as const,available:true,deviceClass:'cpu' as const },
  { id:'igpu-webgpu',backend:'webgpu' as const,available:true,deviceClass:'integrated-gpu' as const,vramBytes:2e9,features:['shader-f16'] },
  { id:'dgpu-vulkan',backend:'vulkan' as const,available:true,deviceClass:'discrete-gpu' as const,vramBytes:12e9 },
];

function router() { const value=new SovereignXRouter({clock:()=>1700000000000}); registerSovereignXRenderIntent(value); return value; }

describe('render bridge',()=>{
  it('honors the requested WebGPU backend when governance permits GPU work',()=>{
    const result=routeSovereignXRender(router(),request,runtime,limits,adapters);
    expect(result.backend).toBe('webgpu'); expect(result.adapter?.id).toBe('igpu-webgpu'); expect(result.evidenceRefs).toHaveLength(1);
  });
  it('falls back to Canvas when GPU capacity is saturated',()=>{
    const result=routeSovereignXRender(router(),request,{...runtime,activeGpuJobs:2},limits,adapters);
    expect(result.backend).toBe('canvas'); expect(result.routeEvaluation.localDecision.target).toBe('CPU');
  });
  it('delays rendering when thermal governance throttles execution',()=>{
    const result=routeSovereignXRender(router(),request,{...runtime,gpuTempC:90},limits,adapters);
    expect(result.backend).toBe('delay'); expect(result.action).toBe('delay');
  });
  it('selects an exact eligible adapter and respects feature requirements',()=>{
    const result=routeSovereignXRender(router(),{...request,requiredFeatures:['shader-f16'],minimumVramBytes:1e9},runtime,limits,adapters);
    expect(result.adapter?.id).toBe('igpu-webgpu');
  });
});
