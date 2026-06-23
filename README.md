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
```

### Запуск без Docker (только веб-сервер)

Если у вас уже есть запущенный PostgreSQL, вы можете запустить только веб-сервер:

```bash
# Установка зависимостей через uv (рекомендуется)
uv venv
uv sync

# Или через pip
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Запуск сервера
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Переменные окружения

| Переменная      | Значение по умолчанию | Описание                     |
|-----------------|----------------------|------------------------------|
| DB_HOST         | localhost            | Хост PostgreSQL              |
| DB_PORT         | 5432                 | Порт PostgreSQL              |
| DB_USER         | postgres             | Пользователь PostgreSQL      |
| DB_PASSWORD     | password             | Пароль PostgreSQL            |
| DB_NAME         | isolation_demo       | Имя базы данных              |

## 🛠️ Технологии

| Компонент          | Технология                    |
|--------------------|-------------------------------|
| Язык               | Python 3.14                   |
| Веб-фреймворк      | FastAPI                       |
| Работа с БД        | asyncpg                       |
| Управление пакетами| uv (с поддержкой pip)         |
| Контейнеризация    | Docker + Docker Compose       |
| База данных        | PostgreSQL 17 Alpine          |

## 🧪 Использование

1. **Подключение к БД**: Введите параметры подключения и нажмите "Подключиться"
2. **Выбор уровня изоляции**: Выберите один из четырёх уровней:
   - READ UNCOMMITTED
   - READ COMMITTED
   - REPEATABLE READ
   - SERIALIZABLE
3. **Ввод запросов**: Введите два SQL-запроса
4. **Выполнение**: Нажмите "Выполнить параллельно" для запуска

### Пример запросов

```sql
-- Запрос 1 (SELECT)
SELECT * FROM users WHERE id = 1;

-- Запрос 2 (UPDATE)
UPDATE users SET balance = balance + 100 WHERE id = 1;
```

Результаты выполнения отображаются в виде таблиц с данными.

## 📡 API Endpoints

| Метод | Эндпоинт           | Описание                           |
|-------|--------------------|------------------------------------|
| POST  | `/connect_db`      | Подключение к БД                   |
| GET   | `/get_tables`      | Получение списка таблиц            |
| POST  | `/execute`         | Выполнение двух запросов параллельно |
| GET   | `/`                | Главная страница                   |

### Пример запроса к `/execute`

```json
{
  "query1": "SELECT
	age age1
FROM sql.trainers WHERE name = 'Misty';
SELECT pg_sleep(2);
SELECT
	age age2
FROM sql.trainers WHERE name = 'Misty';",
  "query2": "UPDATE sql.trainers SET age = age + 10 WHERE name = 'Misty';
SELECT
	age age_real
FROM sql.trainers WHERE name = 'Misty';",
  "isolation_level": "READ COMMITTED"
}
```

## 🐳 Docker-образ

Сборка образа:

```bash
docker build -t sql-isolation-tester .
docker-compose up -d
```

## 📝 Разработка

### Форматирование кода

Проект использует `ruff` для линтинга:

```bash
uv tool run ruff check .
uv tool run ruff format .
```

### Пре-коммит хуки

```bash
uv tool run pre-commit install
```
