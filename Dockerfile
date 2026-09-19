FROM python:3.13-slim

# Install a few basic runtime utilities.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv/uvx from the official uv image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------

# Copy dependency files first so Docker can cache this layer.
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

COPY backend ./backend
COPY knowledge ./knowledge

# Copy the already-ingested read-only Qdrant knowledge store.
COPY memory/qdrant ./memory/qdrant


# ---------------------------------------------------------
# RUNTIME
# ---------------------------------------------------------

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=30s \
    --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]