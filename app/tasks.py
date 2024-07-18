import logging
from celery import Celery
from collections import Counter as CollectionsCounter
import re
import io
from pdfminer.high_level import extract_text
import os
import traceback
from prometheus_client import Counter, Histogram, start_http_server
import time
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = os.environ.get('REDIS_PORT', '6379')

celery_app = Celery('tasks',
                    broker=f'redis://{redis_host}:{redis_port}/0',
                    backend=f'redis://{redis_host}:{redis_port}/0')

STOP_WORDS = set([
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'
])

CELERY_METRICS_PORT = 8001

documents_processed = Counter('documents_processed_total', 'Total number of documents processed', ['worker_id'])
words_processed = Counter('words_processed_total', 'Total number of words processed', ['worker_id'])
document_processing_time = Histogram('document_processing_seconds', 'Time spent processing a document', ['worker_id'])

def start_metrics_server(port):
    start_http_server(port)

@celery_app.on_after_configure.connect
def setup_metrics_server(sender, **kwargs):
    threading.Thread(target=start_metrics_server, args=(CELERY_METRICS_PORT,)).start()
    logger.info(f"Metrics server started on port {CELERY_METRICS_PORT}")

@celery_app.task
def process_document(document):
    worker_id = celery_app.current_task.request.hostname
    try:
        start_time = time.time()
        text = extract_text(io.BytesIO(document))
        words = re.findall(r'\b\w+\b', text.lower())
        filtered_words = [word for word in words if word not in STOP_WORDS]
        result = CollectionsCounter(filtered_words)
        logger.info(f"Processed document. Word count: {len(result)}")

        # Update Prometheus metrics
        documents_processed.labels(worker_id=worker_id).inc()
        words_processed.labels(worker_id=worker_id).inc(len(filtered_words))
        document_processing_time.labels(worker_id=worker_id).observe(time.time() - start_time)

        logger.info(f"Updated metrics for worker {worker_id} - Documents: {documents_processed.labels(worker_id=worker_id)._value.get()}, Words: {words_processed.labels(worker_id=worker_id)._value.get()}")

        return dict(result)
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        logger.error(traceback.format_exc())
        return None

@celery_app.task
def combine_results(results):
    try:
        logger.info(f"Combining results from {len(results)} tasks")
        total_count = CollectionsCounter()
        for result in results:
            if result is not None:
                total_count.update(result)
        logger.info(f"Combined word count: {len(total_count)}")
        return total_count.most_common(10)
    except Exception as e:
        logger.error(f"Error combining results: {str(e)}")
        logger.error(traceback.format_exc())
        return []