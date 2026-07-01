# Cross-language CAS receipt evidence harness (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ReceiptJson = Join-Path $env:TEMP "receipt.json"
$StderrLog = Join-Path $env:TEMP "aaes-cas-evidence.stderr"

Set-Location $Root

cargo run -q -p aaes-cas-evidence 2>$StderrLog | Set-Content -Path $ReceiptJson -Encoding utf8NoBOM
$RustHash = (Select-String -Path $StderrLog -Pattern '^RUST_HASH=(.+)$' | Select-Object -First 1).Matches.Groups[1].Value

$PyOut = python bindings/python/evidence_harness.py $ReceiptJson 2>&1
$PyHash = ($PyOut | Select-String -Pattern '^PY_HASH=(.+)$' | Select-Object -First 1).Matches.Groups[1].Value

Write-Host "RUST_HASH=$RustHash"
Write-Host "PY_HASH=$PyHash"

if (-not $RustHash -or -not $PyHash) {
    Write-Error "Failed to capture cross-language hashes"
    exit 1
}

if ($RustHash -ne $PyHash) {
    Write-Error "Cross-language hash mismatch"
    exit 1
}

Write-Host "Cross-language CAS receipt hash is stable across Rust and Python"
