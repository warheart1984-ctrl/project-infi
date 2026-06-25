# Governed local Lawful LoRA adapter (Qwen2.5-1.5B)
# Source: training/out/jarvis-qwen-lora/final after promote_lawful_lora_adapter.py
$env:AAIS_FORCE_LOCAL_MODEL = "1"
$env:AAIS_TEXT_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
$env:AAIS_ENABLE_TEXT_ADAPTERS = "1"
$env:AAIS_TEXT_ADAPTER_PATH = "E:\project-infi\training\out\jarvis-qwen-lora\final"
Write-Host "Lawful LoRA env configured:"
Write-Host "  AAIS_TEXT_MODEL_NAME=$env:AAIS_TEXT_MODEL_NAME"
Write-Host "  AAIS_TEXT_ADAPTER_PATH=$env:AAIS_TEXT_ADAPTER_PATH"
Write-Host ""
Write-Host "After training, promote then verify (works from any cwd):"
Write-Host "  E:\project-infi\.venv\Scripts\python.exe E:\project-infi\training\promote_lawful_lora_adapter.py"
Write-Host "  E:\project-infi\.venv\Scripts\python.exe E:\project-infi\scripts\verify_lawful_lora_adapter.py --skip-chat"
