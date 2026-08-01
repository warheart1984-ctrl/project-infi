$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot 'resident-validation'
New-Item -ItemType Directory -Force -Path $root | Out-Null
$commands = @()
foreach ($number in 1..2) {
  $jobPath = Join-Path $root "job-$number.json"; $receiptPath = Join-Path $root "receipt-$number.json"
  @{
    version='1.0'; jobId="resident-$number"; sceneId="scene-$number"; backend='vulkan'; scenePath='none'
    outputDir=(Join-Path $root "output-$number"); width=128; height=96; frames=2; fps=30
    surfaceId=$(if($number -eq 1){'hopf-surface'}else{'trefoil-4d'}); evidenceRefs=@("resident-$number"); createdAt=(Get-Date).ToUniversalTime().ToString('o')
    meshPath=$(if($number -eq 1){'G:/New folder/engine/surfaces/meshes/hopf-surface.mesh.json'}else{'G:/New folder/engine/surfaces/meshes/trefoil-4d.mesh.json'})
  } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $jobPath -Encoding utf8
  $commands += @{jobPath=$jobPath;receiptPath=$receiptPath}
}
$cancelPath=Join-Path $root 'cancel.signal'; Set-Content -LiteralPath $cancelPath -Value 'cancelled' -Encoding ascii
$cancelJobPath=Join-Path $root 'cancel-job.json'; $cancelReceiptPath=Join-Path $root 'cancel-receipt.json'
@{version='1.0';jobId='resident-cancel';sceneId='cancel';backend='vulkan';scenePath='none';meshPath='G:/New folder/engine/surfaces/meshes/tesseract.mesh.json';outputDir=(Join-Path $root 'cancel-output');width=128;height=96;frames=4;fps=30;surfaceId='tesseract';cancellationPath=$cancelPath;evidenceRefs=@('resident-cancel');createdAt=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $cancelJobPath -Encoding utf8
$commands=@($commands[0],@{jobPath=$cancelJobPath;receiptPath=$cancelReceiptPath},$commands[1])
$start = [Diagnostics.ProcessStartInfo]::new((Join-Path $PSScriptRoot 'build\sovereignx-vulkan-worker.exe'),'--daemon')
$start.UseShellExecute=$false; $start.CreateNoWindow=$true; $start.RedirectStandardInput=$true; $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true
$process=[Diagnostics.Process]::Start($start); $pidBefore=$process.Id
foreach($command in $commands){
  $process.StandardInput.WriteLine(($command|ConvertTo-Json -Compress)); $process.StandardInput.Flush()
  do{$event=$process.StandardOutput.ReadLine()|ConvertFrom-Json}while($event.event-eq'frame')
  if($event.event-ne'receipt'){throw 'Resident protocol did not return a receipt event'}
}
$process.StandardInput.Close(); $process.WaitForExit()
if($process.ExitCode-ne 0){throw $process.StandardError.ReadToEnd()}
$receipts=$commands|ForEach-Object{Get-Content -Raw -LiteralPath $_.receiptPath|ConvertFrom-Json}
$completed=@($receipts|Where-Object{$_.status-eq'completed'-and$_.outputPaths.Count-eq 2});$cancelled=@($receipts|Where-Object{$_.status-eq'failed'-and$_.error-eq'render cancelled by governance'})
if($completed.Count-ne 2-or$cancelled.Count-ne 1){throw 'Resident receipt or cancellation recovery validation failed'}
[pscustomobject]@{pid=$pidBefore;jobs=$receipts.Count;completedJobs=$completed.Count;cancelledJobs=$cancelled.Count;frames=($completed.outputPaths.Count|Measure-Object -Sum).Sum;device=$receipts[0].deviceName}|ConvertTo-Json
