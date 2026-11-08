"""Testa a lógica do firmware do abrigo no PC, sem placa e sem simulador.

    python3 firmware/cenarios.py

Compila firmware/abrigo.aeg para o alvo "simulado", carrega o Python gerado
sem rodar o laço principal e, para cada cenário, ajusta os sensores falsos do
runtime, executa um ciclo() e confere LEDs, buzzer e estado.
"""

import contextlib
import io
import json
import os
import socket
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "firmware", "abrigo.aeg")
AEGISC = os.path.join(RAIZ, "compilador", "aegisc.js")


def carregar_firmware():
    # os cenários nunca leem o config.json de verdade: com o token do bot lá,
    # cada cenário mandaria mensagens reais para o Telegram
    os.environ["AEGIS_CONFIG"] = ""
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
    for nome in ("chovendo", "solo_encharcado", "deslizamento",
                 "rele_ligado", "houve_fumaca", "armado", "em_entrada", "intruso"):
        g[nome] = False
    g["finger"].fila.clear()
    g["painel"] = False
    g["web"].fila.clear()
    g["bot"] = False
    g["telegram"].fila.clear()
    g["telegram"].enviadas.clear()
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
    assert g["estado"] == g["ALARME"] and g["motivo"] == "DESLIZAMENTO", g["motivo"]
    assert buzzer_ligado(g)


@cenario("chuva para com o solo saturado: o alarme de deslizamento continua")
def _(g):
    molhar(g, "PINO_CHUVA", "CHUVA_SECO", "CHUVA_MOLHADO", 60)
    molhar(g, "PINO_SOLO", "SOLO_SECO", "SOLO_MOLHADO", 90)
    ciclo(g)
    molhar(g, "PINO_CHUVA", "CHUVA_SECO", "CHUVA_MOLHADO", 0)
    ciclo(g, vezes=20)
    assert not g["chovendo"]
    assert g["estado"] == g["ALARME"] and g["motivo"] == "DESLIZAMENTO", g["motivo"]
    molhar(g, "PINO_SOLO", "SOLO_SECO", "SOLO_MOLHADO", 40)      # solo secou
    ciclo(g, vezes=20)
    assert g["estado"] == g["NORMAL"], g["motivo"]


def rele(g):
    return g["gpio"].estado.get(g["PINO_RELE"]) == g["RELE_ATIVO_EM_ALTO"]


@cenario("fumaca liga o exaustor; ele segue ligado RELE_EXTRA_MS depois")
def _(g):
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    log = ciclo(g)
    assert rele(g) and "exaustor ligado" in log, log
    g["adc"].estado[g["PINO_MQ2"]] = 100
    ciclo(g, vezes=10)
    assert g["estado"] == g["NORMAL"] and rele(g), "desligou cedo demais"
    g["ultima_fumaca"] = g["time"].ms() - g["RELE_EXTRA_MS"] - 1
    log = ciclo(g)
    assert not rele(g) and "exaustor desligado" in log, log


@cenario("silenciar o buzzer nao desliga o exaustor")
def _(g):
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    ciclo(g)
    g["gpio"].estado[g["PINO_BOTAO"]] = True
    ciclo(g)
    assert g["silenciado"] and not buzzer_ligado(g) and rele(g)


@cenario("enchente nao liga o exaustor")
def _(g):
    g["sonar"].cm = 10.0
    ciclo(g)
    assert g["estado"] == g["ALARME"] and not rele(g)


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


def passar(g, nome_marca, ms):
    """Volta a marca de tempo nome_marca em ms, como se esse tempo tivesse passado."""
    g[nome_marca] -= ms


@cenario("desarmado: presenca no PIR e ignorada")
def _(g):
    g["gpio"].estado[g["PINO_PIR"]] = True
    ciclo(g)
    assert g["estado"] == g["NORMAL"], g["motivo"]


@cenario("digital arma; presenca no tempo de saida e ignorada")
def _(g):
    g["finger"].fila.append(1)
    log = ciclo(g)
    assert g["armado"] and "armado pela digital 1" in log, log
    g["gpio"].estado[g["PINO_PIR"]] = True       # a pessoa ainda esta saindo
    ciclo(g)
    assert g["estado"] == g["NORMAL"] and not g["em_entrada"]


@cenario("armado: presenca abre o tempo de entrada e depois vira INTRUSO")
def _(g):
    g["finger"].fila.append(1)
    ciclo(g)
    passar(g, "armado_em", g["ATRASO_SAIDA_MS"])
    g["gpio"].estado[g["PINO_PIR"]] = True
    ciclo(g)
    assert g["estado"] == g["ATENCAO"] and g["motivo"] == "use a digital", g["motivo"]
    assert not buzzer_ligado(g)
    passar(g, "entrada_em", g["ATRASO_ENTRADA_MS"])
    g["gpio"].estado[g["PINO_PIR"]] = False      # o intruso saiu da frente do PIR
    log = ciclo(g)
    assert g["estado"] == g["ALARME"] and g["motivo"] == "INTRUSO", g["motivo"]
    assert buzzer_ligado(g) and "ALARME - INTRUSO" in log


@cenario("digital no tempo de entrada desarma sem alarme")
def _(g):
    g["finger"].fila.append(1)
    ciclo(g)
    passar(g, "armado_em", g["ATRASO_SAIDA_MS"])
    g["gpio"].estado[g["PINO_PIR"]] = True
    ciclo(g)
    g["finger"].fila.append(2)
    ciclo(g)
    passar(g, "entrada_em", g["ATRASO_ENTRADA_MS"])
    ciclo(g)
    assert not g["armado"] and g["estado"] == g["NORMAL"], g["motivo"]


@cenario("digital desconhecida: tres bipes e nada muda")
def _(g):
    g["finger"].fila.append(-2)
    log = ciclo(g)
    assert not g["armado"] and "nao reconhecida" in log, log
    assert log.count("tom de 3000 Hz") == 3, log


@cenario("desarmar nao cala o alarme de fumaca")
def _(g):
    g["finger"].fila.append(1)
    ciclo(g)
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    g["finger"].fila.append(1)
    ciclo(g, vezes=6)                            # a media filtrada sobe aos poucos
    assert not g["armado"] and g["estado"] == g["ALARME"] and g["motivo"] == "FUMACA/GAS"


@cenario("ar ruim no MQ-135: ATENCAO")
def _(g):
    g["adc"].estado[g["PINO_MQ135"]] = 3000
    ciclo(g)
    assert g["estado"] == g["ATENCAO"] and g["motivo"] == "ar ruim"


@cenario("chuva + fumaca: o mais grave vence")
def _(g):
    molhar(g, "PINO_CHUVA", "CHUVA_SECO", "CHUVA_MOLHADO", 50)
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


@cenario("painel: /dados devolve JSON valido com o estado e as leituras")
def _(g):
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    ciclo(g)
    dados = json.loads(g["leituras_json"]())
    assert dados["estado"] == g["ALARME"] and dados["nome"] == "ALARME", dados
    assert dados["motivo"] == "FUMACA/GAS" and dados["temp"] == 25.0, dados
    assert dados["fumaca_lim"] == g["MARGEM_FUMACA"] and dados["armado"] == 0, dados


@cenario("painel: servidor HTTP de verdade responde /, /dados e 404")
def _(g):
    web = g["web"]
    assert web.start(18080), "nao abriu a porta 18080"
    g["painel"] = True

    def pedir(linha):
        cliente = socket.create_connection(("127.0.0.1", 18080), timeout=2)
        cliente.sendall(linha.encode() + b"\r\nHost: x\r\n\r\n")
        for _ in range(5):                        # o firmware atende dentro do ciclo
            ciclo(g)
        resposta = b""
        while True:
            parte = cliente.recv(4096)
            if not parte:
                break
            resposta += parte
        cliente.close()
        cabecalho, _, corpo = resposta.partition(b"\r\n\r\n")
        return cabecalho.decode(), corpo.decode()

    try:
        cab, corpo = pedir("GET /dados HTTP/1.1")
        assert cab.startswith("HTTP/1.1 200") and "application/json" in cab, cab
        assert json.loads(corpo)["nome"] == "NORMAL", corpo
        cab, corpo = pedir("GET / HTTP/1.1")
        assert "text/html" in cab and corpo.startswith("<!doctype html>"), cab
        cab, _ = pedir("GET /outra HTTP/1.1")
        assert cab.startswith("HTTP/1.1 404"), cab
    finally:
        web._servidor.close()
        web._servidor = None


@cenario("painel: botao Silenciar cala a sirene, o alarme continua")
def _(g):
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    ciclo(g)
    g["painel"] = True
    g["web"].fila.append("/silenciar")
    log = ciclo(g)
    assert g["silenciado"] and "silenciado pelo painel" in log, log
    assert g["estado"] == g["ALARME"] and leds(g)["vermelho"] and not buzzer_ligado(g)


@cenario("painel: Silenciar fora do alarme nao faz nada")
def _(g):
    g["painel"] = True
    g["web"].fila.append("/silenciar")
    ciclo(g)
    assert not g["silenciado"]


def com_bot(g):
    """Liga o bot e parte de um NORMAL ja relatado, como numa placa ligada ha tempo."""
    g["bot"] = True
    g["estado_anterior"] = g["NORMAL"]
    g["motivo_anterior"] = "tudo em ordem"
    g["telegram"].enviadas.clear()
    return g["telegram"].enviadas


@cenario("Telegram: alarme avisa uma vez; voltar ao NORMAL tambem avisa")
def _(g):
    enviadas = com_bot(g)
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    ciclo(g, vezes=3)
    assert enviadas == ["🚨 ALARME: FUMACA/GAS"], enviadas
    g["adc"].estado[g["PINO_MQ2"]] = 100
    ciclo(g, vezes=10)
    assert enviadas[-1] == "✅ NORMAL: tudo em ordem", enviadas


@cenario("Telegram: o NORMAL da partida nao vira mensagem")
def _(g):
    com_bot(g)
    g["estado_anterior"] = -1
    ciclo(g)
    assert g["telegram"].enviadas == [], g["telegram"].enviadas


@cenario("Telegram: /status responde com as leituras")
def _(g):
    enviadas = com_bot(g)
    g["climate"].temperatura = 31.5
    g["telegram"].fila.append("/status")
    ciclo(g)
    assert len(enviadas) == 1 and enviadas[0].startswith("✅ NORMAL: tudo em ordem"), enviadas
    assert "31.5 °C" in enviadas[0] and "desarmado" in enviadas[0], enviadas[0]


@cenario("Telegram: /silenciar no alarme cala a sirene e confirma")
def _(g):
    enviadas = com_bot(g)
    g["adc"].estado[g["PINO_MQ2"]] = 3000
    ciclo(g)
    g["telegram"].fila.append("/silenciar")
    log = ciclo(g)
    assert g["silenciado"] and "silenciado pelo Telegram" in log, log
    assert not buzzer_ligado(g) and g["estado"] == g["ALARME"]
    assert enviadas[-1].startswith("🔇 Sirene silenciada pelo Telegram"), enviadas


@cenario("Telegram: /silenciar sem alarme so responde")
def _(g):
    enviadas = com_bot(g)
    g["telegram"].fila.append("/silenciar")
    ciclo(g)
    assert not g["silenciado"] and enviadas == ["Nada para silenciar: o abrigo está em NORMAL."], enviadas


@cenario("Telegram: /ajuda lista os comandos; comando desconhecido e avisado")
def _(g):
    enviadas = com_bot(g)
    g["telegram"].fila.extend(["/ajuda", "/abrir"])
    ciclo(g, vezes=2)
    assert "/status" in enviadas[0] and "/silenciar" in enviadas[0], enviadas
    assert enviadas[1] == "Não conheço /abrir. Mande /ajuda.", enviadas


@cenario("Telegram: armar e desarmar pela digital avisam o dono")
def _(g):
    enviadas = com_bot(g)
    g["finger"].fila.append(1)
    ciclo(g)
    assert g["armado"] and enviadas[-1].startswith("🔒 Abrigo armado pela digital 1"), enviadas
    g["finger"].fila.append(1)
    ciclo(g)
    assert not g["armado"] and enviadas[-1] == "🔓 Abrigo desarmado pela digital 1.", enviadas
    g["finger"].fila.append(-2)
    ciclo(g)
    assert "não cadastrada" in enviadas[-1], enviadas


@cenario("Telegram: so aceita comandos do chat configurado, novos e sem @bot")
def _(g):
    bot = g["telegram"]
    respostas = [
        # 1a consulta (offset -1): o que chegou antes de ligar e descartado
        {"ok": True, "result": [{"update_id": 10, "message": {"chat": {"id": 42}, "text": "/silenciar"}}]},
        {"ok": True, "result": [
            {"update_id": 11, "message": {"chat": {"id": 99}, "text": "/silenciar"}},   # outro chat
            {"update_id": 12, "message": {"chat": {"id": 42}, "text": "oi"}},           # nao e comando
            {"update_id": 13, "message": {"chat": {"id": 42}, "text": "/Status@aegis_bot agora"}},
        ]},
    ]
    pedidos = []

    def falso(metodo, dados):
        pedidos.append(dict(dados))
        return respostas.pop(0)

    bot._pedir = falso
    try:
        assert bot.begin("123:abc", 42)
        assert bot.command(0) == "", "comando antigo nao pode ser atendido"
        assert bot.command(0) == "/status"
        assert bot.command(60000) == "" and len(pedidos) == 2, "consultou antes do intervalo"
        assert pedidos[0]["offset"] == -1 and pedidos[1]["offset"] == 11, pedidos
    finally:
        del bot._pedir
        bot.begin("", "")


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
