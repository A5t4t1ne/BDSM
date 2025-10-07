FROM python:3.11-slim

# Create non-root user
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

WORKDIR /app

# Copy and install the application
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY src/ .

# SQLite configuration
RUN mkdir -p /data && chown appuser:appgroup /data
VOLUME /data

RUN mkdir -p /app/heroes && chown appuser:appgroup /app/heroes
VOLUME /app/heroes

USER appuser
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8000", "--workers", "4"]

