FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml ./
COPY requirements.txt ./
ARG CACHE_BUST=v2

RUN uv pip compile pyproject.toml --find-links https://download.pytorch.org/whl/cpu -o requirements.txt && \
    uv venv /app/.venv && \
    uv pip sync requirements.txt --find-links https://download.pytorch.org/whl/cpu --python /app/.venv/bin/python

FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv

COPY ./app ./app

EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]