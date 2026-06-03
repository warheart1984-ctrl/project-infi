# AAIS operator menu — no-browser helpers (PowerShell)
# Usage: .\scripts\operator_menu.ps1

$Base = "http://127.0.0.1:8000"
$Legacy = "$Base/legacy_api"

function Show-Menu {
    Write-Host ""
    Write-Host "=== AAIS Operator Menu ==="
    Write-Host "1) Health check"
    Write-Host "2) List AI providers"
    Write-Host "3) Create chat session"
    Write-Host "4) Send message (needs session id)"
    Write-Host "5) Capability bridge status"
    Write-Host "6) Memory board snapshot"
    Write-Host "7) ARIS boundary status"
    Write-Host "0) Exit"
    Write-Host ""
}

function Invoke-Health {
    Invoke-RestMethod -Uri "$Base/health" -Method Get | ConvertTo-Json
}

function Invoke-Providers {
    Invoke-RestMethod -Uri "$Legacy/api/jarvis/providers" -Method Get | ConvertTo-Json -Depth 5
}

function Invoke-NewSession {
    $body = @{ system_prompt = "You are Jarvis." } | ConvertTo-Json
    $resp = Invoke-RestMethod -Uri "$Legacy/api/chat/sessions" -Method Post -Body $body -ContentType "application/json"
    $resp | ConvertTo-Json -Depth 5
    if ($resp.session_id) {
        Write-Host "Session ID: $($resp.session_id)" -ForegroundColor Green
    }
}

function Invoke-SendMessage {
    param([string]$SessionId)
    if (-not $SessionId) {
        $SessionId = Read-Host "Session ID"
    }
    $msg = Read-Host "Message"
    $body = @{ message = $msg; response_mode = "operator" } | ConvertTo-Json
    Invoke-RestMethod -Uri "$Legacy/api/chat/sessions/$SessionId/message" -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 8
}

function Invoke-BridgeStatus {
    Invoke-RestMethod -Uri "$Legacy/api/jarvis/capability-bridge/status" -Method Get | ConvertTo-Json -Depth 5
}

function Invoke-MemoryBoard {
    Invoke-RestMethod -Uri "$Legacy/api/jarvis/memory/board" -Method Get | ConvertTo-Json -Depth 5
}

function Invoke-ArisStatus {
    Invoke-RestMethod -Uri "$Legacy/api/jarvis/aris-boundary/status" -Method Get | ConvertTo-Json -Depth 5
}

while ($true) {
    Show-Menu
    $choice = Read-Host "Choice"
    switch ($choice) {
        "1" { Invoke-Health }
        "2" { Invoke-Providers }
        "3" { Invoke-NewSession }
        "4" { Invoke-SendMessage -SessionId "" }
        "5" { Invoke-BridgeStatus }
        "6" { Invoke-MemoryBoard }
        "7" { Invoke-ArisStatus }
        "0" { break }
        default { Write-Host "Unknown option" -ForegroundColor Yellow }
    }
}
