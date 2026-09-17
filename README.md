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
| 3 | `compilador/gerador.js` | traduz a AST para Python com runtime embutido e mapa de linha gerada para linha de origem |

`compilador/compilador.js` encadeia as três e para na primeira que acusar erro.

### Rodar

```bash
cd compilador
node testes.js      # 70 testes
```

Para ver cada fase funcionando, abra `compilador/index.html` no navegador: as
abas mostram a tabela de tokens, a AST desenhada em texto, o Python gerado e os
erros com linha e coluna.

### Documentação

- [docs/linguagem.md](docs/linguagem.md) — especificação da linguagem e tabela de tokens
- [docs/gramatica.md](docs/gramatica.md) — gramática EBNF, AST e geração de código
- [docs/ESTADO-DO-PROJETO.md](docs/ESTADO-DO-PROJETO.md) — situação atual e decisões tomadas

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
