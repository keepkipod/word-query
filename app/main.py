import os
import logging
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from app.tasks import process_document, combine_results
from celery import group
import traceback
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import REGISTRY, generate_latest
from app.metrics import PrometheusMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add PrometheusMiddleware
app.add_middleware(PrometheusMiddleware, app_name="word-counter-app")

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

ARTICLES_DIR = "/app/Articles"

class AnalysisRequest(BaseModel):
    file_names: str

@app.get("/health")
async def health_check():
    return Response(content="Healthy", media_type="text/plain")

@app.get("/articles")
async def list_articles():
    articles = [f for f in os.listdir(ARTICLES_DIR) if f.endswith('.pdf')]
    return {"articles": articles}

@app.post("/analyze-documents")
async def analyze_documents(request: AnalysisRequest):
    try:
        file_names = request.file_names.split(',')
        file_contents = []
        for file_name in file_names:
            file_path = os.path.join(ARTICLES_DIR, file_name.strip())
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    file_contents.append(file.read())
            else:
                logger.warning(f"File not found: {file_name}")

        if not file_contents:
            raise HTTPException(status_code=400, detail="No valid files provided")

        logger.info(f"Processing {len(file_contents)} files")

        job = group(process_document.s(doc) for doc in file_contents)
        result = job.apply_async()

        task_results = result.get(timeout=300)  # 5 minutes timeout

        final_result = combine_results.delay(task_results)

        combined_result = final_result.get(timeout=60)  # 1 minute timeout

        return {"most_common_words": combined_result}
    except Exception as e:
        logger.error(f"Error in analyze_documents: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return {"detail": "An unexpected error occurred. Please try again later."}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")