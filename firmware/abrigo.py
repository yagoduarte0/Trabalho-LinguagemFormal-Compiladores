# --- runtime AEGIS para ESP32 (MicroPython, gerado automaticamente) ---
import time as _time
import machine as _machine
import dht as _dht
import framebuf as _framebuf


class _Gpio:
    def __init__(self):
        self._entradas = {}
        self._saidas = {}

    def read(self, pino):
        p = self._entradas.get(pino)
        if p is None:
            p = _machine.Pin(pino, _machine.Pin.IN)
            self._entradas[pino] = p
            self._saidas.pop(pino, None)
        return p.value() == 1

    # botão ligado entre o pino e o GND: pull-up interno, pressionado = 0
    def pressed(self, pino):
        p = self._entradas.get(pino)
        if p is None:
            p = _machine.Pin(pino, _machine.Pin.IN, _machine.Pin.PULL_UP)
            self._entradas[pino] = p
            self._saidas.pop(pino, None)
        return p.value() == 0

    def write(self, pino, valor):
        p = self._saidas.get(pino)
        if p is None:
            p = _machine.Pin(pino, _machine.Pin.OUT)
            self._saidas[pino] = p
            self._entradas.pop(pino, None)
        p.value(1 if valor else 0)


class _Adc:
    def __init__(self):
        self._canais = {}

    # 0..4095; atenuação de 11 dB lê a faixa inteira de 0 a ~3,3 V
    def read(self, pino):
        c = self._canais.get(pino)
        if c is None:
            c = _machine.ADC(_machine.Pin(pino))
            c.atten(_machine.ADC.ATTN_11DB)
            self._canais[pino] = c
        return c.read_u16() >> 4


class _Pwm:
    def __init__(self):
        self._canais = {}

    def tone(self, pino, hz):
        c = self._canais.get(pino)
        if c is None:
            c = _machine.PWM(_machine.Pin(pino))
            self._canais[pino] = c
        c.freq(int(hz))
        c.duty_u16(32768)

    def off(self, pino):
        c = self._canais.get(pino)
        if c is not None:
            c.duty_u16(0)


class _Sonar:
    def __init__(self):
        self._pares = {}

    # HC-SR04: pulso de 10 us no TRIG, o ECHO fica alto pelo tempo de ida e
    # volta do som (58 us por cm). Sem eco em 30 ms devolve -1.
    def distance(self, trig, echo):
        par = self._pares.get(trig)
        if par is None:
            par = (_machine.Pin(trig, _machine.Pin.OUT), _machine.Pin(echo, _machine.Pin.IN))
            self._pares[trig] = par
        t, e = par
        t.value(0)
        _time.sleep_us(2)
        t.value(1)
        _time.sleep_us(10)
        t.value(0)
        duracao = _machine.time_pulse_us(e, 1, 30000)
        if duracao < 0:
            return -1.0
        return duracao / 58.0


class _Clima:
    def __init__(self):
        self._sensores = {}
        self._leituras = {}

    # o DHT22 só aceita uma leitura a cada 2 s: entre elas, devolve a última
    def _medir(self, pino):
        s = self._sensores.get(pino)
        if s is None:
            s = _dht.DHT22(_machine.Pin(pino))
            self._sensores[pino] = s
        ultima = self._leituras.get(pino)
        if ultima is None or _time.ticks_diff(_time.ticks_ms(), ultima[0]) >= 2000:
            try:
                s.measure()
                ultima = (_time.ticks_ms(), s.temperature(), s.humidity())
            except OSError:
                if ultima is None:
                    ultima = (_time.ticks_ms(), -1.0, -1.0)
            self._leituras[pino] = ultima
        return ultima

    def temperature(self, pino):
        return self._medir(pino)[1]

    def humidity(self, pino):
        return self._medir(pino)[2]


# driver mínimo do OLED SSD1306 128x64 por I2C (endereço 0x3C), desenhado
# sobre o framebuf nativo: 8 linhas de 16 caracteres
_SSD1306_INICIO = (0xAE, 0x20, 0x00, 0x40, 0xA1, 0xA8, 0x3F, 0xC8, 0xD3, 0x00,
                   0xDA, 0x12, 0xD5, 0x80, 0xD9, 0xF1, 0xDB, 0x30, 0x81, 0xFF,
                   0xA4, 0xA6, 0x8D, 0x14, 0xAF)


# Desenhos 1 bit por pixel, linha a linha, bit mais alto à esquerda
# (framebuf.MONO_HLSB). Gerados a partir de arte em texto ("#" = aceso).
_LOGO = bytes((0x00, 0x00, 0x00, 0x00, 0x3F, 0xFF, 0xFF, 0xFC, 0x3F, 0xFF, 0xFF, 0xFC, 0x30, 0x00, 0x00, 0x0C, 0x30, 0x00, 0x00, 0x0C, 0x30, 0x01, 0x80, 0x0C, 0x30, 0x03, 0xC0, 0x0C, 0x30, 0x06, 0x60, 0x0C, 0x30, 0x06, 0x60, 0x0C, 0x30, 0x0C, 0x30, 0x0C, 0x30, 0x0C, 0x30, 0x0C, 0x30, 0x18, 0x18, 0x0C, 0x30, 0x18, 0x18, 0x0C, 0x30, 0x3F, 0xFC, 0x0C, 0x30, 0x3F, 0xFC, 0x0C, 0x30, 0x60, 0x06, 0x0C, 0x18, 0x60, 0x06, 0x18, 0x0C, 0xC0, 0x03, 0x30, 0x06, 0x00, 0x00, 0x60, 0x03, 0x00, 0x00, 0xC0, 0x01, 0x80, 0x01, 0x80, 0x00, 0xC0, 0x03, 0x00, 0x00, 0x60, 0x06, 0x00, 0x00, 0x30, 0x0C, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x0C, 0x30, 0x00, 0x00, 0x06, 0x60, 0x00, 0x00, 0x03, 0xC0, 0x00, 0x00, 0x01, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00))
_ICONES = {
    "termometro": bytes((0x18, 0x24, 0x24, 0x24, 0x3C, 0x7E, 0x7E, 0x3C)),
    "gota": bytes((0x18, 0x18, 0x3C, 0x7E, 0x7E, 0x7E, 0x3C, 0x00)),
    "chuva": bytes((0x38, 0x7C, 0xFF, 0xFF, 0x00, 0x49, 0x92, 0x00)),
    "solo": bytes((0x28, 0x10, 0x38, 0x10, 0xFF, 0xAA, 0x55, 0xFF)),
    "fogo": bytes((0x10, 0x18, 0x3A, 0x3E, 0x6E, 0x46, 0x46, 0x3C)),
    "onda": bytes((0x00, 0x66, 0x99, 0x00, 0x66, 0x99, 0x00, 0x00)),
    "cadeado": bytes((0x3C, 0x42, 0x42, 0xFF, 0xE7, 0xE7, 0xFF, 0x00)),
    "aberto": bytes((0x3C, 0x42, 0x40, 0xFF, 0xE7, 0xE7, 0xFF, 0x00)),
    "wifi": bytes((0x3C, 0x42, 0x99, 0x24, 0x00, 0x18, 0x18, 0x00)),
    "mudo": bytes((0x10, 0x30, 0xE9, 0xE6, 0xE6, 0xE9, 0x30, 0x10)),
    "ventoinha": bytes((0x18, 0x99, 0x5A, 0x3C, 0x3C, 0x5A, 0x99, 0x18)),
}


class _Tela:
    ENDERECO = 0x3C

    # Cada comando desenha no framebuffer; show() só envia a imagem ao
    # display. Sem display (OSError no I2C), desenha à toa e segue.
    def __init__(self, sda=21, scl=22):
        self._sda = sda
        self._scl = scl
        self._pronta = None
        self._buffer = bytearray(1024)
        self._fb = _framebuf.FrameBuffer(self._buffer, 128, 64, _framebuf.MONO_VLSB)
        self._imagens = {}

    def _iniciar(self):
        if self._pronta is None:
            try:
                self._i2c = _machine.I2C(0, sda=_machine.Pin(self._sda),
                                         scl=_machine.Pin(self._scl), freq=400000)
                for c in _SSD1306_INICIO:
                    self._comando(c)
                self._pronta = True
            except OSError:
                self._pronta = False
                print("[oled] display nao encontrado, seguindo sem tela")
        return self._pronta

    def _comando(self, c):
        self._i2c.writeto(self.ENDERECO, bytearray((0x80, c)))

    def clear(self):
        self._fb.fill(0)

    # linha de texto 0..7, como antes: apaga só a faixa da linha
    def write(self, linha, texto):
        self._fb.fill_rect(0, int(linha) * 8, 128, 8, 0)
        self._fb.text(str(texto)[:16], 0, int(linha) * 8, 1)

    def text(self, texto, x, y, cor=1):
        self._fb.text(str(texto), int(x), int(y), 1 if cor else 0)

    def center(self, texto, y, cor=1):
        texto = str(texto)[:16]
        self.text(texto, (128 - 8 * len(texto)) // 2, y, cor)

    def rect(self, x, y, largura, altura, cheio=False):
        desenhar = self._fb.fill_rect if cheio else self._fb.rect
        desenhar(int(x), int(y), int(largura), int(altura), 1)

    def bar(self, x, y, largura, altura, valor, maximo):
        x, y, largura, altura = int(x), int(y), int(largura), int(altura)
        self._fb.rect(x, y, largura, altura, 1)
        cheio = int((largura - 2) * min(max(valor, 0), maximo) / maximo) if maximo > 0 else 0
        self._fb.fill_rect(x + 1, y + 1, cheio, altura - 2, 1)

    def _imagem(self, nome, dados, largura, altura):
        img = self._imagens.get(nome)
        if img is None:
            img = _framebuf.FrameBuffer(bytearray(dados), largura, altura, _framebuf.MONO_HLSB)
            self._imagens[nome] = img
        return img

    def icon(self, nome, x, y):
        dados = _ICONES.get(nome)
        if dados is not None:
            self._fb.blit(self._imagem(nome, dados, 8, 8), int(x), int(y))

    def logo(self, x, y):
        self._fb.blit(self._imagem("logo", _LOGO, 32, 32), int(x), int(y))

    def show(self):
        if not self._iniciar():
            return
        try:
            for c in (0x21, 0, 127, 0x22, 0, 7):
                self._comando(c)
            self._i2c.writevto(self.ENDERECO, (bytes((0x40,)), self._buffer))
        except OSError:
            pass


class _Relogio:
    def ms(self):
        return _time.ticks_ms()

    # ticks_ms volta a zero depois de alguns dias: ticks_diff trata isso
    def since(self, marca):
        return _time.ticks_diff(_time.ticks_ms(), marca)

    def sleep(self, segundos):
        _time.sleep(segundos)


class _Wifi:
    def __init__(self):
        self._wlan = None

    def connect(self, ssid, senha, limite_ms=10000):
        try:
            import network
            self._wlan = network.WLAN(network.STA_IF)
            self._wlan.active(True)
            if not self._wlan.isconnected():
                self._wlan.connect(ssid, senha)
                inicio = _time.ticks_ms()
                while (not self._wlan.isconnected()
                       and _time.ticks_diff(_time.ticks_ms(), inicio) < limite_ms):
                    _time.sleep_ms(100)
            return self._wlan.isconnected()
        except Exception as erro:
            print("[wifi] falhou:", erro)
            return False

    def connected(self):
        return self._wlan is not None and self._wlan.isconnected()

    def ip(self):
        if not self.connected():
            return ""
        try:
            return self._wlan.ipconfig("addr4")[0]
        except Exception:
            return self._wlan.ifconfig()[0]


class _Mqtt:
    def __init__(self):
        self._cliente = None

    def connect(self, broker, porta=1883):
        try:
            from umqtt.simple import MQTTClient
            import binascii
            ident = b"aegis-" + binascii.hexlify(_machine.unique_id())
            self._cliente = MQTTClient(ident, broker, port=porta, keepalive=60)
            self._cliente.connect()
            return True
        except Exception as erro:
            self._cliente = None
            print("[mqtt] sem conexao:", erro)
            return False

    def connected(self):
        return self._cliente is not None

    def publish(self, topico, mensagem):
        if self._cliente is None:
            return False
        try:
            self._cliente.publish(str(topico), str(mensagem))
            return True
        except Exception as erro:
            self._cliente = None
            print("[mqtt] conexao perdida:", erro)
            return False


class _Digital:
    # Leitor biométrico AS608 na UART2, pelo protocolo do fabricante: pacote
    # EF 01, endereço FF FF FF FF, tipo (1 = comando), tamanho, dados e soma
    # de 16 bits. Sem o leitor (no Wokwi, por exemplo), as digitais chegam
    # pela serial como linhas "dedo <n>": o Touch ID do Mac (wokwi.sh dedo)
    # ou digitadas no terminal. scan() devolve o número da digital, -1 sem
    # dedo e -2 para digital desconhecida.
    def __init__(self):
        self._uart = None
        self._presente = False
        self._soltar = False
        self._poll = None
        self._linha = ""

    def begin(self, rx, tx):
        try:
            self._uart = _machine.UART(2, baudrate=57600, rx=rx, tx=tx, timeout=300)
            self._presente = self._comando(bytes((0x13, 0, 0, 0, 0)))[0] == 0   # VfyPwd
        except Exception:
            self._presente = False
        if not self._presente:
            import sys, select
            self._poll = select.poll()
            self._poll.register(sys.stdin, select.POLLIN)
            print("[digital] leitor AS608 ausente: aceitando 'dedo <n>' pela serial")
        return self._presente

    def present(self):
        return self._presente

    # envia um comando e devolve os dados da resposta; o primeiro byte é o
    # código de confirmação (0 = ok). Sem resposta válida devolve (0xFF,).
    def _comando(self, dados):
        tamanho = len(dados) + 2
        corpo = bytes((1, tamanho >> 8, tamanho & 0xFF)) + dados
        soma = sum(corpo) & 0xFFFF
        self._uart.read()
        self._uart.write(bytes((0xEF, 0x01, 0xFF, 0xFF, 0xFF, 0xFF)) + corpo + bytes((soma >> 8, soma & 0xFF)))
        cabecalho = self._uart.read(9)
        if not cabecalho or len(cabecalho) < 9 or cabecalho[0] != 0xEF or cabecalho[1] != 0x01:
            return (0xFF,)
        n = (cabecalho[7] << 8) | cabecalho[8]
        resto = self._uart.read(n)
        if not resto or len(resto) < n or n < 3:
            return (0xFF,)
        if (sum(cabecalho[6:9]) + sum(resto[:-2])) & 0xFFFF != (resto[-2] << 8) | resto[-1]:
            return (0xFF,)
        return resto[:-2]

    def _tem_dedo(self):
        return self._comando(bytes((0x01,)))[0] == 0           # GenImg; 0x02 = sem dedo

    def scan(self):
        if not self._presente:
            return self._da_serial()
        dedo = self._tem_dedo()
        if self._soltar:                                       # mesma encostada: ignora
            self._soltar = dedo
            return -1
        if not dedo:
            return -1
        self._soltar = True
        if self._comando(bytes((0x02, 1)))[0] != 0:            # Img2Tz no buffer 1
            return -2
        r = self._comando(bytes((0x04, 1, 0, 0, 0, 200)))     # Search nas posições 0..199
        if r[0] != 0:
            return -2
        return (r[1] << 8) | r[2]

    def _da_serial(self):
        import sys
        while self._poll is not None and self._poll.poll(0):
            c = sys.stdin.read(1)
            if ord(c) not in (10, 13):                            # fim de linha
                self._linha += c
                continue
            linha, self._linha = self._linha.strip(), ""
            if linha.startswith("dedo "):
                try:
                    return int(linha[5:])
                except ValueError:
                    pass
        return -1

    def _esperar(self, com_dedo, limite_ms):
        inicio = _time.ticks_ms()
        while _time.ticks_diff(_time.ticks_ms(), inicio) < limite_ms:
            if self._tem_dedo() == com_dedo:
                return True
            _time.sleep_ms(100)
        return False

    # cadastro: duas leituras do mesmo dedo viram um modelo guardado na
    # posição "numero" da memória do leitor
    def enroll(self, numero, limite_ms=15000):
        if not self._presente:
            return False
        for buffer in (1, 2):
            print("[digital] encoste o dedo" if buffer == 1 else "[digital] encoste o mesmo dedo de novo")
            if not self._esperar(True, limite_ms):
                return False
            if self._comando(bytes((0x02, buffer)))[0] != 0:   # Img2Tz
                return False
            print("[digital] retire o dedo")
            self._esperar(False, limite_ms)
        if self._comando(bytes((0x05,)))[0] != 0:             # RegModel: as leituras não batem
            return False
        return self._comando(bytes((0x06, 1, numero >> 8, numero & 0xFF)))[0] == 0   # Store


class _Config:
    # ajustes desta placa (rede, token do bot) num config.json gravado ao
    # lado do main.py e fora do Git; sem o arquivo, valem os padrões
    def __init__(self, arquivo):
        self._arquivo = arquivo
        self._dados = None

    def get(self, chave, padrao):
        if self._dados is None:
            self._dados = {}
            try:
                import json
                with open(self._arquivo) as f:
                    self._dados = json.load(f)
                print("[config] ajustes lidos de", self._arquivo)
            except OSError:
                pass
            except ValueError:
                print("[config]", self._arquivo, "tem JSON invalido: usando os padroes")
        return self._dados.get(chave, padrao)


_PAINEL_HTML = "<!doctype html>\n<html lang=\"pt-BR\"><head><meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n<title>AEGIS - Abrigo</title>\n<style>\n:root{--fundo:#0A0D0A;--cartao:#131813;--linha:#2A322A;--caqui:#C8B88A;--radar:#A8D04A;--creme:#EDE4CC;--ambar:#E8A33C;--alerta:#E5533D;--apagado:#7D8574}\n*{box-sizing:border-box;margin:0}\nbody{background:var(--fundo);color:var(--creme);font:15px/1.4 system-ui,-apple-system,\"Segoe UI\",Roboto,sans-serif;padding:16px;max-width:760px;margin:0 auto}\nheader{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}\nh1{font:30px Impact,\"Arial Narrow\",sans-serif;letter-spacing:4px;color:var(--caqui)}\n.sub{color:var(--apagado);font-size:11px;letter-spacing:1px;text-transform:uppercase}\n#con{font-size:12px;color:var(--apagado);white-space:nowrap}\n#con:before{content:\"\";display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--alerta);margin-right:6px}\n#con.on:before{background:var(--radar)}\n#estado{border-radius:12px;padding:18px;margin-bottom:12px;border:1px solid var(--linha);background:var(--cartao)}\n#nome{display:block;font:38px Impact,\"Arial Narrow\",sans-serif;letter-spacing:3px;color:var(--radar)}\n#motivo{font-size:18px}\n#estado.s1{border-color:var(--ambar)}#estado.s1 #nome{color:var(--ambar)}\n#estado.s2{border-color:var(--alerta);animation:pisca 1s steps(2) infinite}#estado.s2 #nome{color:var(--alerta)}\n@keyframes pisca{50%{background:#3A1410}}\n.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}\n.c{background:var(--cartao);border:1px solid var(--linha);border-radius:12px;padding:12px}\n.c small{color:var(--apagado);font-size:11px;text-transform:uppercase;letter-spacing:1px}\n.c div{font-size:24px;font-weight:600;margin-top:2px;font-variant-numeric:tabular-nums}\n.barra{height:6px;background:var(--linha);border-radius:3px;margin-top:8px;overflow:hidden}\n.barra i{display:block;height:100%;width:0;background:var(--radar)}\n.barra i.alto{background:var(--alerta)}\n.tags{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}\n.tag{border:1px solid var(--linha);border-radius:999px;padding:4px 12px;font-size:13px;color:var(--apagado)}\n.tag.on{color:var(--fundo);background:var(--caqui);border-color:var(--caqui)}\n.tag.alerta{color:#fff;background:var(--alerta);border-color:var(--alerta)}\nbutton{width:100%;padding:15px;border-radius:12px;border:0;background:var(--alerta);color:#fff;font:600 16px system-ui,sans-serif;cursor:pointer}\nbutton:disabled{background:var(--linha);color:var(--apagado);cursor:default}\nfooter{margin-top:14px;color:var(--apagado);font-size:12px;text-align:center}\n</style></head><body>\n<header><div><h1>AEGIS</h1><div class=\"sub\">painel do abrigo &middot; rede local</div></div><span id=\"con\">conectando</span></header>\n<section id=\"estado\"><span id=\"nome\">...</span><span id=\"motivo\">aguardando o abrigo</span></section>\n<div class=\"grade\">\n<div class=\"c\"><small>Temperatura</small><div id=\"temp\">--</div></div>\n<div class=\"c\"><small>Umidade do ar</small><div id=\"umid\">--</div></div>\n<div class=\"c\"><small>Fuma&ccedil;a / g&aacute;s</small><div id=\"fumaca\">--</div><div class=\"barra\"><i id=\"b_fumaca\"></i></div></div>\n<div class=\"c\"><small>Qualidade do ar</small><div id=\"ar\">--</div><div class=\"barra\"><i id=\"b_ar\"></i></div></div>\n<div class=\"c\"><small>N&iacute;vel da &aacute;gua</small><div id=\"agua\">--</div></div>\n<div class=\"c\"><small>Chuva</small><div id=\"chuva\">--</div><div class=\"barra\"><i id=\"b_chuva\"></i></div></div>\n<div class=\"c\"><small>Solo</small><div id=\"solo\">--</div><div class=\"barra\"><i id=\"b_solo\"></i></div></div>\n<div class=\"c\"><small>Presen&ccedil;a</small><div id=\"pir\">--</div></div>\n</div>\n<div class=\"tags\" id=\"tags\"></div>\n<button id=\"mudo\" disabled>Silenciar sirene</button>\n<footer id=\"rodape\">&nbsp;</footer>\n<script>\nfunction el(i){return document.getElementById(i)}\nfunction barra(id,v,lim){var p=lim>0?Math.max(0,Math.min(100,100*v/lim)):0;var e=el(id);e.style.width=p+\"%\";e.className=p>=100?\"alto\":\"\"}\nfunction tag(t,c){return '<span class=\"tag '+c+'\">'+t+'</span>'}\nfunction duracao(s){var h=Math.floor(s/3600),m=Math.floor(s%3600/60);return h?h+\" h \"+m+\" min\":m?m+\" min\":s+\" s\"}\nvar visto=0,ligado=0;\nfunction mostrar(d){\nvisto=Date.now();ligado=d.ligado_s;\nel(\"con\").className=\"on\";el(\"con\").textContent=\"ao vivo\";\nel(\"estado\").className=\"s\"+d.estado;el(\"nome\").textContent=[\"NORMAL\",\"ATENÇÃO\",\"ALARME\"][d.estado]||d.nome;el(\"motivo\").textContent=d.motivo;\nel(\"temp\").innerHTML=d.temp<0?\"--\":d.temp.toFixed(1)+\" &deg;C\";\nel(\"umid\").textContent=d.umid<0?\"--\":Math.round(d.umid)+\" %\";\nel(\"fumaca\").textContent=d.aquecido?Math.round(100*Math.max(0,d.fumaca)/d.fumaca_lim)+\" %\":\"aquecendo\";\nel(\"ar\").textContent=d.aquecido?Math.round(100*Math.max(0,d.ar)/d.ar_lim)+\" %\":\"aquecendo\";\nbarra(\"b_fumaca\",d.fumaca,d.fumaca_lim);barra(\"b_ar\",d.ar,d.ar_lim);\nel(\"agua\").textContent=d.agua_cm<0?\"sem eco\":Math.round(d.agua_cm)+\" cm\";\nel(\"chuva\").textContent=d.chuva+\" %\";el(\"solo\").textContent=d.solo+\" %\";\nbarra(\"b_chuva\",d.chuva,100);barra(\"b_solo\",d.solo,100);\nel(\"pir\").textContent=d.pir?\"movimento\":\"livre\";\nvar t=tag(d.armado?\"armado\":\"desarmado\",d.armado?\"on\":\"\");\nif(d.entrada)t+=tag(\"entrada: use a digital\",\"alerta\");\nif(d.rele)t+=tag(\"exaustor ligado\",\"on\");\nif(d.mudo)t+=tag(\"sirene silenciada\",\"on\");\nt+=tag(\"Telegram\",d.bot?\"on\":\"\")+tag(\"MQTT\",d.mqtt?\"on\":\"\");\nel(\"tags\").innerHTML=t;\nvar b=el(\"mudo\");b.disabled=!(d.estado==2&&!d.mudo);b.textContent=d.mudo?\"Sirene silenciada\":\"Silenciar sirene\";\n}\nfunction atualizar(){fetch(\"/dados\",{cache:\"no-store\"}).then(function(r){return r.json()}).then(mostrar).catch(function(){el(\"con\").className=\"\";el(\"con\").textContent=\"sem contato\"})}\nel(\"mudo\").onclick=function(){this.disabled=true;fetch(\"/silenciar\",{method:\"POST\"}).then(atualizar)};\nsetInterval(atualizar,2000);atualizar();\nsetInterval(function(){if(visto)el(\"rodape\").textContent=\"abrigo ligado há \"+duracao(ligado)+\" · atualizado há \"+Math.round((Date.now()-visto)/1000)+\" s\"},1000);\n</script></body></html>"


class _Painel:
    # Servidor HTTP mínimo e não bloqueante, para o painel na rede local.
    # waiting() aceita no máximo um pedido por ciclo, para não atrasar os
    # sensores: GET / devolve a página, POST /silenciar vira o comando
    # "/silenciar" (lido por command()) e GET /dados fica esperando o
    # programa responder com serve(), que recebe as leituras em JSON.
    def __init__(self):
        self._servidor = None
        self._cliente = None
        self._porta = 80
        self.fila = []

    def _porta_real(self, porta):
        return porta

    def start(self, porta=80):
        try:
            import socket
            self._porta = self._porta_real(int(porta))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", self._porta))
            s.listen(2)
            s.setblocking(False)
            self._servidor = s
            return True
        except Exception as erro:
            print("[painel] nao abriu:", erro)
            return False

    def url(self, ip):
        return "http://" + str(ip) + ("/" if self._porta == 80 else ":" + str(self._porta) + "/")

    def waiting(self):
        if self._cliente is not None:
            return True
        if self._servidor is None:
            return False
        try:
            cliente, _ = self._servidor.accept()
        except OSError:
            return False
        try:
            cliente.settimeout(1)
            pedido = cliente.recv(1024).split(b"\r\n", 1)[0].decode().split(" ")
        except Exception:
            cliente.close()
            return False
        metodo = pedido[0]
        caminho = pedido[1] if len(pedido) > 1 else "/"
        if caminho.startswith("/dados"):
            self._cliente = cliente
            return True
        if caminho.startswith("/silenciar") and metodo == "POST":
            self.fila.append("/silenciar")
            self._responder(cliente, "200 OK", "application/json", '{"ok":true}')
        elif caminho == "/" or caminho.startswith("/?"):
            self._responder(cliente, "200 OK", "text/html; charset=utf-8", _PAINEL_HTML)
        else:
            self._responder(cliente, "404 Not Found", "text/plain", "nao encontrado")
        return False

    def serve(self, dados):
        cliente, self._cliente = self._cliente, None
        if cliente is not None:
            self._responder(cliente, "200 OK", "application/json", dados)

    def command(self):
        return self.fila.pop(0) if self.fila else ""

    def _responder(self, cliente, situacao, tipo, corpo):
        corpo = str(corpo).encode()
        cabecalho = ("HTTP/1.1 " + situacao + "\r\nContent-Type: " + tipo +
                     "\r\nContent-Length: " + str(len(corpo)) +
                     "\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n")
        try:
            enviar = getattr(cliente, "sendall", None) or cliente.write
            enviar(cabecalho.encode() + corpo)
        except Exception:
            pass
        cliente.close()


class _TelegramBase:
    # Bot do Telegram pela API HTTPS. send() manda uma mensagem ao chat
    # configurado; command() devolve o próximo comando ("/status", ...) que
    # chegou desse chat, consultando a API no máximo a cada intervalo_ms
    # (no ESP32 cada consulta segura o laço por 1 a 2 s). Mensagens de outros
    # chats são ignoradas: só o dono do abrigo manda no bot.
    #
    # Comandos mandados antes de o abrigo ligar não são atendidos. O primeiro
    # envio que dá certo traz a data do servidor; descontando o tempo desde o
    # begin(), ela vira a hora do boot no relógio do Telegram (_desde), e só
    # as mensagens com data anterior a ela são descartadas. Uma consulta que
    # falha (comum no Wokwi) não engole mais o primeiro comando do dono.
    def __init__(self):
        self.fila = []
        self._token = ""
        self._chat = ""
        self._offset = -1      # -1: ainda não varreu o que chegou antes de ligar
        self._ultima = None
        self._ligou = None     # _ms() do begin()
        self._desde = None     # hora do boot em segundos Unix, pelo relógio do Telegram

    def begin(self, token, chat):
        self._token = str(token or "")
        self._chat = str(chat or "")
        self._offset = -1
        self._ultima = None
        self._ligou = self._ms()
        self._desde = None
        if self._token and not self._chat:
            print("[telegram] falta o telegram_chat no config.json: rode firmware/telegram_chat.py")
        return self._ativo()

    def _ativo(self):
        return self._token != "" and self._chat != ""

    def _url(self, metodo):
        return "https://api.telegram.org/bot" + self._token + "/" + metodo

    def send(self, texto):
        if not self._ativo():
            return False
        resposta = self._pedir("sendMessage", {"chat_id": self._chat, "text": str(texto)})
        ok = resposta is not None and resposta.get("ok", False)
        if ok and self._desde is None:
            data = (resposta.get("result") or {}).get("date")
            if data:
                self._desde = data - self._diff(self._ms(), self._ligou) // 1000
        return ok

    def command(self, intervalo_ms=15000):
        if not self.fila and self._ativo():
            agora = self._ms()
            if self._ultima is None or self._diff(agora, self._ultima) >= intervalo_ms:
                self._ultima = agora
                self._consultar()
        return self.fila.pop(0) if self.fila else ""

    def _consultar(self):
        # com a hora do boot conhecida, busca tudo o que está pendente e filtra
        # pela data; sem ela, a primeira consulta descarta o que estava pendente
        if self._offset == -1 and self._desde is not None:
            self._offset = 0
        resposta = self._pedir("getUpdates", {"offset": self._offset, "timeout": 0, "limit": 10})
        if not resposta or not resposta.get("ok"):
            return
        primeira = self._offset == -1
        self._offset = max(self._offset, 0)
        for u in resposta.get("result", []):
            self._offset = u["update_id"] + 1
            m = u.get("message") or {}
            texto = m.get("text") or ""
            antiga = primeira or (self._desde is not None and m.get("date", 0) < self._desde)
            if antiga or str(m.get("chat", {}).get("id")) != self._chat or not texto.startswith("/"):
                continue
            self.fila.append(texto.split()[0].split("@")[0].lower())


class _Telegram(_TelegramBase):
    # O requests do MicroPython faz o HTTPS; o TLS precisa de uns 40 KB de
    # memória livre, por isso o gc.collect() antes de cada pedido. Sem
    # timeout, um pedido sem resposta prendia o laço para sempre (sensores,
    # sirene e painel juntos); com ele, o pedido desiste e tenta de novo na
    # próxima consulta. Cada pedido leva 1 a 2 s na placa e ~5 s no Wokwi.
    def _ms(self):
        return _time.ticks_ms()

    def _diff(self, a, b):
        return _time.ticks_diff(a, b)

    def _pedir(self, metodo, dados):
        import gc
        gc.collect()
        try:
            import requests
            r = requests.post(self._url(metodo), json=dados, timeout=10)
            try:
                return r.json()
            finally:
                r.close()
        except Exception as erro:
            print("[telegram] falhou:", erro)
            return None


gpio = _Gpio()
adc = _Adc()
pwm = _Pwm()
sonar = _Sonar()
climate = _Clima()
display = _Tela()
wifi = _Wifi()
mqtt = _Mqtt()
time = _Relogio()
finger = _Digital()
config = _Config("config.json")
web = _Painel()
telegram = _Telegram()


def radio(pino):
    return pino


def ration(valor):
    return int(valor)


def vital(valor):
    return float(valor)


def paper(valor):
    return str(valor)


def status(valor):
    return bool(valor)


def log_entry(*args):
    print(*args)


def hide(ms):
    _time.sleep_ms(int(ms))


def broadcast(pino):
    gpio.write(pino, True)


def silence(pino):
    gpio.write(pino, False)
# --- fim do runtime ---


# scavenge gpio — módulo fornecido pelo runtime
# scavenge adc — módulo fornecido pelo runtime
# scavenge sonar — módulo fornecido pelo runtime
# scavenge climate — módulo fornecido pelo runtime
# scavenge display — módulo fornecido pelo runtime
# scavenge pwm — módulo fornecido pelo runtime
# scavenge wifi — módulo fornecido pelo runtime
# scavenge mqtt — módulo fornecido pelo runtime
# scavenge time — módulo fornecido pelo runtime
# scavenge finger — módulo fornecido pelo runtime
# scavenge config — módulo fornecido pelo runtime
# scavenge web — módulo fornecido pelo runtime
# scavenge telegram — módulo fornecido pelo runtime
PINO_PIR = 27  # constante
PINO_TRIG = 25  # constante
PINO_ECHO = 26  # constante
PINO_DHT = 4  # constante
PINO_MQ2 = 34  # constante
PINO_MQ135 = 35  # constante
PINO_BOTAO = 14  # constante
PINO_BUZZER = 18  # constante
LED_VERDE = 13  # constante
LED_AMARELO = 33  # constante
LED_VERMELHO = 32  # constante
PINO_CHUVA = 36  # constante
PINO_SOLO = 39  # constante
PINO_RELE = 23  # constante
PINO_DIGITAL_RX = 16  # constante
PINO_DIGITAL_TX = 17  # constante
MARGEM_FUMACA = 800  # constante
HISTERESE_FUMACA = 300  # constante
MARGEM_AR = 800  # constante
HISTERESE_AR = 300  # constante
FILTRO_MQ = 4  # constante
ADAPTA_BASE = 64  # constante
LIMITE_AGUA_CM = 20.0  # constante
TEMP_ATENCAO = 40.0  # constante
TEMP_ALARME = 55.0  # constante
CHUVA_SECO = 4095  # constante
CHUVA_MOLHADO = 1000  # constante
SOLO_SECO = 2900  # constante
SOLO_MOLHADO = 1100  # constante
CHUVA_ATENCAO = 30  # constante
SOLO_ATENCAO = 70  # constante
SOLO_ALARME = 85  # constante
HISTERESE_PCT = 10  # constante
RELE_ATIVO_EM_ALTO = True  # constante
RELE_EXTRA_MS = 30000  # constante
ATRASO_SAIDA_MS = 30000  # constante
ATRASO_ENTRADA_MS = 15000  # constante
AQUECIMENTO_MS = 20000  # constante
SILENCIO_MS = 60000  # constante
CICLO_MS = 500  # constante
TELEMETRIA_MS = 10000  # constante
DEPURAR = True  # constante
DEPURAR_MS = 2000  # constante
PAGINA_MS = 3000  # constante
USAR_REDE = True  # constante
WIFI_SSID = "Wokwi-GUEST"  # constante
WIFI_SENHA = ""  # constante
MQTT_BROKER = "broker.hivemq.com"  # constante
TELEGRAM_CONSULTA_MS = 15000  # constante
PORTA_PAINEL = 80  # constante
usar_rede = config.get("usar_rede", USAR_REDE)
wifi_ssid = config.get("wifi_ssid", WIFI_SSID)
wifi_senha = config.get("wifi_senha", WIFI_SENHA)
aquecimento_ms = config.get("aquecimento_ms", AQUECIMENTO_MS)
telegram_token = config.get("telegram_token", "")
telegram_chat = config.get("telegram_chat", "")
NORMAL = 0  # constante
ATENCAO = 1  # constante
ALARME = 2  # constante
NOMES_ESTADO = ["NORMAL", "ATENCAO", "ALARME"]
EMOJI_ESTADO = ["✅", "⚠️", "🚨"]
inicio = 0
aquecido = False
amostras = 0
filtro_pronto = False
media_fumaca = 0
media_ar = 0
base_fumaca = 0
base_ar = 0
base_registrada = False
leitura_fumaca = 0
leitura_ar = 0
distancia_agua = 0.0
temperatura = 0.0
umidade = 0.0
presenca = False
leitura_chuva = 0
media_chuva = 0
chuva_pct = 0
leitura_solo = 0
media_solo = 0
solo_pct = 0
chovendo = False
solo_encharcado = False
deslizamento = False
rele_ligado = False
houve_fumaca = False
ultima_fumaca = 0
digital = -1
armado = False
armado_em = 0
em_entrada = False
entrada_em = 0
intruso = False
risco_fumaca = 0
risco_ar = 0
risco_agua = 0
risco_calor = 0
risco_presenca = 0
estado = 0
estado_anterior = -1
motivo = "tudo em ordem"
motivo_anterior = ""
silenciado = False
silencio_desde = 0
sirene_alta = False
rede = False
mqtt_ok = False
painel = False
ip = ""
bot = False
ultima_telemetria = 0
ultima_depuracao = 0
pagina = 0
pagina_desde = 0
# survivor: roda como tarefa concorrente no alvo
def sentinela_fumaca():
    global leitura_fumaca, media_fumaca, base_fumaca, risco_fumaca
    leitura_fumaca = adc.read(radio(PINO_MQ2))
    if filtro_pronto:
        media_fumaca = media_fumaca + ration((leitura_fumaca - media_fumaca) / FILTRO_MQ)
    else:
        media_fumaca = leitura_fumaca
    if not aquecido:
        base_fumaca = media_fumaca
        risco_fumaca = NORMAL
    elif media_fumaca >= base_fumaca + MARGEM_FUMACA:
        risco_fumaca = ALARME
    elif media_fumaca < base_fumaca + MARGEM_FUMACA - HISTERESE_FUMACA:
        risco_fumaca = NORMAL
    if aquecido and risco_fumaca == NORMAL:
        base_fumaca = base_fumaca + ration((media_fumaca - base_fumaca) / ADAPTA_BASE)

# survivor: roda como tarefa concorrente no alvo
def sentinela_ar():
    global leitura_ar, media_ar, base_ar, risco_ar
    leitura_ar = adc.read(radio(PINO_MQ135))
    if filtro_pronto:
        media_ar = media_ar + ration((leitura_ar - media_ar) / FILTRO_MQ)
    else:
        media_ar = leitura_ar
    if not aquecido:
        base_ar = media_ar
        risco_ar = NORMAL
    elif media_ar >= base_ar + MARGEM_AR:
        risco_ar = ATENCAO
    elif media_ar < base_ar + MARGEM_AR - HISTERESE_AR:
        risco_ar = NORMAL
    if aquecido and risco_ar == NORMAL:
        base_ar = base_ar + ration((media_ar - base_ar) / ADAPTA_BASE)

# survivor: roda como tarefa concorrente no alvo
def sentinela_agua():
    global distancia_agua, risco_agua
    distancia_agua = sonar.distance(radio(PINO_TRIG), radio(PINO_ECHO))
    risco_agua = NORMAL
    if distancia_agua > 0.0 and distancia_agua < LIMITE_AGUA_CM:
        risco_agua = ALARME

# survivor: roda como tarefa concorrente no alvo
def sentinela_calor():
    global temperatura, umidade, risco_calor
    temperatura = climate.temperature(radio(PINO_DHT))
    umidade = climate.humidity(radio(PINO_DHT))
    risco_calor = NORMAL
    if temperatura >= TEMP_ALARME:
        risco_calor = ALARME
    elif temperatura >= TEMP_ATENCAO:
        risco_calor = ATENCAO

def bipar(vezes):
    for _ in range(vezes):
        pwm.tone(radio(PINO_BUZZER), 3000)
        hide(80)
        pwm.off(radio(PINO_BUZZER))
        hide(80)

# survivor: roda como tarefa concorrente no alvo
def vigia_digital():
    global digital, armado, em_entrada, intruso, armado_em
    digital = finger.scan()
    if digital >= 0:
        armado = not armado
        em_entrada = False
        intruso = False
        if armado:
            armado_em = time.ms()
            log_entry("[AEGIS] armado pela digital", digital, "- saia em", ATRASO_SAIDA_MS / 1000, "s")
        else:
            log_entry("[AEGIS] desarmado pela digital", digital)
        bipar(1)
        if armado:
            avisar("🔒 Abrigo armado pela digital " + paper(digital) + ". Saia em " + paper(ration(ATRASO_SAIDA_MS / 1000)) + " s.")
        else:
            avisar("🔓 Abrigo desarmado pela digital " + paper(digital) + ".")
    elif digital == -2:
        log_entry("[AEGIS] digital nao reconhecida")
        bipar(3)
        avisar("❓ Alguém tentou uma digital não cadastrada.")

# survivor: roda como tarefa concorrente no alvo
def sentinela_presenca():
    global presenca, em_entrada, entrada_em, intruso, risco_presenca
    presenca = gpio.read(radio(PINO_PIR))
    if armado and presenca and not em_entrada and not intruso and time.since(armado_em) >= ATRASO_SAIDA_MS:
        em_entrada = True
        entrada_em = time.ms()
    if em_entrada and time.since(entrada_em) >= ATRASO_ENTRADA_MS:
        em_entrada = False
        intruso = True
    risco_presenca = NORMAL
    if em_entrada:
        risco_presenca = ATENCAO
    elif intruso:
        risco_presenca = ALARME

def percentual_molhado(leitura, seco, molhado):
    pct = ration((seco - leitura) * 100 / (seco - molhado))
    if pct < 0:
        pct = 0
    if pct > 100:
        pct = 100
    return pct

# survivor: roda como tarefa concorrente no alvo
def sentinela_chuva():
    global leitura_chuva, media_chuva, chuva_pct, chovendo
    leitura_chuva = adc.read(radio(PINO_CHUVA))
    if filtro_pronto:
        media_chuva = media_chuva + ration((leitura_chuva - media_chuva) / FILTRO_MQ)
    else:
        media_chuva = leitura_chuva
    chuva_pct = percentual_molhado(media_chuva, CHUVA_SECO, CHUVA_MOLHADO)
    if chuva_pct >= CHUVA_ATENCAO:
        chovendo = True
    elif chuva_pct < CHUVA_ATENCAO - HISTERESE_PCT:
        chovendo = False

# survivor: roda como tarefa concorrente no alvo
def sentinela_solo():
    global leitura_solo, media_solo, solo_pct, solo_encharcado, deslizamento
    leitura_solo = adc.read(radio(PINO_SOLO))
    if filtro_pronto:
        media_solo = media_solo + ration((leitura_solo - media_solo) / FILTRO_MQ)
    else:
        media_solo = leitura_solo
    solo_pct = percentual_molhado(media_solo, SOLO_SECO, SOLO_MOLHADO)
    if solo_pct >= SOLO_ATENCAO:
        solo_encharcado = True
    elif solo_pct < SOLO_ATENCAO - HISTERESE_PCT:
        solo_encharcado = False
    if chovendo and solo_pct >= SOLO_ALARME:
        deslizamento = True
    elif solo_pct < SOLO_ALARME - HISTERESE_PCT:
        deslizamento = False

# survivor: roda como tarefa concorrente no alvo
def vigia_botao():
    global silenciado, silencio_desde
    if not silenciado and estado == ALARME and gpio.pressed(radio(PINO_BOTAO)):
        silenciado = True
        silencio_desde = time.ms()
        log_entry("[AEGIS] buzzer silenciado por", SILENCIO_MS / 1000, "s")
    if silenciado and time.since(silencio_desde) >= SILENCIO_MS:
        silenciado = False

def avisar(texto):
    if bot:
        telegram.send(texto)

def resumo():
    texto = EMOJI_ESTADO[estado] + " " + NOMES_ESTADO[estado] + ": " + motivo
    if temperatura < 0.0:
        texto = texto + "\n🌡 temperatura: sem leitura"
    else:
        texto = texto + "\n🌡 " + paper(temperatura) + " °C   💧 " + paper(ration(umidade)) + " %"
    texto = texto + "\n🌧 chuva " + paper(chuva_pct) + " %   🌱 solo " + paper(solo_pct) + " %"
    if aquecido:
        texto = (texto + "\n🔥 fumaça " + paper(media_fumaca - base_fumaca) + "/" + paper(MARGEM_FUMACA) + "   ar " + paper(media_ar - base_ar) + "/" + paper(MARGEM_AR))
    else:
        texto = texto + "\n🔥 sensores de gás aquecendo"
    if distancia_agua < 0.0:
        texto = texto + "\n🌊 água: sensor sem eco"
    else:
        texto = texto + "\n🌊 água a " + paper(ration(distancia_agua)) + " cm do sensor"
    if armado:
        texto = texto + "\n🔒 armado"
    else:
        texto = texto + "\n🔓 desarmado"
    if rele_ligado:
        texto = texto + " · exaustor ligado"
    if silenciado:
        texto = texto + " · sirene silenciada"
    if painel:
        texto = texto + "\nPainel: " + web.url(ip)
    return texto

def atender_comandos():
    global silenciado, silencio_desde
    origem = "painel"
    cmd = web.command()
    if cmd == "" and bot:
        origem = "Telegram"
        cmd = telegram.command(TELEGRAM_CONSULTA_MS)
    if cmd == "/silenciar":
        if estado == ALARME and not silenciado:
            silenciado = True
            silencio_desde = time.ms()
            log_entry("[AEGIS] buzzer silenciado pelo", origem)
            avisar("🔇 Sirene silenciada pelo " + origem + " por " + paper(ration(SILENCIO_MS / 1000)) + " s. O alarme continua: " + motivo)
        elif origem == "Telegram":
            avisar("Nada para silenciar: o abrigo está em " + NOMES_ESTADO[estado] + ".")
    elif cmd == "/status":
        avisar(resumo())
    elif cmd == "/start" or cmd == "/ajuda" or cmd == "/help":
        avisar("🛡 AEGIS - comandos:\n/status - leituras de agora\n/silenciar - cala a sirene por " + paper(ration(SILENCIO_MS / 1000)) + " s\n/ajuda - esta lista")
    elif cmd != "":
        avisar("Não conheço " + cmd + ". Mande /ajuda.")

def avaliar():
    global estado, motivo
    estado = NORMAL
    motivo = "tudo em ordem"
    if risco_presenca == ATENCAO:
        estado = ATENCAO
        motivo = "use a digital"
    if risco_ar == ATENCAO:
        estado = ATENCAO
        motivo = "ar ruim"
    if chovendo:
        estado = ATENCAO
        motivo = "chovendo"
    if solo_encharcado:
        estado = ATENCAO
        motivo = "solo encharcado"
    if risco_calor == ATENCAO:
        estado = ATENCAO
        motivo = "calor"
    if risco_calor == ALARME:
        estado = ALARME
        motivo = "TEMP ALTA"
    if risco_presenca == ALARME:
        estado = ALARME
        motivo = "INTRUSO"
    if risco_agua == ALARME:
        estado = ALARME
        motivo = "ENCHENTE"
    if deslizamento:
        estado = ALARME
        motivo = "DESLIZAMENTO"
    if risco_fumaca == ALARME:
        estado = ALARME
        motivo = "FUMACA/GAS"

def acender(pino, ligado):
    if ligado:
        broadcast(radio(pino))
    else:
        silence(radio(pino))

def sinalizar():
    global sirene_alta
    acender(LED_VERDE, estado == NORMAL)
    acender(LED_AMARELO, estado == ATENCAO)
    acender(LED_VERMELHO, estado == ALARME)
    if estado == ALARME and not silenciado:
        sirene_alta = not sirene_alta
        if sirene_alta:
            pwm.tone(radio(PINO_BUZZER), 2500)
        else:
            pwm.tone(radio(PINO_BUZZER), 1500)
    else:
        pwm.off(radio(PINO_BUZZER))

def acionar_rele():
    global houve_fumaca, ultima_fumaca, rele_ligado
    if risco_fumaca == ALARME:
        houve_fumaca = True
        ultima_fumaca = time.ms()
    ligar = houve_fumaca and time.since(ultima_fumaca) < RELE_EXTRA_MS
    if ligar != rele_ligado:
        rele_ligado = ligar
        gpio.write(radio(PINO_RELE), ligar == RELE_ATIVO_EM_ALTO)
        if ligar:
            log_entry("[AEGIS] exaustor ligado")
        else:
            log_entry("[AEGIS] exaustor desligado")

def relatar():
    global silenciado, estado_anterior, motivo_anterior
    if estado != estado_anterior or motivo != motivo_anterior:
        log_entry("[AEGIS] estado:", NOMES_ESTADO[estado], "-", motivo)
        if estado == NORMAL:
            silenciado = False
        if mqtt_ok:
            mqtt.publish("aegis/alerta", NOMES_ESTADO[estado] + ": " + motivo)
        if not (estado_anterior == -1 and estado == NORMAL):
            avisar(EMOJI_ESTADO[estado] + " " + NOMES_ESTADO[estado] + ": " + motivo)
        estado_anterior = estado
        motivo_anterior = motivo

def titulo():
    if estado == ALARME and sirene_alta:
        display.rect(0, 0, 128, 11, False)
        display.text("AEGIS", 2, 2, 1)
        display.text(NOMES_ESTADO[estado], 64, 2, 1)
    else:
        display.rect(0, 0, 128, 11, True)
        display.text("AEGIS", 2, 2, 0)
        display.text(NOMES_ESTADO[estado], 64, 2, 0)
    display.center(motivo, 14, 1)
    display.rect(0, 24, 128, 1, True)

def pagina_clima():
    display.icon("termometro", 0, 28)
    display.text(paper(temperatura) + "C", 10, 28, 1)
    display.icon("gota", 72, 28)
    display.text(paper(ration(umidade)) + "%", 82, 28, 1)
    display.icon("chuva", 0, 37)
    display.bar(10, 38, 80, 7, chuva_pct, 100)
    display.text(paper(chuva_pct) + "%", 92, 37, 1)
    display.icon("solo", 0, 46)
    display.bar(10, 47, 80, 7, solo_pct, 100)
    display.text(paper(solo_pct) + "%", 92, 46, 1)

def pagina_gases():
    display.icon("fogo", 0, 28)
    display.text("Fumaca", 10, 28, 1)
    display.bar(62, 29, 64, 7, media_fumaca - base_fumaca, MARGEM_FUMACA)
    display.text("Ar", 10, 37, 1)
    display.bar(62, 38, 64, 7, media_ar - base_ar, MARGEM_AR)
    if not aquecido:
        display.text("aquecendo MQ", 10, 46, 1)
    else:
        display.text("base " + paper(base_fumaca) + "/" + paper(base_ar), 10, 46, 1)

def pagina_agua():
    display.icon("onda", 0, 28)
    if distancia_agua < 0.0:
        display.text("agua: sem eco", 10, 28, 1)
    else:
        display.text("agua a " + paper(ration(distancia_agua)) + " cm", 10, 28, 1)
    display.text("alarme < " + paper(ration(LIMITE_AGUA_CM)) + " cm", 10, 37, 1)
    if presenca:
        display.text("PIR: movimento", 10, 46, 1)
    else:
        display.text("PIR: livre", 10, 46, 1)

def rodape():
    if armado:
        display.icon("cadeado", 0, 56)
    else:
        display.icon("aberto", 0, 56)
    if rede:
        display.icon("wifi", 12, 56)
    if silenciado:
        display.icon("mudo", 24, 56)
    if rele_ligado:
        display.icon("ventoinha", 36, 56)
    if armado and time.since(armado_em) < ATRASO_SAIDA_MS:
        display.text("saia " + paper(ration((ATRASO_SAIDA_MS - time.since(armado_em)) / 1000)) + "s", 38, 56, 1)
    elif em_entrada:
        display.text("digital!", 38, 56, 1)
    display.rect(112, 58, 4, 4, pagina == 0)
    display.rect(118, 58, 4, 4, pagina == 1)
    display.rect(124, 58, 4, 4, pagina == 2)

def atualizar_tela():
    global pagina_desde, pagina
    if time.since(pagina_desde) >= PAGINA_MS:
        pagina_desde = time.ms()
        pagina = pagina + 1
        if pagina > 2:
            pagina = 0
    display.clear()
    titulo()
    if pagina == 0:
        pagina_clima()
    elif pagina == 1:
        pagina_gases()
    else:
        pagina_agua()
    rodape()
    display.show()

def leituras_json():
    return ("{\"estado\":" + paper(estado) + ",\"nome\":\"" + NOMES_ESTADO[estado] + "\"" + ",\"motivo\":\"" + motivo + "\"" + ",\"temp\":" + paper(temperatura) + ",\"umid\":" + paper(umidade) + ",\"fumaca\":" + paper(media_fumaca - base_fumaca) + ",\"fumaca_lim\":" + paper(MARGEM_FUMACA) + ",\"ar\":" + paper(media_ar - base_ar) + ",\"ar_lim\":" + paper(MARGEM_AR) + ",\"agua_cm\":" + paper(distancia_agua) + ",\"chuva\":" + paper(chuva_pct) + ",\"solo\":" + paper(solo_pct) + ",\"pir\":" + paper(ration(presenca)) + ",\"armado\":" + paper(ration(armado)) + ",\"entrada\":" + paper(ration(em_entrada)) + ",\"rele\":" + paper(ration(rele_ligado)) + ",\"mudo\":" + paper(ration(silenciado)) + ",\"aquecido\":" + paper(ration(aquecido)) + ",\"mqtt\":" + paper(ration(mqtt_ok)) + ",\"bot\":" + paper(ration(bot)) + ",\"ligado_s\":" + paper(ration(time.since(inicio) / 1000)) + "}")

def servir_painel():
    if painel and web.waiting():
        web.serve(leituras_json())

def telemetria():
    global mqtt_ok, ultima_telemetria
    mqtt_ok = mqtt.connected()
    if mqtt_ok and time.since(ultima_telemetria) >= TELEMETRIA_MS:
        ultima_telemetria = time.ms()
        mqtt.publish("aegis/telemetria", leituras_json())

def depurar():
    global ultima_depuracao
    if DEPURAR and time.since(ultima_depuracao) >= DEPURAR_MS:
        ultima_depuracao = time.ms()
        log_entry("[leituras] fumaca", leitura_fumaca, "(media", media_fumaca, "base", paper(base_fumaca) + ")", "ar", leitura_ar, "(media", media_ar, "base", paper(base_ar) + ")", "agua", distancia_agua, "cm", "chuva", chuva_pct, "% solo", solo_pct, "%", "temp", temperatura, "umid", umidade, "pir", presenca)

def ciclo():
    global aquecido, amostras, base_registrada, filtro_pronto
    aquecido = time.since(inicio) >= aquecimento_ms
    if not aquecido:
        amostras = amostras + 1
    elif not base_registrada:
        base_registrada = True
        log_entry("[AEGIS] base de ar limpo: fumaca", base_fumaca, "ar", base_ar)
    sentinela_fumaca()
    sentinela_ar()
    sentinela_chuva()
    sentinela_solo()
    filtro_pronto = True
    sentinela_agua()
    sentinela_calor()
    vigia_digital()
    sentinela_presenca()
    vigia_botao()
    atender_comandos()
    avaliar()
    sinalizar()
    acionar_rele()
    relatar()
    atualizar_tela()
    servir_painel()
    telemetria()
    depurar()

def main():
    global rede, ip, mqtt_ok, painel, bot, inicio
    log_entry("[AEGIS] abrigo iniciando")
    gpio.write(radio(PINO_RELE), not RELE_ATIVO_EM_ALTO)
    if finger.begin(radio(PINO_DIGITAL_RX), radio(PINO_DIGITAL_TX)):
        log_entry("[AEGIS] leitor de digital pronto")
    display.clear()
    display.logo(48, 2)
    display.center("AEGIS", 38, 1)
    display.center("protecao offline", 50, 1)
    display.show()
    if usar_rede:
        rede = wifi.connect(wifi_ssid, wifi_senha, 10000)
    if rede:
        ip = wifi.ip()
        mqtt_ok = mqtt.connect(MQTT_BROKER)
        painel = web.start(PORTA_PAINEL)
        bot = telegram.begin(telegram_token, telegram_chat)
        log_entry("[AEGIS] online em", ip)
        if painel:
            log_entry("[AEGIS] painel web:", web.url(ip))
        if bot:
            log_entry("[AEGIS] bot do Telegram ativo")
            avisar("🛡 AEGIS ligado e vigiando.\nPainel na rede de casa: " + web.url(ip) + "\nMande /ajuda para ver os comandos.")
        display.clear()
        display.logo(48, 2)
        display.center("painel web em", 38, 1)
        display.center(ip, 50, 1)
        display.show()
        hide(3000)
    else:
        log_entry("[AEGIS] modo offline: alertas so no local")
    inicio = time.ms()
    while True:
        ciclo()
        hide(CICLO_MS)

if __name__ == "__main__":
    main()
