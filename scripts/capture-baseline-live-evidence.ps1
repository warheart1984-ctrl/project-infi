# Capture live evidence for AAES-OS Production Baseline v1.0
# Requires: kubectl, optional curl. Fails closed if cluster unreachable.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Live = Join-Path $Root "docs\release\production-baseline\aaes-os-v1.0\evidence\live"
$Namespace = if ($env:AAES_OS_NAMESPACE) { $env:AAES_OS_NAMESPACE } else { "aaes-os" }
$Services = @("ops-console", "platform-api", "platform-web", "sovereign-control-plane", "uss-api")

New-Item -ItemType Directory -Force -Path (Join-Path $Live "probes") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Live "hpa") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Live "recovery") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Live "trivy") | Out-Null

$kubectl = Get-Command kubectl -ErrorAction SilentlyContinue
if (-not $kubectl) {
  Write-Error "kubectl not found. Install kubectl and re-run."
}

Write-Host "Checking cluster access (namespace=$Namespace)..."
kubectl get ns $Namespace 2>&1 | Tee-Object -FilePath (Join-Path $Live "probes\namespace.txt")
if ($LASTEXITCODE -ne 0) {
  @{
    baselineId = "AAES-OS-PRODUCTION-BASELINE-v1.0"
    kind = "live-evidence-status"
    status = "pending-cluster-execution"
    updatedAt = (Get-Date).ToUniversalTime().ToString("o")
    slots = @{ probes = "failed-namespace"; trivy = "pending"; hpa = "pending"; recovery = "pending" }
    error = "namespace missing or kubectl failed"
  } | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $Live "STATUS.json")
  exit 1
}

kubectl -n $Namespace get deploy,svc,pods -o wide 2>&1 |
  Tee-Object -FilePath (Join-Path $Live "probes\workloads.txt")

foreach ($svc in $Services) {
  kubectl -n $Namespace get deploy $svc -o json 2>&1 |
    Tee-Object -FilePath (Join-Path $Live "probes\$svc.deploy.json") | Out-Null
}

kubectl -n $Namespace get hpa -o wide 2>&1 |
  Tee-Object -FilePath (Join-Path $Live "hpa\hpa.txt")

@"
# Recovery drill note

Recorded: $((Get-Date).ToUniversalTime().ToString('o'))

Procedure (operator-filled):
1. Note current image digests for one deploy
2. Apply intentional bad tag or scale to 0
3. Observe rollout / readiness failure
4. Rollback / restore known-good digest
5. Confirm probes green

Status: template written by capture script — replace with actual drill log.
"@ | Set-Content (Join-Path $Live "recovery\drill-note.md")

$trivyCi = Join-Path $Root "trivy-results.sarif"
if (Test-Path $trivyCi) {
  Copy-Item $trivyCi (Join-Path $Live "trivy\trivy-results.sarif") -Force
  $trivyStatus = "attached-from-workspace"
} else {
  $trivyStatus = "pending-ci-or-cluster-attach"
  "Place CI trivy-results.sarif here or download the trivy-baseline-sarif workflow artifact." |
    Set-Content (Join-Path $Live "trivy\README.txt")
}

@{
  baselineId = "AAES-OS-PRODUCTION-BASELINE-v1.0"
  kind = "live-evidence-status"
  status = "captured-partial"
  updatedAt = (Get-Date).ToUniversalTime().ToString("o")
  slots = @{
    probes = "captured"
    trivy = $trivyStatus
    hpa = "captured"
    recovery = "template-pending-operator-drill"
  }
  namespace = $Namespace
} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $Live "STATUS.json")

Write-Host "Live evidence written under $Live"
Write-Host "Next: complete recovery drill note; merge GHCR digests; run pnpm exec tsx tools/oel-validate.ts"
