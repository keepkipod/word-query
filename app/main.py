import os
import logging
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from app.tasks import process_document, combine_results
from celery import group
import traceback
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)

ARTICLES_DIR = "/app/Articles"

class AnalysisRequest(BaseModel):
    file_names: str

@app.get("/health")
async def health_check():
    try:
        # You can add more checks here if needed, e.g., database connection
        return Response(content="Healthy", media_type="text/plain")
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

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

        # Use group to process documents
        job = group(process_document.s(doc) for doc in file_contents)
        result = job.apply_async()

        # Wait for all tasks to complete
        task_results = result.get(timeout=120)  # 2 minute timeout

        # Combine results
        final_result = combine_results.delay(task_results)

        # Wait for the final result
        combined_result = final_result.get(timeout=30)  # 30 second timeout for combining

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