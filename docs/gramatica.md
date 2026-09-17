# Gramática, AST e geração de código

Documenta as fases 2 e 3 do compilador. A fase 1 está em
[linguagem.md](linguagem.md).

---

## 1. Gramática

O analisador é **descendente recursivo**, com uma função por regra: a EBNF
abaixo e o código de `parser.js` têm correspondência direta. A gramática vive
na constante `GRAMATICA_EBNF` dentro do próprio parser, de modo que
documentação e implementação não possam divergir.

A gramática é **LL(1)**, com um único ponto de `lookahead(2)`: distinguir uma
atribuição (`IDENT "=" expressao`) de uma chamada solta (`hide(500)`) exige
olhar se o token seguinte ao identificador é `=`.

```ebnf
programa        = { separador } , { declaracao } , FIM_ARQUIVO ;
declaracao      = decl_scavenge | decl_variavel | decl_estrutura
                 | decl_funcao | decl_task | decl_evento | decl_principal
                 | comando ;

decl_scavenge   = "scavenge" , IDENT , separador ;
decl_variavel   = ( "supply" | "law" | "stash" ) , IDENT , "=" , expressao , separador ;
decl_estrutura  = "cache" , IDENT , "{" , { separador } , { campo } , "}" , separador ;
campo           = tipo , IDENT , separador ;
decl_funcao     = "mission" , IDENT , "(" , [ parametros ] , ")" , [ "->" , tipo ] ,
                   bloco_chaves , separador ;
parametros      = parametro , { "," , parametro } ;
parametro       = tipo , IDENT ;
decl_task       = "survivor" , IDENT , bloco_chaves , separador ;
decl_evento     = "ambush" , IDENT , bloco_chaves , separador ;
decl_principal  = "chronicle" , [ IDENT ] , bloco_chaves , separador ;

tipo            = "ration" | "vital" | "status" | "paper" | "radio" | "silent" | IDENT ;

bloco_chaves    = "{" , { separador } , { declaracao } , "}" ;
separador       = ( NOVA_LINHA | ";" ) , { NOVA_LINHA | ";" } ;

comando         = cmd_checkpoint | cmd_watch | cmd_patrol | cmd_quarantine
                 | cmd_outbreak | cmd_extract | cmd_atribuicao | cmd_expressao ;

cmd_checkpoint  = "checkpoint" , "(" , expressao , ")" , bloco_chaves ,
                   [ "fallback" , ( cmd_checkpoint_interno | bloco_chaves ) ] , separador ;
cmd_watch       = "watch" , bloco_chaves , separador ;
cmd_patrol      = "patrol" , "(" , expressao , ")" , bloco_chaves , separador ;
cmd_quarantine  = "quarantine" , bloco_chaves , "catch" , "(" , IDENT , ")" ,
                   bloco_chaves , separador ;
cmd_outbreak    = "outbreak" , expressao , separador ;
cmd_extract     = "extract" , [ expressao ] , separador ;
cmd_atribuicao  = IDENT , "=" , expressao , separador ;
cmd_expressao   = expressao , separador ;

(* expressões — menor para maior precedência *)
expressao       = ou ;
ou              = e , { "||" , e } ;
e               = igualdade , { "&&" , igualdade } ;
igualdade       = comparacao , { ( "==" | "!=" ) , comparacao } ;
comparacao      = adicao , { ( "<" | ">" | "<=" | ">=" ) , adicao } ;
adicao          = multiplicacao , { ( "+" | "-" ) , multiplicacao } ;
multiplicacao   = unario , { ( "*" | "/" ) , unario } ;
unario          = ( "!" | "-" ) , unario | chamada ;
chamada         = primario , { "(" , [ argumentos ] , ")" | "." , IDENT | "[" , expressao , "]" } ;
argumentos      = expressao , { "," , expressao } ;
primario        = INT_LIT | FLOAT_LIT | STRING_LIT | BOOL_LIT
                 | IDENT | palavra_chamavel
                 | "[" , [ argumentos ] , "]"
                 | "(" , expressao , ")" ;
palavra_chamavel = "broadcast" | "silence" | "hide" | "log_entry"
                  | "ration" | "vital" | "status" | "paper" | "radio" | "silent" ;
```

### Precedência de operadores

A precedência não é declarada em tabela: está codificada na **ordem da cadeia
de chamadas**, do menor para o maior nível. Cada regra só chama a de
precedência imediatamente superior.

| Nível | Operadores | Associatividade |
|---|---|---|
| 1 (menor) | `\|\|` | esquerda |
| 2 | `&&` | esquerda |
| 3 | `==` `!=` | esquerda |
| 4 | `<` `>` `<=` `>=` | esquerda |
| 5 | `+` `-` | esquerda |
| 6 | `*` `/` | esquerda |
| 7 | `!` `-` unários | direita |
| 8 (maior) | chamada, `.`, `[ ]` | esquerda |

### Três decisões de projeto

**Palavras chamáveis.** `broadcast`, `silence`, `hide`, `log_entry` e os nomes
de tipo primitivo são palavras reservadas no léxico, mas os programas de
referência as usam como alvo de chamada (`broadcast(radio(PIN))`, `hide(500)`).
O parser as trata como identificadores contextuais: em posição de expressão
produzem o mesmo nó que um identificador produziria; fora dela continuam
reservadas, então `supply hide = 1` segue sendo erro.

**Separadores intercambiáveis.** A linguagem delimita blocos por chaves, como C,
não por indentação. Nova linha e `;` são equivalentes como terminador, e um
bloco aceita qualquer quantidade de um ou de outro entre itens. Um `}` ou o fim
do arquivo também fecham um comando implicitamente.

**Encadeamento de `fallback`.** O campo `outros` de um nó `Checkpoint` guarda
ou outro `Checkpoint` (encadeamento `fallback checkpoint`, equivalente a
`elif`), ou uma lista de comandos (bloco `fallback` final, equivalente a
`else`), ou `null`. Isso deixa o gerador emitir `elif` e `else` sem precisar de
heurística nenhuma.

### Recuperação de erros

O parser usa **modo pânico**. Ao encontrar um erro, `sincronizar()` descarta
tokens até o próximo separador de comando (consome e para) ou até um `}`,
um início de declaração ou o fim do arquivo (para sem consumir). Assim uma
compilação reporta vários erros sintáticos de uma vez, e não só o primeiro.

Sincronizar em **qualquer** separador — e não apenas antes de uma palavra-chave
de declaração — importa porque um comando quebrado costuma ser seguido por
outro comando comum, como uma chamada solta, que não começa com palavra
reservada nenhuma.

---

## 2. A árvore sintática abstrata

São 26 tipos de nó. Todo nó carrega `tipo`, `linha` e `coluna`.

**Estrutura do programa**

| Nó | Campos |
|---|---|
| `Programa` | `declaracoes[]` |
| `Scavenge` | `modulo` |
| `DeclaracaoVariavel` | `categoria` (supply/law/stash), `nome`, `valor` |
| `Estrutura` | `nome`, `campos[]` |
| `Funcao` | `nome`, `parametros[]`, `tipoRetorno`, `corpo[]` |
| `Task` | `nome`, `corpo[]` |
| `Evento` | `nome`, `corpo[]` |
| `Principal` | `nome`, `corpo[]` |

**Comandos**

| Nó | Campos |
|---|---|
| `Checkpoint` | `condicao`, `entao[]`, `outros` |
| `Watch` | `corpo[]` |
| `Patrol` | `vezes`, `corpo[]` |
| `Quarantine` | `tentativa[]`, `nomeErro`, `captura[]` |
| `Outbreak` | `expressao` |
| `Extract` | `expressao` (pode ser nulo) |
| `Atribuicao` | `nome`, `valor` |
| `ExpressaoStmt` | `expressao` |

**Expressões**

| Nó | Campos |
|---|---|
| `Logica` | `operador`, `esquerda`, `direita` |
| `Binaria` | `operador`, `esquerda`, `direita` |
| `Unaria` | `operador`, `operando` |
| `Chamada` | `alvo`, `argumentos[]` |
| `Membro` | `objeto`, `nome` |
| `Indice` | `alvo`, `indice` |
| `Literal` | `valor`, `tipoLiteral` |
| `Identificador` | `nome` |
| `ListaLiteral` | `elementos[]` |
| `Agrupamento` | `expressao` |

### Exemplo

Para este fonte:

```
law ALARME = 5
checkpoint (perigo) {
  broadcast(radio(ALARME))
} fallback {
  log_entry("area limpa")
}
```

o parser produz (saída real de `formatarArvore`):

```
Programa (1:1)
├─ declaracoes[0]: DeclaracaoVariavel (1:1)
│  ├─ categoria: "law"
│  ├─ nome: "ALARME"
│  └─ valor: Literal (1:14)
│     ├─ valor: 5
│     └─ tipoLiteral: "ration"
└─ declaracoes[1]: Checkpoint (2:1)
   ├─ condicao: Identificador (2:13)
   │  └─ nome: "perigo"
   ├─ entao[0]: ExpressaoStmt (3:3)
   │  └─ expressao: Chamada (3:12)
   │     ├─ alvo: Identificador (3:3)
   │     │  └─ nome: "broadcast"
   │     └─ argumentos[0]: Chamada (3:18)
   │        ├─ alvo: Identificador (3:13)
   │        │  └─ nome: "radio"
   │        └─ argumentos[0]: Identificador (3:19)
   │           └─ nome: "ALARME"
   └─ outros[0]: ExpressaoStmt (5:3)
      └─ expressao: Chamada (5:12)
         ├─ alvo: Identificador (5:3)
         │  └─ nome: "log_entry"
         └─ argumentos[0]: Literal (5:13)
            ├─ valor: "area limpa"
            └─ tipoLiteral: "paper"
```

`formatarArvore` é genérico: não conhece os tipos de nó, apenas segue as
chaves do objeto. Um nó novo aparece na árvore sem precisar de alteração.

---

## 3. Geração de código

O gerador é um visitante recursivo por tipo de nó. Não faz otimização nem
análise semântica: confia que a AST já passou pelas fases anteriores.

### Correspondência

| AEGIS | Python |
|---|---|
| `supply x = 1` | `x = 1` |
| `law X = 1` | `X = 1  # constante` |
| `mission f(ration a) -> status { }` | `def f(a):` |
| `chronicle { }` | `def main():` + `if __name__ == "__main__":` |
| `survivor t { }` / `ambush e { }` | `def t():` com comentário de intenção |
| `cache C { vital v }` | `class C:` com `__init__(self, v=None)` |
| `checkpoint (c) { } fallback { }` | `if c:` / `else:` |
| `fallback checkpoint` encadeado | `elif` |
| `watch { }` | `while True:` |
| `patrol(n) { }` | `for _ in range(n):` |
| `quarantine { } catch (e) { }` | `try:` / `except Exception as e:` |
| `outbreak expr` | `raise Exception(expr)` |
| `extract expr` | `return expr` |
| `&&` `\|\|` `!` | `and` `or` `not` |
| `alive` / `dead` | `True` / `False` |

### Decisões do gerador

**Runtime embutido.** A linguagem tem construções de hardware (`broadcast`,
`silence`, `hide`, `radio`) e módulos (`gpio`, `mqtt` e outros) que não existem
em Python. Em vez de gerar `import` de um pacote que precisaria ser instalado,
o gerador emite um runtime simulado no topo do arquivo. O Python gerado roda
sozinho, sem dependência nenhuma.

**Blocos.** AEGIS delimita por chaves e Python por indentação; a conversão
acontece no emissor, que aplica 4 espaços por nível. Bloco vazio vira `pass`,
senão o Python sairia sintaticamente inválido.

**Mapa de linhas.** Cada linha gerada guarda de qual linha do fonte veio. É o
que permite à interface mostrar a origem de cada linha do Python.

**Preservação de tipo.** Um literal `vital` de valor redondo (`10.0`) viraria
`10` pela conversão padrão do JavaScript e chegaria ao Python como inteiro,
apagando a distinção entre `ration` e `vital`. O gerador força o ponto decimal
nesse caso.

### Exemplo

Para o fonte do exemplo acima, o gerador produz (depois do runtime):

```python
ALARME = 5  # constante
if perigo:
    broadcast(radio(ALARME))
else:
    log_entry("area limpa")
```
