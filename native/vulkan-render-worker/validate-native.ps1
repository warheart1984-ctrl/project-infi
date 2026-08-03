param(
  [string]$Worker = "$PSScriptRoot\build\sovereignx-vulkan-worker.exe"
)

$ErrorActionPreference = 'Stop'
$validationRoot = Join-Path $PSScriptRoot 'validation-output'
New-Item -ItemType Directory -Force -Path $validationRoot | Out-Null
$surfaces = @('clifford-torus', 'hopf-surface', 'torus-3d', 'trefoil-4d', 'tesseract')
$hashes = @{}

foreach ($surface in $surfaces) {
  $outputDir = Join-Path $validationRoot $surface
  New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
  $jobPath = Join-Path $validationRoot "$surface-job.json"
  $receiptPath = Join-Path $validationRoot "$surface-receipt.json"
  $job = @{
    version = '1.0'; jobId = "surface-$surface"; sceneId = 'native-parity'
    backend = 'vulkan'; scenePath = 'none'; outputDir = $outputDir
    width = 128; height = 96; frames = 2; fps = 30; surfaceId = $surface
    meshPath = "G:/New folder/engine/surfaces/meshes/$surface.mesh.json"
    evidenceRefs = @('native-surface-parity'); createdAt = (Get-Date).ToUniversalTime().ToString('o')
  }
  $job | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $jobPath -Encoding utf8
  & $Worker --job $jobPath --receipt $receiptPath
  if ($LASTEXITCODE -ne 0) { throw "$surface worker failed with exit code $LASTEXITCODE" }
  $receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
  if ($receipt.status -ne 'completed' -or $receipt.outputPaths.Count -ne 2) { throw "$surface receipt is incomplete" }
  $hashes[$surface] = (Get-FileHash -Algorithm SHA256 -LiteralPath $receipt.outputPaths[0]).Hash
}

if (($hashes.Values | Sort-Object -Unique).Count -ne $surfaces.Count) {
  throw 'Native surface outputs are not distinct'
}

$cancelDir = Join-Path $validationRoot 'cancelled'
New-Item -ItemType Directory -Force -Path $cancelDir | Out-Null
$cancelPath = Join-Path $validationRoot 'cancel.signal'
$cancelJobPath = Join-Path $validationRoot 'cancel-job.json'
$cancelReceiptPath = Join-Path $validationRoot 'cancel-receipt.json'
Remove-Item -Force -ErrorAction SilentlyContinue -LiteralPath $cancelPath, $cancelReceiptPath
@{
  version = '1.0'; jobId = 'cancel-native'; sceneId = 'native-cancellation'; backend = 'vulkan'
  scenePath = 'none'; outputDir = $cancelDir; width = 640; height = 480; frames = 120; fps = 30
  surfaceId = 'trefoil-4d'; cancellationPath = $cancelPath; evidenceRefs = @('native-cancellation')
  meshPath = 'G:/New folder/engine/surfaces/meshes/trefoil-4d.mesh.json'
  createdAt = (Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $cancelJobPath -Encoding utf8

$process = Start-Process -FilePath $Worker -ArgumentList @('--job', $cancelJobPath, '--receipt', $cancelReceiptPath) -PassThru -WindowStyle Hidden
Start-Sleep -Milliseconds 150
Set-Content -LiteralPath $cancelPath -Value 'cancelled' -Encoding ascii
$process.WaitForExit()
if ($process.ExitCode -eq 0) { throw 'Cancelled worker unexpectedly completed' }

[pscustomobject]@{
  device = (Get-Content -Raw -LiteralPath (Join-Path $validationRoot 'clifford-torus-receipt.json') | ConvertFrom-Json).deviceName
  surfaces = $surfaces.Count
  frames = $surfaces.Count * 2
  uniqueFrameHashes = ($hashes.Values | Sort-Object -Unique).Count
  cancellationExitCode = $process.ExitCode
} | ConvertTo-Json
