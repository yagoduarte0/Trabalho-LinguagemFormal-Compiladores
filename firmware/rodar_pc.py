"""Roda o firmware do abrigo no Mac, com sensores simulados.

    python3 firmware/rodar_pc.py

É o mesmo abrigo.aeg da placa, compilado para o alvo "simulado". O painel
abre em http://localhost:8080 e, com o token e o chat no firmware/config.json,
o bot do Telegram funciona de verdade. Para provocar um evento, digite no
terminal e aperte Enter:

    fumaca  agua  calor  chuva  deslizamento  ar   -> liga o evento
    dedo  (arma/desarma)   estranho  (digital desconhecida)
    intruso  (presença no PIR; arme antes com "dedo")
    botao  (botão de silenciar)   normal  (volta tudo ao normal)
"""

import os
import subprocess
import sys
import threading

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

AR_LIMPO = 1200            # leitura dos MQ no ar limpo (vira a base no aquecimento)
AQUECIMENTO_PC_MS = 5000   # no PC não há sensor para esquentar


def carregar():
    python = subprocess.run(
        ["node", os.path.join(RAIZ, "compilador", "aegisc.js"),
         os.path.join(AQUI, "abrigo.aeg"), "--alvo", "simulado"],
        check=True, capture_output=True, text=True,
    ).stdout
    os.environ.setdefault("AEGIS_CONFIG", os.path.join(AQUI, "config.json"))
    g = {"__name__": "abrigo_pc"}          # não roda o main() ainda
    exec(compile(python, "abrigo (simulado)", "exec"), g)
    g["aquecimento_ms"] = AQUECIMENTO_PC_MS
    return g


def normal(g):
    adc = g["adc"].estado
    adc[g["PINO_MQ2"]] = AR_LIMPO
    adc[g["PINO_MQ135"]] = AR_LIMPO
    adc[g["PINO_CHUVA"]] = g["CHUVA_SECO"]
    adc[g["PINO_SOLO"]] = g["SOLO_SECO"]
    g["sonar"].cm = 100.0
    g["climate"].temperatura = 25.0
    g["climate"].umidade = 55.0
    g["gpio"].estado[g["PINO_PIR"]] = False


def evento(g, nome):
    adc = g["adc"].estado
    if nome == "normal":
        normal(g)
    elif nome == "fumaca":
        adc[g["PINO_MQ2"]] = AR_LIMPO + 1500
    elif nome == "ar":
        adc[g["PINO_MQ135"]] = AR_LIMPO + 1200
    elif nome == "agua":
        g["sonar"].cm = 10.0
    elif nome == "calor":
        g["climate"].temperatura = 60.0
    elif nome == "chuva":
        adc[g["PINO_CHUVA"]] = 1800                  # ~74 % molhado
    elif nome == "deslizamento":
        adc[g["PINO_CHUVA"]] = 1800
        adc[g["PINO_SOLO"]] = g["SOLO_MOLHADO"]
    elif nome == "intruso":
        g["gpio"].estado[g["PINO_PIR"]] = True
    elif nome == "dedo":
        g["finger"].fila.append(1)
    elif nome == "estranho":
        g["finger"].fila.append(-2)
    elif nome == "botao":
        g["gpio"].estado[g["PINO_BOTAO"]] = True
        threading.Timer(1.0, lambda: g["gpio"].estado.update({g["PINO_BOTAO"]: False})).start()
    else:
        print("?? eventos:", __doc__.split("terminal e aperte Enter:")[1].strip())
        return
    print(">> evento:", nome)


def teclado(g):
    for linha in sys.stdin:
        nome = linha.strip().lower()
        if nome:
            evento(g, nome)


def principal():
    g = carregar()
    normal(g)
    threading.Thread(target=teclado, args=(g,), daemon=True).start()
    try:
        g["main"]()
    except KeyboardInterrupt:
        print("\nabrigo desligado")


if __name__ == "__main__":
    principal()
