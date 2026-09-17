// FASE 2 — Análise sintática da linguagem BNKR.
// Descendente recursivo, uma função por regra da gramática (mapeamento 1:1
// com a EBNF abaixo). Constrói a AST e reporta erros em modo pânico
// (sincronizar() nos limites de declaração) para acusar vários erros de
// uma vez, igual ao léxico faz.

// -----------------------------------------------------------------------
// Gramática (EBNF). Publicada como const para virar documentação (README /
// docs/gramatica.md colam isto direto).
//
// Decisões de projeto registradas aqui porque não são óbvias lendo o código:
//
// 1) "palavra_chamavel": broadcast/silence/hide/log_entry e os nomes de tipo
//    primitivo (ration, vital, status, paper, radio, silent) são palavras
//    RESERVADAS no léxico (não identificadores) mas os exemplos de
//    referência as usam como alvo de chamada — `broadcast(radio(PIN))`,
//    `hide(500)`. O parser as trata como "identificadores contextuais":
//    em `primario` elas produzem o mesmo nó que um IDENT produziria. Fora
//    de posição de expressão elas continuam reservadas (não dá pra usar
//    `supply hide = 1`, por exemplo).
//
// 2) "separador": a linguagem é delimitada por chaves, não por indentação
//    — igual C. NOVA_LINHA e ";" são intercambiáveis como terminador de
//    declaração/comando; um bloco pode ter qualquer quantidade de um ou
//    outro entre itens. Isso é o análogo desta gramática ao "fim_linha"
//    do plano original em Python.
//
// 3) "cmd_checkpoint" com "fallback": `Checkpoint.outros` guarda OU outro
//    nó Checkpoint (encadeamento `fallback checkpoint`, tipo elif) OU um
//    array de comandos (bloco `fallback` final, tipo else) OU null. Mesma
//    ideia do `Se.senao` do plano original — deixa o gerador emitir
//    `elif`/`else` sem heurística nenhuma.
//
// 4) Único ponto de lookahead(2): distinguir `cmd_atribuicao` (IDENT "="
//    expressao) de `cmd_expressao` (uma chamada solta, tipo `hide(500)`)
//    exige olhar se o token após o IDENT é ASSIGN. Fora isso a gramática
//    é LL(1).
// -----------------------------------------------------------------------
const GRAMATICA_EBNF = `
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
`.trim();

// tipos de token que abrem uma declaração no nível de bloco/programa
const INICIO_DECLARACAO = new Set([
  "TOKEN_IMPORT", "TOKEN_LET", "TOKEN_CONST", "TOKEN_ARRAY", "TOKEN_STRUCT",
  "TOKEN_FUNC", "TOKEN_TASK", "TOKEN_EVENT", "TOKEN_MAIN",
  "TOKEN_IF", "TOKEN_LOOP", "TOKEN_FOR", "TOKEN_TRY", "TOKEN_ERROR_TYPE", "TOKEN_RETURN"
]);

const TIPOS_PRIMITIVOS = new Set([
  "TOKEN_TYPE_INT", "TOKEN_TYPE_FLOAT", "TOKEN_TYPE_BOOL",
  "TOKEN_TYPE_STRING", "TOKEN_TYPE_PIN", "TOKEN_TYPE_VOID"
]);

// palavras reservadas que também funcionam como átomo de expressão (ver
// nota de projeto (1) acima da gramática)
const PALAVRA_CHAMAVEL = new Set([
  "TOKEN_GPIO_HIGH", "TOKEN_GPIO_LOW", "TOKEN_DELAY", "TOKEN_PRINT",
  ...TIPOS_PRIMITIVOS
]);

class ErroSintatico extends Error {}

// mensagem de erro legível para um token — os tokens de controle (nova
// linha, fim de arquivo) não têm um lexema apresentável ("\n" ou "")
function descreverToken(t) {
  if (t.tipo === "TOKEN_NEWLINE") return "o fim da linha";
  if (t.tipo === "TOKEN_EOF") return "o fim do arquivo";
  return `'${t.lexema}'`;
}

function analisarSintatico(tokens) {
  const erros = [];
  let pos = 0;

  // --------------------------- núcleo do parser -------------------------
  function atual() { return tokens[pos]; }
  function verificar(...tiposAlvo) { return tiposAlvo.includes(atual().tipo); }
  function verificarProximo(...tiposAlvo) {
    const prox = tokens[pos + 1];
    return prox !== undefined && tiposAlvo.includes(prox.tipo);
  }
  function avancar() { const t = atual(); if (t.tipo !== "TOKEN_EOF") pos++; return t; }

  function erro(token, msg) {
    erros.push({ linha: token.linha, coluna: token.coluna, msg });
    return new ErroSintatico(msg);
  }

  function consumir(tipo, msg) {
    if (verificar(tipo)) return avancar();
    throw erro(atual(), msg);
  }

  // consome 1+ separadores (nova linha e/ou ";"). Um "}" ou o fim do
  // arquivo também fecham o comando implicitamente (não faz sentido exigir
  // nova linha entre o último comando de um bloco e o "}" que o fecha, ou
  // no fim do arquivo). opcional=true além disso tolera declaração seguinte
  // colada sem separador nenhum (usado depois de blocos com chave própria,
  // onde a chave de fechamento já deixou a intenção clara).
  function separador(opcional) {
    if (verificar("TOKEN_NEWLINE", "SEMI")) {
      while (verificar("TOKEN_NEWLINE", "SEMI")) avancar();
      return;
    }
    if (verificar("RBRACE", "TOKEN_EOF")) return;
    if (opcional) return;
    throw erro(atual(), "esperava fim de linha (nova linha ou ';') aqui");
  }

  function pularSeparadoresOpcionais() {
    while (verificar("TOKEN_NEWLINE", "SEMI")) avancar();
  }

  // sincroniza em modo pânico: descarta tokens até o próximo separador de
  // comando (consome-o e para) ou até um "}" / início de declaração /
  // EOF (para sem consumir), para poder reportar mais de um erro por
  // compilação. Parar em QUALQUER separador — não só antes de uma
  // palavra-chave de declaração — importa porque um comando quebrado pode
  // ser seguido por outro comando comum (ex.: uma chamada solta como
  // "hide(1)"), que não começa com palavra reservada nenhuma.
  function sincronizar() {
    while (!verificar("TOKEN_EOF")) {
      if (verificar("TOKEN_NEWLINE", "SEMI")) { avancar(); return; }
      if (verificar("RBRACE") || INICIO_DECLARACAO.has(atual().tipo)) return;
      avancar();
    }
  }

  function no(tipo, campos, origem) {
    return { tipo, linha: origem.linha, coluna: origem.coluna, ...campos };
  }

  // ------------------------------ programa -------------------------------
  function programa() {
    const inicio = atual();
    pularSeparadoresOpcionais();
    const declaracoes = [];
    while (!verificar("TOKEN_EOF")) {
      try {
        declaracoes.push(declaracao());
      } catch (e) {
        if (!(e instanceof ErroSintatico)) throw e;
        sincronizar();
      }
      pularSeparadoresOpcionais();
    }
    return no("Programa", { declaracoes }, inicio);
  }

  function declaracao() {
    switch (atual().tipo) {
      case "TOKEN_IMPORT": return declScavenge();
      case "TOKEN_LET": case "TOKEN_CONST": case "TOKEN_ARRAY": return declVariavel();
      case "TOKEN_STRUCT": return declEstrutura();
      case "TOKEN_FUNC": return declFuncao();
      case "TOKEN_TASK": return declTask();
      case "TOKEN_EVENT": return declEvento();
      case "TOKEN_MAIN": return declPrincipal();
      default: return comando();
    }
  }

  // --------------------------- declarações --------------------------------
  function declScavenge() {
    const t = avancar(); // scavenge
    const nomeTok = consumir("TOKEN_IDENTIFIER", "esperava o nome do módulo depois de 'scavenge'");
    separador(false);
    return no("Scavenge", { modulo: nomeTok.lexema }, t);
  }

  const CATEGORIA_POR_TIPO = { TOKEN_LET: "supply", TOKEN_CONST: "law", TOKEN_ARRAY: "stash" };

  function declVariavel() {
    const t = avancar(); // supply | law | stash
    const categoria = CATEGORIA_POR_TIPO[t.tipo];
    const nomeTok = consumir("TOKEN_IDENTIFIER", `esperava um nome depois de '${t.lexema}'`);
    consumir("ASSIGN", `esperava '=' depois de '${nomeTok.lexema}'`);
    const valor = expressao();
    separador(false);
    return no("DeclaracaoVariavel", { categoria, nome: nomeTok.lexema, valor }, t);
  }

  function declEstrutura() {
    const t = avancar(); // cache
    const nomeTok = consumir("TOKEN_IDENTIFIER", "esperava o nome da estrutura depois de 'cache'");
    consumir("LBRACE", `esperava '{' depois de 'cache ${nomeTok.lexema}'`);
    pularSeparadoresOpcionais();
    const campos = [];
    while (!verificar("RBRACE", "TOKEN_EOF")) {
      campos.push(campo());
      pularSeparadoresOpcionais();
    }
    consumir("RBRACE", "esperava '}' para fechar a estrutura '" + nomeTok.lexema + "'");
    separador(true);
    return no("Estrutura", { nome: nomeTok.lexema, campos }, t);
  }

  function campo() {
    const tipoTok = tipo();
    const nomeTok = consumir("TOKEN_IDENTIFIER", "esperava o nome do campo depois do tipo");
    separador(true);
    return { tipoDado: tipoTok, nome: nomeTok.lexema, linha: nomeTok.linha, coluna: nomeTok.coluna };
  }

  function tipo() {
    if (verificar("TOKEN_IDENTIFIER") || TIPOS_PRIMITIVOS.has(atual().tipo)) {
      return avancar().lexema;
    }
    throw erro(atual(), "esperava um tipo (ration, vital, status, paper, radio, silent ou um nome de estrutura)");
  }

  function declFuncao() {
    const t = avancar(); // mission
    const nomeTok = consumir("TOKEN_IDENTIFIER", "esperava o nome da missão depois de 'mission'");
    consumir("LPAREN", `esperava '(' depois de 'mission ${nomeTok.lexema}'`);
    const parametros = verificar("RPAREN") ? [] : parametros_();
    consumir("RPAREN", "esperava ')' para fechar os parâmetros");
    let tipoRetorno = null;
    if (verificar("ARROW")) { avancar(); tipoRetorno = tipo(); }
    const corpo = blocoChaves();
    separador(true);
    return no("Funcao", { nome: nomeTok.lexema, parametros, tipoRetorno, corpo }, t);
  }

  function parametros_() {
    const lista = [parametro()];
    while (verificar("COMMA")) { avancar(); lista.push(parametro()); }
    return lista;
  }

  function parametro() {
    const tipoTok = tipo();
    const nomeTok = consumir("TOKEN_IDENTIFIER", "esperava o nome do parâmetro depois do tipo");
    return { tipoDado: tipoTok, nome: nomeTok.lexema, linha: nomeTok.linha, coluna: nomeTok.coluna };
  }

  function declTask() {
    const t = avancar(); // survivor
    const nomeTok = consumir("TOKEN_IDENTIFIER", "esperava o nome depois de 'survivor'");
    const corpo = blocoChaves();
    separador(true);
    return no("Task", { nome: nomeTok.lexema, corpo }, t);
  }

  function declEvento() {
    const t = avancar(); // ambush
    const nomeTok = consumir("TOKEN_IDENTIFIER", "esperava o nome depois de 'ambush'");
    const corpo = blocoChaves();
    separador(true);
    return no("Evento", { nome: nomeTok.lexema, corpo }, t);
  }

  function declPrincipal() {
    const t = avancar(); // chronicle
    const nome = verificar("TOKEN_IDENTIFIER") ? avancar().lexema : null;
    const corpo = blocoChaves();
    separador(true);
    return no("Principal", { nome, corpo }, t);
  }

  function blocoChaves() {
    consumir("LBRACE", "esperava '{' para abrir o bloco");
    pularSeparadoresOpcionais();
    const declaracoes = [];
    while (!verificar("RBRACE", "TOKEN_EOF")) {
      try {
        declaracoes.push(declaracao());
      } catch (e) {
        if (!(e instanceof ErroSintatico)) throw e;
        sincronizar();
      }
      pularSeparadoresOpcionais();
    }
    consumir("RBRACE", "esperava '}' para fechar o bloco");
    return declaracoes;
  }

  // ------------------------------ comandos ---------------------------------
  function comando() {
    switch (atual().tipo) {
      case "TOKEN_IF": { const c = cmdCheckpointInterno(); separador(true); return c; }
      case "TOKEN_LOOP": return cmdWatch();
      case "TOKEN_FOR": return cmdPatrol();
      case "TOKEN_TRY": return cmdQuarantine();
      case "TOKEN_ERROR_TYPE": return cmdOutbreak();
      case "TOKEN_RETURN": return cmdExtract();
      default:
        if (verificar("TOKEN_IDENTIFIER") && verificarProximo("ASSIGN")) return cmdAtribuicao();
        return cmdExpressao();
    }
  }

  // não consome o separador final: quem chama decide (permite encadear
  // "fallback checkpoint" sem exigir fim de linha entre os dois)
  function cmdCheckpointInterno() {
    const t = avancar(); // checkpoint
    consumir("LPAREN", "esperava '(' depois de 'checkpoint'");
    const condicao = expressao();
    consumir("RPAREN", "esperava ')' para fechar a condição");
    const entaoBloco = blocoChaves();
    let outros = null;
    if (verificar("TOKEN_ELSE")) {
      avancar(); // fallback
      outros = verificar("TOKEN_IF") ? cmdCheckpointInterno() : blocoChaves();
    }
    return no("Checkpoint", { condicao, entao: entaoBloco, outros }, t);
  }

  function cmdWatch() {
    const t = avancar(); // watch
    const corpo = blocoChaves();
    separador(true);
    return no("Watch", { corpo }, t);
  }

  function cmdPatrol() {
    const t = avancar(); // patrol
    consumir("LPAREN", "esperava '(' depois de 'patrol'");
    const vezes = expressao();
    consumir("RPAREN", "esperava ')' para fechar 'patrol'");
    const corpo = blocoChaves();
    separador(true);
    return no("Patrol", { vezes, corpo }, t);
  }

  function cmdQuarantine() {
    const t = avancar(); // quarantine
    const tentativa = blocoChaves();
    consumir("TOKEN_CATCH", "esperava 'catch' depois do bloco 'quarantine'");
    consumir("LPAREN", "esperava '(' depois de 'catch'");
    const nomeErroTok = consumir("TOKEN_IDENTIFIER", "esperava o nome do erro capturado");
    consumir("RPAREN", "esperava ')' depois do nome do erro");
    const captura = blocoChaves();
    separador(true);
    return no("Quarantine", { tentativa, nomeErro: nomeErroTok.lexema, captura }, t);
  }

  function cmdOutbreak() {
    const t = avancar(); // outbreak
    const expr = expressao();
    separador(false);
    return no("Outbreak", { expressao: expr }, t);
  }

  function cmdExtract() {
    const t = avancar(); // extract
    const semExpressao = verificar("TOKEN_NEWLINE", "SEMI", "RBRACE", "TOKEN_EOF");
    const expr = semExpressao ? null : expressao();
    separador(semExpressao);
    return no("Extract", { expressao: expr }, t);
  }

  function cmdAtribuicao() {
    const nomeTok = avancar();
    consumir("ASSIGN", "esperava '=' depois do identificador");
    const valor = expressao();
    separador(false);
    return no("Atribuicao", { nome: nomeTok.lexema, valor }, nomeTok);
  }

  function cmdExpressao() {
    const t = atual();
    const expr = expressao();
    separador(false);
    return no("ExpressaoStmt", { expressao: expr }, t);
  }

  // ----------------------------- expressões --------------------------------
  function expressao() { return ou(); }

  function ou() {
    let esquerda = e();
    while (verificar("OR")) {
      const op = avancar();
      esquerda = no("Logica", { operador: "||", esquerda, direita: e() }, op);
    }
    return esquerda;
  }

  function e() {
    let esquerda = igualdade();
    while (verificar("AND")) {
      const op = avancar();
      esquerda = no("Logica", { operador: "&&", esquerda, direita: igualdade() }, op);
    }
    return esquerda;
  }

  function igualdade() {
    let esquerda = comparacao();
    while (verificar("EQ", "NEQ")) {
      const op = avancar();
      esquerda = no("Binaria", { operador: op.lexema, esquerda, direita: comparacao() }, op);
    }
    return esquerda;
  }

  function comparacao() {
    let esquerda = adicao();
    while (verificar("LT", "GT", "LE", "GE")) {
      const op = avancar();
      esquerda = no("Binaria", { operador: op.lexema, esquerda, direita: adicao() }, op);
    }
    return esquerda;
  }

  function adicao() {
    let esquerda = multiplicacao();
    while (verificar("PLUS", "MINUS")) {
      const op = avancar();
      esquerda = no("Binaria", { operador: op.lexema, esquerda, direita: multiplicacao() }, op);
    }
    return esquerda;
  }

  function multiplicacao() {
    let esquerda = unario();
    while (verificar("STAR", "SLASH")) {
      const op = avancar();
      esquerda = no("Binaria", { operador: op.lexema, esquerda, direita: unario() }, op);
    }
    return esquerda;
  }

  function unario() {
    if (verificar("NOT", "MINUS")) {
      const op = avancar();
      return no("Unaria", { operador: op.lexema, operando: unario() }, op);
    }
    return chamada();
  }

  function chamada() {
    let expr = primario();
    for (;;) {
      if (verificar("LPAREN")) {
        const t = avancar();
        const argumentos = verificar("RPAREN") ? [] : argumentos_();
        consumir("RPAREN", "esperava ')' para fechar a chamada");
        expr = no("Chamada", { alvo: expr, argumentos }, t);
      } else if (verificar("DOT")) {
        const t = avancar();
        const nomeTok = consumir("TOKEN_IDENTIFIER", "esperava um nome depois de '.'");
        expr = no("Membro", { objeto: expr, nome: nomeTok.lexema }, t);
      } else if (verificar("LBRACKET")) {
        const t = avancar();
        const indice = expressao();
        consumir("RBRACKET", "esperava ']' para fechar o índice");
        expr = no("Indice", { alvo: expr, indice }, t);
      } else {
        break;
      }
    }
    return expr;
  }

  function argumentos_() {
    const lista = [expressao()];
    while (verificar("COMMA")) { avancar(); lista.push(expressao()); }
    return lista;
  }

  function primario() {
    const t = atual();
    if (verificar("TOKEN_INT_LIT", "TOKEN_FLOAT_LIT")) {
      avancar();
      return no("Literal", { valor: t.valor, tipoLiteral: t.tipo === "TOKEN_INT_LIT" ? "ration" : "vital" }, t);
    }
    if (verificar("TOKEN_STRING_LIT")) {
      avancar();
      return no("Literal", { valor: t.valor, tipoLiteral: "paper" }, t);
    }
    if (verificar("TOKEN_BOOL_LIT")) {
      avancar();
      return no("Literal", { valor: t.valor, tipoLiteral: "status" }, t);
    }
    if (verificar("TOKEN_IDENTIFIER") || PALAVRA_CHAMAVEL.has(t.tipo)) {
      avancar();
      return no("Identificador", { nome: t.lexema }, t);
    }
    if (verificar("LBRACKET")) {
      avancar();
      const elementos = verificar("RBRACKET") ? [] : argumentos_();
      consumir("RBRACKET", "esperava ']' para fechar a lista");
      return no("ListaLiteral", { elementos }, t);
    }
    if (verificar("LPAREN")) {
      avancar();
      const expr = expressao();
      consumir("RPAREN", "esperava ')' para fechar a expressão");
      return no("Agrupamento", { expressao: expr }, t);
    }
    throw erro(t, `esperava uma expressão, encontrei ${descreverToken(t)}`);
  }

  const ast = programa();
  return { ast, erros };
}

// ---------------------------------------------------------------------
// Formata qualquer nó da AST como árvore de texto com caracteres de caixa
// e arestas nomeadas (ex.: "condicao:", "entao[0]:"). Genérico: não
// conhece os tipos de nó, só segue as chaves do objeto — então cobre
// qualquer nó novo sem precisar de um caso por tipo.
// ---------------------------------------------------------------------
function ehNo(valor) {
  return valor !== null && typeof valor === "object" && typeof valor.tipo === "string" && !Array.isArray(valor);
}

function formatarArvore(no, prefixo = "", raiz = true) {
  if (no === null || no === undefined) return (raiz ? "" : prefixo) + String(no) + "\n";

  const rotulo = ehNo(no) ? `${no.tipo} (${no.linha}:${no.coluna})` : String(no);
  let saida = (raiz ? "" : prefixo) + rotulo + "\n";

  if (!ehNo(no)) return saida;

  const chaves = Object.keys(no).filter(k => !["tipo", "linha", "coluna"].includes(k));
  const filhos = [];
  for (const chave of chaves) {
    const valor = no[chave];
    if (Array.isArray(valor)) {
      if (valor.length === 0) { filhos.push({ rotulo: `${chave}: []`, valor: null }); continue; }
      valor.forEach((item, i) => filhos.push({ rotulo: `${chave}[${i}]:`, valor: item }));
    } else if (ehNo(valor)) {
      filhos.push({ rotulo: `${chave}:`, valor });
    } else if (valor !== null && typeof valor === "object") {
      filhos.push({ rotulo: `${chave}: ${JSON.stringify(valor)}`, valor: null });
    } else {
      filhos.push({ rotulo: `${chave}: ${JSON.stringify(valor)}`, valor: null });
    }
  }

  filhos.forEach((filho, i) => {
    const ultimo = i === filhos.length - 1;
    const ramo = ultimo ? "└─ " : "├─ ";
    const continuacao = ultimo ? "   " : "│  ";
    if (filho.valor === null) {
      saida += prefixo + ramo + filho.rotulo + "\n";
    } else {
      saida += prefixo + ramo + filho.rotulo + " " + formatarArvore(filho.valor, prefixo + continuacao, false).slice((prefixo + continuacao).length);
    }
  });

  return saida;
}

if (typeof module !== "undefined") {
  module.exports = {
    analisarSintatico,
    formatarArvore,
    GRAMATICA_EBNF,
    INICIO_DECLARACAO,
    TIPOS_PRIMITIVOS,
    PALAVRA_CHAMAVEL
  };
}
