FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99 \
    # Variable crucial para que clientes (ffmpeg/chrome) encuentren el socket de sistema
    PULSE_SERVER=unix:/var/run/pulse/native

# 1. Instalar dependencias
RUN apt-get update && apt-get install -y \
    curl wget gnupg unzip \
    xvfb pulseaudio ffmpeg \
    dbus dbus-x11 \
    procps \
    fonts-liberation libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libasound2 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar Chrome
RUN wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-linux-signing-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# 3. Instalar uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 4. CONFIGURACIÓN CRÍTICA DE PULSEAUDIO
# - Desactivar SHM (Shared Memory) porque Docker la limita y PA crashea.
# - Permitir root.
RUN sed -i 's/^; enable-shm = yes/enable-shm = no/g' /etc/pulse/daemon.conf && \
    sed -i 's/^; exit-idle-time = 20/exit-idle-time = -1/g' /etc/pulse/daemon.conf && \
    # Añadir root al grupo de acceso de audio
    adduser root pulse-access

WORKDIR /app

# 5. Instalar dependencias Python
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen || uv sync --system

# 6. Copiar código
COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uv", "run", "main.py"]
