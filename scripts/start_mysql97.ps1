# Запуск MySQL 9.7 (установка в D:\MySQL) — PowerShell от администратора
$MysqlBin = "D:\MySQL\bin"
$IniFile  = "D:\MySQL\SQL CONFIGURATOR\my.ini"

if (-not (Test-Path $IniFile)) {
    Write-Error "Не найден: $IniFile"
    exit 1
}

Write-Host "Проверка конфига..."
& "$MysqlBin\mysqld.exe" --defaults-file="$IniFile" --validate-config
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Запуск службы MySQL97..."
net start MySQL97

Write-Host "Проверка подключения (введите пароль root при запросе)..."
& "$MysqlBin\mysql.exe" --defaults-file="$IniFile" -u root -p -e "SELECT VERSION(); SHOW DATABASES LIKE 'tour_generator';"
