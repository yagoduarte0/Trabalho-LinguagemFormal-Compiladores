#!/bin/sh
# Trata a narração do vídeo: video/narracao/NN.m4a -> video/narracao/limpo/NN.wav
#
#   1. cola na frente do áudio 0,3 s do trecho mais silencioso do próprio
#      bloco, para o afftdn aprender o perfil do ruído antes da fala começar
#   2. corta graves abaixo de 90 Hz (ronco, batida na mesa) e agudos acima
#      de 12,5 kHz (chiado)
#   3. tira o ruído com o perfil aprendido (afftdn) e o resíduo com médias
#      não locais (anlmdn); o arnndn/RNNoise do ffmpeg 9 devolve NaN e não serve
#   4. gate suave nas pausas, menos "embolado" em 230 Hz, mais clareza em
#      4,5 kHz, de-esser e uma compressão leve
#   5. corta no mesmo ponto da primeira versão (tabela CORTES), para as
#      animações continuarem sincronizadas com os tempos do Whisper
#   6. ganho linear até -16 LUFS e limitador em -1,5 dBFS; nada de loudnorm
#      dinâmico, que subia o ruído das pausas
#
# Também gera a transcrição com o tempo de cada palavra (Whisper), usada para
# sincronizar as animações e as legendas: video/narracao/limpo/NN.json.
# Ela só é refeita se o .json não existir, ou com TRANSCREVER=1.
#
# Uso (na raiz do repositório):
#   sh docs/video/edicao/tratar_audio.sh                 # trata os 14 blocos
#   TRANSCREVER=1 sh docs/video/edicao/tratar_audio.sh   # e refaz as transcrições
#   TRANSCREVER=0 DESTINO=/tmp/x sh ...                   # só o áudio, em outra pasta
set -e
export LC_ALL=C

ORIGEM=video/narracao
DESTINO="${DESTINO:-video/narracao/limpo}"
TEMP="${TMPDIR:-/tmp}/aegis-audio.$$"
WHISPER_MODELO="$HOME/.cache/whisper-cpp/ggml-large-v3-turbo.bin"
VOCABULARIO="AEGIS, scavenge, law, supply, survivor, checkpoint, fallback, watch, patrol, mission, chronicle, Wokwi, ESP32, MicroPython, Telegram, maximal munch, LL(1), tokens"

# bloco  perfil(s)  início(s)  duração(s)
# perfil: onde fica o trecho de 0,3 s mais silencioso do original
# início/duração: medidos por correlação cruzada contra a primeira versão
# (a que gerou os .json). Bloco regravado: tirar a linha da tabela e rodar
# com TRANSCREVER=1; ele passa a usar o áudio inteiro e o perfil em 0 s
CORTES="
01    0.00  0.6678  27.2472
02   12.55  0.2102  38.5422
03a  27.85  0.0355  33.1702
03b  10.55  0.0110  11.4347
03c  10.10  0.0110  20.6507
04    2.45  0.1697  16.3106
05a  16.85  0.9260  16.1758
05b   2.60  0.7342  13.5463
05c  11.05  0.8971  10.2443
05d   8.65  0.0110  18.8754
05e   5.00  0.3852  12.9378
05f  14.75  0.0110  15.5307
06    2.65  0.0110  16.8107
07   17.10  0.1320  25.5643
"

# os dois aformat evitam quedas do ffmpeg 9 (segfault no anlmdn e "Format
# change is not supported" no corte)
LIMPEZA="highpass=f=90,lowpass=f=12500,\
asendcmd=c='0.0 afftdn sn start\; 0.3 afftdn sn stop',afftdn=nr=28:nf=-50,\
aformat=sample_fmts=fltp,anlmdn=s=0.0002,\
agate=threshold=0.004:ratio=3:range=0.12:attack=5:release=220,\
equalizer=f=230:t=q:w=1.2:g=-3,equalizer=f=4500:t=q:w=1.5:g=2,\
deesser=i=0.4,acompressor=threshold=0.1:ratio=2:attack=8:release=160,aformat=sample_fmts=flt"

mkdir -p "$DESTINO" "$TEMP"
trap 'rm -rf "$TEMP"' EXIT

for entrada in "$ORIGEM"/*.m4a; do
  nome=$(basename "$entrada" .m4a)
  saida="$DESTINO/$nome.wav"

  linha=$(echo "$CORTES" | awk -v n="$nome" '$1 == n')
  perfil=$(echo "$linha" | awk '{print $2}')
  inicio=$(echo "$linha" | awk '{print $3}')
  duracao=$(echo "$linha" | awk '{print $4}')
  : "${perfil:=0}" "${inicio:=0}"

  # 1. silêncio de 0,3 s + o bloco inteiro (o recorte sai num arquivo à parte:
  #    com -ss/-t no AAC ele não dá 0,3 s exatos, e juntar tudo num grafo só
  #    derruba o ffmpeg 9)
  ffmpeg -nostdin -hide_banner -loglevel error -y -i "$entrada" \
    -af "atrim=start=$perfil:duration=0.3" -ar 48000 -ac 1 -c:a pcm_f32le "$TEMP/perfil.wav"
  ffmpeg -nostdin -hide_banner -loglevel error -y -i "$TEMP/perfil.wav" -i "$entrada" \
    -filter_complex "[0:a][1:a]concat=v=0:a=1" \
    -ar 48000 -ac 1 -c:a pcm_f32le "$TEMP/pre.wav"

  # 2-5. limpeza e corte (o 0,3 s colado na frente sai aqui também)
  corte="atrim=start=$(awk -v i="$inicio" 'BEGIN{printf "%.4f", 0.3 + i}')"
  [ -n "$duracao" ] && corte="$corte:duration=$duracao"
  ffmpeg -nostdin -hide_banner -loglevel error -y -i "$TEMP/pre.wav" \
    -af "$LIMPEZA,$corte,asetpts=PTS-STARTPTS" -c:a pcm_f32le "$TEMP/limpo.wav"

  # 6. mede a sonoridade e aplica o ganho
  medido=$(ffmpeg -nostdin -hide_banner -nostats -i "$TEMP/limpo.wav" \
    -af loudnorm=I=-16:print_format=json -f null - 2>&1 \
    | grep '"input_i"' | sed 's/.*: "\(.*\)".*/\1/')
  # completa com silêncio até a duração da tabela (o montar.py usa a duração
  # para posicionar as cenas)
  completa=""
  [ -n "$duracao" ] && completa=",apad=whole_dur=$duracao,atrim=duration=$duracao"
  ganho=$(awk -v m="$medido" 'BEGIN{printf "%.2f", -16 - m}')
  ffmpeg -nostdin -hide_banner -loglevel error -y -i "$TEMP/limpo.wav" \
    -af "volume=${ganho}dB,alimiter=limit=0.84:attack=3:release=60:level=disabled$completa" \
    -ar 48000 -ac 1 -c:a pcm_s16le "$saida"

  # transcrição palavra a palavra (o Whisper pede 16 kHz)
  if [ "${TRANSCREVER:-}" = 1 ] || { [ "${TRANSCREVER:-}" != 0 ] && [ ! -f "$DESTINO/$nome.json" ]; }; then
    ffmpeg -nostdin -hide_banner -loglevel error -y -i "$saida" -ar 16000 -ac 1 "$TEMP/16k.wav"
    whisper-cli -m "$WHISPER_MODELO" -f "$TEMP/16k.wav" -l pt \
      --prompt "$VOCABULARIO" -ml 1 -sow -ojf -of "$DESTINO/$nome" >/dev/null 2>&1
  fi

  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$saida")
  printf '%-4s %6.2f s  ganho %+5.1f dB  %s\n' "$nome" "$dur" "$ganho" "$saida"
done
