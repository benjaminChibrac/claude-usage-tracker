# Use Python base image with ARM64 support
FROM --platform=linux/arm64 python:3.11-slim

# Install Node.js, npm, and curl from Debian repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g ccusage \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml .
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Pointe vers le répertoire où les logs Claude sont montés depuis l'hôte
ENV CLAUDE_CONFIG_DIR=/root/.claude

# Expose port
EXPOSE 8383

# Run the application
CMD ["python", "-m", "uvicorn", "claude_usage_api.main:app", "--host", "0.0.0.0", "--port", "8383"]
