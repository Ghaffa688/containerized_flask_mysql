# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# System deps required to compile mysqlclient (C extension)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create an unprivileged user and switch to it
RUN groupadd --system --gid 1001 appgroup \
    && useradd  --system --uid 1001 --gid appgroup --create-home appuser

# Copy the app and hand ownership to appuser
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 5000

CMD ["python", "app.py"]