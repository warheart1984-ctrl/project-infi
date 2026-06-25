# Resolve a Python 3.10+ executable for operator_kernel scripts (writes path to stdout).
$ErrorActionPreference = "SilentlyContinue"
$MinVersion = [version]"3.10.0"

function Test-PythonVersion([string]$Exe, [string[]]$ExtraArgs = @()) {
    if (-not (Test-Path $Exe)) { return $false }
    $out = & $Exe @ExtraArgs -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
    if (-not $out) { return $false }
    try {
        return [version]$out.Trim() -ge $MinVersion
    } catch {
        return $false
    }
}

function Write-PythonPath([string]$Path, [string[]]$ExtraArgs = @()) {
    if (Test-PythonVersion $Path $ExtraArgs) {
        if ($ExtraArgs.Count -gt 0) {
            Write-Output "$Path $($ExtraArgs -join ' ')"
        } else {
            Write-Output $Path
        }
        exit 0
    }
}

if ($env:OPERATOR_PYTHON -and (Test-Path $env:OPERATOR_PYTHON)) {
    Write-PythonPath $env:OPERATOR_PYTHON
}

foreach ($ver in @("3.13", "3.12", "3.11", "3.10")) {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        Write-PythonPath $py.Source @("-$ver")
    }
}

foreach ($name in @("python3.13", "python3.12", "python3.11", "python3.10", "python3", "python")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-PythonPath $cmd.Source
    }
}

$searchRoots = @(
    "$env:LOCALAPPDATA\Programs\Python",
    "${env:ProgramFiles}\Python*",
    "C:\Python*"
)
$candidates = @()
foreach ($root in $searchRoots) {
    $found = Get-ChildItem -Path $root -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -notmatch "\\venv\\|\\.venv\\|Android|ndk-bundle|ndk\\"
        }
    foreach ($item in $found) {
        $candidates += $item.FullName
    }
}
foreach ($path in ($candidates | Sort-Object -Unique)) {
    if (Test-PythonVersion $path) {
        Write-PythonPath $path
    }
}

throw "Python 3.10+ not found. Set OPERATOR_PYTHON or install Python 3.10+."

