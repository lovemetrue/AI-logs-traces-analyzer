import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
import pandas as pd
import numpy as np

from app.config import config
from app.models.telemetry import OTLPLog, OTLPSpan, OTLPMetric, IncidentPattern
from app.services.vector_store import VectorStore
from app.services.ollama_trainer import OllamaTrainer


class IncidentAnalyzer:
    def __init__(self, vector_store: VectorStore, ollama_trainer: OllamaTrainer):
        self.vector_store = vector_store
        self.ollama_trainer = ollama_trainer
        self.incident_patterns = []
        self.active_incidents = []

        # Загружаем базовые паттерны инцидентов
        self._load_incident_patterns()

    def _load_incident_patterns(self):
        """Загрузка базовых паттернов инцидентов"""
        self.incident_patterns = [
            IncidentPattern(
                id="high_latency",
                pattern_type="trace_latency",
                description="Высокая задержка в цепочке вызовов микросервисов",
                symptoms=["Response time > 1s", "Slow database queries", "Network latency"],
                root_causes=["Database overload", "Network issues", "Inefficient code", "Resource constraints"],
                recommendations=["Scale the service", "Optimize database queries", "Add caching",
                                 "Check network connectivity"],
                severity="high",
                services_affected=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            IncidentPattern(
                id="service_error",
                pattern_type="log_error",
                description="Частые ошибки в сервисе",
                symptoms=["5xx errors in logs", "Failed requests", "Exception stack traces"],
                root_causes=["Bug in code", "Dependency failure", "Configuration issues", "Resource exhaustion"],
                recommendations=["Check application logs", "Verify dependencies", "Review recent deployments",
                                 "Check resource usage"],
                severity="medium",
                services_affected=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            IncidentPattern(
                id="memory_pressure",
                pattern_type="metric_anomaly",
                description="Высокое потребление памяти",
                symptoms=["Memory usage > 80%", "Frequent garbage collection", "OOM killer activations"],
                root_causes=["Memory leaks", "Inefficient data structures", "High load", "Insufficient resources"],
                recommendations=["Profile memory usage", "Check for memory leaks", "Increase memory limits",
                                 "Scale horizontally"],
                severity="high",
                services_affected=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

    async def analyze_realtime_data(self, logs: List[OTLPLog], spans: List[OTLPSpan], metrics: List[OTLPMetric]) -> \
    List[Dict[str, Any]]:
        """Анализ данных в реальном времени на наличие инцидентов"""
        incidents = []

        try:
            # Анализ логов на ошибки
            log_incidents = await self._analyze_logs_for_incidents(logs)
            incidents.extend(log_incidents)

            # Анализ трейсов на проблемы производительности
            trace_incidents = await self._analyze_traces_for_incidents(spans)
            incidents.extend(trace_incidents)

            # Анализ метрик на аномалии
            metric_incidents = await self._analyze_metrics_for_anomalies(metrics)
            incidents.extend(metric_incidents)

            # Обогащение инцидентов с помощью AI
            enriched_incidents = await self._enrich_incidents_with_ai(incidents)

            # Сохранение значимых инцидентов
            significant_incidents = [inc for inc in enriched_incidents if
                                     inc.get('severity', 'low') in ['medium', 'high', 'critical']]
            self.active_incidents.extend(significant_incidents)

            logger.info(f"Detected {len(significant_incidents)} significant incidents")
            return significant_incidents

        except Exception as e:
            logger.error(f"Error in realtime analysis: {e}")
            return []

    async def _analyze_logs_for_incidents(self, logs: List[OTLPLog]) -> List[Dict[str, Any]]:
        """Анализ логов для выявления инцидентов"""
        incidents = []

        # Группируем логи по сервису
        logs_by_service = {}
        for log in logs:
            service = log.service_name
            if service not in logs_by_service:
                logs_by_service[service] = []
            logs_by_service[service].append(log)

        # Анализируем каждый сервис
        for service, service_logs in logs_by_service.items():
            service_incidents = await self._analyze_service_logs(service, service_logs)
            incidents.extend(service_incidents)

        return incidents

    async def _analyze_service_logs(self, service: str, logs: List[OTLPLog]) -> List[Dict[str, Any]]:
        """Анализ логов конкретного сервиса"""
        incidents = []

        # Счетчики по типам логов
        error_count = 0
        warning_count = 0
        total_logs = len(logs)

        # Ключевые слова для классификации
        error_keywords = ['error', 'exception', 'failed', 'timeout', 'crash', 'panic']
        warning_keywords = ['warning', 'slow', 'delay', 'retry', 'fallback']

        for log in logs:
            log_text = str(log.body).lower()

            # Проверяем на ошибки
            if any(keyword in log_text for keyword in error_keywords):
                error_count += 1

            # Проверяем на предупреждения
            if any(keyword in log_text for keyword in warning_keywords):
                warning_count += 1

        # Определяем серьезность инцидента на основе статистики
        if total_logs > 0:
            error_rate = error_count / total_logs
            warning_rate = warning_count / total_logs

            if error_rate > 0.1:  # Более 10% ошибок
                incidents.append({
                    'type': 'log_errors',
                    'service': service,
                    'severity': 'critical',
                    'description': f'Высокий уровень ошибок в сервисе {service}',
                    'metrics': {
                        'error_count': error_count,
                        'warning_count': warning_count,
                        'total_logs': total_logs,
                        'error_rate': error_rate
                    },
                    'timestamp': datetime.now()
                })
            elif error_rate > 0.05:  # Более 5% ошибок
                incidents.append({
                    'type': 'log_errors',
                    'service': service,
                    'severity': 'high',
                    'description': f'Повышенный уровень ошибок в сервисе {service}',
                    'metrics': {
                        'error_count': error_count,
                        'warning_count': warning_count,
                        'total_logs': total_logs,
                        'error_rate': error_rate
                    },
                    'timestamp': datetime.now()
                })
            elif warning_rate > 0.2:  # Более 20% предупреждений
                incidents.append({
                    'type': 'log_warnings',
                    'service': service,
                    'severity': 'medium',
                    'description': f'Много предупреждений в сервисе {service}',
                    'metrics': {
                        'error_count': error_count,
                        'warning_count': warning_count,
                        'total_logs': total_logs,
                        'warning_rate': warning_rate
                    },
                    'timestamp': datetime.now()
                })

        return incidents

    async def _analyze_traces_for_incidents(self, spans: List[OTLPSpan]) -> List[Dict[str, Any]]:
        """Анализ трейсов для выявления инцидентов"""
        incidents = []

        if not spans:
            return incidents

        # Группируем спаны по сервису и операции
        spans_by_service = {}
        for span in spans:
            service = span.service_name
            if service not in spans_by_service:
                spans_by_service[service] = []
            spans_by_service[service].append(span)

        # Анализируем каждый сервис
        for service, service_spans in spans_by_service.items():
            service_incidents = await self._analyze_service_traces(service, service_spans)
            incidents.extend(service_incidents)

        return incidents

    async def _analyze_service_traces(self, service: str, spans: List[OTLPSpan]) -> List[Dict[str, Any]]:
        """Анализ трейсов конкретного сервиса"""
        incidents = []

        if not spans:
            return incidents

        # Собираем метрики
        durations = []
        error_count = 0
        total_spans = len(spans)

        for span in spans:
            duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
            durations.append(duration_ms)

            if span.status_code != "OK":
                error_count += 1

        # Анализируем метрики
        if durations:
            avg_duration = np.mean(durations)
            p95_duration = np.percentile(durations, 95)
            max_duration = np.max(durations)
            error_rate = error_count / total_spans if total_spans > 0 else 0

            # Проверяем на высокую задержку
            if p95_duration > 1000:  # P95 > 1s
                incidents.append({
                    'type': 'high_latency',
                    'service': service,
                    'severity': 'high',
                    'description': f'Высокая задержка в сервисе {service}',
                    'metrics': {
                        'p95_duration_ms': p95_duration,
                        'avg_duration_ms': avg_duration,
                        'max_duration_ms': max_duration,
                        'error_rate': error_rate
                    },
                    'timestamp': datetime.now()
                })

            # Проверяем на ошибки
            if error_rate > 0.1:  # Более 10% ошибок
                incidents.append({
                    'type': 'trace_errors',
                    'service': service,
                    'severity': 'critical',
                    'description': f'Много ошибок в трейсах сервиса {service}',
                    'metrics': {
                        'error_count': error_count,
                        'total_spans': total_spans,
                        'error_rate': error_rate
                    },
                    'timestamp': datetime.now()
                })

        return incidents

    async def _analyze_metrics_for_anomalies(self, metrics: List[OTLPMetric]) -> List[Dict[str, Any]]:
        """Анализ метрик на аномалии"""
        incidents = []

        # Группируем метрики по имени и атрибутам
        metrics_by_name = {}
        for metric in metrics:
            key = f"{metric.name}_{json.dumps(metric.attributes, sort_keys=True)}"
            if key not in metrics_by_name:
                metrics_by_name[key] = []
            metrics_by_name[key].append(metric)

        # Анализируем каждую группу метрик
        for key, metric_group in metrics_by_name.items():
            if len(metric_group) < 5:  # Нужно достаточно точек для анализа
                continue

            values = [m.value for m in metric_group]
            timestamps = [m.timestamp for m in metric_group]

            # Простой анализ аномалий (можно заменить на более сложные алгоритмы)
            anomaly_incidents = await self._detect_metric_anomalies(key, values, timestamps, metric_group[0])
            incidents.extend(anomaly_incidents)

        return incidents

    async def _detect_metric_anomalies(self, metric_key: str, values: List[float], timestamps: List[datetime],
                                       metric: OTLPMetric) -> List[Dict[str, Any]]:
        """Обнаружение аномалий в метриках"""
        incidents = []

        if not values:
            return incidents

        # Простые правила для демонстрации
        current_value = values[-1]
        avg_value = np.mean(values[:-1]) if len(values) > 1 else current_value

        metric_name = metric.name

        # Правила для разных типов метрик
        if 'cpu' in metric_name.lower():
            if current_value > 80:  # CPU > 80%
                incidents.append({
                    'type': 'high_cpu',
                    'service': metric.attributes.get('service', 'unknown'),
                    'severity': 'high',
                    'description': f'Высокое использование CPU: {current_value:.1f}%',
                    'metrics': {
                        'current_value': current_value,
                        'avg_value': avg_value
                    },
                    'timestamp': datetime.now()
                })

        elif 'memory' in metric_name.lower():
            if current_value > 85:  # Memory > 85%
                incidents.append({
                    'type': 'high_memory',
                    'service': metric.attributes.get('service', 'unknown'),
                    'severity': 'high',
                    'description': f'Высокое использование памяти: {current_value:.1f}%',
                    'metrics': {
                        'current_value': current_value,
                        'avg_value': avg_value
                    },
                    'timestamp': datetime.now()
                })

        elif 'response_time' in metric_name.lower() or 'duration' in metric_name.lower():
            if current_value > avg_value * 2:  # Удвоение response time
                incidents.append({
                    'type': 'response_time_spike',
                    'service': metric.attributes.get('service', 'unknown'),
                    'severity': 'medium',
                    'description': f'Скачок времени ответа: {current_value:.1f}ms (среднее: {avg_value:.1f}ms)',
                    'metrics': {
                        'current_value': current_value,
                        'avg_value': avg_value
                    },
                    'timestamp': datetime.now()
                })

        return incidents

    async def _enrich_incidents_with_ai(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обогащение инцидентов с помощью AI анализа"""
        enriched_incidents = []

        for incident in incidents:
            try:
                # Создаем промпт для анализа инцидента
                prompt = self._create_incident_analysis_prompt(incident)

                # Получаем анализ от AI
                analysis = await self.ollama_trainer.generate_analysis(prompt)

                # Обогащаем инцидент анализом
                enriched_incident = incident.copy()
                enriched_incident['ai_analysis'] = analysis
                enriched_incident['analyzed_at'] = datetime.now()

                enriched_incidents.append(enriched_incident)

            except Exception as e:
                logger.error(f"Error enriching incident with AI: {e}")
                # Возвращаем исходный инцидент без AI анализа
                enriched_incidents.append(incident)

        return enriched_incidents

    def _create_incident_analysis_prompt(self, incident: Dict[str, Any]) -> str:
        """Создание промпта для анализа инцидента"""
        incident_type = incident.get('type', 'unknown')
        service = incident.get('service', 'unknown')
        description = incident.get('description', '')
        metrics = incident.get('metrics', {})

        prompt = f"""Проанализируй следующий инцидент в микросервисной системе:

Тип инцидента: {incident_type}
Сервис: {service}
Описание: {description}

Метрики:
"""

        for key, value in metrics.items():
            prompt += f"- {key}: {value}\n"

        prompt += """
Проанализируй этот инцидент и предоставь:
1. КОРЕНЬ ПРОБЛЕМЫ: основная вероятная причина
2. СИМПТОМЫ: наблюдаемые проявления проблемы  
3. ВЛИЯНИЕ: на что влияет этот инцидент
4. РЕКОМЕНДАЦИИ: конкретные шаги по устранению

Будь технически точным и предлагай практические решения."""

        return prompt

    async def search_similar_historical_incidents(self, current_incident: Dict[str, Any], limit: int = 5) -> List[
        Dict[str, Any]]:
        """Поиск похожих исторических инцидентов"""
        try:
            # Создаем запрос для поиска
            query = f"{current_incident.get('type', '')} {current_incident.get('service', '')} {current_incident.get('description', '')}"

            # Ищем в векторной БД
            similar_incidents = await self.vector_store.search_similar_incidents(query, limit)

            return similar_incidents

        except Exception as e:
            logger.error(f"Error searching similar incidents: {e}")
            return []

    def get_active_incidents(self) -> List[Dict[str, Any]]:
        """Получение активных инцидентов"""
        # Фильтруем старые инциденты (старше 1 часа)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.active_incidents = [
            inc for inc in self.active_incidents
            if inc.get('timestamp', datetime.min) > cutoff_time
        ]

        return self.active_incidents

    def get_incident_statistics(self) -> Dict[str, Any]:
        """Получение статистики по инцидентам"""
        active_incidents = self.get_active_incidents()

        # Группируем по типу и серьезности
        by_type = {}
        by_severity = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

        for incident in active_incidents:
            inc_type = incident.get('type', 'unknown')
            severity = incident.get('severity', 'low')

            if inc_type not in by_type:
                by_type[inc_type] = 0
            by_type[inc_type] += 1

            by_severity[severity] += 1

        return {
            'total_active_incidents': len(active_incidents),
            'by_type': by_type,
            'by_severity': by_severity,
            'last_updated': datetime.now()
        }