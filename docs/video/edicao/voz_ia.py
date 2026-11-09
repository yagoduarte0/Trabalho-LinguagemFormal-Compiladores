#!/usr/bin/env python3
"""Gera a narração com voz de IA (vozes neurais da Microsoft, via edge-tts).

Lê o texto de cada bloco da transcrição da narração gravada (já com as
CORRECOES do montar.py), sintetiza a mesma fala e grava, em outra pasta:
  NN.wav   a voz, tratada como a gravada (48 kHz, mono, -16 LUFS)
  NN.json  o tempo de cada palavra, no mesmo formato do Whisper

Como as palavras são as mesmas, as cenas (que se prendem a palavras, não a
segundos) se ressincronizam sozinhas; basta rodar o montar.py apontando para
a pasta nova. O texto vai para o serviço de voz da Microsoft.

Uso (na raiz do repositório):
  video/.venv/bin/python docs/video/edicao/voz_ia.py                  # 14 blocos
  video/.venv/bin/python docs/video/edicao/voz_ia.py --voz pt-BR-AntonioNeural --blocos 02 05a
  video/.venv/bin/edge-tts --list-voices | grep pt-BR                 # vozes disponíveis
"""
import argparse
import asyncio
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

import edge_tts

sys.path.insert(0, str(Path(__file__).resolve().parent))
import montar  # noqa: E402

# como a voz deve ler (as legendas continuam com a grafia original)
PRONUNCIA = {"AEGIS": "Égis", "LL(1)": "L L 1", "ESP32": "E S P 32",
             "chronicle": "crónicol"}   # sem isso a voz lê "crônico"


def texto_falado(palavras):
    """Uma lista de (fala, dono): cada palavra exibida vira um ou mais tokens
    falados; 'dono' é o índice da palavra exibida."""
    tokens = []
    for i, p in enumerate(palavras):
        base, pont = re.match(r"^(.*?)([.,;:!?]*)$", p["t"]).groups()
        prox = palavras[i + 1] if i + 1 < len(palavras) else None
        if not pont and (prox is None or montar.frase_nova(prox)):
            pont = "."   # ponto que faltou na transcrição: a entonação fecha a frase
        partes = (PRONUNCIA.get(base, base) + pont).split()
        tokens += [(parte, i) for parte in partes]
    return tokens


async def sintetizar(texto, voz, mp3, velocidade):
    com = edge_tts.Communicate(texto, voz, rate=velocidade, boundary="WordBoundary")
    marcas = []
    with open(mp3, "wb") as f:
        async for c in com.stream():
            if c["type"] == "audio":
                f.write(c["data"])
            elif c["type"] == "WordBoundary":
                ini = c["offset"] / 1e7
                marcas.append((ini, ini + c["duration"] / 1e7, c["text"]))
    return marcas


def alinhar(palavras, tokens, marcas):
    """Tempo de cada palavra exibida a partir das marcas da voz."""
    nossos = [montar.normalizar(t) for t, _ in tokens]
    delas = [montar.normalizar(m[2]) for m in marcas]
    tempo_tok = [None] * len(tokens)
    sm = difflib.SequenceMatcher(None, nossos, delas, autojunk=False)
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            for k in range(a1 - a0):
                tempo_tok[a0 + k] = marcas[b0 + k][:2]
        elif op == "replace":   # ex.: "1.600" lido como "mil e seiscentos"
            s, e = marcas[b0][0], marcas[b1 - 1][1]
            n = a1 - a0
            for k in range(n):
                tempo_tok[a0 + k] = (s + (e - s) * k / n, s + (e - s) * (k + 1) / n)
    tempos = [None] * len(palavras)
    for (t, dono), tt in zip(tokens, tempo_tok):
        if tt is None:
            continue
        s, e = tt
        if tempos[dono] is None:
            tempos[dono] = [s, e]
        else:
            tempos[dono] = [min(tempos[dono][0], s), max(tempos[dono][1], e)]
    # palavra sem marca: entre a anterior e a seguinte
    for i, tp in enumerate(tempos):
        if tp is None:
            ant = next((tempos[j][1] for j in range(i - 1, -1, -1) if tempos[j]), 0.0)
            seg = next((tempos[j][0] for j in range(i + 1, len(tempos)) if tempos[j]), ant + 0.3)
            tempos[i] = [ant, max(ant + 0.05, seg)]
    return tempos


def tratar_audio(mp3, wav):
    """mp3 -> wav 48 kHz mono, ganho linear até -16 LUFS e limitador (como a voz gravada)."""
    medido = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", str(mp3),
         "-af", "loudnorm=I=-16:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    entrada = float(re.search(r'"input_i"\s*:\s*"([-\d.]+)"', medido).group(1))
    subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp3),
         "-af", f"volume={-16 - entrada:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=disabled",
         "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)], check=True)


async def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voz", default="pt-BR-AntonioNeural")
    ap.add_argument("--velocidade", default="+0%", help='ex.: "+5%%", "-5%%"')
    ap.add_argument("--blocos", nargs="*", help="só estes blocos (padrão: todos)")
    ap.add_argument("--saida", default=str(montar.RAIZ / "video/narracao/ia"))
    args = ap.parse_args()
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)

    for bloco, _ in montar.BLOCOS:
        if args.blocos and bloco not in args.blocos:
            continue
        palavras = montar.corrigir(bloco, montar.palavras_do_whisper(montar.LIMPO / f"{bloco}.json"))
        tokens = texto_falado(palavras)
        texto = " ".join(t for t, _ in tokens)
        mp3 = saida / f"{bloco}.mp3"
        marcas = await sintetizar(texto, args.voz, mp3, args.velocidade)
        tratar_audio(mp3, saida / f"{bloco}.wav")
        mp3.unlink()
        tempos = alinhar(palavras, tokens, marcas)
        segs = [{"text": " " + p["t"], "offsets": {"from": round(s * 1000), "to": round(e * 1000)}}
                for p, (s, e) in zip(palavras, tempos)]
        (saida / f"{bloco}.json").write_text(json.dumps({"voz": args.voz, "transcription": segs},
                                                        ensure_ascii=False, indent=1))
        sem = sum(1 for m in marcas) - len(tokens)
        print(f"{bloco:4} {len(palavras):3} palavras  {len(marcas):3} marcas  fim {tempos[-1][1]:6.2f} s")


if __name__ == "__main__":
    asyncio.run(principal())
