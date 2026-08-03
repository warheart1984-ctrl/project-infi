import { execFile, spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { promises as fs } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { promisify } from 'node:util';
import type { RuntimeStats } from './types.js';
import { routeSovereignXRender, type SovereignXRenderAdapter, type SovereignXRenderBackend, type SovereignXRenderRequest, type SovereignXRenderRouteResult } from './renderBridge.js';
import type { GovernanceLimits } from './types.js';
import type { SovereignXRouter } from './SovereignXRouter.js';

const execFileAsync = promisify(execFile);

export interface SovereignXGpuTelemetryDevice {
  index: number;
  uuid: string;
  name: string;
  temperatureC: number;
  utilization: number;
  memoryUsedBytes: number;
  memoryTotalBytes: number;
  powerDrawFraction: number;
}

export interface SovereignXLiveGpuSnapshot {
  source: 'amd-adl' | 'nvidia-smi' | 'unavailable';
  trusted: boolean;
  observedAt: string;
  devices: SovereignXGpuTelemetryDevice[];
  errors: string[];
}

export function parseAmdAdlTelemetry(output:string):SovereignXGpuTelemetryDevice[] {
  const payload=JSON.parse(output) as {source?:string;trusted?:boolean;devices?:Array<Record<string,unknown>>};
  if(payload.source!=='amd-adl' || payload.trusted!==true || !Array.isArray(payload.devices)) return [];
  return payload.devices.map((device)=>({
    index:Number(device.index),uuid:String(device.uuid??''),name:String(device.name??'AMD GPU'),
    temperatureC:Number(device.temperatureC),utilization:Number(device.utilization),
    memoryUsedBytes:0,memoryTotalBytes:0,powerDrawFraction:0,
  })).filter((device)=>Number.isInteger(device.index)&&device.uuid.length>0&&Number.isFinite(device.temperatureC)&&device.temperatureC>=0&&device.temperatureC<=150&&Number.isFinite(device.utilization)&&device.utilization>=0&&device.utilization<=1);
}

export async function collectAmdAdlTelemetry(executable:string,runner:typeof execFileAsync=execFileAsync):Promise<SovereignXLiveGpuSnapshot> {
  const observedAt=new Date().toISOString();
  try {
    const {stdout}=await runner(executable,[],{windowsHide:true,timeout:5_000});
    const devices=parseAmdAdlTelemetry(stdout);
    return {source:devices.length?'amd-adl':'unavailable',trusted:devices.length>0,observedAt,devices,errors:devices.length?[]:['ADL returned no validated physical devices']};
  } catch(error) { return {source:'unavailable',trusted:false,observedAt,devices:[],errors:[error instanceof Error?error.message:String(error)]}; }
}

export interface SovereignXNativeRenderJob {
  version: '1.0';
  jobId: string;
  sceneId: string;
  backend: Exclude<SovereignXRenderBackend, 'canvas' | 'webgpu'>;
  adapterId?: string;
  scenePath: string;
  meshPath?: string;
  sharedFramePath?: string;
  outputDir: string;
  width: number;
  height: number;
  frames: number;
  fps: number;
  time?: number;
  surfaceId?: string;
  renderProfile?: string;
  encoding?: { codec:'h264'|'hevc'|'av1'|'none';hardwarePreferred:boolean };
  cancellationPath?: string;
  evidenceRefs: string[];
  createdAt: string;
}

export interface SovereignXNativeRenderReceipt {
  version: '1.0';
  jobId: string;
  status: 'completed' | 'failed';
  backend: string;
  adapterId?: string;
  deviceName?: string;
  outputPaths: string[];
  startedAt: string;
  completedAt: string;
  evidenceRefs: string[];
  workerEvidenceHash: string;
  meshContract?: {id:string;vertexCount:number;faceCount:number;contentHash:string};
  encodedPath?: string;
  encoder?: string;
  error?: string;
}

export interface SovereignXNativeWorkerOptions {
  executable: string;
  args?: string[];
  timeoutMs?: number;
  environment?: NodeJS.ProcessEnv;
  signal?: AbortSignal;
  onEvent?: (event:{event:string;jobId?:string;frameIndex?:number;outputPath?:string;sharedFramePath?:string})=>void;
}

export async function validateNativeMeshContract(meshPath:string):Promise<{id:string;vertexCount:number;faceCount:number;contentHash:string}> {
  const mesh=JSON.parse(await fs.readFile(meshPath,'utf8')) as Record<string,unknown>;
  if(mesh.contractVersion!=='1.0'||mesh.source!=='4d-renderer'||typeof mesh.id!=='string')throw new Error('invalid Scene4D mesh contract identity');
  const vertices=mesh.vertices as Array<Record<string,unknown>>,faces=mesh.faces as Array<unknown[]>;
  if(!Array.isArray(vertices)||!Array.isArray(faces)||vertices.length!==mesh.vertexCount||faces.length!==mesh.faceCount)throw new Error('Scene4D mesh count mismatch');
  if(vertices.some((v)=>['x','y','z','w'].some((axis)=>!Number.isFinite(Number(v[axis])))))throw new Error('Scene4D mesh contains a non-finite vertex');
  if(faces.some((face)=>!Array.isArray(face)||face.length!==3||face.some((index)=>!Number.isInteger(index)||Number(index)<0||Number(index)>=vertices.length)))throw new Error('Scene4D mesh contains an invalid triangle');
  const expected=createHash('sha256').update(JSON.stringify({id:mesh.id,vertices,edges:mesh.edges,faces})).digest('hex');
  if(mesh.contentHash!==expected)throw new Error('Scene4D mesh content hash mismatch');
  return {id:mesh.id,vertexCount:vertices.length,faceCount:faces.length,contentHash:expected};
}

export class SovereignXNativeRenderDaemon {
  private child:ChildProcessWithoutNullStreams;
  private queue:Promise<unknown>=Promise.resolve();
  private lines:string[]=[];
  private waiters:Array<()=>void>=[];
  constructor(private readonly options:SovereignXNativeWorkerOptions) {
    this.child=spawn(options.executable,[...(options.args??[]),'--daemon'],{stdio:['pipe','pipe','pipe'],env:{...process.env,...options.environment},windowsHide:true});
    let buffered=''; this.child.stdout.setEncoding('utf8');
    this.child.stdout.on('data',(chunk:string)=>{buffered+=chunk;const parts=buffered.split(/\r?\n/);buffered=parts.pop()??'';for(const line of parts)if(line.trim()){this.lines.push(line);this.waiters.shift()?.();}});
  }
  dispatch(job:SovereignXNativeRenderJob,signal?:AbortSignal):Promise<SovereignXNativeRenderReceipt> {
    const operation=this.queue.then(()=>this.dispatchOne(job,signal));
    this.queue=operation.catch(()=>undefined); return operation;
  }
  private async dispatchOne(job:SovereignXNativeRenderJob,signal?:AbortSignal):Promise<SovereignXNativeRenderReceipt> {
    const dir=await fs.mkdtemp(path.join(tmpdir(),'sovereignx-daemon-'));
    const jobPath=path.join(dir,'job.json'),receiptPath=path.join(dir,'receipt.json'),cancellationPath=path.join(dir,'cancel');
    if(job.meshPath)await validateNativeMeshContract(job.meshPath);
    const dispatchedJob={...job,cancellationPath}; await fs.writeFile(jobPath,JSON.stringify(dispatchedJob,null,2),'utf8');
    const cancel=()=>{void fs.writeFile(cancellationPath,'cancelled','utf8').catch(()=>undefined);}; signal?.addEventListener('abort',cancel,{once:true}); if(signal?.aborted)cancel();
    try {
      this.child.stdin.write(`${JSON.stringify({jobPath,receiptPath})}\n`);
      let event:{event?:string;jobId?:string;frameIndex?:number;outputPath?:string};
      do { event=JSON.parse(await this.nextLine(this.options.timeoutMs??120_000));this.options.onEvent?.(event as {event:string}); } while(event.event==='frame');
      if(event.event!=='receipt'||event.jobId!==job.jobId)throw new Error('resident native worker protocol mismatch');
      const receipt=JSON.parse(await fs.readFile(receiptPath,'utf8')) as SovereignXNativeRenderReceipt; verifyNativeRenderReceipt(dispatchedJob,receipt); return receipt;
    } finally {signal?.removeEventListener('abort',cancel);await fs.rm(dir,{recursive:true,force:true});}
  }
  private nextLine(timeoutMs:number):Promise<string>{if(this.lines.length)return Promise.resolve(this.lines.shift()!);return new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('resident native worker timed out')),timeoutMs);this.waiters.push(()=>{clearTimeout(timer);resolve(this.lines.shift()!);});});}
  async close():Promise<void>{this.child.stdin.end();await new Promise<void>((resolve)=>this.child.once('close',()=>resolve()));}
  get processId():number|undefined{return this.child.pid;}
}

export async function collectLiveGpuTelemetry(
  runner: typeof execFileAsync = execFileAsync,
): Promise<SovereignXLiveGpuSnapshot> {
  const observedAt = new Date().toISOString();
  try {
    const query = 'index,uuid,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,power.limit';
    const { stdout } = await runner('nvidia-smi', [`--query-gpu=${query}`, '--format=csv,noheader,nounits'], { windowsHide: true, timeout: 5_000 });
    const devices = parseNvidiaTelemetry(stdout);
    return { source: 'nvidia-smi', trusted: devices.length > 0, observedAt, devices, errors: devices.length ? [] : ['nvidia-smi returned no devices'] };
  } catch (error) {
    return { source: 'unavailable', trusted: false, observedAt, devices: [], errors: [error instanceof Error ? error.message : String(error)] };
  }
}

export function parseNvidiaTelemetry(output: string): SovereignXGpuTelemetryDevice[] {
  return output.split(/\r?\n/).filter(Boolean).map((line) => {
    const [index, uuid, name, temp, util, used, total, draw, limit] = line.split(',').map((value) => value.trim());
    const powerLimit = Number(limit);
    return { index:Number(index),uuid,name,temperatureC:Number(temp),utilization:Number(util)/100,memoryUsedBytes:Number(used)*1024*1024,memoryTotalBytes:Number(total)*1024*1024,powerDrawFraction:powerLimit>0?Number(draw)/powerLimit:0 };
  }).filter((device) => Number.isFinite(device.index) && Number.isFinite(device.temperatureC) && Number.isFinite(device.utilization));
}

export function runtimeStatsFromTelemetry(snapshot: SovereignXLiveGpuSnapshot, activeGpuJobs = 0, activeCpuJobs = 0): RuntimeStats {
  const devices = snapshot.devices;
  return { activeGpuJobs,activeCpuJobs,gpuUtil:devices.length?Math.max(...devices.map((d)=>d.utilization)):0,cpuUtil:0,gpuTempC:devices.length?Math.max(...devices.map((d)=>d.temperatureC)):Number.POSITIVE_INFINITY,vramUsedBytes:devices.reduce((n,d)=>n+d.memoryUsedBytes,0),vramTotalBytes:devices.reduce((n,d)=>n+d.memoryTotalBytes,0) };
}

export async function probeVulkanAdapters(runner: typeof execFileAsync = execFileAsync): Promise<SovereignXRenderAdapter[]> {
  try {
    const { stdout, stderr } = await runner('vulkaninfo', ['--summary'], { windowsHide:true,timeout:10_000 });
    return parseVulkanSummary(`${stdout}\n${stderr}`);
  } catch (error: unknown) {
    const output = typeof error === 'object' && error && 'stdout' in error ? String((error as {stdout?:unknown}).stdout ?? '') : '';
    return parseVulkanSummary(output);
  }
}

export function parseVulkanSummary(output: string): SovereignXRenderAdapter[] {
  const blocks = output.split(/\nGPU\d+:\s*\n/).slice(1);
  return blocks.map((block,index) => {
    const value = (name:string) => block.match(new RegExp(`${name}\\s*=\\s*([^\\r\\n]+)`))?.[1]?.trim();
    const type=value('deviceType') ?? '';
    return { id:`vulkan-${value('deviceUUID') || index}`,backend:'vulkan' as const,available:true,deviceClass:type.includes('DISCRETE')?'discrete-gpu' as const:type.includes('INTEGRATED')?'integrated-gpu' as const:'remote-gpu' as const,name:value('deviceName') ?? `Vulkan GPU ${index}`,features:[`vulkan-${value('apiVersion') ?? 'unknown'}`] };
  });
}

export async function dispatchNativeRenderJob(job: SovereignXNativeRenderJob, options: SovereignXNativeWorkerOptions): Promise<SovereignXNativeRenderReceipt> {
  const dir = await fs.mkdtemp(path.join(tmpdir(), 'sovereignx-render-'));
  const jobPath=path.join(dir,'job.json'),receiptPath=path.join(dir,'receipt.json');
  if(job.meshPath)await validateNativeMeshContract(job.meshPath);
  const cancellationPath=path.join(dir,'cancel');
  const dispatchedJob={...job,cancellationPath};
  await fs.writeFile(jobPath,JSON.stringify(dispatchedJob,null,2),'utf8');
  const cancel=()=>{ void fs.writeFile(cancellationPath,'cancelled','utf8').catch(()=>undefined); };
  options.signal?.addEventListener('abort',cancel,{once:true});
  if(options.signal?.aborted) cancel();
  try {
    const child=spawn(options.executable,[...(options.args??[]),'--job',jobPath,'--receipt',receiptPath],{stdio:['ignore','pipe','pipe'],env:{...process.env,...options.environment},windowsHide:true});
    let stderr=''; child.stderr.setEncoding('utf8'); child.stderr.on('data',(c)=>{stderr+=c;});
    const code=await new Promise<number>((resolve,reject)=>{const timer=setTimeout(()=>{child.kill();reject(new Error('native render worker timed out'));},options.timeoutMs??120_000);child.once('error',reject);child.once('close',(value)=>{clearTimeout(timer);resolve(value??-1);});});
    if(code!==0) throw new Error(`native render worker exited ${code}: ${stderr.trim()}`);
    const receipt=JSON.parse(await fs.readFile(receiptPath,'utf8')) as SovereignXNativeRenderReceipt;
    verifyNativeRenderReceipt(dispatchedJob,receipt);
    return receipt;
  } finally { options.signal?.removeEventListener('abort',cancel); await fs.rm(dir,{recursive:true,force:true}); }
}

export function verifyNativeRenderReceipt(job:SovereignXNativeRenderJob,receipt:SovereignXNativeRenderReceipt):void {
  if(receipt.jobId!==job.jobId) throw new Error('native render receipt jobId mismatch');
  if(receipt.backend!==job.backend) throw new Error('native render receipt backend mismatch');
  if(receipt.status!=='completed') throw new Error(receipt.error || 'native render worker failed');
  const expected=createHash('sha256').update(canonicalJson({jobId:receipt.jobId,backend:receipt.backend,adapterId:receipt.adapterId,outputPaths:receipt.outputPaths,evidenceRefs:receipt.evidenceRefs})).digest('hex');
  if(receipt.workerEvidenceHash!==expected) throw new Error('native render receipt evidence hash mismatch');
}

function canonicalJson(value:unknown):string { if(Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`; if(value&&typeof value==='object') return `{${Object.entries(value as Record<string,unknown>).filter(([,v])=>v!==undefined).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>`${JSON.stringify(k)}:${canonicalJson(v)}`).join(',')}}`; return JSON.stringify(value); }

export function createNativeRenderJob(input:Omit<SovereignXNativeRenderJob,'version'|'jobId'|'createdAt'> & {jobId?:string}):SovereignXNativeRenderJob {
  return {...input,version:'1.0',jobId:input.jobId??randomUUID(),createdAt:new Date().toISOString()};
}

export type SovereignXHardwareEncoder = 'h264_amf'|'hevc_amf'|'av1_amf'|'h264_nvenc'|'hevc_nvenc'|'av1_nvenc'|'h264_qsv'|'hevc_qsv'|'av1_qsv';
export function parseHardwareEncoders(output:string):SovereignXHardwareEncoder[] { const known:SovereignXHardwareEncoder[]=['h264_amf','hevc_amf','av1_amf','h264_nvenc','hevc_nvenc','av1_nvenc','h264_qsv','hevc_qsv','av1_qsv'];return known.filter((name)=>new RegExp(`\\b${name}\\b`).test(output)); }
export async function encodeNativeFrames(job:SovereignXNativeRenderJob,receipt:SovereignXNativeRenderReceipt,options:{ffmpeg?:string;runner?:typeof execFileAsync}={}):Promise<SovereignXNativeRenderReceipt>{
  if(!job.encoding||job.encoding.codec==='none'||!receipt.outputPaths.length)return receipt;
  const encoder=job.encoding.codec==='h264'?'h264_amf':job.encoding.codec==='hevc'?'hevc_amf':'av1_amf';
  const first=receipt.outputPaths[0],pattern=path.join(path.dirname(first),'vulkan-frame-%06d.ppm'),encodedPath=path.join(job.outputDir,`sovereignx-${job.jobId}.${job.encoding.codec==='av1'?'mkv':'mp4'}`);
  await (options.runner??execFileAsync)(options.ffmpeg??'ffmpeg',['-y','-hide_banner','-loglevel','error','-framerate',String(job.fps),'-i',pattern,'-frames:v',String(job.frames),'-c:v',encoder,'-pix_fmt','nv12',encodedPath],{windowsHide:true,timeout:300_000});
  return {...receipt,encodedPath,encoder};
}
export async function probeHardwareEncoders(runner:typeof execFileAsync=execFileAsync):Promise<{available:SovereignXHardwareEncoder[];trusted:boolean;error?:string}>{try{const {stdout,stderr}=await runner('ffmpeg',['-hide_banner','-encoders'],{windowsHide:true,timeout:5_000});const available=parseHardwareEncoders(`${stdout}\n${stderr}`);return {available,trusted:true};}catch(error){return {available:[],trusted:false,error:error instanceof Error?error.message:String(error)};}}

export async function routeWithLiveGpuTelemetry(input:{router:SovereignXRouter;request:SovereignXRenderRequest;limits:GovernanceLimits;activeGpuJobs?:number;activeCpuJobs?:number;telemetryRunner?:typeof execFileAsync;amdAdlExecutable?:string;vulkanRunner?:typeof execFileAsync;extraAdapters?:SovereignXRenderAdapter[]}):Promise<{snapshot:SovereignXLiveGpuSnapshot;adapters:SovereignXRenderAdapter[];decision:SovereignXRenderRouteResult}> {
  const snapshot=input.amdAdlExecutable?await collectAmdAdlTelemetry(input.amdAdlExecutable,input.telemetryRunner):await collectLiveGpuTelemetry(input.telemetryRunner);
  input.router.setMeasurementHealth({trusted:snapshot.trusted,stale:false,sampleCount:snapshot.devices.length,windowMs:5_000,temperatureVarianceC:0,notes:snapshot.errors});
  if(!snapshot.trusted) input.router.setRuntimeMode('MeasurementUntrusted');
  const adapters=[...(await probeVulkanAdapters(input.vulkanRunner)),...(input.extraAdapters??[])];
  const runtime=runtimeStatsFromTelemetry(snapshot,input.activeGpuJobs,input.activeCpuJobs);
  const decision=routeSovereignXRender(input.router,input.request,runtime,input.limits,adapters);
  return {snapshot,adapters,decision};
}
