import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class OllamaConfig:
    host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model: str = os.getenv("OLLAMA_MODEL", "mistral")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    num_ctx: int = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
    temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.3"))

@dataclass
class ChromaConfig:
    host: str = os.getenv("CHROMA_HOST", "http://localhost:8000")
    path: str = os.getenv("CHROMA_DB_PATH", "./storage/chroma")
    collection_logs: str = "observability_logs"
    collection_traces: str = "observability_traces"
    collection_incidents: str = "incident_patterns"

@dataclass
class OTelConfig:
    endpoint: str = os.getenv("OTEL_ENDPOINT", "http://otelier:4318")
    service_name: str = os.getenv("SERVICE_NAME", "ai-observability")
    timeout: int = int(os.getenv("OTEL_TIMEOUT", "30"))
    batch_size: int = int(os.getenv("OTEL_BATCH_SIZE", "100"))

@dataclass
class TrainingConfig:
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "512"))
    overlap_size: int = int(os.getenv("OVERLAP_SIZE", "50"))
    batch_size: int = int(os.getenv("BATCH_SIZE", "32"))
    max_sequence_length: int = int(os.getenv("MAX_SEQUENCE_LENGTH", "2048"))
    training_interval_hours: int = int(os.getenv("TRAINING_INTERVAL_HOURS", "6"))

@dataclass
class APIConfig:
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8080"))
    workers: int = int(os.getenv("API_WORKERS", "1"))
    debug: bool = os.getenv("API_DEBUG", "false").lower() == "true"

@dataclass
class Config:
    ollama: OllamaConfig = OllamaConfig()
    chroma: ChromaConfig = ChromaConfig()
    otel: OTelConfig = OTelConfig()
    training: TrainingConfig = TrainingConfig()
    api: APIConfig = APIConfig()
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    environment: str = os.getenv("ENVIRONMENT", "production")

config = Config()