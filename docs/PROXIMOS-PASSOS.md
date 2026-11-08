# Próximos passos: artigo e vídeo (entrega 09/11/2026)

Documento de passagem para continuar o trabalho em outra conversa. Escrito em 08/11/2026, depois
de concluir o painel web e o bot do Telegram. O contexto completo do projeto está em
[ESTADO-DO-PROJETO.md](ESTADO-DO-PROJETO.md); leia-o primeiro.

**Prazo: artigo e vídeo prontos amanhã, 09/11/2026.**

---

## Como trabalhar neste repositório

- **Commits em português, descritivos e sem nenhuma linha de coautoria de IA** (`Co-Authored-By`
  etc.). É exigência do professor.
- O Yago quer acompanhar: explicar o que vai fazer antes de cada etapa, mostrar o resultado
  depois e **commitar a cada etapa pequena**.
- Notas do Obsidian (vault `~/Study/YagoDuarte`): projeto em
  `01 Faculdade/LFC/Projeto Sobrevivência-Surto/Sobrevivência-Surto.md`; resumo do dia em
  `05 Diário/AAAA-MM-DD.md`.
- `firmware/config.json` guarda a senha do WiFi e o **token do bot**. Fica fora do Git. **Nunca**
  imprimir, commitar ou copiar o conteúdo dele.

## Estado técnico (tudo funcionando)

| Parte | Situação |
|---|---|
| Compilador (léxico, sintático, gerador) | pronto; `node compilador/testes.js` → 84/84 |
| Firmware do abrigo (`firmware/abrigo.aeg`, 810 linhas) | pronto; `python3 firmware/cenarios.py` → 41/41 |
| Wokwi | testado em 08/11: WiFi, painel em `localhost:8180` e bot funcionando |
| Painel web + bot do Telegram (@Aegis_IoT_bot) | prontos e testados no Mac e no Wokwi |
| Placa real | parcialmente montada; **ainda não recebeu o firmware novo** (`./firmware/wokwi.sh placa`, com o WiFi de casa no `config.json`) |

Comandos, configuração e problemas já resolvidos: `docs/hardware.md` (§6 gravação e memória do
ESP32, §8 rede, painel e Telegram).

---

## 1. Artigo IEEE (`artigo/artigo.tex`)

O Yago escreve no **Overleaf** (template *IEEE Conference*); o `.tex` é versionado aqui e
exportado para lá. A máquina **não tem LaTeX** (`brew install tectonic` permite compilar e conferir
localmente). Meta: cerca de 10 páginas.

### Já escrito

Resumo (falta a frase final), introdução, fundamentação teórica (3 subseções), tabela de palavras
reservadas, listagem de exemplo, diagrama das fases (TikZ), análise léxica, gramática EBNF das
expressões, tabela de tradução AEGIS → Python, parágrafo dos dois runtimes, introdução do estudo de
caso, parágrafo de testes e trabalhos futuros.

### Falta escrever (marcadores `\pendente{}`; linha aproximada no arquivo)

Combinado com o Yago: **o Claude redige, o Yago revisa seção por seção**, com um commit por seção.
Tirar cada detalhe do código, nunca de memória.

| Seção | Pendência | De onde tirar |
|---|---|---|
| Autor (l. 69–72) | curso, instituição, cidade, e-mail | **perguntar ao Yago** |
| Resumo (l. 91) | frase de conclusão | — |
| Linguagem (l. 264) | biblioteca de módulos embutidos (gpio, adc, sonar, climate, display, wifi, mqtt, finger, config, web, telegram): não são palavras reservadas e têm a mesma API nos dois alvos | `docs/linguagem.md` (tabela de módulos), `compilador/lexer.js` (`MODULOS_EMBUTIDOS`) |
| Léxico (l. 313) | quebra de linha dentro de `()`/`[]` como no Python, e a heurística que impede um parêntese esquecido de engolir o resto do programa | `compilador/lexer.js` (`parenteseEsquecido`, `INICIA_COMANDO`) |
| Sintático (l. 346) | recuperação em modo pânico: o que `sincronizar()` descarta e por que sincroniza em qualquer separador | `compilador/parser.js` (`sincronizar`, comentário acima dela) |
| Sintático (l. 349) | palavras chamáveis (`broadcast`, `hide`...) como identificadores contextuais; `fallback checkpoint` vira `elif` | `parser.js` (`PALAVRA_CHAMAVEL`, `cmdCheckpointInterno`), `gerador.js` |
| Gerador (l. 391) | emissão automática de `global`, bloco vazio vira `pass`, mapa linha gerada → linha de origem, `vital` 10 vira `10.0` | comentário no topo de `compilador/gerador.js`, `nomesGlobaisAtribuidos` |
| Firmware (l. 413) | máquina de estados NORMAL/ATENÇÃO/ALARME e a prioridade dos riscos | `firmware/abrigo.aeg` (`mission avaliar`) |
| Firmware (l. 416) | sensores MQ: média móvel, base de ar limpo adaptativa, histerese; deslizamento = chuva + solo | `abrigo.aeg` (`sentinela_fumaca`, `sentinela_solo`) e o bloco de comentários dos limites |
| Firmware (l. 419) | arme e desarme pela digital (AS608 na placa, Touch ID no Wokwi), tempos de saída e de entrada | `abrigo.aeg` (`vigia_digital`, `sentinela_presenca`), `docs/hardware.md` §6 |
| Firmware (l. 422) | canais remotos: painel servido pelo ESP32 (HTTP não bloqueante, um pedido por ciclo), bot restrito ao chat do dono, `config.json` fora do Git, nenhum canal remoto desarma; firmware pré-compilado (`.mpy`) por causa da RAM | `docs/hardware.md` §6 e §8, `compilador/gerador.js` (`RUNTIME_REDE`) |
| Resultados (l. 445) | tabela de tamanho dos módulos e testes por fase | dados abaixo |
| Resultados (l. 448) | exemplo de mensagem de erro com linha e coluna, mais de um erro por execução | dados abaixo |
| Resultados (l. 451) | custo do protótipo: R$ 235,92 a base; R$ 408,42 com OLED, biometria e sensores extras | `pitch/aegis/data.py`, `docs/hardware.md` §1 (conferir os valores) |
| Conclusão (l. 458) | retomar o objetivo e o que foi entregue | — |
| Referências (l. 488–490) | conferir IBGE 2018 (dados e link) e completar o relatório do Cemaden 2024 | `docs/ESTADO-DO-PROJETO.md` (Números do pitch) |

**Dados medidos em 08/11** (refazer se o código mudar):

- Linhas: `lexer.js` 311, `parser.js` 610, `gerador.js` 1192 (inclui o texto Python dos dois
  runtimes), `compilador.js` 129, `aegisc.js` 78, `painel.js` 93, `testes.js` 825.
- Testes por fase: léxico 30, sintático 26, gerador 28 (total 84). Firmware: 41 cenários.
- Exemplo de erro (`node compilador/aegisc.js erro.aeg` com quatro linhas quebradas):

  ```
  erro.aeg:1:17: erro sintatica: esperava uma expressão, encontrei o fim da linha
  erro.aeg:2:5: erro sintatica: esperava um nome depois de 'law'
  erro.aeg:4:1: erro sintatica: esperava ')' para fechar a chamada
  aegisc: 3 erro(s), nada foi gerado
  ```

  Fonte usado: `supply x = (1 +` / `law = 5` / `hide(10` / `log_entry("ok")`. Repare que o
  `aegisc` escreve "erro sintatica" (sem acento e com o gênero trocado); vale corrigir para
  "erro sintático" antes de usar no artigo.

### Figuras (`\figura{}`)

O Yago quer pôr imagens próprias. As que já existem estão em `docs/img/`:

| Figura | Situação |
|---|---|
| Tabela de tokens na interface web | **fazer print** da aba Tokens do `compilador/index.html` |
| AST na interface web | **fazer print** da aba AST (exemplo da sentinela de perímetro) |
| Circuito no Wokwi ou foto da montagem | **fazer print** do `firmware/diagram.json` no VS Code |
| Painel web no celular durante um alarme | pronta: `docs/img/painel-celular.png` (alvo simulado, layout real) |
| Telas do OLED | pronta: `docs/img/telas-oled.png` |

As figuras precisam subir para o Overleaf junto com o `.tex`, trocando cada `\figura{...}` por
`\includegraphics[width=\columnwidth]{...}`.

---

## 2. Vídeo de demonstração (6 min)

- **Roteiro completo, com as falas e as cenas: [video/roteiro.md](video/roteiro.md).**
- O Yago **grava** a narração (um arquivo por bloco) e as cenas (tela do Mac, tela do celular e a
  placa real). O Claude **edita**.
- Arquivos brutos em `video/narracao/` e `video/cenas/`, com os nomes do roteiro (`01.m4a`,
  `05d-celular.mp4`...); saída em `video/saida/aegis-demonstracao.mp4`. A pasta `video/` fica fora
  do Git.
- Edição: narração por cima da cena do mesmo número; cortar esperas; títulos e legendas na
  identidade visual do AEGIS; áudio normalizado. Detalhes no fim do roteiro.
- **Instalar o `ffmpeg`** (`brew install ffmpeg`); o Yago vai instalar também skills de vídeo.
- Pré-requisito para a cena 6: gravar o firmware novo na placa real (`./firmware/wokwi.sh placa`).

## Ordem sugerida para amanhã

1. Yago grava a narração (≈ 20 min) e as cenas no Wokwi, seguindo o roteiro.
2. Enquanto isso, o artigo avança seção por seção (o Yago revisa entre as gravações).
3. Placa real: gravar o firmware e filmar a cena 6.
4. Edição do vídeo com os arquivos de `video/`.
5. Figuras do artigo, revisão final e exportação para o Overleaf.
