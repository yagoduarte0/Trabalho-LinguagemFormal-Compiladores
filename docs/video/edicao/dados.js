// Gera docs/video/animacao/assets/dados.js com dados REAIS do projeto para as
// cenas do vídeo: trechos do firmware coloridos pelo próprio léxico do AEGIS,
// os tokens e a AST do exemplo de referência, o Python gerado e os erros.
//
// Uso (na raiz do repositório):  node docs/video/edicao/dados.js
// Rode de novo se o compilador ou o firmware mudarem.

const fs = require("fs");
const path = require("path");

const RAIZ = path.resolve(__dirname, "../../..");
const { analisarLexico } = require(path.join(RAIZ, "compilador/lexer.js"));
const { compilar, EXEMPLOS } = require(path.join(RAIZ, "compilador/compilador.js"));

const escapar = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// classe de cor de cada token (as mesmas classes de .codigo no tema.css)
function classeDoToken(t, proximo) {
  if (t.categoria === "comentario") return "co";
  if (t.tipo === "TOKEN_STRING_LIT") return "st";
  if (t.tipo === "TOKEN_INT_LIT" || t.tipo === "TOKEN_FLOAT_LIT") return "nu";
  if (t.categoria === "tipo") return "ti";
  if (["declaracao", "controle", "hardware", "tratamento_erro", "evento_io", "literal"].includes(t.categoria))
    return "kw";
  if (t.tipo === "TOKEN_IDENTIFIER" && proximo && proximo.tipo === "LPAREN") return "fn";
  return null;
}

// Colore um fonte AEGIS com os tokens do léxico real; devolve uma linha de
// HTML por linha do fonte (o texto entre os tokens, como espaços, é mantido).
function realcar(fonte) {
  const { tokens } = analisarLexico(fonte);
  let html = "";
  let pos = 0;
  tokens.forEach((t, i) => {
    if (t.tipo === "TOKEN_EOF") return;
    html += escapar(fonte.slice(pos, t.inicio));
    const lexema = fonte.slice(t.inicio, t.fim);
    const classe = classeDoToken(t, tokens[i + 1]);
    html += classe ? `<span class="${classe}">${escapar(lexema)}</span>` : escapar(lexema);
    pos = t.fim;
  });
  html += escapar(fonte.slice(pos));
  return html.split("\n");
}

// ----------------------------------------------------------------------------
const firmware = fs.readFileSync(path.join(RAIZ, "firmware/abrigo.aeg"), "utf8");
const linhasFirmware = firmware.split("\n");
if (linhasFirmware[linhasFirmware.length - 1] === "") linhasFirmware.pop();
const firmwareColorido = realcar(firmware);

// trecho do firmware a partir da primeira linha que casa com o padrão
function trecho(padrao, quantas) {
  const i = linhasFirmware.findIndex((l) => padrao.test(l));
  if (i < 0) throw new Error("trecho não encontrado: " + padrao);
  return { linha: i + 1, html: firmwareColorido.slice(i, i + quantas) };
}

// miniatura do arquivo inteiro: recuo, comprimento e cor de cada linha
const miniatura = linhasFirmware.map((l) => {
  const recuo = l.length - l.trimStart().length;
  const texto = l.trim();
  let tipo = "id";
  if (texto === "") tipo = "vazio";
  else if (texto.startsWith("//")) tipo = "co";
  else if (/^(scavenge|law|supply|survivor|mission|chronicle|checkpoint|\} fallback|watch|patrol|extract)\b/.test(texto)) tipo = "kw";
  return [recuo, texto.length, tipo];
});

// ----------------------------------------------------------------------------
const perimetro = EXEMPLOS["sentinela-perimetro"].fonte;
const r = compilar(perimetro);

// tokens da linha 7: supply detected = gpio.read(radio(MOTION_PIN))
const tokensLinha = r.tokens
  .filter((t) => t.linha === 7 && t.tipo !== "TOKEN_NEWLINE")
  .map((t) => ({ lx: t.lexema, tipo: t.tipo, cat: t.categoria, l: t.linha, c: t.coluna }));

// AST simplificada (tipo + rótulo), a mesma estrutura que o parser devolve
function resumirNo(no) {
  if (!no || typeof no !== "object") return null;
  const rotulo = no.nome || no.operador || (no.valor !== undefined && typeof no.valor !== "object" ? String(no.valor) : "");
  const filhos = [];
  for (const chave of Object.keys(no)) {
    const v = no[chave];
    if (Array.isArray(v)) v.forEach((x) => { const f = resumirNo(x); if (f) filhos.push(f); });
    else if (v && typeof v === "object" && v.tipo) { const f = resumirNo(v); if (f) filhos.push(f); }
  }
  return no.tipo ? { tipo: no.tipo, rotulo, filhos } : null;
}

// corpo do programa (sem o runtime): índice 0-based de cada linha no arquivo
// gerado, para consultar o mapa de linhas (que é 1-based)
const pyLinhas = r.python.split("\n");
const fimRuntime = pyLinhas.findIndex((l) => l.startsWith("# --- fim do runtime"));
let inicioCorpo = fimRuntime + 1;
while (pyLinhas[inicioCorpo].trim() === "") inicioCorpo++;
let fimCorpo = pyLinhas.length;
while (pyLinhas[fimCorpo - 1].trim() === "") fimCorpo--;
const corpoPython = pyLinhas.slice(inicioCorpo, fimCorpo);
const mapaCorpo = corpoPython.map((_, i) => r.linhaOrigem(inicioCorpo + i + 1));

// saída real da suíte de testes
const { execFileSync } = require("child_process");
const saidaTestes = execFileSync("node", [path.join(RAIZ, "compilador/testes.js")], { encoding: "utf8" })
  .split("\n").filter((l) => l.trim() !== "");

// começo de cada runtime: é a única parte que muda entre os alvos
const rEsp = compilar(perimetro, { alvo: "esp32" });
const inicioRuntime = (py) => py.split("\n").filter((l) => /^(import|from) /.test(l)).slice(0, 5);

const exemploErro = EXEMPLOS["erros-sintatico"] || Object.values(EXEMPLOS).find((e) => /sint/.test(e.titulo));
const comErro = compilar(exemploErro.fonte);

const dados = {
  firmware: {
    total: linhasFirmware.length,
    miniatura,
    scavenge: trecho(/^scavenge gpio/, 13),
    law: trecho(/^law PINO_PIR/, 5),
    supply: trecho(/^supply temperatura/, 3),
    survivor: trecho(/^survivor sentinela_fumaca/, 14),
    patrol: trecho(/^mission bipar/, 8),
    avaliar: trecho(/^mission avaliar/, 13),
    chronicle: trecho(/^chronicle \{/, 6),
    watch: trecho(/^    watch \{/, 4),
  },
  perimetro: {
    html: realcar(perimetro),
    tokensLinha,
    totalTokens: r.tokens.length,
    ast: resumirNo(r.ast),
    python: corpoPython,
    pythonMapa: mapaCorpo,
    runtimeSimulado: inicioRuntime(r.python),
    runtimeEsp32: inicioRuntime(rEsp.python),
  },
  testes: saidaTestes,
  erro: {
    html: realcar(exemploErro.fonte),
    erros: comErro.erros,
    fase: comErro.fase,
  },
};

const destino = path.join(RAIZ, "docs/video/animacao/assets/dados.js");
fs.writeFileSync(destino,
  "// gerado por docs/video/edicao/dados.js — não editar à mão\nwindow.AEGIS_DADOS = " +
  JSON.stringify(dados, null, 1) + ";\n");
console.log("gravado", path.relative(RAIZ, destino),
  `(${dados.firmware.total} linhas de firmware, ${tokensLinha.length} tokens na linha 7, ${comErro.erros.length} erros)`);
