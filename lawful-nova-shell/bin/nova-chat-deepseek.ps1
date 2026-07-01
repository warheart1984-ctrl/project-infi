# Lawful Nova DeepSeek coding substrate wrapper.
param(
    [Parameter(Position = 0)]
    [string]$Prompt = "observe lawful nova coding substrate",

    [string]$Model = $(if ($env:NOVA_CODING_SUBSTRATE) { $env:NOVA_CODING_SUBSTRATE } else { "coding-substrate-1" })
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "ollama is required for nova-deepseek, but it was not found on PATH."
}

ollama run $Model $Prompt
