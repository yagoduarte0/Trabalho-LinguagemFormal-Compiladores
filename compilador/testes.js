// Suíte de testes — roda no navegador (index.html) e no Node (`node testes.js`).
// Sem dependências externas: mini-framework de asserção + coletor de resultados.

(function (global) {
  const casos = [];

  function teste(nome, fn) {
    casos.push({ nome, fn });
  }

  function afirmar(cond, msg) {
    if (!cond) throw new Error(msg || "asserção falhou");
  }

  function afirmarIgual(atual, esperado, msg) {
    const a = JSON.stringify(atual);
    const e = JSON.stringify(esperado);
    if (a !== e) {
      throw new Error(`${msg || "valores diferentes"}\n  esperado: ${e}\n  obtido:   ${a}`);
    }
  }

  function rodarTestes() {
    const resultados = [];
    for (const c of casos) {
      try {
        c.fn();
        resultados.push({ nome: c.nome, ok: true });
      } catch (e) {
        resultados.push({ nome: c.nome, ok: false, erro: e.message });
      }
    }
    const passou = resultados.filter(r => r.ok).length;
    return { total: resultados.length, passou, falhou: resultados.length - passou, resultados };
  }

  // ---------------------------------------------------------------------
  // Carrega os módulos: no Node via require, no navegador via globais
  // já carregados por <script> (window.analisarLexico etc.).
  // ---------------------------------------------------------------------
  let analisarLexico, resumoTokens, decodificarTexto, analisarSintatico, formatarArvore, gerarCodigo;
  if (typeof module !== "undefined" && typeof require === "function") {
    ({ analisarLexico, resumoTokens, decodificarTexto } = require("./lexer.js"));
    ({ analisarSintatico, formatarArvore } = require("./parser.js"));
    ({ gerarCodigo } = require("./gerador.js"));
  } else {
    ({ analisarLexico, resumoTokens, decodificarTexto } = global);
    ({ analisarSintatico, formatarArvore } = global);
    ({ gerarCodigo } = global);
  }

  // parser.js espera tokens já sem comentários (o orquestrador faz esse
  // filtro antes de chamar analisarSintatico — os testes replicam aqui)
  function analisar(fonte) {
    const { tokens, erros: errosLexicos } = analisarLexico(fonte);
    if (errosLexicos.length > 0) return { ast: null, erros: errosLexicos, fase: "lexica" };
    const relevantes = tokens.filter(t => t.categoria !== "comentario");
    const { ast, erros } = analisarSintatico(relevantes);
    return { ast, erros, fase: erros.length > 0 ? "sintatica" : "ok" };
  }

  // compila até o Python, para os testes da fase 3
  function gerarPython(fonte, opcoes) {
    const { ast, erros, fase } = analisar(fonte);
    if (fase !== "ok") throw new Error(`esperava compilar sem erros, parou em ${fase}: ${JSON.stringify(erros)}`);
    return gerarCodigo(ast, opcoes);
  }

  // o Python gerado começa sempre com o runtime; os testes olham só o
  // trecho que veio do programa do usuário
  function corpoGerado(fonte) {
    const { corpo } = gerarPython(fonte);
    const marca = "# --- fim do runtime ---";
    return corpo.slice(corpo.indexOf(marca) + marca.length).trim();
  }

  // ======================= FASE 1 — LÉXICO ==============================

  teste("lexico: reconhece palavras-chave de declaracao e identificadores", () => {
    const { tokens, erros } = analisarLexico("supply x = 10");
    afirmarIgual(erros, [], "não deveria haver erros");
    const tipos = tokens.map(t => t.tipo);
    afirmarIgual(tipos, ["TOKEN_LET", "TOKEN_IDENTIFIER", "ASSIGN", "TOKEN_INT_LIT", "TOKEN_EOF"]);
  });

  teste("lexico: identificador comum nao e confundido com palavra-chave parecida", () => {
    const { tokens } = analisarLexico("supply supplies = 1");
    afirmarIgual(tokens[1].tipo, "TOKEN_IDENTIFIER");
    afirmarIgual(tokens[1].lexema, "supplies");
  });

  teste("lexico: todas as 8 keywords de declaracao", () => {
    const { tokens } = analisarLexico("chronicle scavenge mission supply law survivor cache stash");
    const tipos = tokens.filter(t => t.categoria === "declaracao").map(t => t.tipo);
    afirmarIgual(tipos, [
      "TOKEN_MAIN", "TOKEN_IMPORT", "TOKEN_FUNC", "TOKEN_LET",
      "TOKEN_CONST", "TOKEN_TASK", "TOKEN_STRUCT", "TOKEN_ARRAY"
    ]);
  });

  teste("lexico: todos os 6 tipos primitivos", () => {
    const { tokens } = analisarLexico("ration vital status paper radio silent");
    const tipos = tokens.filter(t => t.categoria === "tipo").map(t => t.tipo);
    afirmarIgual(tipos, [
      "TOKEN_TYPE_INT", "TOKEN_TYPE_FLOAT", "TOKEN_TYPE_BOOL",
      "TOKEN_TYPE_STRING", "TOKEN_TYPE_PIN", "TOKEN_TYPE_VOID"
    ]);
  });

  teste("lexico: todas as 5 keywords de controle de fluxo", () => {
    const { tokens } = analisarLexico("watch patrol checkpoint fallback extract");
    const tipos = tokens.filter(t => t.categoria === "controle").map(t => t.tipo);
    afirmarIgual(tipos, ["TOKEN_LOOP", "TOKEN_FOR", "TOKEN_IF", "TOKEN_ELSE", "TOKEN_RETURN"]);
  });

  teste("lexico: keywords de hardware", () => {
    const { tokens } = analisarLexico("broadcast silence hide");
    const tipos = tokens.filter(t => t.categoria === "hardware").map(t => t.tipo);
    afirmarIgual(tipos, ["TOKEN_GPIO_HIGH", "TOKEN_GPIO_LOW", "TOKEN_DELAY"]);
  });

  teste("lexico: keywords de tratamento de erro", () => {
    const { tokens } = analisarLexico("outbreak quarantine catch");
    const tipos = tokens.filter(t => t.categoria === "tratamento_erro").map(t => t.tipo);
    afirmarIgual(tipos, ["TOKEN_ERROR_TYPE", "TOKEN_TRY", "TOKEN_CATCH"]);
  });

  teste("lexico: keywords de evento e E/S", () => {
    const { tokens } = analisarLexico("ambush log_entry");
    const tipos = tokens.filter(t => t.categoria === "evento_io").map(t => t.tipo);
    afirmarIgual(tipos, ["TOKEN_EVENT", "TOKEN_PRINT"]);
  });

  teste("lexico: literais booleanos alive/dead carregam o valor certo", () => {
    const { tokens } = analisarLexico("alive dead");
    afirmarIgual(tokens[0].tipo, "TOKEN_BOOL_LIT");
    afirmarIgual(tokens[0].valor, true);
    afirmarIgual(tokens[1].valor, false);
  });

  teste("lexico: nomes de modulo embutido (gpio, mqtt, ...) sao identificadores comuns", () => {
    const { tokens } = analisarLexico("gpio mqtt time");
    for (const t of tokens.slice(0, 3)) {
      afirmarIgual(t.tipo, "TOKEN_IDENTIFIER");
    }
  });

  teste("lexico: numero inteiro e decimal (decimal vence por maximal munch)", () => {
    const { tokens } = analisarLexico("27 0.0977 40.0");
    afirmarIgual(tokens[0].tipo, "TOKEN_INT_LIT");
    afirmarIgual(tokens[0].valor, 27);
    afirmarIgual(tokens[1].tipo, "TOKEN_FLOAT_LIT");
    afirmarIgual(tokens[1].valor, 0.0977);
    afirmarIgual(tokens[2].valor, 40.0);
  });

  teste("lexico: string literal com aspas duplas e escapes", () => {
    const { tokens } = analisarLexico('"area limpa, nenhum sinal"');
    afirmarIgual(tokens[0].tipo, "TOKEN_STRING_LIT");
    afirmarIgual(tokens[0].valor, "area limpa, nenhum sinal");
  });

  teste("lexico: decodificarTexto remove aspas e resolve escapes", () => {
    afirmarIgual(decodificarTexto('"a\\"b"'), 'a"b');
    afirmarIgual(decodificarTexto('"x\\ty"'), "x\ty");
  });

  teste("lexico: string sem fechar gera erro e nao trava o scanner", () => {
    const { tokens, erros } = analisarLexico('supply x = "abc\nsupply y = 1');
    afirmar(erros.length === 1, "deveria haver exatamente 1 erro");
    afirmarIgual(erros[0].msg, "aspas não fechadas");
    afirmar(tokens.some(t => t.tipo === "TOKEN_STRING_LIT_ERRO"), "token de erro deve aparecer na lista");
    afirmar(tokens.some(t => t.tipo === "TOKEN_LET" && t.linha === 2), "scanner continua após o erro");
  });

  teste("lexico: caractere desconhecido gera erro com posicao e o scanner continua", () => {
    const { tokens, erros } = analisarLexico("supply x = 1 & 2");
    afirmarIgual(erros.length, 1);
    afirmarIgual(erros[0].lexema, "&");
    afirmar(tokens.some(t => t.tipo === "TOKEN_INT_LIT" && t.valor === 2), "continua tokenizando após o erro");
  });

  teste("lexico: operadores de dois caracteres vencem sobre um caractere", () => {
    const { tokens } = analisarLexico("a == b != c <= d >= e && f || g");
    const ops = tokens.filter(t => t.categoria === "operador").map(t => t.tipo);
    afirmarIgual(ops, ["EQ", "NEQ", "LE", "GE", "AND", "OR"]);
  });

  teste("lexico: arrow (->) nao e confundido com minus (-)", () => {
    const { tokens } = analisarLexico("mission f() -> ration");
    const arrow = tokens.find(t => t.tipo === "ARROW");
    afirmar(arrow !== undefined, "deveria reconhecer ARROW");
    afirmarIgual(arrow.lexema, "->");
  });

  teste("lexico: dot (.) para acesso a membro de modulo", () => {
    const { tokens } = analisarLexico("gpio.read(1)");
    const dot = tokens.find(t => t.tipo === "DOT");
    afirmar(dot !== undefined, "deveria reconhecer DOT");
  });

  teste("lexico: delimitadores de bloco, parametro e array", () => {
    const { tokens } = analisarLexico("{ } ( ) [ ] , ; :");
    const tipos = tokens.filter(t => t.categoria === "delimitador").map(t => t.tipo);
    afirmarIgual(tipos, ["LBRACE", "RBRACE", "LPAREN", "RPAREN", "LBRACKET", "RBRACKET", "COMMA", "SEMI", "COLON"]);
  });

  teste("lexico: comentario de linha // e reconhecido e nao vira SLASH+SLASH", () => {
    const { tokens } = analisarLexico("supply x = 1 // comentario aqui");
    const comentarios = tokens.filter(t => t.tipo === "TOKEN_COMMENT");
    afirmarIgual(comentarios.length, 1);
    afirmarIgual(comentarios[0].lexema, "// comentario aqui");
  });

  teste("lexico: comentario de bloco /* */ multi-linha e reconhece a linha seguinte corretamente", () => {
    const { tokens } = analisarLexico("supply x = 1 /* bloco\nmulti\nlinha */ supply y = 2");
    const comentario = tokens.find(t => t.tipo === "TOKEN_COMMENT");
    afirmar(comentario !== undefined);
    const segundoLet = tokens.filter(t => t.tipo === "TOKEN_LET")[1];
    afirmarIgual(segundoLet.linha, 3);
  });

  teste("lexico: comentario de bloco nao fechado gera erro", () => {
    const { erros } = analisarLexico("supply x = 1 /* nunca fecha");
    afirmarIgual(erros.length, 1);
    afirmarIgual(erros[0].msg, "comentário de bloco não fechado");
  });

  teste("lexico: divisao (/) nao e confundida com comentario", () => {
    const { tokens, erros } = analisarLexico("supply x = 10 / 2");
    afirmarIgual(erros, []);
    const slash = tokens.find(t => t.tipo === "SLASH");
    afirmar(slash !== undefined, "deveria reconhecer SLASH como divisao");
  });

  teste("lexico: espacos e tabs sao ignorados (nao viram token)", () => {
    const { tokens } = analisarLexico("  supply   x   =   1  ");
    afirmar(!tokens.some(t => t.tipo === "ESPACO"), "ESPACO nunca deve aparecer na lista");
  });

  teste("lexico: nova linha vira token proprio e reinicia a coluna", () => {
    const { tokens } = analisarLexico("supply x = 1\nsupply y = 2");
    const quebra = tokens.find(t => t.tipo === "TOKEN_NEWLINE");
    afirmar(quebra !== undefined, "deve haver um token TOKEN_NEWLINE");
    const segundoLet = tokens.filter(t => t.tipo === "TOKEN_LET")[1];
    afirmarIgual(segundoLet.linha, 2);
    afirmarIgual(segundoLet.coluna, 1);
  });

  teste("lexico: sempre termina com TOKEN_EOF", () => {
    const { tokens } = analisarLexico("");
    afirmarIgual(tokens.length, 1);
    afirmarIgual(tokens[0].tipo, "TOKEN_EOF");
  });

  teste("lexico: resumoTokens conta por categoria", () => {
    const { tokens } = analisarLexico("supply x = 1 + 2");
    const resumo = resumoTokens(tokens);
    afirmarIgual(resumo.declaracao, 1);
    afirmarIgual(resumo.identificador, 1);
    afirmarIgual(resumo.operador, 2);
    afirmarIgual(resumo.literal, 2);
    afirmarIgual(resumo.estrutura, 1);
  });

  teste("lexico: programa de referencia completo tokeniza sem erros", () => {
    const fonte = [
      "scavenge gpio",
      "",
      "law MOTION_PIN = 27",
      "law ALARM_RADIO = 5",
      "",
      "mission check_perimeter() -> status {",
      "    supply detected = gpio.read(radio(MOTION_PIN))",
      "    extract detected",
      "}",
      "",
      "survivor perimeter_watch {",
      "    watch {",
      "        checkpoint (check_perimeter()) {",
      "            broadcast(radio(ALARM_RADIO))",
      "            hide(10000)",
      "            silence(radio(ALARM_RADIO))",
      "        } fallback {",
      '            log_entry("area limpa, nenhum sinal")',
      "        }",
      "        hide(500)",
      "    }",
      "}",
      "",
      "ambush intruder_alert {",
      '    mqtt.publish("perimetro/alerta", "movimento detectado")',
      "}"
    ].join("\n");
    const { erros } = analisarLexico(fonte);
    afirmarIgual(erros, []);
  });

  teste("lexico: quebra de linha dentro de parenteses e colchetes e ignorada", () => {
    const { tokens, erros } = analisarLexico("f(1,\n  2)\nsupply l = [1,\n 2]\n");
    afirmarIgual(erros, []);
    const quebras = tokens.filter(t => t.tipo === "TOKEN_NEWLINE").map(t => t.linha);
    afirmarIgual(quebras, [2, 4], "so as quebras fora de ( ) e [ ] viram token");
  });

  teste("lexico: quebra de linha dentro de chaves continua separando comandos", () => {
    const { tokens } = analisarLexico("watch {\n    hide(1)\n}\n");
    afirmarIgual(tokens.filter(t => t.tipo === "TOKEN_NEWLINE").length, 3);
  });

  teste("sintatico: chamada quebrada em varias linhas compila", () => {
    const { erros, fase } = analisar('mqtt.publish("t",\n    "a" +\n    "b")\nhide(1)\n');
    afirmarIgual(fase, "ok", JSON.stringify(erros));
  });

  // ======================= FASE 2 — SINTÁTICO ============================

  teste("sintatico: declaracao supply vira DeclaracaoVariavel com categoria certa", () => {
    const { ast, erros } = analisar("supply x = 10");
    afirmarIgual(erros, []);
    afirmarIgual(ast.declaracoes[0].tipo, "DeclaracaoVariavel");
    afirmarIgual(ast.declaracoes[0].categoria, "supply");
    afirmarIgual(ast.declaracoes[0].nome, "x");
    afirmarIgual(ast.declaracoes[0].valor.tipo, "Literal");
    afirmarIgual(ast.declaracoes[0].valor.valor, 10);
  });

  teste("sintatico: law e stash tambem viram DeclaracaoVariavel, com categoria distinta", () => {
    const { ast } = analisar('law PIN = 27\nstash itens = [1, 2, 3]');
    afirmarIgual(ast.declaracoes[0].categoria, "law");
    afirmarIgual(ast.declaracoes[1].categoria, "stash");
    afirmarIgual(ast.declaracoes[1].valor.tipo, "ListaLiteral");
    afirmarIgual(ast.declaracoes[1].valor.elementos.length, 3);
  });

  teste("sintatico: scavenge vira no Scavenge", () => {
    const { ast, erros } = analisar("scavenge gpio");
    afirmarIgual(erros, []);
    afirmarIgual(ast.declaracoes[0], { tipo: "Scavenge", linha: 1, coluna: 1, modulo: "gpio" });
  });

  teste("sintatico: mission com parametros tipados e retorno vira Funcao", () => {
    const { ast, erros } = analisar("mission soma(ration a, ration b) -> ration {\n    extract a\n}");
    afirmarIgual(erros, []);
    const f = ast.declaracoes[0];
    afirmarIgual(f.tipo, "Funcao");
    afirmarIgual(f.nome, "soma");
    afirmarIgual(f.parametros, [
      { tipoDado: "ration", nome: "a", linha: 1, coluna: 21 },
      { tipoDado: "ration", nome: "b", linha: 1, coluna: 31 }
    ]);
    afirmarIgual(f.tipoRetorno, "ration");
    afirmarIgual(f.corpo[0].tipo, "Extract");
  });

  teste("sintatico: mission sem parametros e sem seta de retorno", () => {
    const { ast, erros } = analisar("mission tick() {\n    extract\n}");
    afirmarIgual(erros, []);
    const f = ast.declaracoes[0];
    afirmarIgual(f.parametros, []);
    afirmarIgual(f.tipoRetorno, null);
    afirmarIgual(f.corpo[0], { tipo: "Extract", linha: 2, coluna: 5, expressao: null });
  });

  teste("sintatico: survivor, ambush e chronicle viram Task/Evento/Principal", () => {
    const { ast, erros } = analisar(
      'survivor s {\n    watch {\n        hide(1)\n    }\n}\n' +
      'ambush e {\n    log_entry("evento")\n}\n' +
      'chronicle {\n    log_entry("main")\n}\n'
    );
    afirmarIgual(erros, []);
    afirmarIgual(ast.declaracoes.map(d => d.tipo), ["Task", "Evento", "Principal"]);
    afirmarIgual(ast.declaracoes[0].nome, "s");
    afirmarIgual(ast.declaracoes[1].nome, "e");
    afirmarIgual(ast.declaracoes[2].nome, null);
  });

  teste("sintatico: cache vira Estrutura com campos tipados", () => {
    const { ast, erros } = analisar("cache Config {\n    ration limite\n    paper nome\n}");
    afirmarIgual(erros, []);
    const est = ast.declaracoes[0];
    afirmarIgual(est.tipo, "Estrutura");
    afirmarIgual(est.nome, "Config");
    afirmarIgual(est.campos.map(c => [c.tipoDado, c.nome]), [["ration", "limite"], ["paper", "nome"]]);
  });

  teste("sintatico: checkpoint sem fallback vira Checkpoint com outros nulo", () => {
    const { ast, erros } = analisar("checkpoint (alive) {\n    hide(1)\n}");
    afirmarIgual(erros, []);
    const c = ast.declaracoes[0];
    afirmarIgual(c.tipo, "Checkpoint");
    afirmarIgual(c.outros, null);
  });

  teste("sintatico: checkpoint com fallback final vira bloco (array) em outros", () => {
    const { ast } = analisar("checkpoint (dead) {\n    hide(1)\n} fallback {\n    hide(2)\n}");
    const c = ast.declaracoes[0];
    afirmar(Array.isArray(c.outros), "outros deveria ser um array (bloco fallback)");
    afirmarIgual(c.outros[0].tipo, "ExpressaoStmt");
  });

  teste("sintatico: fallback checkpoint encadeado vira outro no Checkpoint (elif)", () => {
    const { ast } = analisar(
      "checkpoint (1 == 1) {\n    hide(1)\n} fallback checkpoint (2 == 2) {\n    hide(2)\n} fallback {\n    hide(3)\n}"
    );
    const c = ast.declaracoes[0];
    afirmarIgual(c.outros.tipo, "Checkpoint");
    afirmar(Array.isArray(c.outros.outros), "o segundo nivel deveria terminar em bloco fallback");
  });

  teste("sintatico: watch (loop infinito) e patrol (repeticao) tem corpo em bloco", () => {
    const { ast, erros } = analisar("watch {\n    hide(1)\n}\npatrol(5) {\n    hide(2)\n}");
    afirmarIgual(erros, []);
    afirmarIgual(ast.declaracoes[0].tipo, "Watch");
    afirmarIgual(ast.declaracoes[1].tipo, "Patrol");
    afirmarIgual(ast.declaracoes[1].vezes, { tipo: "Literal", linha: 4, coluna: 8, valor: 5, tipoLiteral: "ration" });
  });

  teste("sintatico: quarantine/catch vira Quarantine com tentativa e captura", () => {
    const { ast, erros } = analisar(
      "quarantine {\n    outbreak dead\n} catch (falha) {\n    log_entry(falha)\n}"
    );
    afirmarIgual(erros, []);
    const q = ast.declaracoes[0];
    afirmarIgual(q.tipo, "Quarantine");
    afirmarIgual(q.nomeErro, "falha");
    afirmarIgual(q.tentativa[0].tipo, "Outbreak");
    afirmarIgual(q.captura[0].tipo, "ExpressaoStmt");
  });

  teste("sintatico: atribuicao (IDENT = expressao) e distinta de comando de expressao", () => {
    const { ast, erros } = analisar("supply x = 1\nx = 2\nhide(x)");
    afirmarIgual(erros, []);
    afirmarIgual(ast.declaracoes[1], { tipo: "Atribuicao", linha: 2, coluna: 1, nome: "x", valor: { tipo: "Literal", linha: 2, coluna: 5, valor: 2, tipoLiteral: "ration" } });
    afirmarIgual(ast.declaracoes[2].tipo, "ExpressaoStmt");
  });

  teste("sintatico: precedencia de operadores (||, &&, igualdade, relacional, aditivo, multiplicativo)", () => {
    const { ast, erros } = analisar("supply r = 1 + 2 * 3 == 7 && alive || dead");
    afirmarIgual(erros, []);
    const raiz = ast.declaracoes[0].valor;
    afirmarIgual(raiz.tipo, "Logica");
    afirmarIgual(raiz.operador, "||");
    afirmarIgual(raiz.esquerda.operador, "&&");
    afirmarIgual(raiz.esquerda.esquerda.operador, "==");
    afirmarIgual(raiz.esquerda.esquerda.esquerda.operador, "+");
    afirmarIgual(raiz.esquerda.esquerda.esquerda.direita.operador, "*");
  });

  teste("sintatico: unario logico e aritmetico (!, -)", () => {
    const { ast, erros } = analisar("supply x = !alive\nsupply y = -5");
    afirmarIgual(erros, []);
    afirmarIgual(ast.declaracoes[0].valor, { tipo: "Unaria", linha: 1, coluna: 12, operador: "!", operando: { tipo: "Literal", linha: 1, coluna: 13, valor: true, tipoLiteral: "status" } });
    afirmarIgual(ast.declaracoes[1].valor.operador, "-");
  });

  teste("sintatico: parenteses agrupam e alteram a arvore (Agrupamento)", () => {
    const { ast } = analisar("supply r = (1 + 2) * 3");
    afirmarIgual(ast.declaracoes[0].valor.tipo, "Binaria");
    afirmarIgual(ast.declaracoes[0].valor.operador, "*");
    afirmarIgual(ast.declaracoes[0].valor.esquerda.tipo, "Agrupamento");
  });

  teste("sintatico: chamada encadeada com acesso a membro (obj.metodo(args))", () => {
    const { ast, erros } = analisar("supply x = gpio.read(radio(1))");
    afirmarIgual(erros, []);
    const chamada = ast.declaracoes[0].valor;
    afirmarIgual(chamada.tipo, "Chamada");
    afirmarIgual(chamada.alvo.tipo, "Membro");
    afirmarIgual(chamada.alvo.nome, "read");
    afirmarIgual(chamada.alvo.objeto, { tipo: "Identificador", linha: 1, coluna: 12, nome: "gpio" });
    afirmarIgual(chamada.argumentos[0].tipo, "Chamada");
    afirmarIgual(chamada.argumentos[0].alvo.nome, "radio");
  });

  teste("sintatico: indice de lista ([ ]) vira no Indice", () => {
    const { ast, erros } = analisar("stash itens = [1, 2, 3]\nsupply primeiro = itens[0]");
    afirmarIgual(erros, []);
    const indice = ast.declaracoes[1].valor;
    afirmarIgual(indice.tipo, "Indice");
    afirmarIgual(indice.alvo.nome, "itens");
    afirmarIgual(indice.indice.valor, 0);
  });

  teste("sintatico: palavras reservadas de hardware/tipo funcionam como alvo de chamada", () => {
    const { ast, erros } = analisar("broadcast(radio(5))\nsilence(radio(5))\nhide(500)\nlog_entry(\"oi\")");
    afirmarIgual(erros, []);
    afirmarIgual(ast.declaracoes.map(d => d.expressao.alvo.nome), ["broadcast", "silence", "hide", "log_entry"]);
  });

  teste("sintatico: ';' funciona como separador alternativo a nova linha", () => {
    const { ast, erros } = analisar("supply x = 1; supply y = 2; hide(x)");
    afirmarIgual(erros, []);
    afirmarIgual(ast.declaracoes.length, 3);
  });

  teste("sintatico: parenteses nao fechados geram erro com linha/coluna e o parser se recupera na linha seguinte", () => {
    const { ast, erros } = analisar("supply x = (1 + 2\nsupply y = 3");
    afirmarIgual(erros.length, 1);
    afirmarIgual(erros[0].linha, 1);
    afirmarIgual(ast.declaracoes.length, 1, "a declaracao 'y' deveria sobreviver a recuperacao em modo panico");
    afirmarIgual(ast.declaracoes[0].nome, "y");
  });

  teste("sintatico: bloco sem '}' gera erro apontando onde o fechamento era esperado", () => {
    const { erros } = analisar("mission f() {\n    extract\n");
    afirmarIgual(erros.length, 1);
    afirmar(erros[0].msg.includes("'}'"), "mensagem deveria mencionar a chave que falta");
  });

  teste("sintatico: erro em uma declaracao nao impede reportar erro em outra (modo panico)", () => {
    const { ast, erros } = analisar("supply x = )\nsupply y = )\nhide(1)");
    afirmarIgual(erros.length, 2);
    afirmarIgual(ast.declaracoes.length, 1, "so a declaracao valida (hide(1)) sobrevive a recuperacao");
  });

  teste("sintatico: formatarArvore desenha a raiz e os filhos com arestas nomeadas", () => {
    const { ast } = analisar("supply x = 1");
    const texto = formatarArvore(ast);
    afirmar(texto.startsWith("Programa (1:1)"), "primeira linha deveria ser a raiz");
    afirmar(texto.includes("declaracoes[0]:"), "deveria nomear a aresta do array de declaracoes");
    afirmar(texto.includes("DeclaracaoVariavel"), "deveria mostrar o tipo do filho");
  });

  teste("sintatico: programa de referencia completo (sentinela de perimetro) sem erros", () => {
    const fonte = [
      "scavenge gpio",
      "",
      "law MOTION_PIN = 27",
      "law ALARM_RADIO = 5",
      "",
      "mission check_perimeter() -> status {",
      "    supply detected = gpio.read(radio(MOTION_PIN))",
      "    extract detected",
      "}",
      "",
      "survivor perimeter_watch {",
      "    watch {",
      "        checkpoint (check_perimeter()) {",
      "            broadcast(radio(ALARM_RADIO))",
      "            hide(10000)",
      "            silence(radio(ALARM_RADIO))",
      "        } fallback {",
      '            log_entry("area limpa, nenhum sinal")',
      "        }",
      "        hide(500)",
      "    }",
      "}",
      "",
      "ambush intruder_alert {",
      '    mqtt.publish("perimetro/alerta", "movimento detectado")',
      "}"
    ].join("\n");
    const { erros } = analisar(fonte);
    afirmarIgual(erros, []);
  });

  // ======================= FASE 3 — GERAÇÃO ==============================

  teste("gerador: supply e law viram atribuicao, com law marcada como constante", () => {
    const py = corpoGerado("supply x = 10\nlaw LIMITE = 5\n");
    afirmar(py.includes("x = 10"), "esperava a atribuicao de x\n" + py);
    afirmar(py.includes("LIMITE = 5  # constante"), "esperava LIMITE marcada como constante\n" + py);
  });

  teste("gerador: literais booleanos viram True/False", () => {
    const py = corpoGerado("supply ligado = alive\nsupply parado = dead\n");
    afirmar(py.includes("ligado = True"), py);
    afirmar(py.includes("parado = False"), py);
  });

  teste("gerador: vital de valor redondo preserva o ponto decimal", () => {
    const py = corpoGerado("supply limite = 10.0\n");
    afirmar(py.includes("limite = 10.0"), "10.0 nao pode virar int no Python\n" + py);
  });

  teste("gerador: checkpoint/fallback vira if/else", () => {
    const py = corpoGerado('checkpoint (alive) {\n  log_entry("sim")\n} fallback {\n  log_entry("nao")\n}\n');
    afirmar(py.includes("if True:"), py);
    afirmar(py.includes("else:"), py);
  });

  teste("gerador: fallback checkpoint encadeado vira elif", () => {
    const fonte = [
      "supply a = 1",
      "supply b = 2",
      "checkpoint (a) {",
      '  log_entry("a")',
      "} fallback checkpoint (b) {",
      '  log_entry("b")',
      "} fallback {",
      '  log_entry("c")',
      "}"
    ].join("\n");
    const py = corpoGerado(fonte);
    afirmar(py.includes("elif b:"), "esperava elif no encadeamento\n" + py);
    afirmar(py.includes("else:"), py);
  });

  teste("gerador: watch vira laco infinito", () => {
    const py = corpoGerado("watch {\n  hide(500)\n}\n");
    afirmar(py.includes("while True:"), py);
    afirmar(py.includes("hide(500)"), py);
  });

  teste("gerador: patrol vira for com range", () => {
    const py = corpoGerado('patrol(7) {\n  log_entry("dia")\n}\n');
    afirmar(py.includes("for _ in range(7):"), py);
  });

  teste("gerador: mission vira def com os parametros na ordem", () => {
    const py = corpoGerado("mission somar(ration a, ration b) -> ration {\n  extract a + b\n}\n");
    afirmar(py.includes("def somar(a, b):"), py);
    afirmar(py.includes("return a + b"), py);
  });

  teste("gerador: chronicle vira main() com guarda de execucao", () => {
    const py = corpoGerado('chronicle {\n  log_entry("online")\n}\n');
    afirmar(py.includes("def main():"), py);
    afirmar(py.includes('if __name__ == "__main__":'), py);
    afirmar(py.includes("main()"), py);
  });

  teste("gerador: quarantine/catch vira try/except", () => {
    const py = corpoGerado('quarantine {\n  log_entry("tenta")\n} catch (falha) {\n  log_entry(falha)\n}\n');
    afirmar(py.includes("try:"), py);
    afirmar(py.includes("except Exception as falha:"), py);
  });

  teste("gerador: operadores logicos viram and/or/not", () => {
    const py = corpoGerado("supply r = alive && dead || !alive\n");
    afirmar(py.includes("and"), py);
    afirmar(py.includes("or"), py);
    afirmar(py.includes("not "), py);
  });

  teste("gerador: bloco vazio vira pass", () => {
    const py = corpoGerado("chronicle {\n}\n");
    afirmar(py.includes("pass"), "bloco vazio precisa de pass para o Python ser valido\n" + py);
  });

  teste("gerador: outbreak vira raise", () => {
    const py = corpoGerado('outbreak "reserva critica"\n');
    afirmar(py.includes('raise Exception("reserva critica")'), py);
  });

  teste("gerador: acesso a membro e indice sao preservados", () => {
    const py = corpoGerado("supply v = gpio.read(radio(27))\nsupply p = lista[0]\n");
    afirmar(py.includes("gpio.read(radio(27))"), py);
    afirmar(py.includes("lista[0]"), py);
  });

  teste("gerador: cache vira classe com construtor", () => {
    const py = corpoGerado("cache Leitura {\n  vital valor\n  paper origem\n}\n");
    afirmar(py.includes("class Leitura:"), py);
    afirmar(py.includes("def __init__(self, valor=None, origem=None):"), py);
    afirmar(py.includes("self.valor = valor"), py);
  });

  teste("gerador: mapa liga a linha gerada a linha do fonte", () => {
    const { corpo, mapa } = gerarPython("supply x = 1\nsupply y = 2\n");
    const linhas = corpo.split("\n");
    const idxY = linhas.findIndex(l => l.startsWith("y = 2"));
    afirmar(idxY >= 0, "esperava encontrar a linha de y no Python gerado");
    afirmarIgual(mapa[idxY + 1], 2, "a linha de y veio da linha 2 do fonte");
  });

  teste("gerador: programa de referencia gera o Python esperado", () => {
    const fonte = [
      "scavenge gpio",
      "",
      "law ALARM_RADIO = 5",
      "",
      "mission check_perimeter() -> status {",
      "    supply detected = gpio.read(radio(27))",
      "    extract detected",
      "}",
      "",
      "survivor perimeter_watch {",
      "    watch {",
      "        checkpoint (check_perimeter()) {",
      "            broadcast(radio(ALARM_RADIO))",
      "        } fallback {",
      '            log_entry("area limpa")',
      "        }",
      "        hide(500)",
      "    }",
      "}"
    ].join("\n");
    const py = corpoGerado(fonte);
    for (const trecho of [
      "ALARM_RADIO = 5  # constante",
      "def check_perimeter():",
      "detected = gpio.read(radio(27))",
      "return detected",
      "def perimeter_watch():",
      "while True:",
      "if check_perimeter():",
      "broadcast(radio(ALARM_RADIO))",
      "else:",
      'log_entry("area limpa")',
      "hide(500)"
    ]) {
      afirmar(py.includes(trecho), `faltou no Python gerado: ${trecho}\n${py}`);
    }
  });

  teste("gerador: mission que altera supply do topo declara global", () => {
    const py = corpoGerado(
      "supply alarme = dead\nsupply n = 0\nmission disparar() {\n" +
      "    checkpoint (n > 1) {\n        alarme = alive\n    }\n    n = n + 1\n}\n"
    );
    afirmar(py.includes("def disparar():\n    global alarme, n"), py);
  });

  teste("gerador: parametro e supply local nao viram global", () => {
    const py = corpoGerado(
      "supply x = 0\nmission f(ration x) {\n    x = 1\n}\n" +
      "mission g() {\n    supply x = 2\n    x = 3\n}\n"
    );
    afirmar(!py.includes("global"), py);
  });

  teste("gerador: chronicle e survivor tambem declaram global", () => {
    const py = corpoGerado(
      "supply ciclos = 0\nsurvivor t {\n    ciclos = ciclos + 1\n}\n" +
      "chronicle {\n    watch {\n        ciclos = 0\n    }\n}\n"
    );
    afirmar(py.includes("def t():\n    global ciclos"), py);
    afirmar(py.includes("def main():\n    global ciclos"), py);
  });

  teste("gerador: alvo padrao e o simulado, sem modulos do MicroPython", () => {
    const { corpo } = gerarPython("hide(1)\n");
    afirmar(!corpo.includes("import machine"), "o alvo simulado nao pode depender do MicroPython");
    afirmar(corpo.includes("sonar = _Sonar()"), "o simulado tambem oferece a API de sensores");
  });

  teste("gerador: alvo esp32 usa o runtime MicroPython com o mesmo programa", () => {
    const fonte = "law TRIG = 25\nsupply d = sonar.distance(TRIG, 26)\n";
    const simulado = gerarPython(fonte).corpo;
    const esp32 = gerarPython(fonte, { alvo: "esp32" }).corpo;
    afirmar(esp32.includes("import machine as _machine"), esp32);
    afirmar(esp32.includes("time_pulse_us"), "o sonar do esp32 mede o pulso do ECHO");
    const marca = "# --- fim do runtime ---";
    afirmarIgual(esp32.split(marca)[1], simulado.split(marca)[1],
                 "trocar o alvo nao pode mudar o codigo do programa");
  });

  teste("gerador: runtimes sem caracteres de controle (escapes do template JS)", () => {
    // um "\x13" escrito dentro do template string vira o byte 0x13 no Python
    for (const alvo of ["simulado", "esp32"]) {
      const { corpo } = gerarPython("hide(1)\n", { alvo });
      const ruim = [...corpo].findIndex(c => c < " " && c !== "\n");
      afirmar(ruim < 0, `alvo ${alvo}: caractere de controle perto de ${JSON.stringify(corpo.slice(ruim - 40, ruim + 10))}`);
    }
  });

  teste("gerador: os dois runtimes oferecem o leitor de digital", () => {
    for (const alvo of ["simulado", "esp32"]) {
      const { corpo } = gerarPython("supply id = finger.scan()\n", { alvo });
      afirmar(corpo.includes("finger = _Digital()"), `alvo ${alvo} sem finger`);
    }
  });

  teste("gerador: os dois runtimes oferecem config, painel web e Telegram", () => {
    for (const alvo of ["simulado", "esp32"]) {
      const { corpo } = gerarPython('supply t = config.get("telegram_token", "")\n', { alvo });
      afirmar(/^config = _Config\(/m.test(corpo), `alvo ${alvo} sem config`);
      afirmar(/^web = _Painel(Pc)?\(\)/m.test(corpo), `alvo ${alvo} sem web`);
      afirmar(corpo.includes("telegram = _Telegram()"), `alvo ${alvo} sem telegram`);
      afirmar(corpo.includes("def waiting(self):") && corpo.includes("def command(self, intervalo_ms=15000):"),
              `alvo ${alvo} sem a API de rede completa`);
    }
    const esp32 = gerarPython("hide(1)\n", { alvo: "esp32" }).corpo;
    afirmar(esp32.includes("import requests"), "o Telegram do esp32 usa o requests do MicroPython");
  });

  teste("gerador: a pagina do painel entra como string no runtime", () => {
    const { corpo } = gerarPython("hide(1)\n");
    const linha = corpo.split("\n").find(l => l.startsWith("_PAINEL_HTML = "));
    afirmar(linha, "faltou _PAINEL_HTML");
    // o literal emitido pelo JSON.stringify precisa voltar ao HTML original
    const html = JSON.parse(linha.slice("_PAINEL_HTML = ".length));
    afirmar(html.startsWith("<!doctype html>") && html.includes('fetch("/dados"'), html.slice(0, 80));
  });

  teste("gerador: alvo desconhecido e recusado", () => {
    const { ast } = analisar("hide(1)\n");
    let mensagem = "";
    try { gerarCodigo(ast, { alvo: "arduino" }); } catch (e) { mensagem = e.message; }
    afirmar(mensagem.includes("alvo desconhecido: arduino"), mensagem);
  });

  teste("gerador: paper/ration/vital viram conversoes do runtime", () => {
    const { corpo } = gerarPython('log_entry("T=" + paper(ration(25.7)))\n');
    afirmar(corpo.includes("def paper(valor):\n    return str(valor)"), "faltou paper no runtime");
    afirmar(corpo.includes('log_entry("T=" + paper(ration(25.7)))'), corpo);
  });

  // ======================= exposição / execução ==========================

  const api = { teste, afirmar, afirmarIgual, rodarTestes, casos };

  if (typeof module !== "undefined") {
    module.exports = api;
  }
  if (typeof global.window !== "undefined") {
    global.window.testesAegis = api;
  } else {
    global.testesAegis = api;
  }

  // Execução direta via `node testes.js`
  if (typeof require !== "undefined" && typeof module !== "undefined" && require.main === module) {
    const r = rodarTestes();
    for (const res of r.resultados) {
      console.log(`${res.ok ? "OK  " : "FAIL"} ${res.nome}${res.ok ? "" : "\n     " + res.erro}`);
    }
    console.log(`\n${r.passou}/${r.total} testes passaram.`);
    process.exit(r.falhou > 0 ? 1 : 0);
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
