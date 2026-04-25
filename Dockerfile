FROM python:3.12-slim

WORKDIR /app

# Установка PostgreSQL клиента (для psql при загрузке дампов)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY ./app /app/app
COPY ./templates /app/templates

# Создаем директорию для временных файлов
RUN mkdir -p /tmp/dumps

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]