#!/usr/bin/env bash
# Simulação do abrigo no Wokwi (VS Code).
#
#   ./wokwi.sh preparar   baixa o MicroPython e instala o mpremote (uma vez)
#   ./wokwi.sh enviar     recompila o abrigo.aeg e envia o main.py ao simulador
#
# O "enviar" exige a simulação rodando: abra firmware/diagram.json no VS Code
# e aperte play (ou F1 > "Wokwi: Start Simulator").
set -euo pipefail

cd "$(dirname "$0")"

VERSAO="1.29.0"
FIRMWARE="ESP32_GENERIC-20260824-v${VERSAO}.bin"
URL="https://micropython.org/resources/firmware/${FIRMWARE}"
MPREMOTE=".venv/bin/mpremote"
PORTA="port:rfc2217://localhost:4000"

compilar() {
  node ../compilador/aegisc.js abrigo.aeg --alvo esp32 -o main.py
}

preparar() {
  if [ ! -f "$FIRMWARE" ]; then
    echo "baixando MicroPython ${VERSAO} para ESP32..."
    curl -fL --progress-bar -o "$FIRMWARE" "$URL"
  fi
  if [ ! -x "$MPREMOTE" ]; then
    echo "instalando mpremote ${VERSAO} em firmware/.venv..."
    python3 -m venv .venv
    .venv/bin/pip install --quiet "mpremote==${VERSAO}"
  fi
  compilar
  echo "pronto. Agora abra firmware/diagram.json no VS Code, aperte play e rode ./wokwi.sh enviar"
}

enviar() {
  [ -x "$MPREMOTE" ] || { echo "rode ./wokwi.sh preparar primeiro"; exit 1; }
  compilar
  # cp grava o main.py no sistema de arquivos da placa simulada; reset é um
  # reset de hardware, depois do qual o MicroPython roda o main.py sozinho
  "$MPREMOTE" connect "$PORTA" fs cp main.py :main.py + reset
  echo "main.py enviado. Veja a saída no terminal do Wokwi."
}

case "${1:-}" in
  preparar) preparar ;;
  enviar) enviar ;;
  *) echo "uso: ./wokwi.sh preparar | enviar"; exit 2 ;;
esac
