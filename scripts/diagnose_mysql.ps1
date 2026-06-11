# Запуск: PowerShell от администратора
#   Set-ExecutionPolicy -Scope Process Bypass
#   d:\Diplom\tour-generator-module\scripts\diagnose_mysql.ps1

$ErrorActionPreference = "Continue"
Write-Host "=== MySQL97 diagnostics ===" -ForegroundColor Cyan

Write-Host "`n--- Service ---" -ForegroundColor Yellow
Get-Service MySQL97 -ErrorAction SilentlyContinue | Format-List Name, Status, StartType
sc.exe qc MySQL97 2>&1

Write-Host "`n--- Port 3306 ---" -ForegroundColor Yellow
netstat -ano | findstr ":3306"

Write-Host "`n--- MySQL folders ---" -ForegroundColor Yellow
$candidates = @(
    "$env:ProgramData\MySQL",
    "C:\Program Files\MySQL"
)
foreach ($c in $candidates) {
    if (Test-Path $c) {
        Write-Host "FOUND: $c"
        Get-ChildItem $c -Directory | ForEach-Object { Write-Host "  - $($_.FullName)" }
    }
}

Write-Host "`n--- my.ini files ---" -ForegroundColor Yellow
Get-ChildItem "$env:ProgramData\MySQL" -Recurse -Filter "my.ini" -ErrorAction SilentlyContinue |
    ForEach-Object { Write-Host $_.FullName }

Write-Host "`n--- Last error logs (.err) ---" -ForegroundColor Yellow
$errFiles = Get-ChildItem "$env:ProgramData\MySQL" -Recurse -Filter "*.err" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 3
foreach ($f in $errFiles) {
    Write-Host "`n>>> $($f.FullName) (last 25 lines):" -ForegroundColor Green
    Get-Content $f.FullName -Tail 25 -ErrorAction SilentlyContinue
}

Write-Host "`n--- mysqld validate-config ---" -ForegroundColor Yellow
$mysqldPaths = @(
    "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysqld.exe",
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe",
    "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe"
)
foreach ($m in $mysqldPaths) {
    if (Test-Path $m) {
        $ini = "$env:ProgramData\MySQL\MySQL Server 9.7\my.ini"
        if (-not (Test-Path $ini)) {
            $ver = Split-Path (Split-Path $m -Parent) -Leaf
            $ini = "$env:ProgramData\MySQL\$ver\my.ini"
        }
        Write-Host "Using: $m"
        Write-Host "Config: $ini"
        if (Test-Path $ini) {
            & $m --defaults-file="$ini" --validate-config 2>&1
        } else {
            Write-Host "my.ini not found at $ini"
        }
        break
    }
}

Write-Host "`n--- Event Log (last MySQL errors) ---" -ForegroundColor Yellow
Get-WinEvent -LogName Application -MaxEvents 30 -ErrorAction SilentlyContinue |
    Where-Object { $_.ProviderName -match 'MySQL|mysql' -or $_.Message -match 'MySQL' } |
    Select-Object -First 5 TimeCreated, Message |
    Format-List

Write-Host "`nDone. Copy this output and send to assistant." -ForegroundColor Cyan
