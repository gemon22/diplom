#!/bin/bash
# Быстрая установка на VPS Timeweb (Ubuntu 22.04/24.04)
# Запуск от root: bash deploy/setup_vps.sh

set -e

APP_DIR="/var/www/tour-generator"
DOMAIN="${1:-}"

echo "==> Обновление системы"
apt update && apt upgrade -y

echo "==> Установка пакетов"
apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx git \
    default-libmysqlclient-dev build-essential pkg-config

echo "==> Копирование проекта в $APP_DIR"
mkdir -p "$APP_DIR"
# Если скрипт запущен из корня репозитория:
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
rsync -a --exclude venv --exclude __pycache__ --exclude .env "$SCRIPT_DIR/" "$APP_DIR/"

cd "$APP_DIR"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "!!! Отредактируйте $APP_DIR/.env (MySQL, API-ключи) и перезапустите сервис"
fi

echo "==> Systemd"
cp deploy/tour-generator.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable tour-generator
systemctl restart tour-generator

if [ -n "$DOMAIN" ]; then
    sed "s/YOUR_DOMAIN.ru/$DOMAIN/g" deploy/nginx.conf > /etc/nginx/sites-available/tour-generator
    ln -sf /etc/nginx/sites-available/tour-generator /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m admin@"$DOMAIN" || true
fi

echo ""
echo "Готово. Проверка: curl http://127.0.0.1:8000/api/llm/providers"
echo "Логи: journalctl -u tour-generator -f"
