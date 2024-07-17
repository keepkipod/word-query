# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY app/ ./app
COPY celery_config.py .

# Copy the Articles folder into the container
COPY Articles/ ./Articles

# Set up directory for Prometheus multiprocess mode
ENV PROMETHEUS_MULTIPROC_DIR /tmp/prometheus_multiproc
RUN mkdir -p $PROMETHEUS_MULTIPROC_DIR && chmod 777 $PROMETHEUS_MULTIPROC_DIR

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]