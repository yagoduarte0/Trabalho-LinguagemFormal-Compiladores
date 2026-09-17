// Orquestrador das 3 fases: fonte -> tokens -> AST -> Python.
// Léxico (dia 1) e sintático (dia 2) já estão encadeados; gerador.js
// entra no dia 3 e este arquivo passa a encadear as três.

let _analisarLexico, _analisarSintatico, _gerarCodigo;

if (typeof module !== "undefined" && typeof require === "function") {
  _analisarLexico = require("./lexer.js").analisarLexico;
  try { _analisarSintatico = require("./parser.js").analisarSintatico; } catch (e) { /* dia 2 */ }
  try { _gerarCodigo = require("./gerador.js").gerarCodigo; } catch (e) { /* dia 3 */ }
} else {
  _analisarLexico = analisarLexico;
  _analisarSintatico = typeof analisarSintatico !== "undefined" ? analisarSintatico : undefined;
  _gerarCodigo = typeof gerarCodigo !== "undefined" ? gerarCodigo : undefined;
}

const EXEMPLOS = {
  "ola-abrigo": {
    titulo: "Olá, abrigo",
    fonte: 'chronicle {\n    log_entry("BUNKER//OS online")\n}\n'
  },
  "sentinela-perimetro": {
    titulo: "Sentinela de perímetro (exemplo de referência)",
    fonte:
      "scavenge gpio\n\n" +
      "law MOTION_PIN = 27\n" +
      "law ALARM_RADIO = 5\n\n" +
      "mission check_perimeter() -> status {\n" +
      "    supply detected = gpio.read(radio(MOTION_PIN))\n" +
      "    extract detected\n" +
      "}\n\n" +
      "survivor perimeter_watch {\n" +
      "    watch {\n" +
      "        checkpoint (check_perimeter()) {\n" +
      "            broadcast(radio(ALARM_RADIO))\n" +
      "            hide(10000)\n" +
      "            silence(radio(ALARM_RADIO))\n" +
      "        } fallback {\n" +
      '            log_entry("area limpa, nenhum sinal")\n' +
      "        }\n" +
      "        hide(500)\n" +
      "    }\n" +
      "}\n\n" +
      "ambush intruder_alert {\n" +
      '    mqtt.publish("perimetro/alerta", "movimento detectado")\n' +
      "}\n"
  },
  "racionamento": {
    titulo: "Racionamento de suprimentos",
    fonte:
      "mission ration_status(vital estoque) -> status {\n" +
      "    checkpoint (estoque <= 10.0) {\n" +
      "        extract dead\n" +
      "    }\n" +
      "    extract alive\n" +
      "}\n\n" +
      "chronicle {\n" +
      "    supply agua = 45.5\n" +
      "    patrol(7) {\n" +
      "        log_entry(\"racionamento diario\")\n" +
      "    }\n" +
      "}\n"
  },
  "erros-propositais": {
    titulo: "Erros propositais (léxico)",
    fonte:
      'supply mensagem = "porta sem fechar\n' +
      "checkpoint (mensagem) {\n" +
      "    log_entry(mensagem)\n" +
      "}\n" +
      "supply x = 1 & 2\n" +
      "supply y = 3 /* comentario nunca fecha\n"
  },
  "erro-sintatico": {
    titulo: "Erros propositais (sintático)",
    fonte:
      "mission ration_status(vital estoque) -> status {\n" +
      "    checkpoint (estoque <= 10.0 {\n" +
      "        extract dead\n" +
      "    }\n" +
      "    extract alive\n\n" +
      "chronicle {\n" +
      "    supply agua = \n" +
      "    log_entry(agua)\n" +
      "}\n"
  }
};

function compilar(fonte) {
  const resultado = {
    python: "",
    erros: [],
    linhaOrigem: () => null,
    tokens: [],
    ast: null,
    fase: "ok"
  };

  const { tokens, erros: errosLexicos } = _analisarLexico(fonte);
  resultado.tokens = tokens;

  if (errosLexicos.length > 0) {
    resultado.erros = errosLexicos;
    resultado.fase = "lexica";
    return resultado;
  }

  const tokensRelevantes = tokens.filter(t => t.categoria !== "comentario");

  if (typeof _analisarSintatico !== "function") {
    resultado.fase = "lexica-ok (parser ainda não implementado)";
    return resultado;
  }

  const { ast, erros: errosSintaticos } = _analisarSintatico(tokensRelevantes);
  resultado.ast = ast;

  if (errosSintaticos.length > 0) {
    resultado.erros = errosSintaticos;
    resultado.fase = "sintatica";
    return resultado;
  }

  if (typeof _gerarCodigo !== "function") {
    resultado.fase = "sintatica-ok (gerador ainda não implementado)";
    return resultado;
  }

  const { corpo, mapa } = _gerarCodigo(ast);
  resultado.python = corpo;
  resultado.linhaOrigem = (n) => (mapa && mapa[n] !== undefined ? mapa[n] : null);
  resultado.fase = "ok";
  return resultado;
}

if (typeof module !== "undefined") {
  module.exports = { compilar, EXEMPLOS };
}
