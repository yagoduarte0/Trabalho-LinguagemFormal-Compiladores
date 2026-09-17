// FASE 3 — Geração de código: percorre a AST e emite Python equivalente.
//
// O gerador é um visitante recursivo por tipo de nó. Não faz otimização nem
// análise semântica: confia que a AST recebida já passou pelas fases 1 e 2.
//
// Decisões de projeto registradas aqui porque não são óbvias lendo o código:
//
// 1) Runtime embutido: a linguagem tem construções de hardware (broadcast,
//    silence, hide, radio) e módulos (gpio, mqtt, ...) que não existem em
//    Python. Em vez de gerar imports de um pacote que o professor teria que
//    instalar, o gerador emite um pequeno runtime simulado no topo do
//    arquivo. O Python gerado roda sozinho, sem dependência nenhuma.
//
// 2) Indentação: AEGIS delimita blocos por chaves e Python por indentação.
//    A conversão acontece no emissor, que recebe o nível e aplica 4 espaços.
//    Bloco vazio vira "pass", senão o Python fica sintaticamente inválido.
//
// 3) Mapa de linhas: cada linha gerada guarda de qual linha do fonte veio.
//    É o que permite a interface destacar a origem de uma linha do Python.
//
// 4) "survivor" (task) e "ambush" (evento) viram funções comuns. A linguagem
//    prevê execução concorrente, mas concorrência de verdade fugiria do
//    escopo do trabalho — o comentário emitido deixa a intenção registrada.

const INDENT = "    ";

const RUNTIME = `# --- runtime AEGIS (gerado automaticamente) ---
import time as _time


class _Barramento:
    def __init__(self):
        self.estado = {}

    def read(self, pino):
        return self.estado.get(pino, False)

    def write(self, pino, valor):
        self.estado[pino] = valor


gpio = _Barramento()
adc = _Barramento()
pwm = _Barramento()


class _Rede:
    def connect(self, *args):
        return True

    def publish(self, topico, mensagem):
        print("[" + str(topico) + "] " + str(mensagem))


wifi = _Rede()
mqtt = _Rede()
time = _time


def radio(pino):
    return pino


def log_entry(*args):
    print(*args)


def hide(ms):
    _time.sleep(ms / 1000)


def broadcast(pino):
    gpio.write(pino, True)


def silence(pino):
    gpio.write(pino, False)
# --- fim do runtime ---`;

// operadores que mudam de grafia entre as duas linguagens
const OPERADOR_LOGICO = { "||": "or", "&&": "and" };
const OPERADOR_UNARIO = { "!": "not ", "-": "-" };

function gerarCodigo(ast) {
  const linhas = [];
  const mapa = {};

  function emitir(texto, nivel, origem) {
    linhas.push(nivel > 0 ? INDENT.repeat(nivel) + texto : texto);
    if (origem && origem.linha) mapa[linhas.length] = origem.linha;
  }

  function emitirBloco(declaracoes, nivel) {
    if (!declaracoes || declaracoes.length === 0) {
      emitir("pass", nivel);
      return;
    }
    for (const d of declaracoes) gerarDeclaracao(d, nivel);
  }

  // ------------------------------ expressões -------------------------------
  function gerarExpressao(no) {
    switch (no.tipo) {
      case "Literal":
        if (no.tipoLiteral === "status") return no.valor ? "True" : "False";
        if (no.tipoLiteral === "paper") return JSON.stringify(no.valor);
        // um "vital" de valor redondo (10.0) viraria "10" pelo String() do
        // JavaScript e chegaria ao Python como int, perdendo a distinção
        // entre ration e vital que a linguagem faz
        if (no.tipoLiteral === "vital" && Number.isInteger(no.valor)) {
          return no.valor.toFixed(1);
        }
        return String(no.valor);

      case "Identificador":
        return no.nome;

      case "Agrupamento":
        return "(" + gerarExpressao(no.expressao) + ")";

      case "Logica":
        return gerarExpressao(no.esquerda) + " " + OPERADOR_LOGICO[no.operador] +
               " " + gerarExpressao(no.direita);

      case "Binaria":
        return gerarExpressao(no.esquerda) + " " + no.operador + " " +
               gerarExpressao(no.direita);

      case "Unaria":
        return OPERADOR_UNARIO[no.operador] + gerarExpressao(no.operando);

      case "Chamada":
        return gerarExpressao(no.alvo) + "(" +
               no.argumentos.map(gerarExpressao).join(", ") + ")";

      case "Membro":
        return gerarExpressao(no.objeto) + "." + no.nome;

      case "Indice":
        return gerarExpressao(no.alvo) + "[" + gerarExpressao(no.indice) + "]";

      case "ListaLiteral":
        return "[" + no.elementos.map(gerarExpressao).join(", ") + "]";

      default:
        return `# expressão não suportada: ${no.tipo}`;
    }
  }

  // ------------------------- declarações e comandos -------------------------
  function gerarDeclaracao(no, nivel) {
    switch (no.tipo) {
      case "Scavenge":
        emitir(`# scavenge ${no.modulo} — módulo fornecido pelo runtime`, nivel, no);
        break;

      case "DeclaracaoVariavel": {
        const sufixo = no.categoria === "law" ? "  # constante" : "";
        emitir(`${no.nome} = ${gerarExpressao(no.valor)}${sufixo}`, nivel, no);
        break;
      }

      case "Estrutura": {
        emitir(`class ${no.nome}:`, nivel, no);
        const params = no.campos.map(c => `${c.nome}=None`).join(", ");
        emitir(`def __init__(self${params ? ", " + params : ""}):`, nivel + 1);
        if (no.campos.length === 0) {
          emitir("pass", nivel + 2);
        } else {
          for (const c of no.campos) {
            emitir(`self.${c.nome} = ${c.nome}`, nivel + 2, c);
          }
        }
        emitir("", nivel);
        break;
      }

      case "Funcao": {
        const params = no.parametros.map(p => p.nome).join(", ");
        emitir(`def ${no.nome}(${params}):`, nivel, no);
        emitirBloco(no.corpo, nivel + 1);
        emitir("", nivel);
        break;
      }

      case "Task":
        emitir(`# survivor: roda como tarefa concorrente no alvo`, nivel, no);
        emitir(`def ${no.nome}():`, nivel, no);
        emitirBloco(no.corpo, nivel + 1);
        emitir("", nivel);
        break;

      case "Evento":
        emitir(`# ambush: disparado por evento no alvo`, nivel, no);
        emitir(`def ${no.nome}():`, nivel, no);
        emitirBloco(no.corpo, nivel + 1);
        emitir("", nivel);
        break;

      case "Principal":
        emitir("def main():", nivel, no);
        emitirBloco(no.corpo, nivel + 1);
        emitir("", nivel);
        break;

      case "Checkpoint":
        gerarCheckpoint(no, nivel, "if");
        break;

      case "Watch":
        emitir("while True:", nivel, no);
        emitirBloco(no.corpo, nivel + 1);
        break;

      case "Patrol":
        emitir(`for _ in range(${gerarExpressao(no.vezes)}):`, nivel, no);
        emitirBloco(no.corpo, nivel + 1);
        break;

      case "Quarantine":
        emitir("try:", nivel, no);
        emitirBloco(no.tentativa, nivel + 1);
        emitir(`except Exception as ${no.nomeErro}:`, nivel, no);
        emitirBloco(no.captura, nivel + 1);
        break;

      case "Outbreak":
        emitir(`raise Exception(${gerarExpressao(no.expressao)})`, nivel, no);
        break;

      case "Extract":
        emitir(no.expressao ? `return ${gerarExpressao(no.expressao)}` : "return",
               nivel, no);
        break;

      case "Atribuicao":
        emitir(`${no.nome} = ${gerarExpressao(no.valor)}`, nivel, no);
        break;

      case "ExpressaoStmt":
        emitir(gerarExpressao(no.expressao), nivel, no);
        break;

      default:
        emitir(`# nó não suportado: ${no.tipo}`, nivel, no);
    }
  }

  // "fallback checkpoint" encadeado vira elif; "fallback" com bloco vira else
  function gerarCheckpoint(no, nivel, palavra) {
    emitir(`${palavra} ${gerarExpressao(no.condicao)}:`, nivel, no);
    emitirBloco(no.entao, nivel + 1);

    if (no.outros === null || no.outros === undefined) return;

    if (Array.isArray(no.outros)) {
      emitir("else:", nivel);
      emitirBloco(no.outros, nivel + 1);
    } else {
      gerarCheckpoint(no.outros, nivel, "elif");
    }
  }

  // ------------------------------- montagem --------------------------------
  for (const linha of RUNTIME.split("\n")) linhas.push(linha);
  linhas.push("");
  linhas.push("");

  const declaracoes = ast && ast.declaracoes ? ast.declaracoes : [];
  for (const d of declaracoes) gerarDeclaracao(d, 0);

  const temPrincipal = declaracoes.some(d => d.tipo === "Principal");
  if (temPrincipal) {
    emitir('if __name__ == "__main__":');
    emitir("main()", 1);
  }

  // remove linhas em branco repetidas no fim, preservando o mapa
  while (linhas.length > 0 && linhas[linhas.length - 1].trim() === "") {
    linhas.pop();
  }

  return { corpo: linhas.join("\n") + "\n", mapa };
}

if (typeof module !== "undefined") {
  module.exports = { gerarCodigo, RUNTIME };
}
