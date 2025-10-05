Зоны ответственности.

Kubernetes Cluster (продакшн)
├── Oteleier (сбор телеметрии)
├── Микросервисы
└── Ingress → направляет данные наружу

VDS (аналитика и AI)
├── Go-сервис (прием и анализ)
├── Ollama (LLM)
├── ChromaDB (векторная БД)
└── Open Web UI