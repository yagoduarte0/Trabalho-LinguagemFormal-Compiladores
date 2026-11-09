#!/bin/sh
# Monta artigo/figuras/sensores.jpg: uma grade 5 x 2 com a foto e o nome de
# cada módulo. Cada foto é recortada no objeto (fundo claro), centrada num
# quadro branco e ganha o rótulo embaixo. Créditos em CREDITOS.md.
#
# Uso (de qualquer pasta):  sh artigo/figuras/sensores/montar.sh
set -e
cd "$(dirname "$0")"
FONTE=/System/Library/Fonts/Supplemental/Arial.ttf
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
i=0
while IFS='|' read -r arq rotulo; do
  [ -z "$arq" ] && continue
  i=$((i+1))
  magick "$arq" -auto-orient -fuzz 12% -trim +repage -resize 460x300 \
    -background white -gravity center -extent 500x330 \
    \( -size 500x56 xc:white -font "$FONTE" -pointsize 27 -fill '#222' \
       -gravity center -annotate +0+0 "$rotulo" \) \
    -append "$T/$(printf %02d $i).png"
done <<'LISTA'
esp32.jpg|ESP32 DevKit V1
dht22.jpg|DHT22 (temperatura)
mq2.jpg|MQ-2 (fumaça e gás)
mq135.jpg|MQ-135 (qualidade do ar)
pir.jpg|PIR HC-SR501 (presença)
hcsr04.jpg|HC-SR04 (nível da água)
chuva.jpg|Sensor de chuva
solo.jpg|Umidade do solo v1.2
as608.jpg|AS608 (digital)
rele.jpg|Relé 5 V (exaustor)
LISTA
magick montage "$T"/*.png -tile 5x -geometry +8+8 -background white -quality 90 ../sensores.jpg
echo "gerado: artigo/figuras/sensores.jpg"
