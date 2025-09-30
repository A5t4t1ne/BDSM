FROM python:3.11-slim

# Create non-root user
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

WORKDIR /app

# Copy only the necessary files for dependency installation
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir .

# Copy the rest of your application
COPY src/ .

# SQLite configuration (optional)
RUN mkdir -p /data && chown appuser:appgroup /data
VOLUME /data

RUN chown -R appuser:appgroup /app/heroes
VOLUME /app/heroes

# WORKDIR /app/src
USER appuser
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8000", "--workers", "4"]

