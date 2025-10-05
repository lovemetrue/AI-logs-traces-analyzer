import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from loguru import logger

from app.config import config
from app.models.telemetry import OTLPLog, OTLPSpan, TrainingExample

class VectorStore:
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=config.chroma.host.split('//')[1].split(':')[0],
            port=8000
        )
        self.collections = {}
        self._initialize_collections()
    
    def _initialize_collections(self):
        collections_config = [
            ("logs", "Observability logs collection"),
            ("traces", "Observability traces collection"), 
            ("incidents", "Incident patterns and solutions"),
            ("training", "Training examples for LLM")
        ]
        
        for name, description in collections_config:
            try:
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"description": description}
                )
                logger.info(f"Initialized collection: {name}")
            except Exception as e:
                logger.error(f"Error initializing collection {name}: {e}")
    
    async def store_logs(self, logs: List[OTLPLog]):
        """Сохранение логов в векторную БД"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, log in enumerate(logs):
                doc_text = f"Service: {log.service_name}\nMessage: {log.body}\nTimestamp: {log.timestamp}"
                documents.append(doc_text)
                
                metadata = {
                    "service": log.service_name,
                    "timestamp": log.timestamp.isoformat(),
                    "type": "log",
                    "has_errors": any(keyword in str(log.body).lower() 
                                    for keyword in ['error', 'exception', 'failed'])
                }
                metadatas.append(metadata)
                ids.append(f"log_{log.timestamp.timestamp()}_{i}")
            
            if documents:
                self.collections["logs"].add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Stored {len(documents)} logs in vector DB")
                
        except Exception as e:
            logger.error(f"Error storing logs: {e}")
    
    async def store_traces(self, spans: List[OTLPSpan]):
        """Сохранение трейсов в векторную БД"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for span in spans:
                duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
                doc_text = f"Trace: {span.trace_id}\nSpan: {span.name}\nService: {span.service_name}\nDuration: {duration_ms:.2f}ms\nStatus: {span.status_code}"
                documents.append(doc_text)
                
                metadata = {
                    "trace_id": span.trace_id,
                    "service": span.service_name,
                    "operation": span.name,
                    "duration_ms": duration_ms,
                    "status": span.status_code,
                    "has_errors": span.status_code != "OK",
                    "timestamp": span.start_time.isoformat()
                }
                metadatas.append(metadata)
                ids.append(f"span_{span.trace_id}_{span.span_id}")
            
            if documents:
                self.collections["traces"].add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Stored {len(documents)} spans in vector DB")
                
        except Exception as e:
            logger.error(f"Error storing traces: {e}")
    
    async def store_training_examples(self, examples: List[TrainingExample]):
        """Сохранение обучающих примеров"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, example in enumerate(examples):
                documents.append(f"{example.input}\n\n{example.output}")
                metadatas.append({
                    "pattern_type": example.pattern_type,
                    "services": ",".join(example.services),
                    "severity": example.severity,
                    "created_at": example.created_at.isoformat()
                })
                ids.append(f"training_{example.created_at.timestamp()}_{i}")
            
            if documents:
                self.collections["training"].add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Stored {len(documents)} training examples")
                
        except Exception as e:
            logger.error(f"Error storing training examples: {e}")
    
    async def search_similar_incidents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск похожих инцидентов"""
        try:
            results = self.collections["incidents"].query(
                query_texts=[query],
                n_results=limit
            )
            
            similar = []
            for i, doc in enumerate(results['documents'][0]):
                similar.append({
                    "document": doc,
                    "metadata": results['metadatas'][0][i],
                    "similarity": 1 - (results['distances'][0][i] if results['distances'] else 0)
                })
            
            return similar
            
        except Exception as e:
            logger.error(f"Error searching similar incidents: {e}")
            return []