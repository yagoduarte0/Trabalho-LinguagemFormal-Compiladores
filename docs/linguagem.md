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

`gpio`, `adc`, `pwm`, `wifi`, `mqtt` e `time` são convenção da biblioteca
padrão, **não** palavras reservadas. O lexer os trata como identificadores
comuns, então um programa pode tecnicamente usar esses nomes para outra coisa.

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

## 3. Como verificar

```
cd compilador
node testes.js        # 70 testes das três fases
```

Para inspecionar visualmente cada fase, abra `compilador/index.html` no
navegador: as abas mostram a tabela de tokens, a AST desenhada em texto, o
Python gerado e os erros com linha e coluna.
