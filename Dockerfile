# Build stage
FROM node:20-alpine AS node-builder
RUN npm install -g ccusage

# Python stage
FROM python:3.11-slim

# Install Node.js for npx and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY --from=node-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=node-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml .
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CLAUDE_CONFIG_DIR=/data/claude

# Expose port
EXPOSE 8383

# Run the application
CMD ["python", "-m", "uvicorn", "claude_usage_api.main:app", "--host", "0.0.0.0", "--port", "8383"]
