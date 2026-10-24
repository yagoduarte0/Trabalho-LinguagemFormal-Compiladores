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
    def __init__(self):
        self.linhas = {}
        self.ultima = None

    def write(self, linha, texto):
        self.linhas[linha] = str(texto)

    def show(self):
        quadro = " | ".join(self.linhas[k] for k in sorted(self.linhas))
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


gpio = _Barramento()
adc = _Analogico()
pwm = _Pwm()
sonar = _Sonar()
climate = _Clima()
display = _Tela()
wifi = _Rede()
mqtt = _Rede()
time = _Relogio()


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
