// FASE 3 — Geração de código: percorre a AST e emite Python equivalente.
//
// O gerador é um visitante recursivo por tipo de nó. Não faz otimização nem
// análise semântica: confia que a AST recebida já passou pelas fases 1 e 2.
//
// Decisões de projeto registradas aqui porque não são óbvias lendo o código:
//
// 1) Runtime embutido: a linguagem tem construções de hardware (broadcast,
//    silence, hide, radio) e módulos (gpio, mqtt, ...) que não existem em
//    Python. Em vez de gerar imports de um pacote que o professor teria que
//    instalar, o gerador emite um pequeno runtime no topo do arquivo. O
//    Python gerado roda sozinho, sem dependência nenhuma. Há dois alvos com
//    a mesma API: "simulado" (PC, valores fixos) e "esp32" (MicroPython com
//    o hardware real). Trocar de alvo troca só o runtime, nunca o programa.
//
// 2) Indentação: AEGIS delimita blocos por chaves e Python por indentação.
//    A conversão acontece no emissor, que recebe o nível e aplica 4 espaços.
//    Bloco vazio vira "pass", senão o Python fica sintaticamente inválido.
//
// 3) Mapa de linhas: cada linha gerada guarda de qual linha do fonte veio.
//    É o que permite a interface destacar a origem de uma linha do Python.
//
// 4) "survivor" (task) e "ambush" (evento) viram funções comuns. A linguagem
//    prevê execução concorrente, mas concorrência de verdade fugiria do
//    escopo do trabalho — o comentário emitido deixa a intenção registrada.

const INDENT = "    ";

// Funções que os dois runtimes compartilham: conversões de tipo (os nomes
// dos tipos são "palavra_chamavel" no parser) e o pino como valor.
const RUNTIME_CONVERSOES = `def radio(pino):
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
    print(*args)`;

// A página do painel web: no Node vem do require, no navegador já foi
// carregada pelo <script src="painel.js"> do index.html.
const PAINEL_HTML_TEXTO = (typeof require === "function" && typeof module !== "undefined")
  ? require("./painel.js").PAINEL_HTML
  : PAINEL_HTML;

// Módulos de rede que os dois runtimes compartilham. Só o transporte do
// Telegram muda (urllib no PC, requests no MicroPython), por isso _Telegram
// é definido em cada runtime sobre a base _TelegramBase. O HTML entra como
// literal de string pelo JSON.stringify, que também é um literal válido em
// Python.
const RUNTIME_REDE = `class _Config:
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


_PAINEL_HTML = ${JSON.stringify(PAINEL_HTML_TEXTO)}


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
            pedido = cliente.recv(1024).split(b"\\r\\n", 1)[0].decode().split(" ")
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
        cabecalho = ("HTTP/1.1 " + situacao + "\\r\\nContent-Type: " + tipo +
                     "\\r\\nContent-Length: " + str(len(corpo)) +
                     "\\r\\nCache-Control: no-store\\r\\nConnection: close\\r\\n\\r\\n")
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
    def __init__(self):
        self.fila = []
        self._token = ""
        self._chat = ""
        self._offset = -1      # -1: a primeira consulta só descarta o que chegou antes de ligar
        self._ultima = None

    def begin(self, token, chat):
        self._token = str(token or "")
        self._chat = str(chat or "")
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
        return resposta is not None and resposta.get("ok", False)

    def command(self, intervalo_ms=15000):
        if not self.fila and self._ativo():
            agora = self._ms()
            if self._ultima is None or self._diff(agora, self._ultima) >= intervalo_ms:
                self._ultima = agora
                self._consultar()
        return self.fila.pop(0) if self.fila else ""

    def _consultar(self):
        resposta = self._pedir("getUpdates", {"offset": self._offset, "timeout": 0, "limit": 10})
        if not resposta or not resposta.get("ok"):
            return
        primeira = self._offset == -1
        self._offset = max(self._offset, 0)
        for u in resposta.get("result", []):
            self._offset = u["update_id"] + 1
            m = u.get("message") or {}
            texto = m.get("text") or ""
            if primeira or str(m.get("chat", {}).get("id")) != self._chat or not texto.startswith("/"):
                continue
            self.fila.append(texto.split()[0].split("@")[0].lower())`;

// Alvo "simulado": roda no PC com Python comum. Os sensores devolvem valores
// fixos (alteráveis pelos atributos) e o hardware só imprime o que faria.
const RUNTIME = `# --- runtime AEGIS (gerado automaticamente) ---
import time as _time


class _Barramento:
    def __init__(self):
        self.estado = {}

    def read(self, pino):
        return self.estado.get(pino, False)

    def write(self, pino, valor):
        self.estado[pino] = valor

    def pressed(self, pino):
        return self.estado.get(pino, False)


class _Analogico(_Barramento):
    def read(self, pino):
        return self.estado.get(pino, 0)


class _Pwm(_Barramento):
    def tone(self, pino, hz):
        if self.estado.get(pino) != hz:
            print("[pwm " + str(pino) + "] tom de " + str(hz) + " Hz")
        self.estado[pino] = hz

    def off(self, pino):
        if self.estado.get(pino):
            print("[pwm " + str(pino) + "] desligado")
        self.estado[pino] = 0


class _Sonar:
    def __init__(self):
        self.cm = 100.0

    def distance(self, trig, echo):
        return self.cm


class _Clima:
    def __init__(self):
        self.temperatura = 25.0
        self.umidade = 50.0

    def temperature(self, pino):
        return self.temperatura

    def humidity(self, pino):
        return self.umidade


class _Tela:
    # resume em texto o que seria desenhado: textos, <ícones> e barras em %
    def __init__(self):
        self.linhas = {}
        self.quadro = []
        self.ultima = None

    def write(self, linha, texto):
        self.linhas[linha] = str(texto)

    def clear(self):
        self.linhas = {}
        self.quadro = []

    def text(self, texto, x, y, cor=1):
        self.quadro.append(str(texto))

    def center(self, texto, y, cor=1):
        self.quadro.append(str(texto))

    def rect(self, x, y, largura, altura, cheio=False):
        pass

    def bar(self, x, y, largura, altura, valor, maximo):
        pct = int(100 * min(max(valor, 0), maximo) / maximo) if maximo > 0 else 0
        self.quadro.append("[" + str(pct) + "%]")

    def icon(self, nome, x, y):
        self.quadro.append("<" + str(nome) + ">")

    def logo(self, x, y):
        self.quadro.append("<logo>")

    def show(self):
        quadro = " | ".join([self.linhas[k] for k in sorted(self.linhas)] + self.quadro)
        self.quadro = []
        if quadro != self.ultima:
            print("[oled] " + quadro)
            self.ultima = quadro


class _Relogio:
    def ms(self):
        return int(_time.time() * 1000)

    def since(self, marca):
        return self.ms() - marca

    def sleep(self, segundos):
        _time.sleep(segundos)


class _Rede:
    def connect(self, *args):
        return True

    def connected(self):
        return True

    def publish(self, topico, mensagem):
        print("[" + str(topico) + "] " + str(mensagem))
        return True

    def ip(self):
        return "localhost"


${RUNTIME_REDE}


class _PainelPc(_Painel):
    # no PC, portas abaixo de 1024 exigem administrador: a 80 vira 8080
    def _porta_real(self, porta):
        return 8080 if porta < 1024 else porta


class _Telegram(_TelegramBase):
    # Sem token e chat, só imprime e guarda em "enviadas" (é o que os
    # cenários usam). Com os dois no config.json, fala com o bot de verdade.
    def __init__(self):
        _TelegramBase.__init__(self)
        self.enviadas = []

    def begin(self, token, chat):
        _TelegramBase.begin(self, token, chat)
        return True

    def send(self, texto):
        self.enviadas.append(str(texto))
        print("[telegram] " + str(texto).replace("\\n", " / "))
        return _TelegramBase.send(self, texto) if self._ativo() else True

    def _ms(self):
        return int(_time.time() * 1000)

    def _diff(self, a, b):
        return a - b

    # Alguns Pythons (o do python.org sem os certificados instalados, ou atrás
    # de antivírus/proxy que intercepta HTTPS) recusam o certificado do
    # Telegram. O curl do sistema confia nos certificados do próprio sistema,
    # então ele é o plano B.
    def _pedir(self, metodo, dados):
        import json
        import urllib.request
        corpo = json.dumps(dados)
        try:
            pedido = urllib.request.Request(self._url(metodo), data=corpo.encode(),
                                            headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(pedido, timeout=10) as r:
                return json.loads(r.read().decode())
        except Exception as erro_python:
            import subprocess
            try:
                saida = subprocess.run(["curl", "-sS", "-m", "10", "-H", "Content-Type: application/json",
                                        "-d", corpo, self._url(metodo)],
                                       capture_output=True, text=True, timeout=15)
                if saida.returncode == 0:
                    return json.loads(saida.stdout)
                print("[telegram] falhou:", erro_python, "/ curl:", saida.stderr.strip())
            except Exception as erro_curl:
                print("[telegram] falhou:", erro_python, "/", erro_curl)
            return None


class _Digital:
    # leitor biométrico: os testes colocam em "fila" as digitais encostadas
    def __init__(self):
        self.fila = []
        self.presente = True

    def begin(self, rx, tx):
        return self.presente

    def present(self):
        return self.presente

    def scan(self):
        return self.fila.pop(0) if self.fila else -1

    def enroll(self, numero):
        print("[digital] digital " + str(numero) + " cadastrada")
        return True


gpio = _Barramento()
adc = _Analogico()
pwm = _Pwm()
sonar = _Sonar()
climate = _Clima()
display = _Tela()
wifi = _Rede()
mqtt = _Rede()
time = _Relogio()
finger = _Digital()
config = _Config(__import__("os").environ.get("AEGIS_CONFIG", "config.json"))
web = _PainelPc()
telegram = _Telegram()


${RUNTIME_CONVERSOES}


def hide(ms):
    _time.sleep(ms / 1000)


def broadcast(pino):
    gpio.write(pino, True)


def silence(pino):
    gpio.write(pino, False)
# --- fim do runtime ---`;

// Alvo "esp32": MicroPython no ESP32 real ou no Wokwi. Mesma API do
// simulado, implementada com machine/dht/framebuf/network/umqtt. Toda falha
// de periférico opcional (display, rede) é tratada aqui dentro: o firmware
// continua rodando offline e sem tela se for preciso.
const RUNTIME_ESP32 = `# --- runtime AEGIS para ESP32 (MicroPython, gerado automaticamente) ---
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


${RUNTIME_REDE}


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


${RUNTIME_CONVERSOES}


def hide(ms):
    _time.sleep_ms(int(ms))


def broadcast(pino):
    gpio.write(pino, True)


def silence(pino):
    gpio.write(pino, False)
# --- fim do runtime ---`;

const RUNTIMES = { simulado: RUNTIME, esp32: RUNTIME_ESP32 };

// operadores que mudam de grafia entre as duas linguagens
const OPERADOR_LOGICO = { "||": "or", "&&": "and" };
const OPERADOR_UNARIO = { "!": "not ", "-": "-" };

function gerarCodigo(ast, opcoes = {}) {
  const alvo = opcoes.alvo || "simulado";
  const runtime = RUNTIMES[alvo];
  if (!runtime) {
    throw new Error(`alvo desconhecido: ${alvo} (use ${Object.keys(RUNTIMES).join(" ou ")})`);
  }
  const linhas = [];
  const mapa = {};
  const declaracoes = ast && ast.declaracoes ? ast.declaracoes : [];
  // variáveis do topo do programa: as únicas que podem precisar de "global"
  const globais = new Set(
    declaracoes.filter(d => d.tipo === "DeclaracaoVariavel").map(d => d.nome)
  );

  function emitir(texto, nivel, origem) {
    linhas.push(nivel > 0 ? INDENT.repeat(nivel) + texto : texto);
    if (origem && origem.linha) mapa[linhas.length] = origem.linha;
  }

  // Em Python, atribuir dentro de uma função cria uma variável local. Para
  // que uma mission altere um supply do topo é preciso declarar "global".
  // Coleta os nomes atribuídos no corpo que são globais e não foram
  // sombreados por parâmetro ou por supply local.
  function nomesGlobaisAtribuidos(corpo, parametros) {
    const locais = new Set(parametros || []);
    const atribuidos = [];

    function visitar(nos) {
      for (const no of nos || []) {
        if (!no) continue;
        if (no.tipo === "DeclaracaoVariavel") locais.add(no.nome);
        if (no.tipo === "Atribuicao" && !atribuidos.includes(no.nome)) atribuidos.push(no.nome);
        if (no.tipo === "Checkpoint") {
          visitar(no.entao);
          if (Array.isArray(no.outros)) visitar(no.outros);
          else if (no.outros) visitar([no.outros]);
        }
        if (no.tipo === "Watch" || no.tipo === "Patrol") visitar(no.corpo);
        if (no.tipo === "Quarantine") {
          locais.add(no.nomeErro);
          visitar(no.tentativa);
          visitar(no.captura);
        }
      }
    }

    visitar(corpo);
    return atribuidos.filter(n => globais.has(n) && !locais.has(n));
  }

  function emitirCorpoFuncao(no, nivel, parametros) {
    const nomes = nomesGlobaisAtribuidos(no.corpo, parametros);
    if (nomes.length > 0) emitir(`global ${nomes.join(", ")}`, nivel);
    emitirBloco(no.corpo, nivel);
  }

  function emitirBloco(declaracoes, nivel) {
    if (!declaracoes || declaracoes.length === 0) {
      emitir("pass", nivel);
      return;
    }
    for (const d of declaracoes) gerarDeclaracao(d, nivel);
  }

  // ------------------------------ expressões -------------------------------
  function gerarExpressao(no) {
    switch (no.tipo) {
      case "Literal":
        if (no.tipoLiteral === "status") return no.valor ? "True" : "False";
        if (no.tipoLiteral === "paper") return JSON.stringify(no.valor);
        // um "vital" de valor redondo (10.0) viraria "10" pelo String() do
        // JavaScript e chegaria ao Python como int, perdendo a distinção
        // entre ration e vital que a linguagem faz
        if (no.tipoLiteral === "vital" && Number.isInteger(no.valor)) {
          return no.valor.toFixed(1);
        }
        return String(no.valor);

      case "Identificador":
        return no.nome;

      case "Agrupamento":
        return "(" + gerarExpressao(no.expressao) + ")";

      case "Logica":
        return gerarExpressao(no.esquerda) + " " + OPERADOR_LOGICO[no.operador] +
               " " + gerarExpressao(no.direita);

      case "Binaria":
        return gerarExpressao(no.esquerda) + " " + no.operador + " " +
               gerarExpressao(no.direita);

      case "Unaria":
        return OPERADOR_UNARIO[no.operador] + gerarExpressao(no.operando);

      case "Chamada":
        return gerarExpressao(no.alvo) + "(" +
               no.argumentos.map(gerarExpressao).join(", ") + ")";

      case "Membro":
        return gerarExpressao(no.objeto) + "." + no.nome;

      case "Indice":
        return gerarExpressao(no.alvo) + "[" + gerarExpressao(no.indice) + "]";

      case "ListaLiteral":
        return "[" + no.elementos.map(gerarExpressao).join(", ") + "]";

      default:
        return `# expressão não suportada: ${no.tipo}`;
    }
  }

  // ------------------------- declarações e comandos -------------------------
  function gerarDeclaracao(no, nivel) {
    switch (no.tipo) {
      case "Scavenge":
        emitir(`# scavenge ${no.modulo} — módulo fornecido pelo runtime`, nivel, no);
        break;

      case "DeclaracaoVariavel": {
        const sufixo = no.categoria === "law" ? "  # constante" : "";
        emitir(`${no.nome} = ${gerarExpressao(no.valor)}${sufixo}`, nivel, no);
        break;
      }

      case "Estrutura": {
        emitir(`class ${no.nome}:`, nivel, no);
        const params = no.campos.map(c => `${c.nome}=None`).join(", ");
        emitir(`def __init__(self${params ? ", " + params : ""}):`, nivel + 1);
        if (no.campos.length === 0) {
          emitir("pass", nivel + 2);
        } else {
          for (const c of no.campos) {
            emitir(`self.${c.nome} = ${c.nome}`, nivel + 2, c);
          }
        }
        emitir("", nivel);
        break;
      }

      case "Funcao": {
        const params = no.parametros.map(p => p.nome).join(", ");
        emitir(`def ${no.nome}(${params}):`, nivel, no);
        emitirCorpoFuncao(no, nivel + 1, no.parametros.map(p => p.nome));
        emitir("", nivel);
        break;
      }

      case "Task":
        emitir(`# survivor: roda como tarefa concorrente no alvo`, nivel, no);
        emitir(`def ${no.nome}():`, nivel, no);
        emitirCorpoFuncao(no, nivel + 1);
        emitir("", nivel);
        break;

      case "Evento":
        emitir(`# ambush: disparado por evento no alvo`, nivel, no);
        emitir(`def ${no.nome}():`, nivel, no);
        emitirCorpoFuncao(no, nivel + 1);
        emitir("", nivel);
        break;

      case "Principal":
        emitir("def main():", nivel, no);
        emitirCorpoFuncao(no, nivel + 1);
        emitir("", nivel);
        break;

      case "Checkpoint":
        gerarCheckpoint(no, nivel, "if");
        break;

      case "Watch":
        emitir("while True:", nivel, no);
        emitirBloco(no.corpo, nivel + 1);
        break;

      case "Patrol":
        emitir(`for _ in range(${gerarExpressao(no.vezes)}):`, nivel, no);
        emitirBloco(no.corpo, nivel + 1);
        break;

      case "Quarantine":
        emitir("try:", nivel, no);
        emitirBloco(no.tentativa, nivel + 1);
        emitir(`except Exception as ${no.nomeErro}:`, nivel, no);
        emitirBloco(no.captura, nivel + 1);
        break;

      case "Outbreak":
        emitir(`raise Exception(${gerarExpressao(no.expressao)})`, nivel, no);
        break;

      case "Extract":
        emitir(no.expressao ? `return ${gerarExpressao(no.expressao)}` : "return",
               nivel, no);
        break;

      case "Atribuicao":
        emitir(`${no.nome} = ${gerarExpressao(no.valor)}`, nivel, no);
        break;

      case "ExpressaoStmt":
        emitir(gerarExpressao(no.expressao), nivel, no);
        break;

      default:
        emitir(`# nó não suportado: ${no.tipo}`, nivel, no);
    }
  }

  // "fallback checkpoint" encadeado vira elif; "fallback" com bloco vira else
  function gerarCheckpoint(no, nivel, palavra) {
    emitir(`${palavra} ${gerarExpressao(no.condicao)}:`, nivel, no);
    emitirBloco(no.entao, nivel + 1);

    if (no.outros === null || no.outros === undefined) return;

    if (Array.isArray(no.outros)) {
      emitir("else:", nivel);
      emitirBloco(no.outros, nivel + 1);
    } else {
      gerarCheckpoint(no.outros, nivel, "elif");
    }
  }

  // ------------------------------- montagem --------------------------------
  for (const linha of runtime.split("\n")) linhas.push(linha);
  linhas.push("");
  linhas.push("");

  for (const d of declaracoes) gerarDeclaracao(d, 0);

  const temPrincipal = declaracoes.some(d => d.tipo === "Principal");
  if (temPrincipal) {
    emitir('if __name__ == "__main__":');
    emitir("main()", 1);
  }

  // remove linhas em branco repetidas no fim, preservando o mapa
  while (linhas.length > 0 && linhas[linhas.length - 1].trim() === "") {
    linhas.pop();
  }

  return { corpo: linhas.join("\n") + "\n", mapa };
}

if (typeof module !== "undefined") {
  module.exports = { gerarCodigo, RUNTIME, RUNTIME_ESP32 };
}
