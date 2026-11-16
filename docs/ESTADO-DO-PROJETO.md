# Estado do projeto

Documento de continuidade: registra o que está pronto, o que falta e as decisões
já tomadas. Serve para retomar o trabalho sem precisar reconstruir o contexto.

Última atualização: 16/11/2026

---

## O que é o projeto

Duas entregas que andam juntas:

1. **Estrutural (Linguagem Formal e Compiladores)** — uma linguagem de programação
   própria, com análise léxica e tabela de tokens, análise sintática e AST,
   back-end gerando Python, e o código-fonte documentado no Git.
2. **Pitch** — apresentação de negócio do produto que a linguagem serve:
   plano de negócios, pesquisa, logo, ideia, cores, cronograma e orçamento.

O produto se chama **AEGIS**: um sistema de automação de sobrevivência para
residências. Um ESP32 com sensores monitora presença, nível de água, fumaça,
qualidade do ar e temperatura, e avisa em emergências. O diferencial é que a
automação residencial comum cuida de conforto e depende da nuvem, enquanto o
AEGIS cuida de resiliência e funciona offline.

A linguagem AEGIS é o que descreve as regras de automação desse sistema. Ela tem
tema de sobrevivência: `chronicle` (principal), `mission` (função), `supply`
(variável), `law` (constante), `checkpoint`/`fallback` (condicional),
`watch` (laço), `patrol` (repetição contada), `broadcast`/`silence` (GPIO),
`log_entry` (saída), `quarantine`/`catch` (erros).

**Atenção a um ponto de confusão:** existe uma pasta separada em
`C:\Users\yagod\OneDrive\Desktop\bunker-website` com um dashboard e uma linguagem
antiga chamada BNKR, escrita em português e traduzida por expressões regulares.
**Aquilo não é a entrega do compilador.** A linguagem válida é a deste
repositório. Ficou decidido unificar tudo sob o nome AEGIS.

---

## Onde está cada coisa

| Caminho | O que é |
|---|---|
| `compilador/lexer.js` | Fase 1 — análise léxica e tabela de tokens |
| `compilador/parser.js` | Fase 2 — análise sintática, gramática EBNF e AST |
| `compilador/gerador.js` | Fase 3 — back-end que emite Python |
| `compilador/compilador.js` | Orquestrador das fases e exemplos da linguagem |
| `compilador/testes.js` | Suíte de testes (roda com `node testes.js`) |
| `compilador/aegisc.js` | Linha de comando: `.aeg` → Python, alvo `simulado` ou `esp32` |
| `compilador/index.html` | Interface web que mostra cada fase |
| `firmware/abrigo.aeg` | Firmware do abrigo escrito em AEGIS |
| `firmware/abrigo.py` | MicroPython gerado a partir do `abrigo.aeg` (entra no Git); vai para a placa pré-compilado como `abrigo.mpy` |
| `firmware/main.py`, `firmware/boot.py` | Lançador do `abrigo.mpy` e WiFi ligado antes de tudo (ver "Memória do ESP32" em `docs/hardware.md` §6) |
| `firmware/cenarios.py` | Cenários que testam a lógica do firmware no PC |
| `firmware/cadastro.aeg` | Cadastro das digitais no leitor AS608 |
| `firmware/teste_digital.py` | Testa o driver do AS608 contra um leitor falso |
| `firmware/touchid.swift` | Touch ID do Mac no lugar do AS608 durante a simulação |
| `firmware/rodar_pc.py` | Roda o firmware no Mac com eventos pelo teclado (painel em `localhost:8080`) |
| `firmware/telegram_chat.py` | Descobre o chat do dono e grava no `config.json` |
| `firmware/config.exemplo.json` | Modelo do `config.json` (WiFi, token do bot, aquecimento) |
| `compilador/painel.js` | Página do painel web, embutida pelo gerador no runtime |
| `firmware/diagram.json`, `wokwi.toml`, `wokwi.sh` | Simulação no Wokwi (VS Code) |
| `docs/` | Documentação da linguagem e do hardware |
| `pitch/` | Pitch animado em Manim (`pitch.html`) e a fala de cada cena (`ROTEIRO.md`) |

A pasta `C:\Users\yagod\OneDrive\Desktop\Apresentacao-Comp` foi a origem do
pitch e pode ser descartada: tudo que importa já está versionado aqui.

---

## Situação atual

### Pronto

- **Análise léxica** — 29 palavras reservadas em 7 categorias, 25 símbolos,
  literais inteiros/decimais/textuais/booleanos, maximal munch com regex sticky,
  rastreio de linha e coluna, e coleta de erros sem interromper a análise.
- **Análise sintática** — descendente recursivo, uma função por regra, gramática
  publicada em `GRAMATICA_EBNF`, AST com 26 tipos de nó, precedência codificada
  na cadeia de chamadas e recuperação em modo pânico.
- **Geração de código** — `gerador.js` traduz a AST para Python, com runtime
  embutido (o código gerado roda sozinho) e mapa de linha gerada para linha de
  origem. Verificado: o Python gerado dos exemplos compila e executa.
- **Dois alvos de compilação** — `simulado` (PC) e `esp32` (MicroPython), com a
  mesma API de hardware; `global` emitido automaticamente; expressões podem
  quebrar linha dentro de parênteses e colchetes.
- **Testes** — 84 casos das três fases, todos passando.
- **Firmware do abrigo** — `abrigo.aeg` com sete sensores (inclui chuva e solo,
  que juntos dão o alerta de risco de deslizamento), relé do exaustor e modo
  armado/desarmado pela digital (AS608 na placa, Touch ID do Mac no Wokwi), máquina de estados
  NORMAL/ATENÇÃO/ALARME, sirene, botão de silenciar, OLED e MQTT opcional.
  Os MQ usam média móvel, base de ar limpo adaptativa e histerese. 42 cenários
  passando no PC e circuito testado no simulador Wokwi.
- **Guia de hardware** — `docs/hardware.md` com lista de compras, mapa de
  pinos, divisores de tensão, calibração e gravação no ESP32 real.
- **Interface web** — mostra tokens, AST, Python gerado e erros, com a origem de
  cada linha do Python.
- **Documentação** — `linguagem.md` e `gramatica.md`, com tabela de tokens e
  árvore de exemplo extraídas do próprio código.
- **Pitch** — 10 cenas animadas, com a cena de arquitetura mostrando a linguagem
  real ao lado da saída verdadeira do compilador. Fala de cada cena em
  [pitch/ROTEIRO.md](../pitch/ROTEIRO.md).
- **Rede** (08/11) — painel web local servido pelo ESP32 (porta 80; no Wokwi em
  `localhost:8180`), bot do Telegram com alertas e os comandos `/status`,
  `/silenciar` e `/ajuda`, e ajustes da placa (WiFi, token, aquecimento) no
  `firmware/config.json`, fora do Git. Configuração em `docs/hardware.md` §8.
  Funciona no Mac (`./firmware/wokwi.sh pc`) e no Wokwi.
- **Protótipo físico** (15/11) — o mesmo `abrigo.aeg` rodando na NodeMCU ESP-32S
  com LEDs, buzzer, botão, OLED, DHT22, PIR, chuva e solo. Teste na bancada:
  normal → atenção → alarme de deslizamento → sirene silenciada → normal.
- **Artigo IEEE** — `artigo/artigo.tex` completo, com a seção do protótipo físico
  e as referências conferidas. Compilar com `cd artigo && tectonic -X compile artigo.tex`.
- **Vídeos** — `video/saida/aegis-completo.mp4` (14:56): a animação narrada
  (`docs/video/animacao/`) seguida do protótipo físico (`docs/video/prototipo/`).

### Pendente

1. **Ensaiar o pitch cronometrado** (10 minutos), seguindo `pitch/ROTEIRO.md`.
2. **Alimentação da placa** — pelo USB, o ESP32 não aguenta o WiFi (brownout ao
   ligar o rádio), os sensores de gás MQ-2 e MQ-135 nem o relé. Precisa de fonte
   própria (12 V com step-down). Até lá, painel e Telegram rodam no Mac
   (`./firmware/wokwi.sh pc`) e no Wokwi.
3. **HC-SR04 novo** — o atual derrubava a placa.
4. **Print do Telegram para o artigo** (opcional) — se `artigo/figuras/telegram.png`
   existir, a figura dos canais remotos mostra a conversa ao lado do painel;
   sem ele, mostra só o painel.
5. **Possível melhoria do compilador** — não há análise semântica: os tipos
   declarados (`ration`, `vital`, `status`) são registrados na AST mas não
   verificados. Se a disciplina exigir uma quarta fase, é o caminho natural.

---

## Decisões já tomadas

| Assunto | Decisão |
|---|---|
| Nome | Tudo sob a marca **AEGIS** (produto e linguagem) |
| Apresentação | 22 a 24/09/2026, 10 minutos |
| Formato do pitch | `manim-slides` exportado para HTML, aberto no Chrome em tela cheia |
| Receita do produto | Kit de hardware + assinatura mensal |
| Público | Famílias em áreas de risco de desastre e entusiastas de preparo |
| Identidade visual | Fundo `#0A0D0A`, cáqui `#C8B88A`, verde radar `#A8D04A`, creme `#EDE4CC`, fonte display Impact |
| Commits | Mensagens em português, descritivas, **sem coautoria de ferramenta de IA** (exigência do professor) |
| Arquivos pesados | `media/` e `slides/` ficam fora do Git; o `pitch.html` entra |
| Firmware | Escrito em AEGIS e compilado para MicroPython; o mesmo `.aeg` roda no PC e no ESP32 |
| Hardware | Lista do pitch + OLED SSD1306 I2C + botão; sensores analógicos só no ADC1 |
| Rede | Local primeiro; MQTT (`broker.hivemq.com`, público) só para demonstração |
| Segredos | WiFi e token do bot só no `firmware/config.json` (ignorado pelo Git); modelo em `config.exemplo.json` |
| Comandos remotos | Painel e Telegram só leem e silenciam; **desarmar exige a digital**; o bot só atende o chat do dono |
| Simulação | Wokwi no VS Code com MicroPython 1.29.0; o MQ-135 vira um potenciômetro |

---

## Números do pitch

Todos vivem em `pitch/aegis/data.py`, separados do código de animação.

**Orçamento do protótipo:** R$ 235,92 (preços de varejo reais, set/2026).
Em escala de 100 unidades o hardware cai para R$ 153,35 — esse desconto de 35%
é estimativa do padrão do setor, **não** cotação fechada, e isso está declarado
no próprio slide.

**Modelo:** custo unitário R$ 198,35, preço de venda R$ 549 (margem de 64%),
assinatura R$ 29,90/mês. Investimento inicial R$ 24.900, custo fixo R$ 3.900/mês,
ponto de equilíbrio em **12 kits por mês**.

**Dados de mercado com fonte primária:**

- 8,27 milhões de pessoas e 2,47 milhões de domicílios em áreas de risco —
  IBGE + Cemaden (cruzamento do Censo 2010, o levantamento público mais recente).
- R$ 14 bilhões no setor de segurança eletrônica em 2024, +16,1% — ABESE.
- Mais de 1.600 desastres registrados em 2024 — Cemaden. Alta de 250% frente à
  década de 1990 — S2iD/MIDR.

Não há dado público confiável sobre o tamanho do nicho "prepper" no Brasil.
Não inventar um número para essa lacuna.

---

## Como rodar

```powershell
# testes do compilador e do firmware
node compilador/testes.js
python3 firmware/cenarios.py

# interface web do compilador
# basta abrir compilador/index.html no navegador

# renderizar o pitch (rascunho rápido)
cd pitch
.\render_all.ps1

# renderizar em qualidade final e gerar o pitch.html
.\render_all.ps1 -Qualidade h
```

O pitch depende de Python 3.13 com `manim` 0.21 e `manim-slides` 5.7 instalados.
O modo `present` nativo do manim-slides não funciona nesta máquina (o PySide6
não instala por causa do limite de caminho longo do Windows), por isso a
apresentação é feita pelo `pitch.html` no Chrome.
