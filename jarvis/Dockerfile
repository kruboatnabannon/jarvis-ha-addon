FROM python:3.11-slim-bookworm

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    jq \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements & install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Set permissions
RUN chmod +x run.sh

# Expose Jarvis API port
EXPOSE 5050

# Run entrypoint
CMD [ "./run.sh" ]
