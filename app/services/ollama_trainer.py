import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import ollama
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np

from app.config import config
from app.models.telemetry import OTLPLog, OTLPSpan, TrainingExample
from app.services.vector_store import VectorStore

class OllamaTrainer:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.ollama_client = ollama.Client(host=config.ollama.host)
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.training_history = []
        
        # Проверяем доступность Ollama
        self._check_ollama_connection()
    
    def _check_ollama_connection(self):
        """Проверка подключения к Ollama"""
        try:
            models = self.ollama_client.list()
            logger.info(f"Connected to Ollama. Available models: {[m['name'] for m in models['models']]}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    async def start_periodic_training(self):
        """Запуск периодического обучения"""
        while True:
            try:
                logger.info("Starting periodic training cycle")
                await self.train_observability_model()
                
                # Ждем заданный интервал
                await asyncio.sleep(config.training.training_interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"Error in periodic training: {e}")
                await asyncio.sleep(300)  # Ждем 5 минут перед повторной попыткой
    
    async def train_observability_model(self, model_name: str = "observability-expert"):
        """Основной метод обучения модели observability"""
        try:
            logger.info(f"Starting training for model: {model_name}")
            
            # 1. Сбор данных для обучения
            training_data = await self._gather_training_data()
            
            if not training_data:
                logger.warning("No training data available")
                return False
            
            # 2. Подготовка обучающих примеров
            training_examples = self._prepare_training_examples(training_data)
            
            # 3. Сохранение примеров в векторную БД
            await self.vector_store.store_training_examples(training_examples)
            
            # 4. Создание Modelfile
            modelfile_content = self._create_modelfile(training_examples)
            
            # 5. Создание/обновление модели в Ollama
            success = await self._create_or_update_model(model_name, modelfile_content)
            
            if success:
                logger.info(f"Model {model_name} trained successfully with {len(training_examples)} examples")
                self.training_history.append({
                    'timestamp': datetime.now(),
                    'model_name': model_name,
                    'examples_count': len(training_examples),
                    'status': 'success'
                })
            else:
                logger.error(f"Failed to train model {model_name}")
                self.training_history.append({
                    'timestamp': datetime.now(),
                    'model_name': model_name,
                    'examples_count': len(training_examples),
                    'status': 'failed'
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Error in train_observability_model: {e}")
            return False
    
    async def _gather_training_data(self) -> Dict[str, Any]:
        """Сбор данных для обучения из различных источников"""
        training_data = {
            'logs': [],
            'traces': [],
            'synthetic': []
        }
        
        try:
            # Получаем данные из векторной БД (последние 24 часа)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # Здесь можно добавить логику получения данных из векторной БД
            # Пока используем синтетические данные для демонстрации
            
            training_data['synthetic'] = self._generate_synthetic_training_data()
            
            logger.info(f"Gathered training data: {len(training_data['synthetic'])} synthetic examples")
            return training_data
            
        except Exception as e:
            logger.error(f"Error gathering training data: {e}")
            return training_data
    
    def _generate_synthetic_training_data(self) -> List[Dict[str, Any]]:
        """Генерация синтетических обучающих данных"""
        synthetic_data = [
            # Примеры с логами
            {
                'type': 'log_error',
                'input': 'В логах auth-service появляются ошибки: "Redis connection timeout after 5000ms"',
                'output': """КОРЕНЬ ПРОБЛЕМЫ: Проблемы с подключением к Redis серверу
СИМПТОМЫ: Таймауты подключения к Redis, ошибки аутентификации
ВЛИЯНИЕ: Пользователи не могут войти в систему, сервис аутентификации недоступен
РЕКОМЕНДАЦИИ:
1. Проверить доступность Redis сервера и сетевые настройки
2. Увеличить timeout подключения к Redis
3. Добавить retry механизм для подключений
4. Мониторить использование памяти Redis""",
                'services': ['auth-service'],
                'severity': 'high'
            },
            {
                'type': 'log_warning', 
                'input': 'В логах payment-service предупреждения: "High response time detected: 4500ms for processPayment"',
                'output': """КОРЕНЬ ПРОБЛЕМЫ: Высокая задержка в обработке платежей
СИМПТОМЫ: Медленные ответы от payment-service, предупреждения в логах
ВЛИЯНИЕ: Пользователи испытывают задержки при оплате, возможны таймауты
РЕКОМЕНДАЦИИ:
1. Проверить нагрузку на базу данных платежей
2. Оптимизировать запросы к внешним платежным шлюзам
3. Рассмотреть кэширование часто используемых данных
4. Увеличить ресурсы сервиса при необходимости""",
                'services': ['payment-service'],
                'severity': 'medium'
            },
            
            # Примеры с трейсами
            {
                'type': 'trace_latency',
                'input': 'Трейс показывает высокую задержку между user-service и order-service: 2.3s при норме 200ms',
                'output': """КОРЕНЬ ПРОБЛЕМЫ: Высокая сетевая задержка между микросервисами
СИМПТОМЫ: Медленные вызовы между user-service и order-service
ВЛИЯНИЕ: Задержки в создании заказов, плохой пользовательский опыт
РЕКОМЕНДАЦИИ:
1. Проверить сетевую связность между нодами
2. Оптимизировать размер передаваемых данных
3. Рассмотреть использование gRPC вместо HTTP для внутренней коммуникации
4. Добавить circuit breaker для graceful degradation""",
                'services': ['user-service', 'order-service'],
                'severity': 'high'
            },
            {
                'type': 'trace_error',
                'input': 'В трейсе обнаружена ошибка 500 при вызове inventory-service из order-service',
                'output': """КОРЕНЬ ПРОБЛЕМЫ: Сервис inventory-service возвращает ошибки 500
СИМПТОМЫ: Сбои при проверке наличия товара, прерванные заказы
ВЛИЯНИЕ: Пользователи не могут завершить заказ, потеря продаж
РЕКОМЕНДАЦИИ:
1. Проверить логи inventory-service на наличие исключений
2. Убедиться в доступности базы данных inventory
3. Временно увеличить количество реплик inventory-service
4. Реализовать fallback механизм для случаев недоступности""",
                'services': ['order-service', 'inventory-service'],
                'severity': 'critical'
            },
            
            # Примеры с метриками
            {
                'type': 'metric_anomaly',
                'input': 'Резкий рост потребления CPU на нодах с order-service с 30% до 95% за 5 минут',
                'output': """КОРЕНЬ ПРОБЛЕМЫ: Неожиданный рост нагрузки или утечка ресурсов
СИМПТОМЫ: Высокое использование CPU, возможные таймауты
ВЛИЯНИЕ: Замедление работы order-service, возможные сбои
РЕКОМЕНДАЦИИ:
1. Немедленно масштабировать order-service
2. Проверить на наличие бесконечных циклов или рекурсий
3. Анализировать логи на предмет аномальной активности
4. Рассмотреть горизонтальное масштабирование""",
                'services': ['order-service'],
                'severity': 'critical'
            },
            {
                'type': 'metric_memory',
                'input': 'Постепенный рост использования памяти notification-service до 85% за 2 часа',
                'output': """КОРЕНЬ ПРОБЛЕМЫ: Возможная утечка памяти или неэффективное использование
СИМПТОМЫ: Постепенный рост использования памяти, снижение производительности
ВЛИЯНИЕ: Риск OOM killer, перезапуски сервиса
РЕКОМЕНДАЦИИ:
1. Провести профилирование памяти приложения
2. Проверить на утечки памяти в коде
3. Увеличить лимиты памяти для pod
4. Настроить автоматическое масштабирование по памяти""",
                'services': ['notification-service'],
                'severity': 'medium'
            }
        ]
        
        return synthetic_data
    
    def _prepare_training_examples(self, training_data: Dict[str, Any]) -> List[TrainingExample]:
        """Подготовка обучающих примеров из собранных данных"""
        examples = []
        
        # Обрабатываем синтетические данные
        for synthetic in training_data.get('synthetic', []):
            example = TrainingExample(
                input=synthetic['input'],
                output=synthetic['output'],
                pattern_type=synthetic['type'],
                services=synthetic['services'],
                severity=synthetic['severity'],
                source_data=synthetic
            )
            examples.append(example)
        
        # Здесь можно добавить обработку реальных данных из логов и трейсов
        # examples.extend(self._prepare_examples_from_real_data(training_data))
        
        logger.info(f"Prepared {len(examples)} training examples")
        return examples
    
    def _create_modelfile(self, training_examples: List[TrainingExample]) -> str:
        """Создание Modelfile для Ollama"""
        modelfile = f"""FROM {config.ollama.model}

# Системный промпт для observability анализа
SYSTEM \"\"\"Ты - опытный DevOps инженер и SRE специалист с глубокими знаниями в микросервисной архитектуре, Kubernetes и облачных технологиях.

Твоя задача - анализировать логи, трейсы, метрики и другие observability данные для выявления проблем в распределенных системах.

Структура ответа ДОЛЖНА быть следующей:
1. КОРЕНЬ ПРОБЛЕМЫ: краткое и точное описание основной причины
2. СИМПТОМЫ: перечень наблюдаемых проблем и аномалий
3. ВЛИЯНИЕ: на какие компоненты/пользователей/бизнес-процессы влияет
4. РЕКОМЕНДАЦИИ: конкретные, выполнимые шаги по решению (пронумерованный список)

Будь технически точным, предлагай практические решения и учитывай контекст микросервисной архитектуры.
Используй профессиональную терминологию, но объясняй сложные понятия доступно.\"\"\"

# Параметры модели для observability анализа
PARAMETER temperature 0.3
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER num_ctx {config.ollama.num_ctx}

# Template для анализа observability данных
TEMPLATE \"\"\"{{{{ if .System }}}}<|start_header_id|>system<|end_header_id|>

{{{{ .System }}}}<|eot_id|>{{{{ end }}}}

{{{{ if .Prompt }}}}<|start_header_id|>user<|end_header_id|>

{{{{ .Prompt }}}}<|eot_id|>{{{{ end }}}}

<|start_header_id|>assistant<|end_header_id|>

\"\"\"

"""

        # Добавляем few-shot learning примеры
        modelfile += "# Few-shot learning examples for observability analysis\n"
        
        for i, example in enumerate(training_examples[:15]):  # Ограничиваем количество примеров
            modelfile += f"\n# Пример {i+1}: {example.pattern_type}\n"
            modelfile += f"MESSAGE user \"\"\"{example.input}\"\"\"\n"
            modelfile += f"MESSAGE assistant \"\"\"{example.output}\"\"\"\n"
        
        return modelfile
    
    async def _create_or_update_model(self, model_name: str, modelfile_content: str) -> bool:
        """Создание или обновление модели в Ollama"""
        try:
            logger.info(f"Creating/updating model {model_name} in Ollama")
            
            # Создаем модель
            response = self.ollama_client.create(
                model=model_name,
                modelfile=modelfile_content
            )
            
            if 'status' in response and response['status'] == 'success':
                logger.info(f"Model {model_name} successfully created/updated")
                return True
            else:
                logger.error(f"Failed to create model: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating model in Ollama: {e}")
            return False
    
    async def generate_analysis(self, prompt: str, model_name: str = "observability-expert") -> str:
        """Генерация анализа с использованием обученной модели"""
        try:
            response = self.ollama_client.generate(
                model=model_name,
                prompt=prompt,
                options={
                    'temperature': config.ollama.temperature,
                    'top_k': 40,
                    'top_p': 0.9,
                }
            )
            
            return response['response']
            
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            return f"Ошибка при анализе: {str(e)}"
    
    def get_training_status(self) -> Dict[str, Any]:
        """Получение статуса обучения"""
        return {
            'training_history': self.training_history,
            'last_training': self.training_history[-1] if self.training_history else None,
            'ollama_connected': self._check_ollama_connection()
        }