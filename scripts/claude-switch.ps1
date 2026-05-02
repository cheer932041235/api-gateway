# Claude Code 端点切换器
# 用法: . .\claude-switch.ps1 [端点名]
# 例:   . .\claude-switch.ps1 codex
#       . .\claude-switch.ps1 qwen
#       . .\claude-switch.ps1 vector
#       . .\claude-switch.ps1 list

param([string]$Profile = 'codex')

# ========== 从 secrets.json 加载密钥 ==========
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$secretsPath = Join-Path $scriptDir "secrets.json"
if (Test-Path $secretsPath) {
    $secrets = Get-Content $secretsPath -Raw | ConvertFrom-Json
} else {
    Write-Host "[WARN] secrets.json not found at $secretsPath" -ForegroundColor Yellow
    $secrets = @{}
}

# ========== 在这里添加/修改你的端点 ==========
# Type: 'anthropic' 设置 ANTHROPIC_* 变量; 'openai' 设置 OPENAI_* 变量
$endpoints = @{
    'codex' = @{
        Name  = 'Sub2API (Codex GPT-5.4 via local proxy)'
        URL   = 'http://127.0.0.1:5678'
        Key   = 'sk-proxy'  # local proxy handles real key
        Model = 'gpt-5.4'
        Type  = 'anthropic'
    }
    'qwen' = @{
        Name  = 'Qwen (自建反代)'
        URL   = 'http://170.106.65.175:3000/openai-qwen-oauth'
        Key   = $secrets.qwen_key
        Model = 'qwen3-coder-plus'
        Type  = 'anthropic'
    }
    'vector' = @{
        Name  = 'VectorEngine (Claude)'
        URL   = 'https://api.vectorengine.ai'
        Key   = $secrets.vectorengine_key
        Model = 'claude-opus-4-6'
        Type  = 'anthropic'
    }
}
# ================================================

if ($Profile -eq 'list') {
    Write-Host ""
    Write-Host "=== Claude Code 可用端点 ===" -ForegroundColor Cyan
    foreach ($k in $endpoints.Keys) {
        $e = $endpoints[$k]
        $display = "  {0,-10} -> {1} ({2})" -f $k, $e.Name, $e.Model
        Write-Host $display -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "用法: . .\claude-switch.ps1 端点名" -ForegroundColor Yellow
    Write-Host "切换后直接运行: claude"
    Write-Host ""
    return
}

if (-not $endpoints.ContainsKey($Profile)) {
    Write-Host "未知端点: $Profile" -ForegroundColor Red
    Write-Host "可用端点: $($endpoints.Keys -join ', ')"
    return
}

$ep = $endpoints[$Profile]

# 先清除所有端点变量，避免冲突
Remove-Item Env:ANTHROPIC_BASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:OPENAI_BASE_URL -ErrorAction SilentlyContinue

if ($ep.Type -eq 'openai') {
    $env:OPENAI_BASE_URL = $ep.URL
    $env:OPENAI_API_KEY  = $ep.Key
} else {
    $env:ANTHROPIC_BASE_URL = $ep.URL
    $env:ANTHROPIC_API_KEY  = $ep.Key
}
$env:CLAUDE_MODEL = $ep.Model

Write-Host ""
Write-Host "=== 已切换到: $($ep.Name) ===" -ForegroundColor Green
Write-Host "Type:  $($ep.Type)"
Write-Host "URL:   $($ep.URL)"
Write-Host "Model: $($ep.Model)"
Write-Host ""
Write-Host "现在可以直接运行: claude" -ForegroundColor Yellow
Write-Host ""
