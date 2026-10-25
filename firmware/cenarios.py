"""Testa a lógica do firmware do abrigo no PC, sem placa e sem simulador.

    python3 firmware/cenarios.py

Compila firmware/abrigo.aeg para o alvo "simulado", carrega o Python gerado
sem rodar o laço principal e, para cada cenário, ajusta os sensores falsos do
runtime, executa um ciclo() e confere LEDs, buzzer e estado.
"""

import contextlib
import io
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "firmware", "abrigo.aeg")
AEGISC = os.path.join(RAIZ, "compilador", "aegisc.js")


def carregar_firmware():
    python = subprocess.run(
        ["node", AEGISC, FONTE, "--alvo", "simulado"],
        check=True, capture_output=True, text=True,
    ).stdout
    g = {"__name__": "cenarios"}  # evita o if __name__ == "__main__"
    exec(compile(python, "abrigo (simulado)", "exec"), g)
    return g


def zerar_sensores(g):
    g["gpio"].estado.clear()
    g["adc"].estado.clear()
    g["adc"].estado[g["PINO_CHUVA"]] = g["CHUVA_SECO"]   # chuva e solo leem alto secos
    g["adc"].estado[g["PINO_SOLO"]] = g["SOLO_SECO"]
    g["pwm"].estado.clear()
    g["sonar"].cm = 100.0
    g["climate"].temperatura = 25.0
    g["climate"].umidade = 50.0
    g["inicio"] = 0                 # já passou do aquecimento dos MQ
    g["silenciado"] = False
    g["estado"] = g["NORMAL"]
    g["rede"] = False
    for nome in ("risco_fumaca", "risco_ar", "base_fumaca", "base_ar",
                 "media_fumaca", "media_ar", "amostras"):
        g[nome] = 0
    for nome in ("chovendo", "solo_encharcado", "deslizamento"):
        g[nome] = False
    g["filtro_pronto"] = False      # a primeira leitura vira a média
    g["base_registrada"] = True


def ciclo(g, vezes=1):
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        for _ in range(vezes):
            g["ciclo"]()
    return saida.getvalue()


def leds(g):
    pinos = g["gpio"].estado
    return {
        "verde": pinos.get(g["LED_VERDE"]),
        "amarelo": pinos.get(g["LED_AMARELO"]),
        "vermelho": pinos.get(g["LED_VERMELHO"]),
    }


def buzzer_ligado(g):
    return bool(g["pwm"].estado.get(g["PINO_BUZZER"]))


CENARIOS = []


def cenario(nome):
    def registrar(fn):
        CENARIOS.append((nome, fn))
        return fn
    return registrar


@cenario("tudo normal: LED verde, buzzer desligado")
def _(g):
    ciclo(g)
    assert g["estado"] == g["NORMAL"]
    assert leds(g) == {"verde": True, "amarelo": False, "vermelho": False}
    assert not buzzer_ligado(g)


@cenario("fumaca acima do limite: ALARME com sirene")
def _(g):
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    log = ciclo(g)
    assert g["estado"] == g["ALARME"] and g["motivo"] == "FUMACA/GAS", g["motivo"]
    assert leds(g)["vermelho"] and not leds(g)["verde"]
    assert buzzer_ligado(g)
    assert "ALARME - FUMACA/GAS" in log, log


@cenario("fumaca durante o aquecimento dos MQ: ignorada")
def _(g):
    g["inicio"] = g["time"].ms()
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    ciclo(g)
    assert g["estado"] == g["NORMAL"]


@cenario("ar limpo com leitura alta (o caso do Wokwi): vira a base, sem alarme")
def _(g):
    g["inicio"] = g["time"].ms()                 # comeca aquecendo
    g["base_registrada"] = False
    g["adc"].estado[g["PINO_MQ2"]] = 2500
    ciclo(g, vezes=5)
    assert g["base_fumaca"] == 2500, g["base_fumaca"]
    g["inicio"] = g["time"].ms() - g["AQUECIMENTO_MS"] - 1   # aquecimento acabou
    log = ciclo(g, vezes=3)
    assert g["estado"] == g["NORMAL"], g["motivo"]
    assert "base de ar limpo: fumaca 2500" in log, log


@cenario("histerese: alarme so desliga bem abaixo do limite, sem liga-desliga")
def _(g):
    g["base_fumaca"] = 2500                      # limite de alarme = 3300
    g["adc"].estado[g["PINO_MQ2"]] = 3400
    ciclo(g)
    assert g["estado"] == g["ALARME"]
    g["adc"].estado[g["PINO_MQ2"]] = 3100        # caiu, mas ainda acima de 3000
    ciclo(g)
    assert g["estado"] == g["ALARME"], "nao pode desligar dentro da histerese"
    g["adc"].estado[g["PINO_MQ2"]] = 2900        # abaixo de base + 500
    ciclo(g, vezes=20)                           # a média filtrada desce aos poucos
    assert g["estado"] == g["NORMAL"]


@cenario("ruido do MQ-2 do Wokwi (1800..2400) em torno da base: sem alarme")
def _(g):
    g["base_fumaca"] = g["media_fumaca"] = 2100
    g["filtro_pronto"] = True
    # as leituras do log do Wokwi, repetidas: picos passam de base + 800 na
    # leitura crua de vez em quando, mas a média não
    for leitura in [1987, 2093, 1806, 2372, 2264, 2950, 1700, 2400] * 10:
        g["adc"].estado[g["PINO_MQ2"]] = leitura
        ciclo(g)
        assert g["estado"] == g["NORMAL"], (leitura, g["media_fumaca"], g["base_fumaca"])


@cenario("deriva lenta do sensor (+5 por ciclo): a base acompanha, sem alarme")
def _(g):
    g["base_fumaca"] = g["media_fumaca"] = 1600
    g["filtro_pronto"] = True
    for i in range(300):                         # 2,5 min subindo ate 3100
        g["adc"].estado[g["PINO_MQ2"]] = 1600 + 5 * i
        ciclo(g)
        assert g["estado"] == g["NORMAL"], (i, g["media_fumaca"], g["base_fumaca"])
    assert g["base_fumaca"] > 2500, g["base_fumaca"]


@cenario("fumaca de verdade (salto de +1200): alarma em ate 3 s")
def _(g):
    g["base_fumaca"] = g["media_fumaca"] = 2000
    g["filtro_pronto"] = True
    g["adc"].estado[g["PINO_MQ2"]] = 3200
    ciclo(g, vezes=6)                            # 6 ciclos de 500 ms
    assert g["estado"] == g["ALARME"], (g["media_fumaca"], g["base_fumaca"])


def molhar(g, pino, seco, molhado, pct):
    """Leitura do ADC equivalente a pct% de molhado."""
    g["adc"].estado[g[pino]] = int(g[seco] - (g[seco] - g[molhado]) * pct / 100)


@cenario("percentual_molhado: 0 no seco, 100 no molhado, limitado nos extremos")
def _(g):
    p = g["percentual_molhado"]
    assert p(4095, 4095, 1000) == 0 and p(1000, 4095, 1000) == 100
    assert p(5000, 4095, 1000) == 0 and p(0, 4095, 1000) == 100
    assert p(2000, 2900, 1100) == 50


@cenario("chuva a 50%: ATENCAO chovendo, sem sirene")
def _(g):
    molhar(g, "PINO_CHUVA", "CHUVA_SECO", "CHUVA_MOLHADO", 50)
    log = ciclo(g)
    assert g["estado"] == g["ATENCAO"] and g["motivo"] == "chovendo", g["motivo"]
    assert not buzzer_ligado(g)
    assert "ATENCAO - chovendo" in log, log


@cenario("solo a 90% sem chuva: so ATENCAO, nao e deslizamento")
def _(g):
    molhar(g, "PINO_SOLO", "SOLO_SECO", "SOLO_MOLHADO", 90)
    ciclo(g)
    assert g["estado"] == g["ATENCAO"] and g["motivo"] == "solo encharcado", g["motivo"]


@cenario("chuva + solo a 90%: ALARME de deslizamento")
def _(g):
    molhar(g, "PINO_CHUVA", "CHUVA_SECO", "CHUVA_MOLHADO", 60)
    molhar(g, "PINO_SOLO", "SOLO_SECO", "SOLO_MOLHADO", 90)
    ciclo(g)
    assert g["estado"] == g["ALARME"] and g["motivo"] == "RISCO DESLIZAMENTO", g["motivo"]
    assert buzzer_ligado(g)


@cenario("chuva para com o solo saturado: o alarme de deslizamento continua")
def _(g):
    molhar(g, "PINO_CHUVA", "CHUVA_SECO", "CHUVA_MOLHADO", 60)
    molhar(g, "PINO_SOLO", "SOLO_SECO", "SOLO_MOLHADO", 90)
    ciclo(g)
    molhar(g, "PINO_CHUVA", "CHUVA_SECO", "CHUVA_MOLHADO", 0)
    ciclo(g, vezes=20)
    assert not g["chovendo"]
    assert g["estado"] == g["ALARME"] and g["motivo"] == "RISCO DESLIZAMENTO", g["motivo"]
    molhar(g, "PINO_SOLO", "SOLO_SECO", "SOLO_MOLHADO", 40)      # solo secou
    ciclo(g, vezes=20)
    assert g["estado"] == g["NORMAL"], g["motivo"]


@cenario("agua a 10 cm do sensor: ALARME de enchente")
def _(g):
    g["sonar"].cm = 10.0
    ciclo(g)
    assert g["estado"] == g["ALARME"] and g["motivo"] == "ENCHENTE"


@cenario("sonar sem eco (-1): nao dispara enchente")
def _(g):
    g["sonar"].cm = -1.0
    ciclo(g)
    assert g["estado"] == g["NORMAL"]


@cenario("45 graus: ATENCAO; 60 graus: ALARME")
def _(g):
    g["climate"].temperatura = 45.0
    ciclo(g)
    assert g["estado"] == g["ATENCAO"] and g["motivo"] == "calor"
    assert leds(g)["amarelo"] and not buzzer_ligado(g)
    g["climate"].temperatura = 60.0
    ciclo(g)
    assert g["estado"] == g["ALARME"] and g["motivo"] == "TEMP ALTA"


@cenario("presenca no PIR: ATENCAO sem sirene")
def _(g):
    g["gpio"].estado[g["PINO_PIR"]] = True
    ciclo(g)
    assert g["estado"] == g["ATENCAO"] and g["motivo"] == "presenca"
    assert not buzzer_ligado(g)


@cenario("ar ruim no MQ-135: ATENCAO")
def _(g):
    g["adc"].estado[g["PINO_MQ135"]] = 3000
    ciclo(g)
    assert g["estado"] == g["ATENCAO"] and g["motivo"] == "ar ruim"


@cenario("fumaca + presenca: o mais grave vence")
def _(g):
    g["gpio"].estado[g["PINO_PIR"]] = True
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    ciclo(g)
    assert g["estado"] == g["ALARME"] and g["motivo"] == "FUMACA/GAS"


@cenario("botao cala o buzzer, LED vermelho continua; volta apos SILENCIO_MS")
def _(g):
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    ciclo(g)
    g["gpio"].estado[g["PINO_BOTAO"]] = True     # pressionado
    log = ciclo(g)
    assert g["silenciado"] and "silenciado" in log
    assert not buzzer_ligado(g) and leds(g)["vermelho"]
    g["gpio"].estado[g["PINO_BOTAO"]] = False
    g["silencio_desde"] = g["time"].ms() - g["SILENCIO_MS"] - 1
    ciclo(g)
    assert not g["silenciado"] and buzzer_ligado(g)


@cenario("alarme resolvido: volta ao NORMAL e libera o silencio")
def _(g):
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    ciclo(g)
    g["silenciado"] = True
    g["adc"].estado[g["PINO_MQ2"]] = 100
    ciclo(g, vezes=10)
    assert g["estado"] == g["NORMAL"] and not g["silenciado"]
    assert leds(g)["verde"] and not buzzer_ligado(g)


def principal():
    g = carregar_firmware()
    falhas = 0
    for nome, fn in CENARIOS:
        zerar_sensores(g)
        try:
            fn(g)
            print("OK  ", nome)
        except AssertionError as erro:
            falhas += 1
            print("FAIL", nome, "-", erro)
    print(f"\n{len(CENARIOS) - falhas}/{len(CENARIOS)} cenarios passaram.")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(principal())
