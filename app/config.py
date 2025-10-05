import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        # Ollama Configuration
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "mistral")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        self.ollama_num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        self.ollama_temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.3"))

        # ChromaDB Configuration
        self.chroma_host = os.getenv("CHROMA_HOST", "http://localhost:8000")
        self.chroma_db_path = os.getenv("CHROMA_DB_PATH", "./storage/chroma")
        self.collection_logs = "observability_logs"
        self.collection_traces = "observability_traces"
        self.collection_incidents = "incident_patterns"

        # OpenTelemetry Configuration
        self.otel_endpoint = os.getenv("OTEL_ENDPOINT", "http://otelier:4318")
        self.service_name = os.getenv("SERVICE_NAME", "ai-observability")
        self.otel_timeout = int(os.getenv("OTEL_TIMEOUT", "30"))
        self.otel_batch_size = int(os.getenv("OTEL_BATCH_SIZE", "100"))

        # Training Configuration
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "512"))
        self.overlap_size = int(os.getenv("OVERLAP_SIZE", "50"))
        self.batch_size = int(os.getenv("BATCH_SIZE", "32"))
        self.max_sequence_length = int(os.getenv("MAX_SEQUENCE_LENGTH", "2048"))
        self.training_interval_hours = int(os.getenv("TRAINING_INTERVAL_HOURS", "6"))

        # API Configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8080"))
        self.api_workers = int(os.getenv("API_WORKERS", "1"))
        self.api_debug = os.getenv("API_DEBUG", "false").lower() == "true"

        # General Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.environment = os.getenv("ENVIRONMENT", "production")


config = Config()