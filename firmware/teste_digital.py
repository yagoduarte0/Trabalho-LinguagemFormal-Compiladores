"""Testa o driver do leitor biométrico AS608 do runtime esp32, sem a placa.

    python3 firmware/teste_digital.py

Gera o runtime esp32, troca o machine.UART por um leitor falso que fala o
protocolo do fabricante (cabeçalho EF 01, endereço, tipo, tamanho, dados e
soma de 16 bits) e confere reconhecimento, digital desconhecida, cadastro e
o modo sem leitor, em que as digitais chegam pela serial ("dedo <n>").
"""
import os, subprocess, sys, types, time as _t

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
python_esp32 = subprocess.run(
    ["node", os.path.join(RAIZ, "compilador", "aegisc.js"), "/dev/stdin", "--alvo", "esp32"],
    input="scavenge finger\n", check=True, capture_output=True, text=True,
).stdout

class LeitorFalso:
    """Responde aos pacotes como um AS608: valida cabeçalho, tamanho e soma."""
    def __init__(self):
        self.dedo = False          # tem dedo encostado?
        self.digital = 7           # posição da digital que o dedo "é" (None = desconhecida)
        self.guardadas = {}
        self.comandos = []
        self.saida = b""
    def write(self, pacote):
        assert pacote[:6] == bytes((0xEF, 1, 0xFF, 0xFF, 0xFF, 0xFF)), pacote
        assert pacote[6] == 1, "tipo deve ser comando"
        n = (pacote[7] << 8) | pacote[8]
        dados = pacote[9:9 + n - 2]
        soma = (pacote[-2] << 8) | pacote[-1]
        assert sum(pacote[6:-2]) & 0xFFFF == soma, "soma errada"
        assert len(pacote) == 9 + n, "tamanho errado"
        cmd = dados[0]
        self.comandos.append(cmd)
        if cmd == 0x13: resp = [0]
        elif cmd == 0x01: resp = [0 if self.dedo else 0x02]
        elif cmd == 0x02: resp = [0]
        elif cmd == 0x04:
            resp = [0, 0, self.digital, 0, 99] if self.digital is not None else [0x09, 0, 0, 0, 0]
        elif cmd == 0x05: resp = [0]
        elif cmd == 0x06:
            self.guardadas[(dados[2] << 8) | dados[3]] = True; resp = [0]
        else: resp = [0x01]
        corpo = bytes((7, 0, len(resp) + 2)) + bytes(resp)
        s = sum(corpo) & 0xFFFF
        self.saida += bytes((0xEF, 1, 0xFF, 0xFF, 0xFF, 0xFF)) + corpo + bytes((s >> 8, s & 0xFF))
    def read(self, n=None):
        if n is None:
            b, self.saida = self.saida, b""
            return b or None
        b, self.saida = self.saida[:n], self.saida[n:]
        return b or None

leitor = LeitorFalso()
class Pin:
    IN, OUT, PULL_UP = 1, 2, 3
    def __init__(self, *a, **k): pass
    def value(self, v=None): return 0
def UART(numero, baudrate, rx, tx, timeout):
    assert (numero, baudrate, rx, tx) == (2, 57600, 16, 17), (numero, baudrate, rx, tx)
    return leitor
machine = types.SimpleNamespace(Pin=Pin, UART=UART)
tempo = types.ModuleType("time")
tempo.sleep_ms = lambda ms: None; tempo.sleep_us = lambda us: None
tempo.ticks_ms = lambda: int(_t.time() * 1000); tempo.ticks_diff = lambda a, b: a - b
framebuf = types.SimpleNamespace(FrameBuffer=lambda *a: None, MONO_VLSB=0, MONO_HLSB=3)
sys.modules.update(machine=machine, dht=types.SimpleNamespace(),
                   framebuf=framebuf, time=tempo)
g = {"__name__": "teste"}
exec(compile(python_esp32, "runtime esp32", "exec"), g)
f = g["finger"]

assert f.begin(16, 17) is True and f.present()
assert f.scan() == -1, "sem dedo"
leitor.dedo = True
assert f.scan() == 7, "digital 7 reconhecida"
assert f.scan() == -1, "mesma encostada nao conta de novo"
leitor.dedo = False
assert f.scan() == -1
leitor.dedo, leitor.digital = True, None
assert f.scan() == -2, "digital desconhecida"
leitor.dedo = False; f.scan()

# cadastro: o dedo encosta, sai, encosta de novo (o leitor falso alterna)
estados = iter([True, False, True, False] * 3)
leitor.write_orig = leitor.write
def write_alternando(p):
    if p[9] == 0x01: leitor.dedo = next(estados)
    leitor.write_orig(p)
leitor.write = write_alternando
assert f.enroll(3) is True and 3 in leitor.guardadas, leitor.guardadas
print("AS608 ok: comandos", sorted(set(leitor.comandos)))

# leitor ausente: cai para a serial
class Mudo:
    def write(self, p): pass
    def read(self, n=None): return None
machine.UART = lambda *a, **k: Mudo()
entrada = list("dedo 1\nlixo\ndedo -2\n")
class Poll:
    def register(self, *a): pass
    def poll(self, t): return [1] if entrada else []
sys.modules["select"] = types.SimpleNamespace(poll=Poll, POLLIN=1)
class Stdin:
    def read(self, n): return entrada.pop(0)
sys.stdin = Stdin()
f2 = g["_Digital"]()
assert f2.begin(16, 17) is False
assert f2.scan() == 1 and f2.scan() == -2 and f2.scan() == -1
print("serial ok: 'dedo 1' e 'dedo -2' lidos, 'lixo' ignorado")
