"""Corta o vídeo bruto do protótipo e limpa o áudio.

    python3 docs/video/edicao/prototipo_cortes.py

Entrada: video/fisico/bruto.mov (gravado no Photo Booth, fora do Git).
Saída:   docs/video/prototipo/assets/base.mp4 (os trechos escolhidos, já
         emendados, com a voz limpa) e docs/video/prototipo/assets/cortes.json
         (onde cada trecho começa no vídeo editado, para as animações).

Cada TRECHO é (início, fim, rótulo) em segundos do bruto. Dentro de cada
trecho, pausas de mais de PAUSA_MAX s viram PAUSA_FICA s (silencedetect).
"""

import json
import os
import subprocess
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BRUTO = os.path.join(RAIZ, "video", "fisico", "bruto.mov")
SAIDA = os.path.join(RAIZ, "docs", "video", "prototipo", "assets")

PAUSA_MAX = 0.7
PAUSA_FICA = 0.4

TRECHOS = [
    (0.0, 21.0, "abertura"),
    (23.0, 41.0, "abertura"),
    (41.0, 59.0, "rele"),
    (59.0, 80.0, "mq135"),
    (80.0, 91.0, "mq2"),
    (91.0, 122.0, "hcsr04"),
    (122.0, 171.0, "solo"),
    (171.0, 189.0, "chuva"),
    (189.0, 207.0, "pir"),
    (207.0, 212.0, "protoboard"),
    (212.0, 235.0, "oled"),
    (235.0, 257.0, "botao"),
    (257.0, 274.0, "dht22"),
    (274.0, 281.0, "leds"),
    (293.0, 311.0, "leds"),
    (317.0, 318.6, "leds"),
    (319.0, 332.0, "esp32"),
    (332.0, 337.0, "energia"),
    (339.0, 346.0, "energia"),
    (348.0, 353.0, "energia"),
    (357.0, 382.0, "energia"),
    (382.0, 441.0, "ligando"),
    (441.0, 479.0, "solo-agua"),
    (479.0, 495.0, "pir-demo"),
    (495.0, 568.0, "deslizamento"),
    (568.0, 600.0, "silenciar"),
    (600.0, 646.0, "normal"),
    (650.0, 677.0, "limites"),
    (740.0, 763.5, "fim"),
]

# o afftdn aprende o ruído do quarto nos primeiros 0,5 s (uma amostra de
# silêncio colada na frente e cortada no fim)
LIMPEZA = (
    "highpass=f=90,lowpass=f=12500,"
    "asendcmd=c='0.0 afftdn sn start; 0.5 afftdn sn stop',afftdn=nr=24:nf=-48,"
    "agate=threshold=0.012:ratio=2.5:range=0.25:attack=5:release=250,"
    "equalizer=f=230:t=q:w=1.2:g=-3,equalizer=f=4500:t=q:w=1.5:g=2,"
    "deesser=i=0.3,acompressor=threshold=0.1:ratio=2:attack=8:release=160"
)


def rodar(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


_ENVELOPE = []


def envelope():
    """Volume (dB) do bruto a cada 50 ms. O quarto tem um ruído de fundo
    forte (~-31 dB), então um limiar fixo de silêncio não serve: cada trecho
    usa o próprio piso de ruído."""
    if not _ENVELOPE:
        with tempfile.TemporaryDirectory() as tmp:
            arq = os.path.join(tmp, "rms.txt")
            rodar(["ffmpeg", "-y", "-i", BRUTO, "-vn", "-ac", "1", "-ar", "16000", "-af",
                   "aresample=16000,asetnsamples=n=800:p=0,astats=metadata=1:reset=1:measure_overall=RMS_level:"
                   "measure_perchannel=none,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=" + arq,
                   "-f", "null", "-"])
            for linha in open(arq):
                if "RMS_level" in linha:
                    v = linha.split("=")[1].strip()
                    _ENVELOPE.append(-120.0 if "inf" in v else float(v))
    return _ENVELOPE


def pausas(ini, fim):
    """Pausas longas (início, fim) dentro de um trecho, em segundos do bruto:
    trechos de mais de PAUSA_MAX s abaixo do piso de ruído + 3 dB (com +6 dB
    a fala mais baixa sumia junto)."""
    env = envelope()
    a, b = int(ini * 20), int(fim * 20)
    trecho = sorted(env[a:b])
    limiar = trecho[len(trecho) // 10] + 4
    lista, comeco = [], None
    for i in range(a, b):
        if env[i] < limiar:
            comeco = i if comeco is None else comeco
        else:
            if comeco is not None and (i - comeco) / 20 >= PAUSA_MAX:
                lista.append((comeco / 20, i / 20))
            comeco = None
    # a fala baixa às vezes fica abaixo do limiar: uma pausa que tem o começo
    # de uma palavra (Whisper) no meio não é pausa
    return lista


_PALAVRAS = []


def inicios_de_palavra():
    """Início de cada palavra do bruto, pela transcrição palavra a palavra do
    Whisper (video/fisico/trab/palavras.json)."""
    if not _PALAVRAS:
        arq = os.path.join(RAIZ, "video", "fisico", "trab", "palavras.json")
        for s in json.load(open(arq))["transcription"]:
            if s["text"].strip():
                _PALAVRAS.append(s["offsets"]["from"] / 1000)
    return _PALAVRAS


def pedacos():
    """Quebra cada trecho nas pausas longas, deixando PAUSA_FICA de respiro."""
    saida = []
    for ini, fim, rotulo in TRECHOS:
        cursor = ini
        for p0, p1 in pausas(ini, fim):
            meio = PAUSA_FICA / 2
            if p0 + meio > cursor + 0.2:
                saida.append((cursor, p0 + meio, rotulo))
            cursor = max(cursor, p1 - meio)
        if fim - cursor > 0.2:
            saida.append((cursor, fim, rotulo))
    return saida


def main():
    os.makedirs(SAIDA, exist_ok=True)
    lista = pedacos()
    with tempfile.TemporaryDirectory() as tmp:
        arquivos, cortes, t = [], [], 0.0
        for i, (a, b, rotulo) in enumerate(lista):
            arq = os.path.join(tmp, f"p{i:03d}.mp4")
            d = b - a
            # cada pedaço com um fade de 15 ms no som para a emenda não estalar
            rodar(["ffmpeg", "-y", "-ss", f"{a:.3f}", "-i", BRUTO, "-t", f"{d:.3f}",
                   "-vf", "fps=30,format=yuv420p",
                   "-af", f"afade=t=in:d=0.015,afade=t=out:st={max(0, d - 0.015):.3f}:d=0.015",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                   "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "1", arq])
            real = float(rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", arq]).stdout)
            cortes.append({"rotulo": rotulo, "bruto": [round(a, 3), round(b, 3)],
                           "inicio": round(t, 3), "duracao": round(real, 3)})
            t += real
            arquivos.append(arq)
        lista_txt = os.path.join(tmp, "lista.txt")
        with open(lista_txt, "w") as f:
            f.writelines(f"file '{a}'\n" for a in arquivos)
        emendado = os.path.join(tmp, "emendado.mkv")
        rodar(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista_txt, "-c", "copy", emendado])

        # voz: limpeza + ganho até -16 LUFS
        limpo = os.path.join(tmp, "limpo.wav")
        env = envelope()
        janela = 10  # 0,5 s
        quieto = min(range(0, int(640 * 20)), key=lambda i: sum(env[i:i + janela]))
        amostra = os.path.join(tmp, "ruido.wav")
        rodar(["ffmpeg", "-y", "-ss", f"{quieto / 20:.2f}", "-t", "0.5", "-i", BRUTO, "-vn",
               "-ar", "48000", "-ac", "1", "-c:a", "pcm_f32le", amostra])
        voz = os.path.join(tmp, "voz.wav")
        rodar(["ffmpeg", "-y", "-i", amostra, "-i", emendado, "-filter_complex",
               "[1:a]aresample=48000,aformat=sample_fmts=flt:channel_layouts=mono[v];[0:a]aformat=sample_fmts=flt:channel_layouts=mono[r];[r][v]concat=v=0:a=1",
               "-c:a", "pcm_f32le", voz])
        rodar(["ffmpeg", "-y", "-i", voz, "-af", LIMPEZA + ",atrim=start=0.5,asetpts=PTS-STARTPTS",
               "-ar", "48000", "-ac", "1", limpo])
        medida = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", limpo, "-af",
                                 "loudnorm=I=-16:print_format=json", "-f", "null", "-"],
                                capture_output=True, text=True).stderr
        entrada_i = float(medida.split('"input_i" : "')[1].split('"')[0])
        ganho = -16 - entrada_i
        rodar(["ffmpeg", "-y", "-i", emendado, "-i", limpo, "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-af", f"volume={ganho:.2f}dB,alimiter=limit=0.89:level=disabled",
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
               os.path.join(SAIDA, "base.mp4")])

    with open(os.path.join(SAIDA, "cortes.json"), "w") as f:
        json.dump({"duracao": round(t, 3), "cortes": cortes}, f, ensure_ascii=False, indent=1)
    print(f"{len(cortes)} pedaços, {t:.1f} s ({t / 60:.1f} min), ganho {ganho:+.1f} dB")


if __name__ == "__main__":
    main()
