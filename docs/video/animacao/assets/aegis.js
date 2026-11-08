// Ajudantes das cenas do vídeo do AEGIS.
//
// Tempo da narração (tempos de assets/tempos.js, já no relógio da cena):
//   AEGIS.w("02", "scavenge")       -> início da 1ª vez que "scavenge" é dita
//   AEGIS.w("05b", "base de ar", 1) -> início da expressão (palavras seguidas)
//   AEGIS.fim("02", "supply")       -> fim da palavra
//   A comparação ignora maiúsculas, acentos e pontuação, e cada palavra da
//   busca só precisa ser o começo da palavra dita ("sobreviv" acha
//   "sobrevivência").
//
// Câmera: cada cena desenha num "palco" maior que a tela; a câmera é a
// transformação do palco. AEGIS.camera(tl, "#palco", t, {x, y, s}) centraliza
// o ponto (x, y) do palco com zoom s.
//
// Movimento: AEGIS.letras / AEGIS.palavras quebram um texto em pedaços
// animáveis; AEGIS.placar faz um número rolar como placar; AEGIS.digitar
// revela uma linha de código como se fosse digitada.
(function () {
  const normalizar = (s) =>
    s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]/g, "");

  function achar(bloco, busca, n) {
    const cena = window.AEGIS_TEMPOS[bloco];
    if (!cena) throw new Error("AEGIS: bloco desconhecido " + bloco);
    const alvo = busca.split(/\s+/).map(normalizar);
    const ps = cena.palavras;
    let achadas = 0;
    for (let i = 0; i + alvo.length <= ps.length; i++) {
      const casa = alvo.every((a, k) => normalizar(ps[i + k].t).startsWith(a));
      if (casa && ++achadas === n) return [ps[i], ps[i + alvo.length - 1]];
    }
    throw new Error(`AEGIS: "${busca}" (${n}ª vez) não aparece na narração ${bloco}`);
  }

  // posição do palco que põe o ponto (x, y) no centro da tela com zoom s
  const enquadrar = ({ x, y, s = 1, r = 0 }) => ({ x: 960 - x * s, y: 540 - y * s, scale: s, rotation: r });

  function quebrar(el, separador, classe) {
    const alvo = typeof el === "string" ? document.querySelector(el) : el;
    const partes = alvo.textContent.split(separador);
    alvo.innerHTML = partes
      .map((p) => (p.trim() === "" ? p.replace(/ /g, "&nbsp;") : `<span class="${classe}" style="display:inline-block">${p}</span>`))
      .join(separador === "" ? "" : " ");
    return Array.from(alvo.querySelectorAll("." + classe));
  }

  window.AEGIS = {
    w: (bloco, busca, n = 1) => achar(bloco, busca, n)[0].s,
    fim: (bloco, busca, n = 1) => achar(bloco, busca, n)[1].e,
    dur: (bloco) => window.AEGIS_TEMPOS[bloco].duracao,

    // ---- câmera -------------------------------------------------------------
    cameraEm(tl, palco, t, quadro) {
      tl.set(palco, { transformOrigin: "0 0", ...enquadrar(quadro) }, t);
    },
    camera(tl, palco, t, quadro, dur = 0.9, ease = "power2.inOut") {
      tl.to(palco, { ...enquadrar(quadro), duration: dur, ease }, t);
    },
    // tremida curta (impacto), determinística
    tremer(tl, alvo, t, forca = 10, dur = 0.35) {
      const passos = 7;
      for (let i = 0; i < passos; i++) {
        const k = 1 - i / passos;
        tl.to(alvo, { x: (i % 2 ? -1 : 1) * forca * k, y: ((i * 7) % 3 - 1) * forca * 0.6 * k,
          duration: dur / passos, ease: "none" }, t + (i * dur) / passos);
      }
      tl.to(alvo, { x: 0, y: 0, duration: 0.05 }, t + dur);
    },

    // ---- texto --------------------------------------------------------------
    letras: (el) => quebrar(el, "", "letra"),
    palavras: (el) => quebrar(el, " ", "palavra"),

    // número que rola dígito a dígito até o valor final (texto, ex.: "8,27")
    placar(tl, el, t, final, dur = 1.3) {
      const alvo = typeof el === "string" ? document.querySelector(el) : el;
      alvo.innerHTML = "";
      const colunas = [];
      [...final].forEach((ch, i) => {
        if (!/\d/.test(ch)) {
          alvo.insertAdjacentHTML("beforeend", `<span style="display:inline-block">${ch}</span>`);
          return;
        }
        const d = Number(ch);
        const voltas = 2 + (i % 2);                      // dígitos vizinhos giram diferente
        const seq = [];
        for (let v = 0; v < voltas; v++) for (let k = 0; k < 10; k++) seq.push(k);
        for (let k = 0; k <= d; k++) seq.push(k);
        const janela = document.createElement("span");
        janela.style.cssText = "display:inline-block;height:1em;line-height:1;overflow:hidden;vertical-align:top";
        janela.innerHTML = `<span style="display:block">${seq.map((k) => `<span style="display:block;height:1em">${k}</span>`).join("")}</span>`;
        alvo.appendChild(janela);
        colunas.push([janela.firstChild, seq.length]);
      });
      colunas.forEach(([col, n], i) => {
        tl.fromTo(col, { yPercent: 0 }, { yPercent: -((n - 1) / n) * 100, duration: dur + i * 0.12, ease: "power3.out" }, t);
      });
    },

    // revela uma linha como digitação: clip da direita, em degraus por caractere
    digitar(tl, linha, t, dur) {
      const n = Math.max(1, linha.textContent.length);
      tl.fromTo(linha, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: dur, ease: `steps(${n})` }, t);
    },
  };
})();
