# AEGIS

Trabalho de Linguagens Formais e Compiladores.

**AEGIS** é uma linguagem de programação para automação de sobrevivência,
compilada para Python. Ela descreve as regras que um ESP32 executa para
monitorar um abrigo — presença, nível de água, fumaça, qualidade do ar e
temperatura — e reagir a emergências.

```
scavenge gpio

law ALARM_RADIO = 5

mission check_perimeter() -> status {
    supply detected = gpio.read(radio(27))
    extract detected
}

survivor perimeter_watch {
    watch {
        checkpoint (check_perimeter()) {
            broadcast(radio(ALARM_RADIO))
            hide(10000)
        } fallback {
            log_entry("area limpa, nenhum sinal")
        }
        hide(500)
    }
}
```

---

## O compilador

Três fases, todas implementadas:

```
fonte  ->  [análise léxica]  ->  tokens
       ->  [análise sintática]  ->  AST
       ->  [geração de código]  ->  Python
```

| Fase | Arquivo | O que faz |
|---|---|---|
| 1 | `compilador/lexer.js` | 29 palavras reservadas, 25 símbolos e literais; maximal munch, rastreio de linha e coluna, coleta de erros sem parar a análise |
| 2 | `compilador/parser.js` | descendente recursivo LL(1), gramática EBNF publicada no código, AST de 26 tipos de nó, recuperação em modo pânico |
| 3 | `compilador/gerador.js` | traduz a AST para Python com runtime embutido e mapa de linha gerada para linha de origem; dois alvos: `simulado` (PC) e `esp32` (MicroPython) |

`compilador/compilador.js` encadeia as três e para na primeira que acusar erro.
`compilador/aegisc.js` é a linha de comando.

### Rodar

```bash
node compilador/testes.js                                   # 84 testes
node compilador/aegisc.js programa.aeg | python3            # compila e roda no PC
node compilador/aegisc.js programa.aeg --alvo esp32 -o main.py
```

Para ver cada fase funcionando, abra `compilador/index.html` no navegador: as
abas mostram a tabela de tokens, a AST desenhada em texto, o Python gerado e os
erros com linha e coluna.

### Documentação

- [docs/linguagem.md](docs/linguagem.md) — especificação da linguagem e tabela de tokens
- [docs/gramatica.md](docs/gramatica.md) — gramática EBNF, AST e geração de código
- [docs/hardware.md](docs/hardware.md) — lista de compras, mapa de pinos, montagem e gravação no ESP32
- [docs/ESTADO-DO-PROJETO.md](docs/ESTADO-DO-PROJETO.md) — situação atual e decisões tomadas

---

## O firmware

`firmware/abrigo.aeg` é o programa do abrigo escrito em AEGIS. Um ESP32 lê
presença (PIR), nível da água (HC-SR04), fumaça (MQ-2), qualidade do ar
(MQ-135), temperatura (DHT22), chuva e umidade do solo (risco de
deslizamento), classifica cada leitura em NORMAL, ATENÇÃO ou ALARME e reage
com LEDs, sirene, display OLED e relé do exaustor. Se houver WiFi, serve um
painel web na rede de casa, avisa o dono por um bot do Telegram e publica por
MQTT. Uma digital arma e desarma o alarme de intruso. Funciona offline: a rede
é só um canal a mais.

```bash
python3 firmware/cenarios.py      # 41 cenários testando a lógica no PC
python3 firmware/teste_digital.py # driver do leitor de digital contra um AS608 falso
./firmware/wokwi.sh preparar      # uma vez: baixa o MicroPython e o mpremote
./firmware/wokwi.sh enviar        # com a simulação aberta no VS Code (Wokwi)
./firmware/wokwi.sh dedo          # Touch ID do Mac no lugar do leitor de digital
./firmware/wokwi.sh placa         # grava o firmware + config.json no ESP32 real
./firmware/wokwi.sh pc            # roda no Mac, eventos pelo teclado, painel em localhost:8080
python3 firmware/telegram_chat.py # configura o bot do Telegram
```

WiFi e token do bot ficam no `firmware/config.json`, fora do Git (modelo em
`firmware/config.exemplo.json`). Configuração em [docs/hardware.md](docs/hardware.md#8-rede-painel-web-e-telegram).

O circuito do Wokwi (`firmware/diagram.json`) usa as mesmas ligações da placa
real, então o `firmware/abrigo.py` gerado roda nos dois (pré-compilado para
`abrigo.mpy`, porque compilar o arquivo inteiro na placa esgota a RAM interna). A montagem física está
em [docs/hardware.md](docs/hardware.md).

---

## O pitch

`pitch/` traz a apresentação de negócio do produto, feita em
[Manim](https://www.manim.community/): dez cenas animadas cobrindo problema,
solução, mercado, modelo de negócio, plano financeiro e cronograma.

```powershell
cd pitch
.\render_all.ps1                 # rascunho rápido
.\render_all.ps1 -Qualidade h    # qualidade final e gera pitch.html
```

A apresentação é o `pitch.html`: um arquivo único e autocontido, aberto no
Chrome em tela cheia, que avança com as setas e funciona sem internet.

Requer Python 3.13 com `manim` 0.21 e `manim-slides` 5.7.
