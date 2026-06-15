# ScriptForge 本地开发一键启动（Windows）
# 用法：在项目根目录执行  npm run start
# 或：  powershell -File scripts/start-dev.ps1

$ErrorActionPreference = "Stop"
$dockerBin = "C:\Program Files\Docker\Docker\resources\bin"
if (Test-Path $dockerBin) {
    $env:Path = "$dockerBin;$env:Path"
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host ""
Write-Host "========== ScriptForge 开发环境 ==========" -ForegroundColor Cyan
Write-Host ""

# 1) Docker 基础设施
Write-Host "[1/4] 启动 Postgres + Redis（Docker）..." -ForegroundColor Yellow
docker compose up db redis -d | Out-Null
Start-Sleep -Seconds 3
docker compose ps
Write-Host ""

# 2) 检查 .env
$envFile = Join-Path $root "backend\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root "backend\.env.example") $envFile
    Write-Host "[提示] 已生成 backend\.env，请确认 FUSION_SKILL_ROOT 路径正确" -ForegroundColor Magenta
}

# 3) 依赖（仅首次需要，已装过会跳过很快）
if (-not (Test-Path (Join-Path $root "node_modules"))) {
    Write-Host "[2/4] 安装根目录依赖..." -ForegroundColor Yellow
    npm install
} else {
    Write-Host "[2/4] 根目录依赖已存在，跳过" -ForegroundColor DarkGray
}

if (-not (Test-Path (Join-Path $root "frontend\node_modules"))) {
    Write-Host "[3/4] 安装前端依赖..." -ForegroundColor Yellow
    npm run install:frontend
} else {
    Write-Host "[3/4] 前端依赖已存在，跳过" -ForegroundColor DarkGray
}

Write-Host "[4/4] 启动 前端 + 后端 + 任务Worker ..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  前端页面   http://localhost:5173" -ForegroundColor Green
Write-Host "  后端 API   http://localhost:8000" -ForegroundColor Green
Write-Host "  管理后台   http://localhost:8000/admin" -ForegroundColor Green
Write-Host ""
Write-Host "  按 Ctrl+C 停止全部进程" -ForegroundColor DarkGray
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

npm run dev
