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


class _Tela:
    ENDERECO = 0x3C

    def __init__(self, sda=21, scl=22):
        self._sda = sda
        self._scl = scl
        self._pronta = None
        self._linhas = {}

    def _iniciar(self):
        if self._pronta is None:
            try:
                self._i2c = _machine.I2C(0, sda=_machine.Pin(self._sda),
                                         scl=_machine.Pin(self._scl), freq=400000)
                self._buffer = bytearray(1024)
                self._fb = _framebuf.FrameBuffer(self._buffer, 128, 64, _framebuf.MONO_VLSB)
                for c in _SSD1306_INICIO:
                    self._comando(c)
                self._pronta = True
            except OSError:
                self._pronta = False
                print("[oled] display nao encontrado, seguindo sem tela")
        return self._pronta

    def _comando(self, c):
        self._i2c.writeto(self.ENDERECO, bytearray((0x80, c)))

    def write(self, linha, texto):
        self._linhas[linha] = str(texto)

    def show(self):
        if not self._iniciar():
            return
        self._fb.fill(0)
        for linha in self._linhas:
            self._fb.text(self._linhas[linha][:16], 0, linha * 8, 1)
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


gpio = _Gpio()
adc = _Adc()
pwm = _Pwm()
sonar = _Sonar()
climate = _Clima()
display = _Tela()
wifi = _Wifi()
mqtt = _Mqtt()
time = _Relogio()


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
MARGEM_FUMACA = 800  # constante
HISTERESE_FUMACA = 300  # constante
MARGEM_AR = 800  # constante
HISTERESE_AR = 300  # constante
FILTRO_MQ = 4  # constante
ADAPTA_BASE = 64  # constante
LIMITE_AGUA_CM = 20.0  # constante
TEMP_ATENCAO = 40.0  # constante
TEMP_ALARME = 55.0  # constante
AQUECIMENTO_MS = 20000  # constante
SILENCIO_MS = 60000  # constante
CICLO_MS = 500  # constante
TELEMETRIA_MS = 10000  # constante
DEPURAR = True  # constante
DEPURAR_MS = 2000  # constante
USAR_REDE = True  # constante
WIFI_SSID = "Wokwi-GUEST"  # constante
WIFI_SENHA = ""  # constante
MQTT_BROKER = "broker.hivemq.com"  # constante
NORMAL = 0  # constante
ATENCAO = 1  # constante
ALARME = 2  # constante
NOMES_ESTADO = ["NORMAL", "ATENCAO", "ALARME"]
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
ultima_telemetria = 0
ultima_depuracao = 0
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

# survivor: roda como tarefa concorrente no alvo
def sentinela_presenca():
    global presenca, risco_presenca
    presenca = gpio.read(radio(PINO_PIR))
    risco_presenca = NORMAL
    if presenca:
        risco_presenca = ATENCAO

# survivor: roda como tarefa concorrente no alvo
def vigia_botao():
    global silenciado, silencio_desde
    if not silenciado and estado == ALARME and gpio.pressed(radio(PINO_BOTAO)):
        silenciado = True
        silencio_desde = time.ms()
        log_entry("[AEGIS] buzzer silenciado por", SILENCIO_MS / 1000, "s")
    if silenciado and time.since(silencio_desde) >= SILENCIO_MS:
        silenciado = False

def avaliar():
    global estado, motivo
    estado = NORMAL
    motivo = "tudo em ordem"
    if risco_presenca == ATENCAO:
        estado = ATENCAO
        motivo = "presenca"
    if risco_ar == ATENCAO:
        estado = ATENCAO
        motivo = "ar ruim"
    if risco_calor == ATENCAO:
        estado = ATENCAO
        motivo = "calor"
    if risco_calor == ALARME:
        estado = ALARME
        motivo = "TEMP ALTA"
    if risco_agua == ALARME:
        estado = ALARME
        motivo = "ENCHENTE"
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

def relatar():
    global silenciado, estado_anterior, motivo_anterior
    if estado != estado_anterior or motivo != motivo_anterior:
        log_entry("[AEGIS] estado:", NOMES_ESTADO[estado], "-", motivo)
        if estado == NORMAL:
            silenciado = False
        if rede:
            mqtt.publish("aegis/alerta", NOMES_ESTADO[estado] + ": " + motivo)
        estado_anterior = estado
        motivo_anterior = motivo

def atualizar_tela():
    display.write(0, "AEGIS " + NOMES_ESTADO[estado])
    display.write(1, motivo)
    display.write(2, "base F" + paper(base_fumaca) + " A" + paper(base_ar))
    display.write(3, "Fumaca  " + paper(media_fumaca))
    display.write(4, "Ar      " + paper(media_ar))
    display.write(5, "Agua    " + paper(ration(distancia_agua)) + " cm")
    display.write(6, "T " + paper(temperatura) + "C U " + paper(ration(umidade)) + "%")
    if not aquecido:
        display.write(7, "aquecendo MQ...")
    elif silenciado:
        display.write(7, "BUZZER MUDO")
    elif rede:
        display.write(7, "rede: online")
    else:
        display.write(7, "rede: offline")
    display.show()

def telemetria():
    global rede, ultima_telemetria
    rede = mqtt.connected()
    if rede and time.since(ultima_telemetria) >= TELEMETRIA_MS:
        ultima_telemetria = time.ms()
        mqtt.publish("aegis/telemetria", "{\"estado\":" + paper(estado) + ",\"fumaca\":" + paper(media_fumaca) + ",\"ar\":" + paper(media_ar) + ",\"agua_cm\":" + paper(distancia_agua) + ",\"temp\":" + paper(temperatura) + ",\"umid\":" + paper(umidade) + "}")

def depurar():
    global ultima_depuracao
    if DEPURAR and time.since(ultima_depuracao) >= DEPURAR_MS:
        ultima_depuracao = time.ms()
        log_entry("[leituras] fumaca", leitura_fumaca, "(media", media_fumaca, "base", paper(base_fumaca) + ")", "ar", leitura_ar, "(media", media_ar, "base", paper(base_ar) + ")", "agua", distancia_agua, "cm", "temp", temperatura, "umid", umidade, "pir", presenca)

def ciclo():
    global aquecido, amostras, base_registrada, filtro_pronto
    aquecido = time.since(inicio) >= AQUECIMENTO_MS
    if not aquecido:
        amostras = amostras + 1
    elif not base_registrada:
        base_registrada = True
        log_entry("[AEGIS] base de ar limpo: fumaca", base_fumaca, "ar", base_ar)
    sentinela_fumaca()
    sentinela_ar()
    filtro_pronto = True
    sentinela_agua()
    sentinela_calor()
    sentinela_presenca()
    vigia_botao()
    avaliar()
    sinalizar()
    relatar()
    atualizar_tela()
    telemetria()
    depurar()

def main():
    global inicio, rede
    log_entry("[AEGIS] abrigo iniciando")
    inicio = time.ms()
    display.write(0, "AEGIS")
    display.write(2, "iniciando...")
    display.show()
    if USAR_REDE:
        if wifi.connect(WIFI_SSID, WIFI_SENHA, 10000):
            rede = mqtt.connect(MQTT_BROKER)
    if rede:
        log_entry("[AEGIS] online: alertas tambem vao por MQTT")
    else:
        log_entry("[AEGIS] modo offline: alertas so no local")
    while True:
        ciclo()
        hide(CICLO_MS)

if __name__ == "__main__":
    main()
