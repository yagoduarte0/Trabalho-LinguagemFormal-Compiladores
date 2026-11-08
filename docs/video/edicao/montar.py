#!/usr/bin/env python3
"""Monta a linha do tempo do vídeo animado a partir da narração tratada.

Lê video/narracao/limpo/NN.wav e NN.json (saída do tratar_audio.sh) e gera,
dentro do projeto HyperFrames (docs/video/animacao/):

  assets/narracao/NN.wav     cópia dos áudios (fora do Git)
  assets/tempos.js           tempo de cada palavra, no relógio de cada cena
  compositions/legendas.html legendas queimadas, de 3 a 6 palavras por vez
  index.html                 as 14 cenas e os 14 áudios em sequência

As cenas (compositions/cNN.html) são escritas à mão e usam os tempos das
palavras para que cada elemento apareça quando a narração o cita.

Uso (na raiz do repositório):  python3 docs/video/edicao/montar.py
"""
import html
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
LIMPO = RAIZ / "video/narracao/limpo"
PROJETO = RAIZ / "docs/video/animacao"
MODELOS = RAIZ / "docs/video/edicao/modelos"   # fora do projeto: o HyperFrames leria como outra raiz

# (bloco, título da cena) na ordem do roteiro
BLOCOS = [
    ("01", "O problema"),
    ("02", "A linguagem"),
    ("03a", "Análise léxica e sintática"),
    ("03b", "Erros"),
    ("03c", "Geração de código"),
    ("04", "Do código à placa"),
    ("05a", "Os sensores"),
    ("05b", "Fumaça"),
    ("05c", "Painel web"),
    ("05d", "Telegram"),
    ("05e", "Deslizamento"),
    ("05f", "Digital"),
    ("06", "Protótipo real"),
    ("07", "Testes e encerramento"),
]

ANTES = 0.35   # silêncio antes da voz em cada cena (s)
DEPOIS = 0.45  # respiro depois da voz, antes da próxima cena (s)

# O que o Whisper ouviu errado: (bloco, palavras ouvidas, texto certo).
# As palavras ouvidas viram uma só, com o tempo da primeira à última.
CORRECOES = [
    ("01", ["iago"], "Yago"),
    ("01", ["aegis"], "AEGIS"),
    ("02", ["egis"], "AEGIS"),
    ("02", ["os", "cavens"], "scavenge"),
    ("02", ["chronicle"], "chronicle"),
    ("03a", ["javascript"], "JavaScript"),
    ("03a", ["ll1"], "LL(1)"),
    ("04", ["a", "edge"], "o AEGIS"),
    ("05e", ["acontece"], "antecede"),
    ("05f", ["desarme"], "desarma"),
    ("06", ["verdade"], "de verdade"),
    ("07", ["com", "os"], "Como"),
    ("07", ["aegis"], "AEGIS"),
]


def normalizar(texto):
    """minúsculas, sem acento e sem pontuação: 'Sobrevivência.' -> 'sobrevivencia'"""
    sem_acento = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", sem_acento.lower())


def duracao(arquivo):
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arquivo)],
        capture_output=True, text=True, check=True)
    return float(saida.stdout)


def palavras_do_whisper(arquivo):
    dados = json.loads(arquivo.read_text())
    palavras = []
    for seg in dados["transcription"]:
        texto = seg["text"].strip()
        if not texto or texto.startswith("["):
            continue
        palavras.append({"t": texto,
                         "s": seg["offsets"]["from"] / 1000,
                         "e": seg["offsets"]["to"] / 1000})
    return palavras


def corrigir(bloco, palavras):
    for alvo_bloco, ouvidas, certo in CORRECOES:
        if alvo_bloco != bloco:
            continue
        n = len(ouvidas)
        i = 0
        while i <= len(palavras) - n:
            janela = palavras[i:i + n]
            if [normalizar(p["t"]) for p in janela] == ouvidas:
                pontuacao = re.search(r"[.,;:!?]*$", janela[-1]["t"]).group(0)
                palavras[i:i + n] = [{"t": certo + pontuacao, "s": janela[0]["s"], "e": janela[-1]["e"]}]
            i += 1
    return palavras


def grupos_de_legenda(palavras):
    """3 a 6 palavras por grupo; quebra em fim de frase, vírgula ou pausa."""
    grupos, atual = [], []
    for i, p in enumerate(palavras):
        atual.append(p)
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        fim_frase = p["t"][-1] in ".!?"
        virgula = p["t"][-1] in ",;:"
        pausa = prox is not None and prox["s"] - p["e"] >= 0.25
        if (prox is None or fim_frase or len(atual) >= 6
                or (len(atual) >= 3 and (virgula or pausa))):
            grupos.append(atual)
            atual = []
    return grupos


def main():
    (PROJETO / "assets/narracao").mkdir(parents=True, exist_ok=True)
    (PROJETO / "compositions").mkdir(exist_ok=True)

    tempos = {}
    hosts, audios, legendas, roteiro_tl = [], [], [], []
    inicio = 0.0
    for indice, (bloco, titulo) in enumerate(BLOCOS):
        wav = LIMPO / f"{bloco}.wav"
        shutil.copyfile(wav, PROJETO / f"assets/narracao/{bloco}.wav")
        dur_voz = duracao(wav)
        slot = round(ANTES + dur_voz + DEPOIS, 2)
        palavras = corrigir(bloco, palavras_do_whisper(LIMPO / f"{bloco}.json"))

        # tempos no relógio da cena (0 = começo da cena)
        tempos[bloco] = {
            "titulo": titulo,
            "duracao": slot,
            "voz": round(ANTES, 2),
            "palavras": [{"t": p["t"], "s": round(ANTES + p["s"], 2), "e": round(ANTES + p["e"], 2)}
                         for p in palavras],
        }

        cid = f"c{bloco}"
        hosts.append(
            f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html"\n'
            f'        data-start="{inicio:.2f}" data-duration="{slot:.2f}" data-track-index="1"\n'
            f'        data-track-kind="graphics" data-width="1920" data-height="1080"></div>')
        audios.append(
            f'      <audio id="voz-{bloco}" class="clip" src="assets/narracao/{bloco}.wav"\n'
            f'        data-start="{inicio + ANTES:.2f}" data-duration="{dur_voz:.2f}" '
            f'data-track-index="2" data-volume="1"></audio>')

        # legendas no relógio do vídeo inteiro
        grupos = grupos_de_legenda(palavras)
        for g, grupo in enumerate(grupos):
            gid = f"leg-{bloco}-{g}"
            s = inicio + ANTES + grupo[0]["s"] - 0.05
            e = inicio + ANTES + grupo[-1]["e"] + 0.15
            if g + 1 < len(grupos):  # sai antes de o próximo grupo entrar
                e = min(e, inicio + ANTES + grupos[g + 1][0]["s"] - 0.06)
            spans = " ".join(
                f'<span class="pal" data-s="{inicio + ANTES + p["s"]:.2f}">{html.escape(p["t"])}</span>'
                for p in grupo)
            legendas.append(f'    <div id="{gid}" class="grupo" data-s="{s:.2f}" data-e="{e:.2f}">{spans}</div>')
        roteiro_tl.append((bloco, titulo, inicio, slot))
        inicio = round(inicio + slot, 2)

    total = inicio

    (PROJETO / "assets/tempos.js").write_text(
        "// gerado por docs/video/edicao/montar.py — não editar à mão\n"
        "window.AEGIS_TEMPOS = " + json.dumps(tempos, ensure_ascii=False, indent=1) + ";\n")

    modelo_legendas = (MODELOS / "legendas.html").read_text()
    (PROJETO / "compositions/legendas.html").write_text(
        modelo_legendas.replace("<!-- GRUPOS -->", "\n".join(legendas)))

    modelo_index = (MODELOS / "index.html").read_text()
    (PROJETO / "index.html").write_text(
        modelo_index
        .replace("{{DURACAO}}", f"{total:.2f}")
        .replace("/* TEMA */", (PROJETO / "assets/tema.css").read_text())
        .replace("<!-- CENAS -->", "\n".join(hosts))
        .replace("<!-- AUDIOS -->", "\n".join(audios)))

    for bloco, titulo, ini, slot in roteiro_tl:
        print(f"{bloco:4} {ini:7.2f} s  +{slot:5.2f} s  {titulo}")
    print(f"total: {total:.2f} s ({int(total // 60)} min {total % 60:.0f} s)")


if __name__ == "__main__":
    main()
