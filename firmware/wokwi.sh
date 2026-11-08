#!/usr/bin/env bash
# Simulação do abrigo no Wokwi (VS Code).
#
#   ./wokwi.sh preparar   baixa o MicroPython e instala o mpremote (uma vez)
#   ./wokwi.sh enviar     recompila o abrigo.aeg e envia o firmware ao simulador
#   ./wokwi.sh dedo       lê a digital pelo Touch ID do Mac e manda ao simulador
#                         (o Wokwi não tem o leitor AS608)
#   ./wokwi.sh placa      recompila e grava o firmware + config.json no ESP32 real
#                         pelo USB (porta automática; outra: AEGIS_PORTA=/dev/cu.xxx)
#   ./wokwi.sh pc         roda o firmware no Mac com sensores simulados
#                         (painel em http://localhost:8080)
#
# O config.json (WiFi, token do bot) fica fora do Git: modelo em
# config.exemplo.json. No Wokwi a rede vira sempre a Wokwi-GUEST.
#
# O "enviar" exige a simulação rodando: abra firmware/diagram.json no VS Code
# e aperte play (ou F1 > "Wokwi: Start Simulator").
set -euo pipefail

cd "$(dirname "$0")"

VERSAO="1.29.0"
FIRMWARE="ESP32_GENERIC-20260824-v${VERSAO}.bin"
URL="https://micropython.org/resources/firmware/${FIRMWARE}"
MPREMOTE=".venv/bin/mpremote"
MPYCROSS=".venv/bin/mpy-cross"
TOUCHID=".venv/touchid"
PORTA="port:rfc2217://localhost:4000"

# Gera o abrigo.py e pré-compila para bytecode no Mac. Na placa vão o
# boot.py (liga o WiFi com a memória livre), o main.py (carrega o abrigo) e
# o abrigo.mpy: compilar o abrigo.py no ESP32 esgota a RAM interna.
compilar() {
  node ../compilador/aegisc.js abrigo.aeg --alvo esp32 -o abrigo.py
  [ -x "$MPYCROSS" ] || .venv/bin/pip install --quiet "mpy-cross==${VERSAO}.post2"
  "$MPYCROSS" abrigo.py -o .venv/abrigo.mpy
}

# argumentos do mpremote que gravam os arquivos do firmware na placa
ARQUIVOS=(fs cp boot.py :boot.py + fs cp main.py :main.py + fs cp .venv/abrigo.mpy :abrigo.mpy)

preparar() {
  if [ ! -f "$FIRMWARE" ]; then
    echo "baixando MicroPython ${VERSAO} para ESP32..."
    curl -fL --progress-bar -o "$FIRMWARE" "$URL"
  fi
  if [ ! -x "$MPREMOTE" ]; then
    echo "instalando mpremote ${VERSAO} em firmware/.venv..."
    python3 -m venv .venv
    .venv/bin/pip install --quiet "mpremote==${VERSAO}" "mpy-cross==${VERSAO}.post2"
  fi
  compilar
  echo "pronto. Agora abra firmware/diagram.json no VS Code, aperte play e rode ./wokwi.sh enviar"
}

# cópia do config.json para o simulador: mesma conta do bot, mas a rede é a
# aberta do Wokwi e os MQ simulados não precisam de aquecimento longo
config_wokwi() {
  python3 - config.json .venv/config-wokwi.json <<'PY2'
import json, sys
c = json.load(open(sys.argv[1], encoding="utf-8"))
c.update(wifi_ssid="Wokwi-GUEST", wifi_senha="", usar_rede=True)
c.pop("aquecimento_ms", None)
json.dump(c, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
PY2
}

enviar() {
  [ -x "$MPREMOTE" ] || { echo "rode ./wokwi.sh preparar primeiro"; exit 1; }
  compilar
  # cp grava os arquivos no sistema de arquivos da placa simulada; reset é
  # um reset de hardware, depois do qual o MicroPython roda o main.py sozinho
  if [ -f config.json ]; then
    config_wokwi
    "$MPREMOTE" connect "$PORTA" "${ARQUIVOS[@]}" + fs cp .venv/config-wokwi.json :config.json + reset
  else
    "$MPREMOTE" connect "$PORTA" "${ARQUIVOS[@]}" + reset
  fi
  echo "firmware enviado. Veja a saída no terminal do Wokwi; painel em http://localhost:8180"
}

placa() {
  [ -x "$MPREMOTE" ] || { echo "rode ./wokwi.sh preparar primeiro"; exit 1; }
  compilar
  local porta="${AEGIS_PORTA:-auto}"
  if [ -f config.json ]; then
    "$MPREMOTE" connect "$porta" "${ARQUIVOS[@]}" + fs cp config.json :config.json + reset
  else
    echo "sem config.json: a placa sobe na rede do Wokwi, ou seja, offline (modelo em config.exemplo.json)"
    "$MPREMOTE" connect "$porta" "${ARQUIVOS[@]}" + reset
  fi
  echo "gravado. Para ver o serial: $MPREMOTE connect $porta repl  (sair: Ctrl+])"
}

dedo() {
  [ -x "$MPREMOTE" ] || { echo "rode ./wokwi.sh preparar primeiro"; exit 1; }
  if [ ! -x "$TOUCHID" ]; then
    echo "compilando o leitor do Touch ID..."
    swiftc -O touchid.swift -o "$TOUCHID"
  fi
  set +e
  "$TOUCHID"
  status=$?
  set -e
  case $status in
    0) linha="dedo 1"; echo "digital aceita" ;;
    1) linha="dedo -2"; echo "digital recusada" ;;
    *) exit 1 ;;
  esac
  # o firmware lê "dedo <n>" da serial quando não encontra o AS608. DTR e RTS
  # ficam desligados antes de abrir: nas placas ESP32 eles reiniciam o chip.
  .venv/bin/python - "$linha" <<'PY'
import sys, serial
porta = serial.serial_for_url("rfc2217://localhost:4000", do_not_open=True, timeout=1)
porta.dtr = False
porta.rts = False
porta.open()
porta.write((sys.argv[1] + "\n").encode())
porta.flush()
porta.close()
PY
}

case "${1:-}" in
  preparar) preparar ;;
  enviar) enviar ;;
  dedo) dedo ;;
  placa) placa ;;
  pc) python3 rodar_pc.py ;;
  *) echo "uso: ./wokwi.sh preparar | enviar | dedo | placa | pc"; exit 2 ;;
esac
