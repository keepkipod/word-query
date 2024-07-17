from celery import Celery
from collections import Counter as CollectionsCounter
import re
import io
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError
import os
import traceback
import time
from app.metrics import inc_documents_processed, inc_words_processed, observe_processing_time

import logging
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

@celery_app.task
def process_document(document):
    try:
        logger.info("Starting document processing")
        start_time = time.time()
        
        try:
            text = extract_text(io.BytesIO(document))
            words = re.findall(r'\b\w+\b', text.lower())
            filtered_words = [word for word in words if word not in STOP_WORDS]
            result = CollectionsCounter(filtered_words)
            
            processing_time = time.time() - start_time
            
            # Update metrics
            inc_documents_processed()
            inc_words_processed(len(filtered_words))
            observe_processing_time(processing_time)
            
            logger.info(f"Processed document. Word count: {len(result)}. Processing time: {processing_time:.2f} seconds")
            
            return dict(result)
        except PDFSyntaxError as e:
            logger.error(f"Invalid PDF: {str(e)}")
            return None
        
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