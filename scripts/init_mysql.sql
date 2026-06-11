-- Выполнить в MySQL Workbench или: mysql -u root -p < scripts/init_mysql.sql
CREATE DATABASE IF NOT EXISTS tour_generator
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE tour_generator;

-- Таблицы создаются автоматически при первом запуске backend/database.py
