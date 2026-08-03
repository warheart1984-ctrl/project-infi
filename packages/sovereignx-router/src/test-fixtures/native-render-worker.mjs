import { createHash } from 'node:crypto';
import { access, readFile, writeFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
const args=Object.fromEntries(process.argv.slice(2).reduce((a,v,i,all)=>i%2===0?[...a,[v.replace(/^--/,''),all[i+1]]]:a,[]));
const run=async(jobPath,receiptPath)=>{
const job=JSON.parse(await readFile(jobPath,'utf8'));
const outputPaths=[];
for(let frame=0;frame<job.frames;frame++){
  if(job.testDelayMs) await new Promise((resolve)=>setTimeout(resolve,job.testDelayMs));
  if(job.cancellationPath){try{await access(job.cancellationPath);process.stderr.write('render cancelled by governance');process.exit(2);}catch{/* ignore */}}
  outputPaths.push(`${job.outputDir}/frame-${String(frame).padStart(6,'0')}.png`);
}
const receipt={version:'1.0',jobId:job.jobId,status:'completed',backend:job.backend,adapterId:job.adapterId,deviceName:'Test Vulkan Device',outputPaths,startedAt:new Date().toISOString(),completedAt:new Date().toISOString(),evidenceRefs:job.evidenceRefs};
const canonical=(v)=>Array.isArray(v)?`[${v.map(canonical).join(',')}]`:v&&typeof v==='object'?`{${Object.entries(v).filter(([,x])=>x!==undefined).sort(([a],[b])=>a.localeCompare(b)).map(([k,x])=>`${JSON.stringify(k)}:${canonical(x)}`).join(',')}}`:JSON.stringify(v);
receipt.workerEvidenceHash=createHash('sha256').update(canonical({jobId:receipt.jobId,backend:receipt.backend,adapterId:receipt.adapterId,outputPaths:receipt.outputPaths,evidenceRefs:receipt.evidenceRefs})).digest('hex');
await writeFile(receiptPath,JSON.stringify(receipt),'utf8');
return job;
};
if(process.argv.includes('--daemon')){
  const input=createInterface({input:process.stdin,crlfDelay:Infinity});
  for await(const line of input){const command=JSON.parse(line);const job=await run(command.jobPath,command.receiptPath);process.stdout.write(`${JSON.stringify({event:'receipt',jobId:job.jobId,receiptPath:command.receiptPath})}\n`);}
}else await run(args.job,args.receipt);
