# A linguagem AEGIS

Linguagem de domínio específico para automação de sobrevivência: descreve as
regras que um microcontrolador executa para monitorar um abrigo — presença,
nível de água, fumaça, qualidade do ar e temperatura — e reagir a emergências.

O vocabulário é temático de propósito: em vez de `function`, `if` e `print`, a
linguagem usa `mission`, `checkpoint` e `log_entry`. A intenção é que o código
se leia como o diário de operação de um abrigo.

O compilador tem três fases e traduz AEGIS para Python:

```
fonte .aeg  ->  [léxico]  ->  tokens  ->  [sintático]  ->  AST  ->  [gerador]  ->  Python
```

---

## 1. Análise léxica

O analisador percorre o fonte uma única vez, testando na posição atual uma
lista ordenada de expressões regulares *sticky*. A primeira que casar vence,
e a ordem implementa **maximal munch**:

- símbolos de dois caracteres antes dos de um (`->` antes de `-`, `&&` antes de `&`);
- comentários antes do operador de divisão (`//` e `/*` antes de `/`);
- decimal antes de inteiro (`10.5` não vira `10` seguido de `.5`);
- string bem-formada antes de string aberta.

Cada token registra **tipo**, **categoria**, **lexema**, **valor já convertido**,
**linha**, **coluna** e a posição absoluta no fonte.

**Quebra de linha dentro de parênteses e colchetes.** A quebra de linha é o
separador de comandos, mas, como em Python, ela é ignorada enquanto houver um
`(` ou `[` aberto. Assim uma chamada longa pode ocupar várias linhas:

```
mqtt.publish("aegis/telemetria",
    "{\"temp\":" + paper(temperatura) + "}")
```

Para que um parêntese esquecido não engula o resto do programa, o lexer volta a
contar a quebra de linha quando a linha seguinte começa com uma palavra que só
pode abrir um comando novo (`supply`, `checkpoint`, `mission`...) ou com `}`.

### Palavras reservadas

São 29, agrupadas em sete categorias.

**Declaração (8)**

| Lexema | Token | Significado |
|---|---|---|
| `chronicle` | TOKEN_MAIN | ponto de entrada do programa |
| `scavenge` | TOKEN_IMPORT | importa um módulo |
| `mission` | TOKEN_FUNC | declara uma função |
| `supply` | TOKEN_LET | declara uma variável |
| `law` | TOKEN_CONST | declara uma constante |
| `survivor` | TOKEN_TASK | declara uma tarefa |
| `cache` | TOKEN_STRUCT | declara uma estrutura |
| `stash` | TOKEN_ARRAY | declara um arranjo |

**Tipo (6)**

| Lexema | Token | Corresponde a |
|---|---|---|
| `ration` | TOKEN_TYPE_INT | inteiro |
| `vital` | TOKEN_TYPE_FLOAT | ponto flutuante |
| `status` | TOKEN_TYPE_BOOL | booleano |
| `paper` | TOKEN_TYPE_STRING | texto |
| `radio` | TOKEN_TYPE_PIN | pino de hardware |
| `silent` | TOKEN_TYPE_VOID | sem retorno |

**Controle de fluxo (5)**

| Lexema | Token | Equivalente |
|---|---|---|
| `checkpoint` | TOKEN_IF | `if` |
| `fallback` | TOKEN_ELSE | `else` |
| `watch` | TOKEN_LOOP | laço infinito |
| `patrol` | TOKEN_FOR | repetição contada |
| `extract` | TOKEN_RETURN | `return` |

**Hardware (3)**

| Lexema | Token | Ação |
|---|---|---|
| `broadcast` | TOKEN_GPIO_HIGH | coloca o pino em nível alto |
| `silence` | TOKEN_GPIO_LOW | coloca o pino em nível baixo |
| `hide` | TOKEN_DELAY | aguarda em milissegundos |

**Tratamento de erro (3)**

| Lexema | Token | Equivalente |
|---|---|---|
| `quarantine` | TOKEN_TRY | `try` |
| `catch` | TOKEN_CATCH | `except` |
| `outbreak` | TOKEN_ERROR_TYPE | lança um erro |

**Evento e E/S (2)**

| Lexema | Token | Significado |
|---|---|---|
| `ambush` | TOKEN_EVENT | rotina disparada por evento |
| `log_entry` | TOKEN_PRINT | escreve na saída |

**Literais booleanos (2)**

| Lexema | Token | Valor |
|---|---|---|
| `alive` | TOKEN_BOOL_LIT | verdadeiro |
| `dead` | TOKEN_BOOL_LIT | falso |

### Símbolos

São 25, testados do mais longo para o mais curto.

| Operadores | | | Delimitadores | |
|---|---|---|---|---|
| `+` PLUS | `-` MINUS | `*` STAR | `(` LPAREN | `)` RPAREN |
| `/` SLASH | `=` ASSIGN | `!` NOT | `{` LBRACE | `}` RBRACE |
| `==` EQ | `!=` NEQ | `<` LT | `[` LBRACKET | `]` RBRACKET |
| `>` GT | `<=` LE | `>=` GE | `,` COMMA | `;` SEMI |
| `&&` AND | `||` OR | | `:` COLON | `.` DOT |
| | | | `->` ARROW | |

O `.` não constava da tabela original da linguagem e foi acrescentado porque os
programas de referência usam acesso a membro (`gpio.read(...)`,
`mqtt.publish(...)`); sem ele o ponto viraria caractere não reconhecido.

### Literais e identificadores

| Categoria | Token | Forma |
|---|---|---|
| Inteiro | TOKEN_INT_LIT | `42` |
| Decimal | TOKEN_FLOAT_LIT | `10.5` |
| Texto | TOKEN_STRING_LIT | `"abrigo"`, com escapes `\n`, `\t`, `\r`, `\\`, `\"` |
| Identificador | TOKEN_IDENTIFIER | começa com letra ou `_`, segue com letras, dígitos ou `_` |
| Comentário | TOKEN_COMMENT | `// até o fim da linha` ou `/* em bloco */` |

### Módulos embutidos

Os módulos abaixo são convenção da biblioteca padrão, **não** palavras
reservadas. O lexer os trata como identificadores comuns, então um programa
pode tecnicamente usar esses nomes para outra coisa. A API é a mesma nos dois
alvos de compilação (seção 3): o mesmo programa roda no PC e no ESP32.

| Chamada | O que faz | No ESP32 (MicroPython) |
|---|---|---|
| `gpio.read(p)` / `gpio.write(p, v)` | lê ou escreve um pino digital | `machine.Pin` |
| `gpio.pressed(p)` | botão entre o pino e o GND, com pull-up interno | `Pin.PULL_UP`, pressionado = 0 |
| `adc.read(p)` | leitura analógica, 0 a 4095 | `machine.ADC`, atenuação de 11 dB |
| `pwm.tone(p, hz)` / `pwm.off(p)` | toca ou cala um buzzer passivo | `machine.PWM` |
| `sonar.distance(trig, echo)` | distância do HC-SR04 em cm, `-1` sem eco | pulso de 10 µs + `time_pulse_us` |
| `climate.temperature(p)` / `climate.humidity(p)` | DHT22, `-1` se a leitura falhar | `dht.DHT22`, uma leitura a cada 2 s |
| `display.write(linha, texto)` / `display.show()` | OLED SSD1306 128×64: texto nas linhas 0 a 7; `show()` envia a imagem | driver mínimo embutido, I2C SDA 21 / SCL 22 |
| `display.clear()` / `display.text(t, x, y, cor)` / `display.center(t, y, cor)` | limpa; texto em pixels ou centralizado (`cor` 0 = apagado sobre fundo aceso) | `framebuf`, fonte 8×8 |
| `display.rect(x, y, l, a, cheio)` / `display.bar(x, y, l, a, valor, maximo)` | retângulo; barra de nível proporcional | `framebuf.fill_rect` |
| `display.icon(nome, x, y)` / `display.logo(x, y)` | ícone 8×8 (`termometro`, `gota`, `chuva`, `solo`, `fogo`, `onda`, `cadeado`, `aberto`, `wifi`, `mudo`, `ventoinha`); escudo AEGIS 32×32 | bitmaps embutidos no runtime |
| `wifi.connect(ssid, senha, limite_ms)` | conecta ao WiFi, devolve `alive`/`dead` | `network.WLAN` |
| `wifi.ip()` | IP da placa na rede (vazio sem conexão) | `WLAN.ipconfig` |
| `mqtt.connect(broker)` / `mqtt.publish(topico, msg)` / `mqtt.connected()` | avisos pela rede; falhas nunca derrubam o programa | `umqtt.simple` |
| `config.get(chave, padrao)` | ajuste lido do `config.json` da placa (fora do Git); sem a chave, devolve o padrão | `json` |
| `web.start(porta)` / `web.url(ip)` | abre o servidor do painel; endereço para mostrar ao usuário | `socket` não bloqueante |
| `web.waiting()` / `web.serve(json)` | há um navegador pedindo `/dados`? responde com as leituras | atende um pedido por ciclo |
| `web.command()` | próximo comando do painel (`"/silenciar"`) ou `""` | botão da página |
| `telegram.begin(token, chat)` / `telegram.send(texto)` | liga o bot; manda mensagem ao dono | API HTTPS do Telegram, `requests` |
| `telegram.command(intervalo_ms)` | próximo comando do dono (`"/status"`...) ou `""`; consulta no máximo a cada `intervalo_ms` | `getUpdates`, só o chat configurado |
| `time.ms()` / `time.since(marca)` | relógio em milissegundos | `time.ticks_ms` / `ticks_diff` |
| `finger.begin(rx, tx)` / `finger.present()` | liga o leitor de digital, diz se ele respondeu | AS608 na UART2, 57600 bps |
| `finger.scan()` | número da digital encostada, `-1` sem dedo, `-2` desconhecida | sem o leitor, lê linhas `dedo <n>` da serial |
| `finger.enroll(n)` | cadastra um dedo na posição `n` (duas leituras) | comandos GenImg, Img2Tz, RegModel e Store |

### Conversões de tipo

Os nomes de tipo também funcionam como funções de conversão: `ration(x)`
(inteiro), `vital(x)` (decimal), `paper(x)` (texto), `status(x)` (booleano) e
`radio(x)` (pino). É assim que um número entra numa mensagem:
`log_entry("temperatura " + paper(t))`.

### Variáveis globais

Um `supply` declarado no topo do arquivo é global: uma `mission`, um `survivor`
ou o `chronicle` podem lê-lo e alterá-lo. Um `supply` declarado dentro de um
bloco, ou um parâmetro, é local e esconde o global de mesmo nome.

### Erros léxicos

Os três erros abaixo são registrados **sem interromper a análise**, para que o
programador veja todos de uma vez em vez de um por compilação:

| Erro | Token emitido |
|---|---|
| aspas não fechadas | TOKEN_STRING_LIT_ERRO |
| comentário de bloco não fechado | TOKEN_COMMENT_ERRO |
| caractere não reconhecido | TOKEN_UNKNOWN |

---

## 2. Exemplo completo

```
scavenge gpio

law MOTION_PIN = 27
law ALARM_RADIO = 5

mission check_perimeter() -> status {
    supply detected = gpio.read(radio(MOTION_PIN))
    extract detected
}

survivor perimeter_watch {
    watch {
        checkpoint (check_perimeter()) {
            broadcast(radio(ALARM_RADIO))
            hide(10000)
            silence(radio(ALARM_RADIO))
        } fallback {
            log_entry("area limpa, nenhum sinal")
        }
        hide(500)
    }
}

ambush intruder_alert {
    mqtt.publish("perimetro/alerta", "movimento detectado")
}
```

O Python que o compilador gera para esse programa está em
[gramatica.md](gramatica.md#3-geração-de-código), junto da correspondência
construção a construção.

---

## 3. Compilar e verificar

```
node compilador/aegisc.js programa.aeg                      # Python no terminal
node compilador/aegisc.js programa.aeg | python3            # compila e roda no PC
node compilador/aegisc.js programa.aeg --alvo esp32 -o main.py   # MicroPython para o ESP32
```

O **alvo** escolhe só o runtime embutido no topo do Python gerado. O programa
traduzido é o mesmo:

- `simulado` (padrão): roda com Python comum. Os sensores devolvem valores
  fixos, e o hardware imprime o que faria (`[oled] ...`, `[mqtt] ...`).
- `esp32`: usa `machine`, `dht`, `network` e `umqtt` do MicroPython.

Erros saem no formato `arquivo:linha:coluna: erro <fase>: mensagem`, com código
de saída 1.

```
cd compilador
node testes.js        # 80 testes das três fases e dos dois alvos
```

Para inspecionar visualmente cada fase, abra `compilador/index.html` no
navegador: as abas mostram a tabela de tokens, a AST desenhada em texto, o
Python gerado e os erros com linha e coluna.

Um programa completo, o firmware do abrigo, está em `firmware/abrigo.aeg`. Os
cenários que testam esse firmware estão em `firmware/cenarios.py`, e o guia de
montagem em [hardware.md](hardware.md).
