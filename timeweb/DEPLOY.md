# Деплой «под ключ» на Timeweb Cloud

Проект: **модуль генерации турпакета** (FastAPI + Vue + MySQL).

> Виртуальный хостинг **hosting.timeweb.ru** не подходит — нужен **Timeweb Cloud**: [timeweb.cloud](https://timeweb.cloud)

---

## Что получится

- Сайт с чатом: `https://ваш-домен.ru` или технический URL `*.timeweb.cloud`
- API: `/api/chat`, `/health`
- MySQL в облаке Timeweb
- Демо-режим: фраза «давай перейдем в режим демонстрации»

---

## Шаг 1. Регистрация и баланс

1. Откройте [timeweb.cloud](https://timeweb.cloud)
2. Войдите тем же аккаунтом, что и на hosting.timeweb.ru
3. Пополните баланс **~500–800 ₽** (App + MySQL на месяц)

---

## Шаг 2. Облачная MySQL

1. **Базы данных** → **Создать** → **MySQL 8**
2. Регион: **тот же**, что выберете для App Platform (например Москва)
3. Тариф: минимальный
4. Имя БД: `default_db` (или создайте `tour_generator` в phpMyAdmin)
5. **Сеть** → включите **«Доступ по публичному IP»** (для App Platform)
6. Вкладка **«Подключение»** — скопируйте:
   - Host (например `xxxxx.twc1.net`)
   - Port `3306`
   - User `gen_user`
   - Password
   - Database name

---

## Шаг 3. GitHub (обязательно для App Platform)

На ПК в PowerShell:

```powershell
cd D:\Diplom\tour-generator-module
git init
git add .
git commit -m "Deploy to Timeweb Cloud"
```

Создайте репозиторий на [github.com](https://github.com/new) (приватный можно).

```powershell
git remote add origin https://github.com/ВАШ_ЛОГИН/tour-generator.git
git branch -M main
git push -u origin main
```

Или запустите скрипт:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\prepare_timeweb.ps1
```

---

## Шаг 4. App Platform — Backend FastAPI

1. **App Platform** → **Добавить** → **Backend**
2. Фреймворк: **FastAPI**
3. Подключите **GitHub** → выберите репозиторий `tour-generator`
4. Ветка: `main`
5. Регион: **как у MySQL**

### Команды (если спрашивает вручную)

| Поле | Значение |
|------|----------|
| Команда сборки | `pip3 install --upgrade -r requirements.txt` |
| Команда запуска | `uvicorn main:app --host 0.0.0.0 --port 8000` |
| Путь проверки | `/health` |
| Python | 3.11 или 3.12 |

### Переменные окружения

Скопируйте `timeweb/.env.production.example` → заполните → в панели:

**App Platform → ваше приложение → Переменные → Загрузить из файла** (файл должен называться `.env`)

Минимум:

```env
DB_HOST=xxxxx.twc1.net
DB_PORT=3306
DB_USER=gen_user
DB_PASSWORD=ваш_пароль
DB_NAME=default_db
DB_SKIP_CREATE=true
DB_SSL_DISABLED=true

DEEPSEEK_API_KEY=sk-...
LLM_PROVIDER=auto
LLM_PRIMARY=gigachat

SEED_DEMO_ON_START=true
PORT=8000
```

6. **Запустить деплой**
7. Дождитесь зелёного статуса → откройте URL из вкладки **Дашборд**

---

## Шаг 5. Проверка

Откройте в браузере:

- `https://ВАШ-URL.timeweb.cloud/health` → `{"status":"ok","database":"connected"}`
- `https://ВАШ-URL.timeweb.cloud/` → чат
- Напишите: **давай перейдем в режим демонстрации**
- Затем: **Китай, с 10 июля по 20 июля, бюджет 80000 руб**

---

## Шаг 6. Свой домен (опционально)

1. В **hosting.timeweb.ru** или у регистратора домена
2. DNS → **A-запись** `@` и `www` → IP из App Platform (вкладка Дашборд)
3. В App Platform → **Домены** → добавить домен
4. SSL включится автоматически

Для вставки на bonvoyage28.ru:

```html
<iframe src="https://ваш-домен.ru" width="100%" height="850" style="border:none;"></iframe>
```

---

## Альтернатива: Docker Compose

Если FastAPI-шаблон не подходит:

1. App Platform → **Docker Compose**
2. Репозиторий тот же
3. Файл: `docker-compose.cloud.yml` (в корне)
4. Переменные — в панели (как в шаге 4)

---

## Частые ошибки

| Проблема | Решение |
|----------|---------|
| `Can't connect to MySQL` | Проверьте DB_HOST (домен `.twc1.net`, не IP), `DB_SKIP_CREATE=true`, публичный IP у БД |
| 502 / приложение не стартует | Логи во вкладке **Деплой**; проверьте `DEEPSEEK_API_KEY` |
| `/health` → degraded | Неверный пароль MySQL или БД недоступна из App Platform |
| ИИ не отвечает | Баланс DeepSeek или ключ GigaChat |
| Нет туров | `SEED_DEMO_ON_START=true` или фраза «режим демонстрации» |

---

## Стоимость (ориентир)

| Сервис | ~₽/мес |
|--------|--------|
| App Platform (минимум) | 200–400 |
| MySQL Cloud (минимум) | 200–350 |
| **Итого** | **400–750** |

---

## Файлы проекта для облака

| Файл | Назначение |
|------|------------|
| `main.py` | Точка входа для Timeweb |
| `requirements.txt` | Зависимости |
| `timeweb/.env.production.example` | Шаблон переменных |
| `docker-compose.cloud.yml` | Деплой через Docker |
| `Dockerfile` | Образ приложения |
