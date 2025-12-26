# Multi-stage build for production
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}

# Development stage
FROM base as development

RUN pip install --upgrade pip setuptools wheel

COPY . .

RUN pip install -r requirements.txt
RUN pip install -e ".[dev]"

EXPOSE 8000

CMD ["pytest", "tests/", "-v"]

# Production stage
FROM base as production

RUN pip install --upgrade pip setuptools wheel gunicorn

COPY . .

RUN pip install -r requirements.txt
RUN pip install -e .

# Install FastAPI dependencies
RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary prometheus-client

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.data_quality_framework.api:app", "--host", "0.0.0.0", "--port", "8000"]
