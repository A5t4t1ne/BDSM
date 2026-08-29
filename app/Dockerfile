FROM python:3.11-slim

# Create non-root user with a real home, so tools that write there (gunicorn's
# control server, for one) do not fail against /nonexistent
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /home/appuser --shell /usr/sbin/nologin appuser

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

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz').read()"

CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8000", "--workers", "4"]
