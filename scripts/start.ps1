# Запуск из корня проекта (PowerShell)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Создан .env — укажите DEEPSEEK_API_KEY и пароль MySQL"
}

if (-not (Test-Path "venv")) {
    python -m venv venv
    & .\venv\Scripts\pip install -r requirements.txt
}

& .\venv\Scripts\python.exe run_server.py
