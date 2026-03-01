FROM python:3.12-slim

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System deps (only if grpc needs build tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Default command (overridden by compose)
CMD ["python", "-m", "orchestrator"]