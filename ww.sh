#!/bin/bash

# Создаём корневую директорию проекта (опционально — можно запускать в пустой папке)
PROJECT_ROOT="."
cd "$PROJECT_ROOT"

# Функция для создания файла, если он не существует
create_file() {
    local filepath="$1"
    mkdir -p "$(dirname "$filepath")"
    if [ ! -f "$filepath" ]; then
        touch "$filepath"
        echo "# Auto-generated file" > "$filepath"
    fi
}

# === 1. Папка app/ и подпапки ===
create_file "app/__init__.py"
create_file "app/main.py"
create_file "app/config.py"

# models/
create_file "app/models/__init__.py"
create_file "app/models/telemetry.py"
create_file "app/models/training.py"

# services/
create_file "app/services/__init__.py"
create_file "app/services/otel_receiver.py"
create_file "app/services/vector_store.py"
create_file "app/services/ollama_trainer.py"
create_file "app/services/incident_analyzer.py"

# api/
create_file "app/api/__init__.py"
create_file "app/api/routes.py"
create_file "app/api/models.py"

# utils/
create_file "app/utils/__init__.py"
create_file "app/utils/logging.py"
create_file "app/utils/helpers.py"

# === 2. Корневые папки ===
mkdir -p data/raw
mkdir -p data/processed
mkdir -p models
mkdir -p storage
mkdir -p tests

# === 3. Корневые файлы ===
create_file "docker-compose.yml"
create_file "Dockerfile"
create_file "requirements.txt"
create_file "pyproject.toml"
create_file ".env.example"
create_file "README.md"

# === 4. Добавим базовое содержимое в ключевые файлы (опционально) ===

# README.md
cat > README.md << 'EOF'
# Observability-to-LLM Pipeline

Микросервис для приёма телеметрии (логи, метрики, трейсы) из Kubernetes и анализа через LLM.
EOF

# .env.example
cat > .env.example << 'EOF'
# Пример переменных окружения
LLM_MODEL=llama3
CHROMA_PATH=./storage/chroma
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=INFO
EOF

# requirements.txt (минимальный набор)
cat > requirements.txt << 'EOF'
fastapi==0.111.0
uvicorn==0.29.0
pydantic==2.7.1
opentelemetry-api==1.24.0
opentelemetry-sdk==1.24.0
chromadb==0.5.0
sentence-transformers==3.0.1
langchain==0.2.3
ollama==0.1.8
python-dotenv==1.0.1
numpy==1.26.4
pandas==2.2.2
EOF

# pyproject.toml
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "observability-llm"
version = "0.1.0"
description = "LLM-powered observability analyzer"
dependencies = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "chromadb",
    "langchain",
    "ollama",
    "python-dotenv"
]
EOF

# Dockerfile (простой шаблон)
cat > Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  observability-llm:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CHROMA_PATH=/app/storage/chroma
    volumes:
      - ./storage:/app/storage
    restart: unless-stopped
EOF

echo "✅ Структура проекта успешно создана!"
echo "📁 Проверьте содержимое текущей директории."
