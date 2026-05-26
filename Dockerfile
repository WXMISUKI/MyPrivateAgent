FROM python:3.11-slim

WORKDIR /app

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
ARG INSTALL_FROM_WHEELHOUSE=auto

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
COPY .docker/wheelhouse/backend /tmp/wheelhouse
RUN set -eux; \
    python -m pip install --upgrade pip -i "${PIP_INDEX_URL}" --trusted-host "${PIP_TRUSTED_HOST}"; \
    if [ "${INSTALL_FROM_WHEELHOUSE}" = "offline" ]; then \
        python -m pip install --no-index --find-links=/tmp/wheelhouse -r /tmp/requirements.txt; \
    elif [ "${INSTALL_FROM_WHEELHOUSE}" = "auto" ] && find /tmp/wheelhouse -type f \( -name '*.whl' -o -name '*.tar.gz' \) | grep -q .; then \
        python -m pip install --no-index --find-links=/tmp/wheelhouse -r /tmp/requirements.txt; \
    else \
        python -m pip install --no-cache-dir -r /tmp/requirements.txt -i "${PIP_INDEX_URL}" --trusted-host "${PIP_TRUSTED_HOST}"; \
    fi

COPY . /app

ENV PROJECT_ROOT=/app
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE ${PORT}

CMD ["sh", "-c", "exec python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
