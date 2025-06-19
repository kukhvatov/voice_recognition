FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry или pip — здесь pip
WORKDIR /app

COPY requirements/production.txt .

RUN pip install --no-cache-dir -r production.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "web.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
