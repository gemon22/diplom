# Деплой на VPS одной командой с Windows
# Использование:
#   $env:VPS_PASS = 'ваш-пароль'
#   powershell -ExecutionPolicy Bypass -File scripts\deploy_vps.ps1

param(
    [string]$VpsHost = "185.177.219.244",
    [string]$VpsUser = "root",
    [string]$RepoUrl = "https://github.com/gemon22/diplom.git"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")

if (-not $env:VPS_PASS) {
    Write-Host "Задайте пароль: `$env:VPS_PASS = 'пароль'" -ForegroundColor Yellow
    exit 1
}

# Проверка plink (PuTTY)
$plink = Get-Command plink -ErrorAction SilentlyContinue
if (-not $plink) {
    Write-Host "Установите PuTTY (plink) или выполните на сервере вручную:" -ForegroundColor Yellow
    Write-Host "  ssh ${VpsUser}@${VpsHost}"
    Write-Host "  bash deploy/bootstrap_vps.sh"
    exit 1
}

Write-Host "=== Загрузка bootstrap на сервер ===" -ForegroundColor Cyan
$bootstrap = Join-Path $Root "deploy\bootstrap_vps.sh"
$remoteCmd = @"
apt-get update -qq && apt-get install -y -qq git
mkdir -p /var/www/tour-generator
cd /var/www/tour-generator
if [ -d .git ]; then git pull; else git clone $RepoUrl .; fi
bash deploy/bootstrap_vps.sh $VpsHost
"@

& plink -batch -pw $env:VPS_PASS "${VpsUser}@${VpsHost}" $remoteCmd

Write-Host ""
Write-Host "Проверка: http://${VpsHost}/health" -ForegroundColor Green
