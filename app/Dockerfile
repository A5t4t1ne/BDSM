# ---- build stage: resolve dependencies from the lockfile ----
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build

# --frozen fails the build if the lockfile does not match pyproject.toml, so an
# image can never be built from an unresolved dependency set
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


# ---- runtime stage ----
FROM python:3.14-slim

# Non-root user with a real home, so tools that write there (gunicorn's control
# server, for one) do not fail against /nonexistent
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --home /home/appuser --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
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
