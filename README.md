# SQL Isolation Level Tester

Веб-приложение для тестирования SQL-запросов с различными уровнями изоляции транзакций в PostgreSQL.

## 📋 Описание

Приложение позволяет выполнять два SQL-запроса параллельно в разных транзакциях с заданным уровнем изоляции. Это полезно для:

- Тестирования поведения БД при разных уровнях изоляции
- Отладки конкурентных запросов
- Обучения работе с транзакциями в PostgreSQL

## 🚀 Быстрый старт

### Требования

- Python >= 3.14
- Docker и Docker Compose (для локального запуска БД)

### Запуск с Docker (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com/Arekabu/sql-requests-tester.git
cd sql-requests-tester

# Запустите PostgreSQL и веб-сервер
docker-compose up -d

# Приложение доступно по адресу: http://localhost:8000


Запуск без Docker (только веб-сервер)

Если у вас уже есть запущенный PostgreSQL, вы можете запустить только веб-сервер:
bash

# Установка зависимостей через uv (рекомендуется)
uv venv
uv sync

# Или через pip
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Запуск сервера
uvicorn app.main:app --host 0.0.0.0 --port 8000

Переменные окружения
Переменная	Значение по умолчанию	Описание
DB_HOST	localhost	Хост PostgreSQL
DB_PORT	5432	Порт PostgreSQL
DB_USER	postgres	Пользователь PostgreSQL
DB_PASSWORD	password	Пароль PostgreSQL
DB_NAME	isolation_demo	Имя базы данных
