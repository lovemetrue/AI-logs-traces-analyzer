import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from app.config import config
from app.services.otel_receiver import OTelReceiver
from app.services.vector_store import VectorStore
from app.services.ollama_trainer import OllamaTrainer
from app.api.routes import router as api_router

from app.services.incident_analyzer import IncidentAnalyzer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Observability Service")
    
    # Инициализация сервисов
    app.state.vector_store = VectorStore()
    app.state.ollama_trainer = OllamaTrainer(app.state.vector_store)

    # В lifespan после инициализации сервисов добавьте:
    app.state.incident_analyzer = IncidentAnalyzer(
        app.state.vector_store,
        app.state.ollama_trainer
    )
    # Запуск фоновых задач
    app.state.background_tasks = set()
    
    # Запуск периодического обучения
    if config.training.training_interval_hours > 0:
        task = asyncio.create_task(
            app.state.ollama_trainer.start_periodic_training()
        )
        app.state.background_tasks.add(task)
        task.add_done_callback(app.state.background_tasks.remove)
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Observability Service")
    
    # Остановка фоновых задач
    for task in app.state.background_tasks:
        task.cancel()
    
    await asyncio.gather(*app.state.background_tasks, return_exceptions=True)

# Создание FastAPI приложения
app = FastAPI(
    title="AI Observability Service",
    description="Real-time observability analysis with Ollama LLM",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение роутеров
otel_receiver = OTelReceiver()
app.include_router(otel_receiver.router)
app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "service": "AI Observability", 
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "components": {
            "api": "ok",
            "vector_store": "ok",  # В реальности нужно проверять подключение
            "ollama": "ok"         # В реальности нужно проверять подключение
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug,
        workers=config.api.workers
    )