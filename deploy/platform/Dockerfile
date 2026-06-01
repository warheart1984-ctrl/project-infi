FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir fastapi uvicorn pydantic httpx redis psycopg[binary] 2>/dev/null || \
    pip install --no-cache-dir fastapi uvicorn pydantic httpx redis

ENV PYTHONPATH=/app
EXPOSE 8090

CMD ["python", "-m", "platform", "serve", "--host", "0.0.0.0", "--port", "8090"]
