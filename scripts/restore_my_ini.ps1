# Восстановление my.ini для MySQL 9.7 на D:\MySQL
# Запуск: PowerShell от администратора

$ini     = "D:\MySQL\SQL CONFIGURATOR\my.ini"
$backup  = "D:\MySQL\SQL CONFIGURATORmy_2026-05-15T20-25-01.ini"
$mysqld  = "D:\MySQL\bin\mysqld.exe"

if (-not (Test-Path $backup)) {
    Write-Error "Резервная копия не найдена: $backup"
    exit 1
}

Copy-Item -LiteralPath $ini -Destination "$ini.broken_$(Get-Date -Format yyyyMMdd_HHmmss)" -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $backup -Destination $ini -Force
Write-Host "Восстановлен: $ini"

& $mysqld --defaults-file="$ini" --validate-config
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Запуск службы..."
net start MySQL97
