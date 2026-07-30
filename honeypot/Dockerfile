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

EXPOSE 2222

CMD ["python", "server.py"]
