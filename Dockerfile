FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директорий для данных
RUN mkdir -p data/raw data/processed models storage

# Создание volume для моделей Ollama
VOLUME /root/.ollama

# Экспорт портов
EXPOSE 8080

# Запуск сервиса
CMD ["python", "-m", "app.main"]