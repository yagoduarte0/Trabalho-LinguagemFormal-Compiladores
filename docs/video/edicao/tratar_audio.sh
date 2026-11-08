#!/bin/sh
# Trata a narração do vídeo: video/narracao/NN.m4a -> video/narracao/limpo/NN.wav
#
#   1. corta os graves abaixo de 80 Hz (ronco, batida na mesa)
#   2. tira o ruído de fundo por FFT (afftdn; o arnndn/RNNoise do ffmpeg 9
#      devolve amostras NaN e não serve)
#   3. corta o silêncio do começo e do fim (deixa 0,25 s de folga)
#   4. normaliza a voz em -16 LUFS em duas passadas (EBU R128)
#
# Também gera a transcrição com o tempo de cada palavra (Whisper), usada
# para sincronizar as animações e as legendas: video/narracao/limpo/NN.json
#
# Uso (na raiz do repositório):  sh docs/video/edicao/tratar_audio.sh
set -e
export LC_ALL=C

ORIGEM=video/narracao
DESTINO=video/narracao/limpo
WHISPER_MODELO="$HOME/.cache/whisper-cpp/ggml-large-v3-turbo.bin"
VOCABULARIO="AEGIS, scavenge, law, supply, survivor, checkpoint, fallback, watch, patrol, mission, chronicle, Wokwi, ESP32, MicroPython, Telegram, maximal munch, LL(1), tokens"

mkdir -p "$DESTINO"

# limpeza sem a normalização; o silêncio é cortado no começo, a faixa é
# invertida, cortada de novo e desinvertida (assim corta também o fim)
LIMPEZA="highpass=f=80,afftdn=nr=12:nf=-50:tn=1,\
silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,\
areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse"

for entrada in "$ORIGEM"/*.m4a; do
  nome=$(basename "$entrada" .m4a)
  saida="$DESTINO/$nome.wav"

  # passada 1: mede a sonoridade
  medidas=$(ffmpeg -hide_banner -nostats -i "$entrada" \
    -af "$LIMPEZA,loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" \
    -f null - 2>&1 | sed -n '/^{/,/^}/p')
  valor() { echo "$medidas" | grep "\"$1\"" | sed 's/.*: "\(.*\)".*/\1/'; }

  # passada 2: aplica a normalização com as medidas
  ffmpeg -hide_banner -loglevel error -y -i "$entrada" \
    -af "$LIMPEZA,loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=$(valor input_i):\
measured_TP=$(valor input_tp):measured_LRA=$(valor input_lra):\
measured_thresh=$(valor input_thresh):offset=$(valor target_offset):linear=true" \
    -ar 48000 -ac 1 "$saida"

  # transcrição palavra a palavra (o Whisper pede 16 kHz)
  ffmpeg -hide_banner -loglevel error -y -i "$saida" -ar 16000 -ac 1 "$DESTINO/$nome.16k.wav"
  whisper-cli -m "$WHISPER_MODELO" -f "$DESTINO/$nome.16k.wav" -l pt \
    --prompt "$VOCABULARIO" -ml 1 -sow -ojf -of "$DESTINO/$nome" >/dev/null 2>&1
  rm "$DESTINO/$nome.16k.wav"

  duracao=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$saida")
  printf '%-4s %6.2f s  %s\n' "$nome" "$duracao" "$saida"
done
