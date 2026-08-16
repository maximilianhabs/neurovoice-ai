FROM python:3.11-slim-bookworm

# build-essential/cmake: praat-parselmouth hat KEIN vorgebautes Wheel fuer linux/arm64 (nur
# fuer linux/amd64 und macOS) -- auf Apple Silicon (primaeres Zielsystem fuer die lokale
# Nutzung, siehe docs/konzept_p9_hintergrundjob_lokal.md) baut pip es deshalb aus dem Quellcode,
# braucht dafuer einen C++-Compiler + CMake. Auf amd64 wird das fertige Wheel installiert, diese
# Pakete bleiben dort ungenutzt aber harmlos (etwas groesseres Image, kein Laufzeit-Nachteil).
# Empirisch verifiziert 2026-08-16 (nativer arm64-Testbuild) -- ohne diese Pakete schlaegt der
# Build auf Apple Silicon fehl (CMake findet keinen Compiler).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libsndfile1 \
        ffmpeg \
        build-essential \
        cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# CPU-only Torch zuerst installieren (kein GPU auf dem Server, und Apple Silicon/Windows-
# Docker haben in diesem Linux-Container ohnehin keinen GPU-Zugriff -- siehe
# docs/konzept_p9_hintergrundjob_lokal.md). WICHTIG (Fund 2026-08-16, empirisch verifiziert):
# das CPU-Wheel-Repository (https://download.pytorch.org/whl/cpu) hat AUCH fuer linux/arm64
# fertige "+cpu"-Wheels -- ein normales "pip install torch" OHNE dieses Repository zieht auf
# arm64 dagegen die volle CUDA/NVIDIA-Toolkit-Kette mit (mehrere hundert MB voellig nutzloser
# GPU-Pakete, massiv langsamerer Build). Deshalb IMMER dieses Repository nutzen, unabhaengig
# von der Architektur -- kein TARGETARCH-Unterschied noetig.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
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
