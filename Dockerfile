FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md uv.lock ./
COPY src ./src
RUN python -m pip install .

COPY models/manifest.json ./models/manifest.json
COPY scripts/download_models.py ./scripts/download_models.py
RUN python scripts/download_models.py

COPY app.py ./
COPY .streamlit ./.streamlit
COPY assets ./assets

RUN useradd --create-home --uid 10001 autoace \
    && chown -R autoace:autoace /app
USER autoace

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8501') + '/_stcore/health', timeout=3)"

CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501}"]
