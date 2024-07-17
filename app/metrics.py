from prometheus_client import CollectorRegistry, Counter, Histogram, REGISTRY as DEFAULT_REGISTRY
from prometheus_client.core import GaugeMetricFamily, HistogramMetricFamily
import os

class CustomCollector(object):
    def __init__(self):
        self.documents_processed = Counter('documents_processed_total', 'Total number of documents processed', ['worker_id'])
        self.words_processed = Counter('words_processed_total', 'Total number of words processed', ['worker_id'])
        self.document_processing_time = Histogram('document_processing_seconds', 'Time spent processing a document', ['worker_id'])
        self.worker_id = os.environ.get('HOSTNAME', 'unknown')

    def collect(self):
        yield GaugeMetricFamily('documents_processed_total', 'Total number of documents processed', 
                                value=self.documents_processed.labels(worker_id=self.worker_id)._value.get())
        yield GaugeMetricFamily('words_processed_total', 'Total number of words processed', 
                                value=self.words_processed.labels(worker_id=self.worker_id)._value.get())
        
        hist = HistogramMetricFamily('document_processing_seconds', 'Time spent processing a document', labels=['worker_id'])
        hist_metric = self.document_processing_time.labels(worker_id=self.worker_id)
        buckets = []
        acc = 0
        for upper_bound, count in zip(hist_metric._upper_bounds, hist_metric._buckets):
            acc += count
            buckets.append((upper_bound, acc))
        hist.add_metric([self.worker_id], buckets, hist_metric._sum.get())
        yield hist

    def inc_documents_processed(self):
        self.documents_processed.labels(worker_id=self.worker_id).inc()

    def inc_words_processed(self, count):
        self.words_processed.labels(worker_id=self.worker_id).inc(count)

    def observe_processing_time(self, seconds):
        self.document_processing_time.labels(worker_id=self.worker_id).observe(seconds)

# Create a custom collector
collector = CustomCollector()

# Register the custom collector with the default registry
DEFAULT_REGISTRY.register(collector)

# Export the methods for easy access
inc_documents_processed = collector.inc_documents_processed
inc_words_processed = collector.inc_words_processed
observe_processing_time = collector.observe_processing_time