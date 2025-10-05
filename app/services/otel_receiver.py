import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Request
import httpx
from loguru import logger

from app.config import config
from app.models.telemetry import OTLPLog, OTLPSpan, OTLPMetric

class OTelReceiver:
    def __init__(self):
        self.router = APIRouter(prefix="/otel", tags=["opentelemetry"])
        self._setup_routes()
        
    def _setup_routes(self):
        @self.router.post("/v1/logs")
        async def receive_logs(request: Request):
            return await self._process_otlp_request(request, "logs")
        
        @self.router.post("/v1/traces")
        async def receive_traces(request: Request):
            return await self._process_otlp_request(request, "traces")
        
        @self.router.post("/v1/metrics")
        async def receive_metrics(request: Request):
            return await self._process_otlp_request(request, "metrics")

    async def _process_otlp_request(self, request: Request, data_type: str):
        try:
            body = await request.json()
            logger.info(f"Received OTLP {data_type} data")
            
            processed_data = []
            
            if data_type == "logs":
                processed_data = self._parse_logs_data(body)
            elif data_type == "traces":
                processed_data = self._parse_traces_data(body)
            elif data_type == "metrics":
                processed_data = self._parse_metrics_data(body)
            
            # Асинхронная обработка данных
            await self._process_data_async(processed_data, data_type)
            
            return {"status": "success", "processed": len(processed_data)}
            
        except Exception as e:
            logger.error(f"Error processing OTLP {data_type}: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def _parse_logs_data(self, body: Dict[str, Any]) -> List[OTLPLog]:
        logs = []
        try:
            resource_logs = body.get("resourceLogs", [])
            
            for resource_log in resource_logs:
                resource = resource_log.get("resource", {}).get("attributes", {})
                service_name = self._extract_service_name(resource)
                
                scope_logs = resource_log.get("scopeLogs", [])
                for scope_log in scope_logs:
                    log_records = scope_log.get("logRecords", [])
                    for record in log_records:
                        log = OTLPLog(
                            timestamp=self._parse_timestamp(record.get("timeUnixNano")),
                            body=self._parse_log_body(record),
                            attributes=record.get("attributes", []),
                            resource=resource,
                            service_name=service_name
                        )
                        logs.append(log)
            
            logger.info(f"Parsed {len(logs)} logs")
            return logs
            
        except Exception as e:
            logger.error(f"Error parsing logs: {e}")
            return []

    def _parse_traces_data(self, body: Dict[str, Any]) -> List[OTLPSpan]:
        spans = []
        try:
            resource_spans = body.get("resourceSpans", [])
            
            for resource_span in resource_spans:
                resource = resource_span.get("resource", {}).get("attributes", {})
                service_name = self._extract_service_name(resource)
                
                scope_spans = resource_span.get("scopeSpans", [])
                for scope_span in scope_spans:
                    span_records = scope_span.get("spans", [])
                    for span_data in span_records:
                        span = OTLPSpan(
                            trace_id=span_data.get("traceId", ""),
                            span_id=span_data.get("spanId", ""),
                            parent_span_id=span_data.get("parentSpanId"),
                            name=span_data.get("name", "unknown"),
                            start_time=self._parse_timestamp(span_data.get("startTimeUnixNano")),
                            end_time=self._parse_timestamp(span_data.get("endTimeUnixNano")),
                            attributes=span_data.get("attributes", []),
                            events=span_data.get("events", []),
                            service_name=service_name,
                            status_code=span_data.get("status", {}).get("code", "OK"),
                            status_message=span_data.get("status", {}).get("message")
                        )
                        spans.append(span)
            
            logger.info(f"Parsed {len(spans)} spans")
            return spans
            
        except Exception as e:
            logger.error(f"Error parsing traces: {e}")
            return []

    def _parse_metrics_data(self, body: Dict[str, Any]) -> List[OTLPMetric]:
        metrics = []
        try:
            resource_metrics = body.get("resourceMetrics", [])
            
            for resource_metric in resource_metrics:
                scope_metrics = resource_metric.get("scopeMetrics", [])
                for scope_metric in scope_metrics:
                    metric_records = scope_metric.get("metrics", [])
                    for metric_data in metric_records:
                        metric = self._parse_single_metric(metric_data)
                        if metric:
                            metrics.append(metric)
            
            logger.info(f"Parsed {len(metrics)} metrics")
            return metrics
            
        except Exception as e:
            logger.error(f"Error parsing metrics: {e}")
            return []

    def _parse_single_metric(self, metric_data: Dict[str, Any]) -> Optional[OTLPMetric]:
        try:
            name = metric_data.get("name", "")
            unit = metric_data.get("unit", "")
            
            # Обработка разных типов метрик
            gauge = metric_data.get("gauge", {})
            if gauge:
                data_points = gauge.get("dataPoints", [])
                for point in data_points:
                    return OTLPMetric(
                        name=name,
                        value=point.get("asDouble", 0),
                        timestamp=self._parse_timestamp(point.get("timeUnixNano")),
                        attributes=point.get("attributes", []),
                        unit=unit
                    )
            
            # Добавьте обработку других типов метрик при необходимости
            return None
            
        except Exception as e:
            logger.error(f"Error parsing single metric: {e}")
            return None

    def _parse_timestamp(self, nano_timestamp: Optional[str]) -> datetime:
        if nano_timestamp:
            try:
                # Конвертация наносекунд в секунды
                seconds = int(nano_timestamp) / 1_000_000_000
                return datetime.fromtimestamp(seconds)
            except (ValueError, TypeError):
                pass
        return datetime.now()

    def _parse_log_body(self, record: Dict[str, Any]) -> Dict[str, Any]:
        body = {}
        try:
            # OTLP log record body может быть в разных форматах
            body_str = record.get("body", {}).get("stringValue")
            if body_str:
                body = {"message": body_str}
            else:
                body = record.get("body", {})
        except Exception as e:
            logger.warning(f"Error parsing log body: {e}")
            body = {"raw": str(record)}
        
        return body

    def _extract_service_name(self, attributes: List[Dict[str, Any]]) -> str:
        for attr in attributes:
            if attr.get("key") == "service.name":
                return attr.get("value", {}).get("stringValue", "unknown")
        return "unknown"

    async def _process_data_async(self, data: List, data_type: str):
        """Асинхронная обработка полученных данных"""
        try:
            # Здесь будет интеграция с другими сервисами
            # Пока просто логируем
            logger.info(f"Processing {len(data)} {data_type} records asynchronously")
            
            # В будущем: сохранение в векторную БД, анализ аномалий и т.д.
            
        except Exception as e:
            logger.error(f"Error in async processing: {e}")