#!/bin/bash
# Ежедневное обновление каталога туров с bon-voyage28.ru
# Crontab: 0 3 * * * /var/www/tour-generator/scripts/cron_update_catalog.sh >> /var/log/tour-parser.log 2>&1

set -e
cd /var/www/tour-generator
source venv/bin/activate 2>/dev/null || true
python run_parser.py
