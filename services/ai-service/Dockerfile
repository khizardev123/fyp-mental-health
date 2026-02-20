FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ─── Production Image ────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1001 appuser && \
    mkdir -p /models && \
    chown -R appuser:appuser /app /models

USER appuser

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/models/cache
ENV MODEL_PATH=/models

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
    "--workers", "2", "--log-level", "info"]
