FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 platform \
    && useradd --uid 1000 --gid platform --create-home platform

COPY pyproject.toml README.md LICENSE ./
COPY platform ./platform
COPY src ./src
COPY governance ./governance
COPY tools ./tools

RUN pip install --upgrade pip wheel setuptools \
    && pip install .

RUN mkdir -p /app/.runtime \
    && chown -R platform:platform /app

USER platform

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8090/v1/health || exit 1

CMD ["python", "-m", "platform", "serve", "--host", "0.0.0.0", "--port", "8090"]
