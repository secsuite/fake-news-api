# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

WORKDIR /build

COPY requirements.txt requirements-train.txt ./

RUN python -m venv /opt/venv
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install --no-cache-dir --index-url ${TORCH_INDEX_URL} --extra-index-url https://pypi.org/simple torch \
    && pip install --no-cache-dir --extra-index-url ${TORCH_INDEX_URL} -r requirements.txt -r requirements-train.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

# Keep model artifacts in a dedicated layer for better Docker cache reuse.
COPY app/ml/models ./app/ml/models

COPY app/__init__.py app/config.py app/dependencies.py app/main.py app/schemas.py ./app/
COPY app/routers ./app/routers
COPY app/services ./app/services
COPY app/ml/__init__.py ./app/ml/__init__.py

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
