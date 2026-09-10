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

# Copy the rest of the Flask app
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]