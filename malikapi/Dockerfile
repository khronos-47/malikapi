FROM python:3.10-slim

WORKDIR /app

# Установка системных зависимостей для psycopg2 и oracledb (thin режим не требует Oracle Instant Client)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000 8501

# Команда по умолчанию – запуск API (будет переопределена в compose)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]