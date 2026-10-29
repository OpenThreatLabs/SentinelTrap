FROM python:3.10-slim

WORKDIR /app

# Install build dependencies for cryptography/paramiko
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose all multi-protocol honeypot decoy ports
EXPOSE 2222 2223 8080 2121 2525 3306 6379 5353/udp 3389

CMD ["python", "runner.py"]
