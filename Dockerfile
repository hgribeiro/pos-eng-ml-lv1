FROM python:3.11-slim

# Basic environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PYTHONPATH=/app/src:${PYTHONPATH}


WORKDIR /app

# Install system deps required for many Python packages; keep minimal
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m appuser

# Copy requirements and install Python deps
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . /app

# Adjust ownership and switch to non-root user for runtime
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE ${PORT}

# Use shell form so env var PORT is expanded
ENTRYPOINT ["sh", "-c", "uvicorn src.tc_01.api.main:app --host 0.0.0.0 --port ${PORT} --workers 4"]

# Optional healthcheck (requires curl present in image) — uncomment if desired
# HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1
