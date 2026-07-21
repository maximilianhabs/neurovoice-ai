FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# 127.0.0.1 statt localhost - Streamlit lauscht nur IPv4, localhost kann auf ::1 aufloesen
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health').read()==b'ok' else 1)" || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
