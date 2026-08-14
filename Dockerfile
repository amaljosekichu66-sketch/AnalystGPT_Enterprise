# ==========================================================
# AnalystGPT Enterprise — Production Multi-Stage Dockerfile
#
# Target Stages:
# - base: Minimal Python runtime with non-root security context
# - builder: Compiles dependencies into user site-packages
# - runtime-base: Shared slim runtime layer with application code
# - api: Production FastAPI backend service (Port 8000)
# - frontend: Production Streamlit frontend service (Port 8501)
# - cli: Batch execution entrypoint (main.py)
# ==========================================================

# ----------------------------------------------------------
# Stage 1: Base Runtime Environment
# ----------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/home/appuser/.local/bin:$PATH"

# Install curl for container healthchecks
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# ----------------------------------------------------------
# Stage 2: Builder (Compile and Cache Dependencies)
# ----------------------------------------------------------
FROM base AS builder

# Install build dependencies if needed for C-extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ libpq-dev && \
    rm -rf /var/lib/apt/lists/*

USER appuser

# Copy dependency specification only to leverage Docker layer caching
COPY --chown=appuser:appuser requirements.txt .

# Install dependencies into user local directory
RUN pip install --no-cache-dir --user -r requirements.txt

# ----------------------------------------------------------
# Stage 3: Runtime Base (Shared Application Layer)
# ----------------------------------------------------------
FROM base AS runtime-base

# Copy installed Python packages from builder stage
COPY --from=builder --chown=appuser:appuser /home/appuser/.local /home/appuser/.local

# Create operational directories with proper permissions
RUN mkdir -p /app/logs /app/reports /app/sample_data && \
    chown -R appuser:appuser /app

# Copy application source files
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser sample_data/ /app/sample_data/
COPY --chown=appuser:appuser main.py /app/main.py

USER appuser

# ----------------------------------------------------------
# Stage 4: API Target (FastAPI + Uvicorn)
# ----------------------------------------------------------
FROM runtime-base AS api

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]

# ----------------------------------------------------------
# Stage 5: Frontend Target (Streamlit UI)
# ----------------------------------------------------------
FROM runtime-base AS frontend

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "src/frontend/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

# ----------------------------------------------------------
# Stage 6: CLI Target (Batch Execution)
# ----------------------------------------------------------
FROM runtime-base AS cli

ENTRYPOINT ["python", "main.py"]
