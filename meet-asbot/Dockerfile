FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99 \
    PULSE_SERVER=unix:/var/run/pulse/native

WORKDIR /app

# Sistema + Chrome + herramientas para uv en un solo RUN
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl wget gnupg unzip \
        xvfb pulseaudio ffmpeg \
        dbus dbus-x11 \
        procps \
        fonts-liberation libnss3 libatk1.0-0 libatk-bridge2.0-0 \
        libasound2 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
        libgbm1 libgtk-3-0 \
    && wget -qO- https://dl.google.com/linux/linux_signing_key.pub \
        | gpg --dearmor > /usr/share/keyrings/google-linux-signing-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-keyring.gpg] \
        http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv y limpiar residuos de instalación
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    rm -rf /root/.cache

ENV PATH="/root/.local/bin:${PATH}"

# Configuración de PulseAudio
RUN sed -i 's/^; enable-shm = yes/enable-shm = no/g' /etc/pulse/daemon.conf && \
    sed -i 's/^; exit-idle-time = 20/exit-idle-time = -1/g' /etc/pulse/daemon.conf && \
    adduser root pulse-access

# Dependencias Python
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen || uv sync --system && \
    # limpiar cachés de uv para reducir tamaño
    rm -rf /root/.cache/uv

# Código
COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uv", "run", "main.py"]
