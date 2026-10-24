#!/usr/bin/env node
// aegisc — compilador AEGIS de linha de comando.
//
//   node aegisc.js <fonte.aeg> [--alvo simulado|esp32] [-o saida.py]
//
// Encadeia as mesmas três fases da interface web (compilar() de
// compilador.js). Sem -o, o Python vai para a saída padrão, o que permite
// `node aegisc.js prog.aeg | python3`. Com erro, lista todos com
// arquivo:linha:coluna (formato que editores reconhecem) e sai com código 1.

const fs = require("fs");
const path = require("path");
const { compilar } = require("./compilador.js");

const USO = "uso: node aegisc.js <fonte.aeg> [--alvo simulado|esp32] [-o saida.py]";

function lerArgumentos(args) {
  const opcoes = { fonte: null, alvo: "simulado", saida: null };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === "--alvo") opcoes.alvo = args[++i];
    else if (a === "-o") opcoes.saida = args[++i];
    else if (a === "-h" || a === "--help") return null;
    else if (opcoes.fonte === null) opcoes.fonte = a;
    else throw new Error(`argumento inesperado: ${a}`);
  }
  if (!opcoes.fonte || !opcoes.alvo || (opcoes.saida === undefined)) return null;
  return opcoes;
}

function principal() {
  let opcoes;
  try {
    opcoes = lerArgumentos(process.argv.slice(2));
  } catch (e) {
    console.error(`aegisc: ${e.message}\n${USO}`);
    return 2;
  }
  if (!opcoes) {
    console.error(USO);
    return 2;
  }

  let fonte;
  try {
    fonte = fs.readFileSync(opcoes.fonte, "utf8");
  } catch (e) {
    console.error(`aegisc: não foi possível ler ${opcoes.fonte}: ${e.message}`);
    return 2;
  }

  let resultado;
  try {
    resultado = compilar(fonte, { alvo: opcoes.alvo });
  } catch (e) {
    console.error(`aegisc: ${e.message}`);
    return 2;
  }

  if (resultado.erros.length > 0) {
    const nome = path.basename(opcoes.fonte);
    for (const e of resultado.erros) {
      console.error(`${nome}:${e.linha}:${e.coluna}: erro ${resultado.fase}: ${e.msg}`);
    }
    console.error(`aegisc: ${resultado.erros.length} erro(s), nada foi gerado`);
    return 1;
  }

  if (opcoes.saida) {
    fs.writeFileSync(opcoes.saida, resultado.python);
    console.error(`aegisc: ${opcoes.fonte} -> ${opcoes.saida} (alvo ${opcoes.alvo})`);
  } else {
    process.stdout.write(resultado.python);
  }
  return 0;
}

process.exitCode = principal();
