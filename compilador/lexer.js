// FASE 1 — Análise léxica da linguagem AEGIS.
// Converte o texto-fonte em uma lista de tokens, usando regex sticky (/y)
// testadas em ordem na posição atual. A primeira que casar vence (maximal munch:
// símbolos de 2 caracteres antes de 1, comentários antes do operador "/",
// decimal antes de inteiro, string bem-formada antes da aberta).

// -----------------------------------------------------------------------
// Palavras reservadas: lexema -> { tipo, categoria, valor? }
// categoria segue as seções da tabela de base léxica (declaracao, tipo,
// controle, hardware, tratamento_erro, evento_io, literal para os booleanos).
// -----------------------------------------------------------------------
const PALAVRAS_RESERVADAS = {
  // declarações
  chronicle: { tipo: "TOKEN_MAIN", categoria: "declaracao" },
  scavenge: { tipo: "TOKEN_IMPORT", categoria: "declaracao" },
  mission: { tipo: "TOKEN_FUNC", categoria: "declaracao" },
  supply: { tipo: "TOKEN_LET", categoria: "declaracao" },
  law: { tipo: "TOKEN_CONST", categoria: "declaracao" },
  survivor: { tipo: "TOKEN_TASK", categoria: "declaracao" },
  cache: { tipo: "TOKEN_STRUCT", categoria: "declaracao" },
  stash: { tipo: "TOKEN_ARRAY", categoria: "declaracao" },
  // tipos primitivos
  ration: { tipo: "TOKEN_TYPE_INT", categoria: "tipo" },
  vital: { tipo: "TOKEN_TYPE_FLOAT", categoria: "tipo" },
  status: { tipo: "TOKEN_TYPE_BOOL", categoria: "tipo" },
  paper: { tipo: "TOKEN_TYPE_STRING", categoria: "tipo" },
  radio: { tipo: "TOKEN_TYPE_PIN", categoria: "tipo" },
  silent: { tipo: "TOKEN_TYPE_VOID", categoria: "tipo" },
  // controle de fluxo
  watch: { tipo: "TOKEN_LOOP", categoria: "controle" },
  patrol: { tipo: "TOKEN_FOR", categoria: "controle" },
  checkpoint: { tipo: "TOKEN_IF", categoria: "controle" },
  fallback: { tipo: "TOKEN_ELSE", categoria: "controle" },
  extract: { tipo: "TOKEN_RETURN", categoria: "controle" },
  // sinal / hardware
  broadcast: { tipo: "TOKEN_GPIO_HIGH", categoria: "hardware" },
  silence: { tipo: "TOKEN_GPIO_LOW", categoria: "hardware" },
  hide: { tipo: "TOKEN_DELAY", categoria: "hardware" },
  // erros
  outbreak: { tipo: "TOKEN_ERROR_TYPE", categoria: "tratamento_erro" },
  quarantine: { tipo: "TOKEN_TRY", categoria: "tratamento_erro" },
  catch: { tipo: "TOKEN_CATCH", categoria: "tratamento_erro" },
  // eventos e E/S
  ambush: { tipo: "TOKEN_EVENT", categoria: "evento_io" },
  log_entry: { tipo: "TOKEN_PRINT", categoria: "evento_io" },
  // literais booleanos (são palavras reservadas, mas carregam valor, não estrutura)
  alive: { tipo: "TOKEN_BOOL_LIT", categoria: "literal", valor: true },
  dead: { tipo: "TOKEN_BOOL_LIT", categoria: "literal", valor: false }
};

// Nomes de módulo embutidos (gpio, adc, pwm, wifi, mqtt, time): NÃO são
// palavras reservadas — são só convenção da biblioteca padrão reconhecida
// pelo gerador/semântica, não pelo lexer. Um programa pode, tecnicamente,
// usar um desses nomes como identificador comum (o lexer não impede isso).
const MODULOS_EMBUTIDOS = ["gpio", "adc", "pwm", "wifi", "mqtt", "time", "config", "web", "telegram"];

// Símbolos: ordenados por tamanho (maior primeiro) para maximal munch.
// "->" precisa vencer antes de "-"; "&&"/"||" antes de operadores de 1 char.
// "." foi adicionado além da tabela original: o exemplo de referência da
// linguagem usa `gpio.read(...)` e `mqtt.publish(...)`, então precisa de um
// token de acesso a membro — sem ele "." vira caractere não reconhecido.
const SIMBOLOS = [
  { lexema: "->", tipo: "ARROW", categoria: "delimitador" },
  { lexema: "&&", tipo: "AND", categoria: "operador" },
  { lexema: "||", tipo: "OR", categoria: "operador" },
  { lexema: "==", tipo: "EQ", categoria: "operador" },
  { lexema: "!=", tipo: "NEQ", categoria: "operador" },
  { lexema: "<=", tipo: "LE", categoria: "operador" },
  { lexema: ">=", tipo: "GE", categoria: "operador" },
  { lexema: "+", tipo: "PLUS", categoria: "operador" },
  { lexema: "-", tipo: "MINUS", categoria: "operador" },
  { lexema: "*", tipo: "STAR", categoria: "operador" },
  { lexema: "/", tipo: "SLASH", categoria: "operador" },
  { lexema: "<", tipo: "LT", categoria: "operador" },
  { lexema: ">", tipo: "GT", categoria: "operador" },
  { lexema: "!", tipo: "NOT", categoria: "operador" },
  { lexema: "=", tipo: "ASSIGN", categoria: "operador" },
  { lexema: "{", tipo: "LBRACE", categoria: "delimitador" },
  { lexema: "}", tipo: "RBRACE", categoria: "delimitador" },
  { lexema: "(", tipo: "LPAREN", categoria: "delimitador" },
  { lexema: ")", tipo: "RPAREN", categoria: "delimitador" },
  { lexema: "[", tipo: "LBRACKET", categoria: "delimitador" },
  { lexema: "]", tipo: "RBRACKET", categoria: "delimitador" },
  { lexema: ",", tipo: "COMMA", categoria: "delimitador" },
  { lexema: ";", tipo: "SEMI", categoria: "delimitador" },
  { lexema: ":", tipo: "COLON", categoria: "delimitador" },
  { lexema: ".", tipo: "DOT", categoria: "delimitador" }
];

const MAPA_SIMBOLOS = new Map(SIMBOLOS.map(s => [s.lexema, s]));

// regex único para todos os símbolos, escapado e ordenado maior->menor
function construirRegexSimbolos() {
  const escapar = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const partes = [...SIMBOLOS].sort((a, b) => b.lexema.length - a.lexema.length).map(s => escapar(s.lexema));
  return new RegExp(partes.join("|"), "y");
}

const DEFINICOES_TOKEN = [
  { tipo: "ESPACO", categoria: "ignorado", regex: /[ \t\r]+/y, ignorar: true },
  { tipo: "COMENTARIO_BLOCO", categoria: "comentario", regex: /\/\*[\s\S]*?\*\//y },
  { tipo: "COMENTARIO_BLOCO_ABERTO", categoria: "erro", regex: /\/\*[\s\S]*/y, erro: "comentário de bloco não fechado" },
  { tipo: "COMENTARIO_LINHA", categoria: "comentario", regex: /\/\/[^\n]*/y },
  { tipo: "NOVA_LINHA", categoria: "estrutura", regex: /\n/y },
  { tipo: "TEXTO", categoria: "literal", regex: /"(?:[^"\\\n]|\\.)*"/y },
  { tipo: "TEXTO_ABERTO", categoria: "erro", regex: /"[^\n]*/y, erro: "aspas não fechadas" },
  { tipo: "DECIMAL", categoria: "literal", regex: /\d+\.\d+/y },
  { tipo: "INTEIRO", categoria: "literal", regex: /\d+/y },
  { tipo: "IDENTIFICADOR", categoria: "identificador", regex: /[a-zA-Z_][a-zA-Z0-9_]*/y },
  { tipo: "SIMBOLO", categoria: null, regex: construirRegexSimbolos() }
];

function decodificarTexto(lexema) {
  const interior = lexema.slice(1, -1);
  return interior.replace(/\\(.)/g, (_, ch) => {
    switch (ch) {
      case "n": return "\n";
      case "t": return "\t";
      case "r": return "\r";
      case "\\": return "\\";
      case "\"": return "\"";
      default: return ch;
    }
  });
}

function valorDoToken(tipo, lexema, reservada) {
  if (reservada && reservada.valor !== undefined) return reservada.valor;
  if (tipo === "INTEIRO") return parseInt(lexema, 10);
  if (tipo === "DECIMAL") return parseFloat(lexema);
  if (tipo === "TEXTO") return decodificarTexto(lexema);
  if (tipo === "TOKEN_IDENTIFIER") return lexema;
  return null;
}

// Palavras que só podem abrir um comando, nunca continuar uma expressão.
// Se uma linha começa com uma delas enquanto há "(" aberto, o parêntese
// ficou sem fechar: o léxico volta a emitir a quebra de linha para que o
// parser acuse o erro e se recupere na linha certa (modo pânico).
const INICIA_COMANDO = new Set([
  "chronicle", "scavenge", "mission", "supply", "law", "survivor", "cache", "stash",
  "ambush", "checkpoint", "fallback", "watch", "patrol", "extract",
  "quarantine", "catch", "outbreak"
]);
const PROXIMA_LINHA = /[ \t\r\n]*(?:([a-zA-Z_][a-zA-Z0-9_]*)|(\}))?/y;

function parenteseEsquecido(fonte, pos) {
  PROXIMA_LINHA.lastIndex = pos;
  const m = PROXIMA_LINHA.exec(fonte);
  return Boolean(m && ((m[1] && INICIA_COMANDO.has(m[1])) || m[2]));
}

function analisarLexico(fonte) {
  const tokens = [];
  const erros = [];
  let pos = 0;
  let linha = 1;
  let coluna = 1;
  const tam = fonte.length;
  // ( e [ abertos: dentro deles a quebra de linha não encerra o comando,
  // como no Python. Permite quebrar uma chamada longa em várias linhas.
  // Chaves não contam: dentro de um bloco a quebra separa comandos.
  let profundidade = 0;

  while (pos < tam) {
    let casou = false;

    for (const def of DEFINICOES_TOKEN) {
      def.regex.lastIndex = pos;
      const m = def.regex.exec(fonte);
      if (!m || m.index !== pos) continue;

      casou = true;
      const lexema = m[0];
      const inicio = pos;
      const linhaInicio = linha;
      const colunaInicio = coluna;

      if (def.tipo === "NOVA_LINHA") {
        linha += 1;
        coluna = 1;
      } else {
        // comentário de bloco pode conter quebras de linha
        const quebras = lexema.split("\n");
        if (quebras.length > 1) {
          linha += quebras.length - 1;
          coluna = quebras[quebras.length - 1].length + 1;
        } else {
          coluna += lexema.length;
        }
      }
      pos += lexema.length;

      if (def.ignorar) break;
      if (def.tipo === "NOVA_LINHA" && profundidade > 0) {
        if (!parenteseEsquecido(fonte, pos)) break;
        profundidade = 0;
      }

      let tipo = def.tipo;
      let categoria = def.categoria;
      let reservada = null;

      if (tipo === "NOVA_LINHA") {
        tipo = "TOKEN_NEWLINE";
      } else if (tipo === "IDENTIFICADOR") {
        reservada = PALAVRAS_RESERVADAS[lexema] || null;
        if (reservada) {
          tipo = reservada.tipo;
          categoria = reservada.categoria;
        } else {
          tipo = "TOKEN_IDENTIFIER";
        }
      } else if (tipo === "SIMBOLO") {
        const info = MAPA_SIMBOLOS.get(lexema);
        tipo = info.tipo;
        categoria = info.categoria;
        if (tipo === "LPAREN" || tipo === "LBRACKET") profundidade += 1;
        if ((tipo === "RPAREN" || tipo === "RBRACKET") && profundidade > 0) profundidade -= 1;
      } else if (tipo === "INTEIRO") {
        tipo = "TOKEN_INT_LIT";
      } else if (tipo === "DECIMAL") {
        tipo = "TOKEN_FLOAT_LIT";
      } else if (tipo === "TEXTO") {
        tipo = "TOKEN_STRING_LIT";
      } else if (tipo === "TEXTO_ABERTO") {
        tipo = "TOKEN_STRING_LIT_ERRO";
      } else if (tipo === "COMENTARIO_LINHA" || tipo === "COMENTARIO_BLOCO") {
        tipo = "TOKEN_COMMENT";
      } else if (tipo === "COMENTARIO_BLOCO_ABERTO") {
        tipo = "TOKEN_COMMENT_ERRO";
      }

      const token = {
        indice: tokens.length,
        tipo,
        categoria,
        lexema,
        valor: valorDoToken(def.tipo === "IDENTIFICADOR" ? tipo : def.tipo, lexema, reservada),
        linha: linhaInicio,
        coluna: colunaInicio,
        inicio,
        fim: pos
      };

      if (def.erro) {
        erros.push({ linha: linhaInicio, coluna: colunaInicio, msg: def.erro, lexema });
      }

      tokens.push(token);
      break;
    }

    if (!casou) {
      const ch = fonte[pos];
      erros.push({
        linha,
        coluna,
        msg: `caractere não reconhecido '${ch}'`,
        lexema: ch
      });
      tokens.push({
        indice: tokens.length,
        tipo: "TOKEN_UNKNOWN",
        categoria: "erro",
        lexema: ch,
        valor: null,
        linha,
        coluna,
        inicio: pos,
        fim: pos + 1
      });
      pos += 1;
      coluna += 1;
    }
  }

  tokens.push({
    indice: tokens.length,
    tipo: "TOKEN_EOF",
    categoria: "estrutura",
    lexema: "",
    valor: null,
    linha,
    coluna,
    inicio: pos,
    fim: pos
  });

  return { tokens, erros };
}

function resumoTokens(tokens) {
  const resumo = {};
  for (const t of tokens) {
    resumo[t.categoria] = (resumo[t.categoria] || 0) + 1;
  }
  return resumo;
}

if (typeof module !== "undefined") {
  module.exports = {
    analisarLexico,
    decodificarTexto,
    resumoTokens,
    DEFINICOES_TOKEN,
    PALAVRAS_RESERVADAS,
    MODULOS_EMBUTIDOS,
    SIMBOLOS
  };
}
