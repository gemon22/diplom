# Подготовка проекта к деплою на Timeweb Cloud
# Запуск: powershell -ExecutionPolicy Bypass -File scripts\prepare_timeweb.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")

Set-Location $Root
Write-Host "=== Подготовка Timeweb Cloud ===" -ForegroundColor Cyan
Write-Host "Папка: $Root"

# Пример env для облака
$envExample = Join-Path $Root "timeweb\.env.production.example"
$envProd = Join-Path $Root "timeweb\.env.production"
if (-not (Test-Path $envProd)) {
    Copy-Item $envExample $envProd
    Write-Host "Создан timeweb\.env.production — заполните перед загрузкой в панель" -ForegroundColor Yellow
}

# Git
if (-not (Test-Path ".git")) {
    git init
    Write-Host "Git инициализирован"
}

$status = git status --porcelain 2>$null
if ($status) {
    git add -A
    git commit -m "Prepare Timeweb Cloud deploy" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Коммит создан" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== Дальше ===" -ForegroundColor Cyan
Write-Host "1. Заполните timeweb\.env.production (MySQL + API-ключи)"
Write-Host "2. Создайте репозиторий на GitHub"
Write-Host "3. git remote add origin https://github.com/USER/tour-generator.git"
Write-Host "4. git push -u origin main"
Write-Host "5. timeweb.cloud -> App Platform -> FastAPI -> подключить GitHub"
Write-Host ""
Write-Host "Полная инструкция: timeweb\DEPLOY.md" -ForegroundColor Green
