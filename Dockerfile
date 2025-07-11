# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
RUN adduser --disabled-password --gecos "" appuser
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*
COPY --chown=appuser:appuser . .
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

