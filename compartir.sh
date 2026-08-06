#!/usr/bin/env bash
# Abre un túnel público hacia el Client para que los compañeros entren desde
# sus casas. No toca los servidores: cloudflared sólo hace de proxy hacia el
# runserver que ya tienes levantado, así que puedes seguir editando código
# mientras ellos están dentro.
#
#   ./compartir.sh
#
# Ctrl+C cierra el túnel (y con él, el acceso de fuera).
set -euo pipefail

PUERTO=8001
CLOUDFLARED="$HOME/.local/bin/cloudflared"

if [ ! -x "$CLOUDFLARED" ]; then
    echo "Falta cloudflared en $CLOUDFLARED"
    exit 1
fi

# El túnel apunta al puerto, no lo levanta: si el Client está caído, los de
# fuera verían un error de Cloudflare y no se entendería de dónde viene.
if ! (exec 3<>"/dev/tcp/127.0.0.1/$PUERTO") 2>/dev/null; then
    echo "No hay nada escuchando en 127.0.0.1:$PUERTO."
    echo "Levanta el Client primero:"
    echo "    cd Client && python manage.py runserver $PUERTO"
    exit 1
fi

echo "Túnel hacia http://127.0.0.1:$PUERTO"
echo "Comparte la URL https://....trycloudflare.com que aparece abajo."
echo
exec "$CLOUDFLARED" tunnel --url "http://127.0.0.1:$PUERTO"
