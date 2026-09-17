# Estado do projeto

Documento de continuidade: registra o que está pronto, o que falta e as decisões
já tomadas. Serve para retomar o trabalho sem precisar reconstruir o contexto.

Última atualização: 17/09/2026

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
| `compilador/gerador.js` | Fase 3 — back-end que emite Python (**pendente**) |
| `compilador/compilador.js` | Orquestrador das fases e exemplos da linguagem |
| `compilador/testes.js` | Suíte de testes (roda com `node testes.js`) |
| `compilador/index.html` | Interface web que mostra cada fase |
| `docs/` | Documentação da linguagem |
| `pitch/` | Apresentação animada em Manim (**a mover para cá**) |

O pitch ainda está em `C:\Users\yagod\OneDrive\Desktop\Apresentacao-Comp` e será
movido para `pitch/` dentro deste repositório.

---

## Situação atual

### Pronto

- **Análise léxica** — 29 palavras reservadas em 7 categorias, 25 símbolos,
  literais inteiros/decimais/textuais/booleanos, maximal munch com regex sticky,
  rastreio de linha e coluna, e coleta de erros sem interromper a análise.
- **Análise sintática** — descendente recursivo, uma função por regra, gramática
  publicada em `GRAMATICA_EBNF`, AST com 26 tipos de nó, precedência codificada
  na cadeia de chamadas e recuperação em modo pânico.
- **Testes** — 53 casos, todos passando.
- **Interface web** — mostra tokens, AST, Python e erros.
- **Pitch** — 10 cenas animadas prontas e renderizadas em 1080p, exportadas para
  um `pitch.html` autocontido.

### Pendente

1. **`compilador/gerador.js`** — é o "back-end funcionando" exigido. O
   `compilador.js` já o procura e cai num fallback quando não o encontra, então
   basta criar o módulo exportando `gerarCodigo(ast)` que devolva
   `{ corpo, mapa }`, onde `corpo` é o Python e `mapa` liga linha gerada a linha
   de origem.
2. **Documentação em `docs/`** — especificação da linguagem com a tabela de
   tokens, a gramática e a descrição da AST.
3. **Mover o pitch para `pitch/`** neste repositório.
4. **Corrigir a cena 5 do pitch** — ela mostra código em português da linguagem
   BNKR antiga. Deve mostrar a linguagem real, usando o exemplo da sentinela de
   perímetro que está em `compilador/compilador.js`.

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
# testes do compilador
cd compilador
node testes.js

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
