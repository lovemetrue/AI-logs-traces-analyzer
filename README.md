# AI-observer

### Микросервис для приёма телеметрии (логи, метрики, трейсы) из Kubernetes кластера и AI анализа.

### Структура проекта

```
ai-observer/
├── app/                          # Основной код Python
│   ├── __init__.py
│   ├── main.py                   # Точка входа
│   ├── config.py                 # Конфигурация
│   ├── models/                   # Модели данных
│   │   ├── __init__.py
│   │   ├── telemetry.py          # Модели для телеметрии
│   │   └── training.py           # Модели для обучения
│   ├── services/                 # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── otel_receiver.py      # Приемник OTLP данных
│   │   ├── vector_store.py       # Работа с ChromaDB
│   │   ├── ollama_trainer.py     # Обучение Ollama
│   │   └── incident_analyzer.py  # Анализатор инцидентов
│   ├── api/                      # API endpoints
│   │   ├── __init__.py
│   │   ├── routes.py             # Маршруты FastAPI
│   │   └── models.py             # Pydantic модели для API
│   └── utils/                    # Утилиты
│       ├── __init__.py
│       ├── logging.py            # Настройка логирования
│       └── helpers.py            # Вспомогательные функции
├── data/                         # Данные для обучения
│   ├── raw/                      # Сырые данные
│   └── processed/                # Обработанные данные
├── models/                       # Сохраненные модели
├── storage/                      # Хранилище ChromaDB
├── tests/                        # Тесты
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml               # Конфигурация проекта
├── .env.example                 # Пример переменных окружения
└── README.md
```