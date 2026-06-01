FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./
COPY mechanic ./mechanic
COPY src ./src

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8765

CMD ["uvicorn", "mechanic.hosted.api:app", "--host", "0.0.0.0", "--port", "8765"]
