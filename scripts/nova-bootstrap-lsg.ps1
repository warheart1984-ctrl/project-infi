# Seed the local LSG JSONL store from the core YAML bundle.
param(
    [string]$RepoRoot = $env:LAWFUL_NOVA_REPO_ROOT
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot) {
    $RepoRoot = Split-Path $ScriptDir -Parent
}

$env:LAWFUL_NOVA_REPO_ROOT = $RepoRoot
if (-not $env:NOVA_LSG_PATH) {
    $env:NOVA_LSG_PATH = Join-Path $RepoRoot "lsg\LSG-CORE.v1.yaml"
}
if (-not $env:NOVA_LSG_STORE) {
    $env:NOVA_LSG_STORE = Join-Path $env:USERPROFILE ".nova\lsg\local.jsonl"
}

$python = "python"
$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
}

Write-Host "[nova-bootstrap-lsg] bundle=$($env:NOVA_LSG_PATH)"
Write-Host "[nova-bootstrap-lsg] store=$($env:NOVA_LSG_STORE)"

& $python -c @"
from nova.lsg_loader import load_lsg_bundle, default_lsg_bundle_path, default_lsg_store_path
result = load_lsg_bundle(default_lsg_bundle_path(), store_path=default_lsg_store_path())
print(result)
"@
