# Apresentação técnica do AEGIS

19 slides animados que contam o projeto inteiro: a linguagem, as três fases do
compilador, o firmware do abrigo, o simulador Wokwi e o protótipo físico.

**Para apresentar:** abra https://claude.ai/artifact/RL5g9Koejv1eXDPppxbWfD e use o
modo **Apresentar**. As animações (elementos entrando por clique, a transição entre as
fases do compilador e o lexer tokenizando uma linha ao vivo) só rodam nesse modo. Cada
slide tem notas do apresentador com o que falar. A página é privada: para outras pessoas
abrirem, compartilhe pelo menu Share. De lá também dá para exportar em PDF ou PPTX.

## Arquivos

| Arquivo | O que é |
|---|---|
| `deck.json` | índice: título, ordem dos slides, seções e fontes (Oswald, IBM Plex Sans, JetBrains Mono) |
| `slides/<id>.html` | um slide por arquivo, numa tela fixa de 1920×1080, com as notas no `<aside>` final |

Ordem: `cover`, `problema`, `visao`, `linguagem`, `lexico`, `sintatico`, `panico`,
`gerador`, `testes`, `firmware`, `estados`, `sensores`, `wokwi`, `interfaces`, `pinos`,
`fisico`, `demo`, `conclusao`, `fim`.

## Imagens

Os slides apontam para cópias das figuras do próprio repositório, guardadas na página
publicada (`/_blob/<id>`). Fora da página, essas imagens não carregam; o original de
cada uma está aqui:

| `/_blob/…` | Arquivo no repositório |
|---|---|
| `53923db9…` | `docs/marca/logo-bot.png` |
| `7c81c7d2…` | `artigo/figuras/wokwi.png` |
| `a757418e…` | `artigo/figuras/telas-oled.png` |
| `37cfbe78…` | `artigo/figuras/painel-celular.png` |

## De onde vêm os números

Tudo foi conferido no código em 09/11/2026: tokens, árvore e Python da linha de exemplo
saem do `compilador/aegisc.js`; as duas mensagens do modo pânico são a saída real para o
arquivo do slide 7; 84/84 testes (`node compilador/testes.js`) e 42/42 cenários
(`python3 firmware/cenarios.py`); pinos, custos e cuidados elétricos de
`docs/hardware.md`; dados do problema de `docs/ESTADO-DO-PROJETO.md` e do artigo
(IBGE + Cemaden, S2iD/MIDR).
