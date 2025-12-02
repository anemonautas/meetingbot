#!/bin/bash
set -e

echo "🧹 [ENTRYPOINT] Limpiando procesos y locks previos..."
pkill -f chrome || true
pkill -f ffmpeg || true
pkill -f pulseaudio || true
rm -rf /var/run/pulse /var/lib/pulse /root/.config/pulse
rm -rf /tmp/.X99-lock
rm -rf /tmp/runtime-appuser

echo "🖥️ [ENTRYPOINT] Iniciando Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 +extension GLX +extension render -noreset &
export DISPLAY=:99
sleep 1

echo "🚌 [ENTRYPOINT] Iniciando D-Bus (System)..."
mkdir -p /var/run/dbus
# Borramos pid anterior si existe
rm -f /var/run/dbus/pid
dbus-daemon --system --fork
sleep 1

echo "🔊 [ENTRYPOINT] Iniciando PulseAudio (Modo System)..."
# --system: Permite ejecutar como root (requiere config en Dockerfile)
# --disallow-exit: Evita que se cierre si no hay actividad
# --exit-idle-time=-1: Desactiva timeout
pulseaudio -D --system --disallow-exit --exit-idle-time=-1

# Bucle de espera para asegurar que PA está listo
echo "⏳ [ENTRYPOINT] Esperando a PulseAudio..."
for i in {1..10}; do
    if pactl info >/dev/null 2>&1; then
        echo "✅ [ENTRYPOINT] PulseAudio online."
        break
    fi
    sleep 1
done

# Verificación final
if ! pactl info >/dev/null 2>&1; then
    echo "❌ [ENTRYPOINT] Error: PulseAudio no arrancó."
    # Mostrar logs si falló
    cat /var/log/syslog || true
    exit 1
fi

echo "🎛️ [ENTRYPOINT] Configurando VirtualSpeaker..."
# Creamos el sink explícitamente aquí, no confiamos en default.pa
pactl load-module module-null-sink sink_name=VirtualSpeaker sink_properties=device.description=VirtualSpeaker
pactl set-default-sink VirtualSpeaker
pactl set-default-source VirtualSpeaker.monitor
pactl set-sink-mute VirtualSpeaker 0
pactl set-sink-volume VirtualSpeaker 100%

echo "🐍 [ENTRYPOINT] Ejecutando Python..."
exec "$@"
