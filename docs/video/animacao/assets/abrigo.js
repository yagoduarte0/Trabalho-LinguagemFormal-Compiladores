// Peças compartilhadas das cenas de hardware (04 a 06).
//
//   AEGIS.abrigo(px)   SVG do abrigo em corte (1800 x 1000), com os sete
//                      sensores, a central (ESP32, OLED, LEDs, buzzer) e os
//                      atuadores. Ids com o prefixo px: `${px}-pir`, ...
//   AEGIS.SENSORES     posição, nome e GPIO de cada peça (do abrigo.aeg)
//   AEGIS.celular(px, html)  moldura de celular com o conteúdo dado
//
// As posições estão no sistema do SVG; some a posição onde ele foi colocado
// no palco para achar o ponto no mundo da cena.
(function () {
  // pinos reais (firmware/abrigo.aeg, law PINO_*)
  const SENSORES = {
    pir:     { x: 1320, y: 352, nome: "presença", peca: "PIR", gpio: "GPIO 27" },
    agua:    { x: 1630, y: 372, nome: "nível da água", peca: "HC-SR04", gpio: "GPIO 25/26" },
    mq2:     { x: 950, y: 352, nome: "fumaça", peca: "MQ-2", gpio: "GPIO 34" },
    mq135:   { x: 560, y: 352, nome: "qualidade do ar", peca: "MQ-135", gpio: "GPIO 35" },
    dht:     { x: 700, y: 470, nome: "temperatura", peca: "DHT22", gpio: "GPIO 4" },
    chuva:   { x: 600, y: 206, nome: "chuva", peca: "sensor de chuva", gpio: "GPIO 36" },
    solo:    { x: 160, y: 770, nome: "umidade do solo", peca: "capacitivo", gpio: "GPIO 39" },
    digital: { x: 1222, y: 590, nome: "digital", peca: "AS608", gpio: "GPIO 16/17" },
    rele:    { x: 1080, y: 482, nome: "exaustor", peca: "relé", gpio: "GPIO 23" },
  };
  const ESP = { x: 520, y: 615 };

  function fio(px, id, a, b) {
    const mx = (a.x + b.x) / 2;
    return `<path id="${px}-fio-${id}" class="${px}-fio" d="M${a.x} ${a.y} C ${mx} ${a.y}, ${mx} ${b.y}, ${b.x} ${b.y}"
      fill="none" stroke="#A8D04A" stroke-width="2.5" stroke-dasharray="8 8" stroke-opacity="0.35"/>`;
  }

  function etiqueta(px, id, s, dx = 0, dy = -64) {
    const w = Math.max(s.peca.length, s.gpio.length) * 13 + 34;
    return `<g id="${px}-tag-${id}" class="${px}-tag" transform="translate(${s.x + dx} ${s.y + dy})">
      <rect x="${-w / 2}" y="-30" width="${w}" height="58" rx="6" fill="#0d110c" stroke="#A8D04A" stroke-width="2"/>
      <text y="-6" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" font-size="20" fill="#A8D04A">${s.peca}</text>
      <text y="18" text-anchor="middle" font-family="JetBrains Mono" font-size="16" fill="#C8B88A">${s.gpio}</text>
    </g>`;
  }

  function abrigo(px) {
    const S = SENSORES;
    const fios = Object.entries(S).map(([id, s]) => fio(px, id, ESP, s)).join("");
    const tags = [
      etiqueta(px, "pir", S.pir, 0, 74), etiqueta(px, "agua", S.agua, 30, -70), etiqueta(px, "mq2", S.mq2, 0, 74),
      etiqueta(px, "mq135", S.mq135, 0, -66), etiqueta(px, "dht", S.dht, 0, 76), etiqueta(px, "chuva", S.chuva, -40, -66),
      etiqueta(px, "solo", S.solo, 30, -86), etiqueta(px, "digital", S.digital, 0, -70), etiqueta(px, "rele", S.rele, 0, 66),
    ].join("");
    return `<svg id="${px}" viewBox="0 0 1800 1000" width="1800" height="1000" overflow="visible">
  <!-- chão e terreno -->
  <rect id="${px}-solo-area" x="0" y="780" width="300" height="220" fill="#2a2418"/>
  <rect x="300" y="780" width="1210" height="220" fill="#16130d"/>
  <rect x="1510" y="780" width="290" height="220" fill="#16130d"/>
  <path d="M0 830 H1800 M0 880 H1800 M0 940 H1800" stroke="#2e281c" stroke-width="2"/>
  <line x1="0" y1="780" x2="1800" y2="780" stroke="#C8B88A" stroke-width="3" stroke-opacity="0.5"/>
  <rect id="${px}-agua" x="1510" y="1000" width="290" height="0" fill="#3d7fa8" fill-opacity="0.55"/>

  <!-- casa em corte -->
  <path d="M300 780 V330 L900 110 L1500 330 V780" fill="#11160f" stroke="#C8B88A" stroke-width="5" stroke-linejoin="round"/>
  <path d="M760 330 V780 M1140 330 V780" stroke="#C8B88A" stroke-width="2" stroke-opacity="0.35"/>
  <text x="330" y="770" font-family="JetBrains Mono" font-size="18" letter-spacing="3" fill="#6f7a66">SALA</text>
  <text x="960" y="770" font-family="JetBrains Mono" font-size="18" letter-spacing="3" fill="#6f7a66">COZINHA</text>
  <text x="1170" y="770" font-family="JetBrains Mono" font-size="18" letter-spacing="3" fill="#6f7a66">ENTRADA</text>
  <rect id="${px}-porta" x="1390" y="600" width="74" height="180" fill="#0d110c" stroke="#C8B88A" stroke-width="3"/>
  <circle cx="1450" cy="696" r="5" fill="#C8B88A"/>
  <rect x="330" y="420" width="0" height="0"/>

  ${fios}

  <!-- central: OLED, ESP32, LEDs, buzzer -->
  <rect x="392" y="412" width="256" height="136" rx="6" fill="#050605" stroke="#C8B88A" stroke-width="3"/>
  <image id="${px}-oled" href="assets/img/oled-abertura.png" x="400" y="420" width="240" height="120" preserveAspectRatio="none"/>
  <rect id="${px}-esp" x="450" y="580" width="140" height="70" rx="5" fill="#1b2416" stroke="#A8D04A" stroke-width="3"/>
  <path d="M462 580 v-8 M478 580 v-8 M494 580 v-8 M510 580 v-8 M526 580 v-8 M542 580 v-8 M558 580 v-8 M574 580 v-8 M462 650 v8 M478 650 v8 M494 650 v8 M510 650 v8 M526 650 v8 M542 650 v8 M558 650 v8 M574 650 v8" stroke="#A8D04A" stroke-width="3"/>
  <text x="520" y="623" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" font-size="22" fill="#EDE4CC">ESP32</text>
  <circle id="${px}-pulso" cx="520" cy="615" r="40" fill="none" stroke="#A8D04A" stroke-width="3" opacity="0"/>
  <circle id="${px}-led-verde" cx="616" cy="592" r="9" fill="#2a3a1c" stroke="#A8D04A" stroke-width="2"/>
  <circle id="${px}-led-amar" cx="616" cy="616" r="9" fill="#3a3018" stroke="#F0B545" stroke-width="2"/>
  <circle id="${px}-led-verm" cx="616" cy="640" r="9" fill="#3a1c18" stroke="#EF5A4C" stroke-width="2"/>
  <circle id="${px}-buzzer" cx="420" cy="615" r="17" fill="#1a1a1a" stroke="#C8B88A" stroke-width="3"/>
  <g id="${px}-ondas" opacity="0" fill="none" stroke-width="4" stroke-linecap="round">
    <path id="${px}-onda1" d="M392 590 a40 40 0 0 0 0 50" stroke="#EF5A4C"/>
    <path id="${px}-onda2" d="M374 575 a62 62 0 0 0 0 80" stroke="#F0B545"/>
    <path id="${px}-onda3" d="M356 562 a84 84 0 0 0 0 106" stroke="#EF5A4C"/>
  </g>

  <!-- sala: DHT22 e MQ-135 -->
  <rect x="684" y="446" width="32" height="48" rx="4" fill="#e8e4d8"/>
  <path d="M690 456 h20 M690 466 h20 M690 476 h20 M690 486 h20" stroke="#9aa08a" stroke-width="3"/>
  <circle cx="560" cy="345" r="20" fill="#5a6a4a" stroke="#C8B88A" stroke-width="3"/>
  <circle cx="560" cy="345" r="9" fill="#2a3220"/>

  <!-- cozinha: MQ-2, fogão, exaustor no relé -->
  <circle cx="950" cy="345" r="20" fill="#5a6a4a" stroke="#C8B88A" stroke-width="3"/>
  <circle cx="950" cy="345" r="9" fill="#2a3220"/>
  <rect x="810" y="700" width="120" height="80" fill="#1a1d17" stroke="#C8B88A" stroke-width="3"/>
  <rect x="822" y="690" width="96" height="10" fill="#C8B88A"/>
  <circle cx="1080" cy="410" r="40" fill="#0d110c" stroke="#C8B88A" stroke-width="3"/>
  <g id="${px}-helice"><path d="M1080 410 L1080 376 Q1094 392 1080 410 L1114 410 Q1098 424 1080 410 L1080 444 Q1066 428 1080 410 L1046 410 Q1062 396 1080 410 Z" fill="#9aa08a"/></g>
  <rect id="${px}-rele" x="1058" y="468" width="44" height="28" rx="3" fill="#1b3a5a" stroke="#C8B88A" stroke-width="2"/>
  <g id="${px}-fumaca" opacity="0">
    <circle cx="850" cy="660" r="22" fill="#9aa08a" fill-opacity="0.35"/><circle cx="880" cy="620" r="30" fill="#9aa08a" fill-opacity="0.3"/>
    <circle cx="900" cy="560" r="36" fill="#9aa08a" fill-opacity="0.28"/><circle cx="930" cy="490" r="42" fill="#9aa08a" fill-opacity="0.25"/>
    <circle cx="945" cy="420" r="40" fill="#9aa08a" fill-opacity="0.22"/><circle cx="860" cy="520" r="30" fill="#9aa08a" fill-opacity="0.2"/>
  </g>

  <!-- entrada: PIR, digital -->
  <polygon id="${px}-cone" points="1320,360 1170,780 1470,780" fill="#A8D04A" fill-opacity="0.07"/>
  <path d="M1296 340 h48 a24 24 0 0 1 -48 0 Z" fill="#e8e4d8" stroke="#C8B88A" stroke-width="2"/>
  <rect id="${px}-digital" x="1200" y="560" width="44" height="62" rx="6" fill="#1a1d17" stroke="#C8B88A" stroke-width="3"/>
  <g fill="none" stroke="#A8D04A" stroke-width="2" stroke-opacity="0.8">
    <path d="M1212 600 q10 -26 20 0"/><path d="M1208 604 q14 -36 28 0"/><path d="M1216 598 q6 -14 12 0"/>
  </g>

  <!-- fora: chuva no telhado, solo, nível da água -->
  <g transform="rotate(-20 600 206)"><rect x="560" y="196" width="80" height="18" rx="2" fill="#2c4a2a" stroke="#C8B88A" stroke-width="2"/>
    <path d="M568 205 h64" stroke="#C8B88A" stroke-dasharray="4 4" stroke-width="2"/></g>
  <path d="M150 740 V850 M170 740 V850" stroke="#C8B88A" stroke-width="5"/>
  <rect x="140" y="720" width="40" height="24" rx="3" fill="#1a1d17" stroke="#C8B88A" stroke-width="2"/>
  <path d="M1500 360 H1610" stroke="#C8B88A" stroke-width="4"/>
  <rect x="1596" y="356" width="70" height="28" rx="3" fill="#1b3a5a" stroke="#C8B88A" stroke-width="2"/>
  <circle cx="1612" cy="388" r="9" fill="#c8c8c8"/><circle cx="1650" cy="388" r="9" fill="#c8c8c8"/>
  <g id="${px}-eco" opacity="0" fill="none" stroke="#9fd1c9" stroke-width="3">
    <path d="M1600 430 q31 14 62 0"/><path d="M1594 480 q37 16 74 0"/><path d="M1588 530 q43 18 86 0"/>
  </g>

  ${tags}
</svg>`;
  }

  function celular(px, html) {
    return `<div id="${px}" style="position:absolute;width:420px;height:860px;border-radius:56px;background:#050605;
        border:3px solid #C8B88A;box-shadow:0 30px 80px rgba(0,0,0,0.6)">
      <div style="position:absolute;left:18px;top:18px;right:18px;bottom:18px;border-radius:40px;overflow:hidden;background:#0a0d0a">${html}</div>
      <div style="position:absolute;left:160px;top:28px;width:100px;height:26px;border-radius:14px;background:#050605;z-index:3"></div>
    </div>`;
  }

  Object.assign(window.AEGIS, { abrigo, celular, SENSORES, ESP });
})();
