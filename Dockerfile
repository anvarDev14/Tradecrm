FROM python:3.11-slim

WORKDIR /app

# Kerakli paketlar
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kod
COPY . .

# Data papkasi
RUN mkdir -p /app/data

CMD ["python", "app.py"]