# Lawful Nova CLI wrapper — Windows PowerShell.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$NovaArgs
)

$ErrorActionPreference = "Stop"
$ShellRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$RepoRoot = if ($env:LAWFUL_NOVA_REPO_ROOT) { $env:LAWFUL_NOVA_REPO_ROOT } else { Split-Path -Parent $ShellRoot }

$VenvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPy) {
    $PyExe = $VenvPy
} elseif ($env:OPERATOR_PYTHON -and (Test-Path $env:OPERATOR_PYTHON)) {
    $PyExe = $env:OPERATOR_PYTHON
} else {
    $PyExe = (Get-Command python -ErrorAction Stop).Source
}

$env:LAWFUL_NOVA_REPO_ROOT = $RepoRoot
$env:NOVA_CORTEX_PATH = if ($env:NOVA_CORTEX_PATH) { $env:NOVA_CORTEX_PATH } else { Join-Path $RepoRoot "nova" }
$env:NOVA_VOSS_RUNTIME_PATH = if ($env:NOVA_VOSS_RUNTIME_PATH) { $env:NOVA_VOSS_RUNTIME_PATH } else { Join-Path $RepoRoot "nova" }
$env:NOVA_RSL_PATH = if ($env:NOVA_RSL_PATH) { $env:NOVA_RSL_PATH } else { Join-Path $RepoRoot "governance" }
$env:NOVA_CLI = $MyInvocation.MyCommand.Path
$env:PYTHONPATH = $RepoRoot

Set-Location $RepoRoot
& $PyExe -m nova.cli @NovaArgs
exit $LASTEXITCODE
