FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Set environment variables
ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}
ENV GOOGLE_CSE_ID=${GOOGLE_CSE_ID}

# Run with proper settings for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

