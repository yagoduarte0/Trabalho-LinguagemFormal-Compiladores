# Hardware do abrigo AEGIS

Guia para montar o circuito real com as mesmas ligações do Wokwi (`firmware/diagram.json`) e gravar
o firmware (`firmware/abrigo.aeg` → `firmware/main.py`). Se a montagem seguir este mapa, o
`main.py` que roda no simulador roda na placa sem nenhuma alteração.

## 1. Lista de compras

| Qtd | Componente | Observação |
|---|---|---|
| 1 | ESP32 DevKit V1 (30 pinos, ESP-WROOM-32) | com cabo micro-USB **de dados** (cabo só de carga não grava) |
| 1 | Sensor de presença PIR HC-SR501 | |
| 1 | Sensor ultrassônico HC-SR04 | nível da água |
| 1 | Sensor de gás/fumaça MQ-2 (módulo com saída AO) | |
| 1 | Sensor de qualidade do ar MQ-135 (módulo com saída AO) | |
| 1 | DHT22 (módulo de 3 pinos) | o módulo já tem o pull-up de 10 kΩ |
| 1 | Display OLED 0,96" SSD1306 **I2C** (4 pinos: GND, VCC, SCL, SDA) | o de 7 pinos é SPI e não serve |
| 1 | Push button 6×6 mm | silenciar o alarme |
| 1 | Buzzer **passivo** | o ativo só faz um tom e ignora a frequência |
| 3 | LEDs 5 mm: verde, amarelo, vermelho | |
| 3 | Resistores 220 Ω | um para cada LED |
| 1 + 1 | Resistores 1 kΩ e 2 kΩ (ou 2× 1 kΩ em série) | divisor do ECHO do HC-SR04 |
| 2 + 2 | Resistores 10 kΩ e 20 kΩ (ou 2× 10 kΩ em série) | divisores das saídas dos MQ |
| 1 | Fonte 5 V 2 A | |
| 1 | Protoboard 830 pontos + jumpers macho-macho e macho-fêmea | |
| 1 | Case | |

## 2. Mapa de pinos

Os sensores analógicos ficam só no ADC1 (GPIO32–39), porque o ADC2 para de funcionar quando o WiFi
está ligado. Os números de pino abaixo são as `law PINO_*` do `abrigo.aeg`. Se mudar uma ligação, mude
também a `law` correspondente.

| Componente | Pino do componente | ESP32 | Alimentação |
|---|---|---|---|
| PIR HC-SR501 | OUT | GPIO27 (D27) | VCC → VIN (5 V); a saída já é 3,3 V |
| HC-SR04 | TRIG | GPIO25 (D25) | VCC → VIN (5 V) |
| HC-SR04 | ECHO | GPIO26 (D26) **pelo divisor 1k/2k** | |
| DHT22 | DATA (SDA) | GPIO4 (D4) | VCC → 3V3 |
| MQ-2 | AO | GPIO34 (D34) **pelo divisor 10k/20k** | VCC → VIN (5 V) |
| MQ-135 | AO | GPIO35 (D35) **pelo divisor 10k/20k** | VCC → VIN (5 V) |
| OLED SSD1306 | SDA / SCL | GPIO21 / GPIO22 | VCC → 3V3 |
| Botão | um lado / outro lado | GPIO14 / GND | usa o pull-up interno |
| Buzzer passivo | + / − | GPIO18 / GND | |
| LED verde | anodo (perna longa) | GPIO13 → 220 Ω → LED → GND | |
| LED amarelo | anodo | GPIO33 → 220 Ω → LED → GND | |
| LED vermelho | anodo | GPIO32 → 220 Ω → LED → GND | |

Não ligue nada nos pinos D34 a D39 como saída: esses pinos são só de entrada. A saída DO dos módulos
MQ (o limiar ajustado no trimpot azul) não é usada.

## 3. Alimentação e divisores de tensão

**Os pinos do ESP32 aceitam no máximo 3,3 V.** Três sensores são alimentados em 5 V e devolvem 5 V no
sinal: o ECHO do HC-SR04 e as saídas AO dos dois MQ. Esses sinais passam por um divisor resistivo
antes de chegar ao ESP32:

```
sinal 5 V ──[ R1 ]──┬── pino do ESP32        Vsaída = 5 V × R2 / (R1 + R2)
                    │
                  [ R2 ]
                    │
                   GND
```

| Sinal | R1 (em cima) | R2 (para o GND) | Tensão máxima no pino |
|---|---|---|---|
| ECHO do HC-SR04 → GPIO26 | 1 kΩ | 2 kΩ | 5 × 2/3 ≈ 3,33 V |
| AO do MQ-2 → GPIO34 | 10 kΩ | 20 kΩ | ≈ 3,33 V |
| AO do MQ-135 → GPIO35 | 10 kΩ | 20 kΩ | ≈ 3,33 V |

O PIR HC-SR501 não precisa de divisor, porque a saída dele já é 3,3 V. O TRIG do HC-SR04 também não
precisa: o ESP32 manda 3,3 V e o sensor aceita.

**Alimentação:**
- Cada MQ tem um aquecedor interno que consome cerca de 150 mA. Os dois juntos com o ESP32 e o WiFi
  passam do que uma porta USB de computador costuma entregar, e a placa pode reiniciar sozinha
  (*brownout*). Para gravar e testar sem os MQ, o USB basta. Com tudo ligado, use a fonte 5 V 2 A no
  pino **VIN** e o GND da fonte no **GND** da placa.
- Não ligue a fonte no VIN e o USB ao mesmo tempo. Para olhar o serial com a fonte ligada, desligue a
  fonte e use só o USB, sem os MQ, ou aceite o risco de reinício.
- Ligue todos os GND juntos: fonte, ESP32 e sensores.

## 4. Montagem passo a passo

Monte com tudo desligado e teste cada bloco antes de passar ao próximo. O roteiro de testes da seção 7
tem o comportamento esperado de cada sensor.

1. **ESP32 na protoboard**, uma fileira de pinos de cada lado do canal central. Ligue os trilhos:
   VIN no trilho + de 5 V, 3V3 no trilho + de 3,3 V (no outro lado da protoboard) e GND nos dois
   trilhos −.
2. **Grave o MicroPython e o `main.py`** (seção 6) antes de ligar os sensores. Só com o USB, o serial
   já mostra `[AEGIS] abrigo iniciando`, e o firmware tolera sensores ausentes.
3. **LEDs, buzzer e botão.** Com todos ligados, o LED verde acende ao iniciar. Se um LED não acender,
   ele provavelmente está invertido: a perna longa vai para o lado do resistor.
4. **OLED** (3V3, GND, SDA→21, SCL→22). Ele deve mostrar o estado. Se ficar apagado, confira se o
   módulo é I2C, com endereço 0x3C (alguns vêm com 0x3D).
5. **DHT22** (3V3, GND, DATA→4). O OLED passa a mostrar a temperatura. Leitura `-1.0` indica falha
   de comunicação: confira o fio de dados.
6. **PIR** (VIN, GND, OUT→27). O módulo leva cerca de 1 minuto para estabilizar depois de ligado e,
   até lá, pode acusar presença sozinho. Os dois trimpots do PIR ajustam a sensibilidade e o tempo de
   disparo.
7. **HC-SR04** com o divisor do ECHO (seção 3). O sensor fica no alto, olhando para baixo. Uma
   distância menor que `LIMITE_AGUA_CM` (20 cm) quer dizer água subindo.
8. **MQ-2 e MQ-135** com os divisores, já com a fonte 5 V no VIN. Depois disso, siga a calibração.

## 5. Calibração dos MQ

Os MQ não dão uma leitura absoluta confiável. Cada unidade, a temperatura, a umidade e até o
simulador dão valores diferentes para o mesmo ar. Por isso o firmware **não usa limite fixo**:

1. Durante os primeiros `AQUECIMENTO_MS` depois de ligar, o firmware ignora os MQ e tira a média das
   leituras. Essa média é a **base de ar limpo**. Ela aparece no serial como
   `[AEGIS] base de ar limpo: fumaca X ar Y` e no OLED como `base F.. A..`.
2. Depois disso, o MQ-2 dispara ALARME quando a leitura passa de `base + MARGEM_FUMACA` (800), e o
   alarme só desliga quando a leitura cai abaixo de `base + MARGEM_FUMACA − HISTERESE_FUMACA` (500).
   O MQ-135 funciona do mesmo jeito, mas o que ele dispara é ATENÇÃO.

O que fazer com os sensores reais:

- **Primeira vez:** deixe os MQ ligados por 24 a 48 horas antes de calibrar. Os fabricantes pedem
  esse *burn-in* inicial, e durante ele a leitura cai aos poucos.
- **Aquecimento a cada partida:** os 20 s de `AQUECIMENTO_MS` foram escolhidos para o simulador. No
  sensor real, o aquecedor leva alguns minutos para estabilizar, e uma base medida cedo demais fica
  acima do normal. Use `law AQUECIMENTO_MS = 180000` (3 min) na placa.
- **Ligue sempre em ar limpo.** A base é aprendida a cada partida. Se o abrigo for ligado com fumaça,
  a fumaça vira o "normal".
- **Ajuste das margens:** com `DEPURAR = alive`, o serial mostra a cada 2 s
  `[leituras] fumaca X (base Y) ar ...`. Anote a leitura em ar limpo e com um pouco de gás perto do
  MQ-2: por 1 a 2 s, o gás de um isqueiro **apagado**, em local ventilado e longe de chamas. A margem
  deve ficar entre as duas leituras, mais perto da de gás, para evitar alarme falso. Com a calibração
  pronta, use `DEPURAR = dead` para limpar o serial.
- Depois de mudar qualquer `law`, recompile e grave de novo (seção 6).

## 6. Gravação no ESP32 real

Pré-requisitos (uma vez só): Python 3 e o `mpremote`, que o `./firmware/wokwi.sh preparar` já instala
em `firmware/.venv`, junto com o `.bin` do MicroPython. Instale também o `esptool`:

```sh
firmware/.venv/bin/pip install esptool
```

**Descobrir a porta:** ligue o ESP32 pelo USB e rode `ls /dev/cu.*` (macOS). A porta costuma
aparecer como `/dev/cu.usbserial-XXXX`, `/dev/cu.SLAB_USBtoUART` ou `/dev/cu.wchusbserial-XXXX`. Se
nada aparecer, o cabo pode ser só de carga, ou falta o driver do chip USB da placa (CP210x ou CH340,
impresso no chip ao lado do conector).

**Gravar o MicroPython** (só na primeira vez, porque apaga a placa inteira):

```sh
cd firmware
PORTA=/dev/cu.usbserial-XXXX          # a porta encontrada acima
.venv/bin/esptool --chip esp32 --port $PORTA erase-flash
.venv/bin/esptool --chip esp32 --port $PORTA --baud 460800 write-flash -z 0x1000 ESP32_GENERIC-20260824-v1.29.0.bin
```

Se o `esptool` ficar em `Connecting....` e não passar disso, segure o botão **BOOT** da placa até a
gravação começar. Em versões antigas do esptool os comandos se escrevem `erase_flash` e
`write_flash`.

**Enviar o firmware** (toda vez que mudar o `abrigo.aeg`):

```sh
node ../compilador/aegisc.js abrigo.aeg --alvo esp32 -o main.py
.venv/bin/mpremote connect $PORTA fs cp main.py :main.py + reset
```

**Ver o serial:** `.venv/bin/mpremote connect $PORTA repl`. Para sair, `Ctrl+]`. Para parar o
firmware e cair no prompt `>>>`, `Ctrl+C`.

## 7. Roteiro de testes

Teste um sensor de cada vez, voltando ao normal entre um teste e outro. No Wokwi, mude os valores
clicando no componente com a simulação rodando. Na placa real, provoque cada situação de verdade.

| Ação | Estado | LEDs / buzzer | Serial |
|---|---|---|---|
| Ligar, ar limpo | NORMAL | verde | `abrigo iniciando`, depois de `AQUECIMENTO_MS` `base de ar limpo: ...` |
| Movimento na frente do PIR | ATENÇÃO | amarelo, sem buzzer | `ATENCAO - presenca` |
| MQ-135 acima da base (no Wokwi: girar o potenciômetro) | ATENÇÃO | amarelo | `ATENCAO - ar ruim` |
| Temperatura acima de 40 °C | ATENÇÃO | amarelo | `ATENCAO - calor` |
| Temperatura acima de 55 °C | ALARME | vermelho + sirene | `ALARME - TEMP ALTA` |
| Objeto/água a menos de 20 cm do HC-SR04 | ALARME | vermelho + sirene | `ALARME - ENCHENTE` |
| Gás no MQ-2 (no Wokwi: subir o ppm) | ALARME | vermelho + sirene | `ALARME - FUMACA/GAS` |
| Apertar o botão durante um ALARME | ALARME | vermelho, buzzer mudo por `SILENCIO_MS` | `buzzer silenciado por 60 s` |
| Situação resolvida | NORMAL | verde | `NORMAL` |

As mudanças de estado aparecem no serial como `[AEGIS] estado: ATENCAO - presenca`.
Com dois problemas ao mesmo tempo, vale o mais grave: um ALARME de fumaça vence a ATENÇÃO de presença.
No Wokwi não existe MQ-135, então um potenciômetro faz o papel dele, ligado no mesmo pino.

## 8. Rede e segurança

- A rede é opcional (`law USAR_REDE`). Sem WiFi, o abrigo funciona igual e só não manda MQTT.
- Na placa real, troque `WIFI_SSID` e `WIFI_SENHA` pela sua rede. **Não faça commit da senha
  real.** Antes do commit, volte para `"Wokwi-GUEST"` ou mantenha a alteração só local.
- Os avisos vão para os tópicos `aegis/alerta` (mudanças de estado) e `aegis/telemetria` (leituras a
  cada `TELEMETRIA_MS`). Para acompanhar de outro computador:
  `mosquitto_sub -h broker.hivemq.com -t 'aegis/#' -v`.
- O `broker.hivemq.com` é **público**: qualquer pessoa pode ler e publicar nesses tópicos. Para a
  demonstração isso basta, mas um produto real precisa de um broker próprio com usuário, senha e TLS.
