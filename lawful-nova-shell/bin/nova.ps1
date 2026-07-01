# Lawful Nova CLI wrapper — Windows PowerShell.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$NovaArgs
)

$ErrorActionPreference = "Stop"
$ShellRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ParentRoot = Split-Path -Parent $ShellRoot
$RepoRoot = if ($env:LAWFUL_NOVA_REPO_ROOT) {
    $env:LAWFUL_NOVA_REPO_ROOT
} elseif ((Test-Path (Join-Path $ShellRoot "pyproject.toml")) -and (Test-Path (Join-Path $ShellRoot "nova"))) {
    $ShellRoot
} else {
    $ParentRoot
}

$VenvCandidates = @(
    (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
    (Join-Path $ParentRoot ".venv\Scripts\python.exe")
)
$VenvPy = $VenvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($VenvPy -and (Test-Path $VenvPy)) {
    $PyExe = $VenvPy
} elseif ($env:OPERATOR_PYTHON -and (Test-Path $env:OPERATOR_PYTHON)) {
    $PyExe = $env:OPERATOR_PYTHON
} else {
    $PyExe = (Get-Command python -ErrorAction Stop).Source
}

$env:LAWFUL_NOVA_REPO_ROOT = $RepoRoot
$env:NOVA_CORTEX_PATH = if ($env:NOVA_CORTEX_PATH) { $env:NOVA_CORTEX_PATH } else { Join-Path $ShellRoot "nova" }
$env:NOVA_VOSS_RUNTIME_PATH = if ($env:NOVA_VOSS_RUNTIME_PATH) { $env:NOVA_VOSS_RUNTIME_PATH } else { Join-Path $ShellRoot "nova" }
$env:NOVA_RSL_PATH = if ($env:NOVA_RSL_PATH) { $env:NOVA_RSL_PATH } else { Join-Path $RepoRoot "governance" }
$env:NOVA_CLI = $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$ShellRoot;$RepoRoot"

Set-Location $RepoRoot
& $PyExe -m nova.cli @NovaArgs
exit $LASTEXITCODE
