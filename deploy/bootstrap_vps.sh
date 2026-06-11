#!/bin/bash
# Полная установка на VPS Timeweb (Ubuntu). Запуск на сервере от root:
#   curl -sL https://raw.githubusercontent.com/gemon22/diplom/main/deploy/bootstrap_vps.sh | bash
# или после git clone:
#   bash deploy/bootstrap_vps.sh

set -e

APP_DIR="/var/www/tour-generator"
REPO_URL="${REPO_URL:-https://github.com/gemon22/diplom.git}"
DOMAIN="${1:-185.177.219.244}"
DB_PASS="${DB_PASS:-$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 20)}"

echo "==> Обновление системы"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nginx git \
    mysql-server default-libmysqlclient-dev build-essential pkg-config curl

echo "==> MySQL"
systemctl enable mysql
systemctl start mysql

mysql -e "CREATE DATABASE IF NOT EXISTS tour_generator CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS 'tour_user'@'localhost' IDENTIFIED BY '${DB_PASS}';" 2>/dev/null || \
  mysql -e "ALTER USER 'tour_user'@'localhost' IDENTIFIED BY '${DB_PASS}';"
mysql -e "GRANT ALL PRIVILEGES ON tour_generator.* TO 'tour_user'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

echo "==> Клонирование репозитория"
mkdir -p /var/www
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR" && git pull
else
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "==> Python venv"
python3 -m venv venv
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q

echo "==> .env"
cat > .env <<EOF
DB_HOST=localhost
DB_PORT=3306
DB_USER=tour_user
DB_PASSWORD=${DB_PASS}
DB_NAME=tour_generator
DB_SKIP_CREATE=true

DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}
GIGACHAT_CREDENTIALS=${GIGACHAT_CREDENTIALS:-}
LLM_PROVIDER=auto
LLM_PRIMARY=gigachat
LLM_FALLBACK=true

SITE_PRIMARY_URL=https://bon-voyage28.ru/
AGENCY_CONTACT_URL=https://bon-voyage28.ru/contacts/
SEED_DEMO_ON_START=true
PORT=8000
EOF
chmod 600 .env

echo "==> Systemd"
cp deploy/tour-generator.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable tour-generator
systemctl restart tour-generator

echo "==> Nginx"
sed "s/YOUR_DOMAIN.ru/${DOMAIN}/g; s/www\.YOUR_DOMAIN.ru//g" deploy/nginx.conf > /etc/nginx/sites-available/tour-generator
ln -sf /etc/nginx/sites-available/tour-generator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "============================================"
echo " ГОТОВО"
echo " Сайт: http://${DOMAIN}/"
echo " Health: http://${DOMAIN}/health"
echo " MySQL user: tour_user"
echo " MySQL pass: ${DB_PASS}"
echo " Файл .env: ${APP_DIR}/.env"
echo "============================================"
echo "Добавьте DEEPSEEK_API_KEY в ${APP_DIR}/.env и: systemctl restart tour-generator"
