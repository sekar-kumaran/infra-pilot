FROM python:3.12-slim

LABEL org.opencontainers.image.title="InfraPilot API" \
      org.opencontainers.image.description="InfraPilot infrastructure operations control plane API" \
      org.opencontainers.image.authors="Sekar Kumaran <https://github.com/sekar-kumaran>" \
      org.opencontainers.image.url="https://github.com/sekar-kumaran/infra-pilot" \
      org.opencontainers.image.source="https://github.com/sekar-kumaran/infra-pilot" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Create a non-root user
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* && \
    addgroup --system appgroup && adduser --system --group appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and migrations
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY entrypoint.sh .

# Set ownership + make entrypoint executable
RUN chown -R appuser:appgroup ${APP_HOME} && chmod +x ${APP_HOME}/entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["sh", "entrypoint.sh"]
