FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app

ENV PROJECT_ROOT=/app
ENV PORT=8000

EXPOSE ${PORT}

CMD sh -c "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}"
